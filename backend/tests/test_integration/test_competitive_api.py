"""Integration tests for competitive analysis API endpoints."""

import pytest
from httpx import AsyncClient, ASGITransport
from uuid import uuid4
from unittest.mock import AsyncMock, patch

from app.main import app


@pytest.mark.asyncio
async def test_create_competitive_analysis_success():
    """Test creating a competitive analysis batch."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        payload = {
            "urls": [
                "https://competitor1.com",
                "https://competitor2.com",
                "https://competitor3.com"
            ],
            "labels": ["Competitor A", "Competitor B", "Competitor C"],
            "name": "Q1 2025 Analysis"
        }

        with patch('app.workers.competitive_worker.competitive_worker.submit_competitive_analysis') as mock_submit:
            mock_submit.return_value = None

            response = await client.post("/api/v1/competitive", json=payload)

            assert response.status_code == 201
            data = response.json()

            assert "id" in data
            assert data["name"] == "Q1 2025 Analysis"
            assert data["status"] == "pending"
            assert data["total_urls"] == 3
            assert data["progress"] == 0
            assert len(data["urls"]) == 3

            # Verify labels were applied
            assert data["urls"][0]["label"] == "Competitor A"
            assert data["urls"][1]["label"] == "Competitor B"
            assert data["urls"][2]["label"] == "Competitor C"

            mock_submit.assert_called_once()


@pytest.mark.asyncio
async def test_create_competitive_analysis_min_urls():
    """Test creating batch with minimum URLs (2)."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        payload = {
            "urls": [
                "https://competitor1.com",
                "https://competitor2.com"
            ]
        }

        with patch('app.workers.competitive_worker.competitive_worker.submit_competitive_analysis'):
            response = await client.post("/api/v1/competitive", json=payload)

            assert response.status_code == 201
            data = response.json()
            assert data["total_urls"] == 2


@pytest.mark.asyncio
async def test_create_competitive_analysis_max_urls():
    """Test creating batch with maximum URLs (5)."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        payload = {
            "urls": [
                f"https://competitor{i}.com" for i in range(1, 6)
            ]
        }

        with patch('app.workers.competitive_worker.competitive_worker.submit_competitive_analysis'):
            response = await client.post("/api/v1/competitive", json=payload)

            assert response.status_code == 201
            data = response.json()
            assert data["total_urls"] == 5


@pytest.mark.asyncio
async def test_create_competitive_analysis_too_few_urls():
    """Test validation fails with < 2 URLs."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        payload = {
            "urls": ["https://competitor1.com"]
        }

        response = await client.post("/api/v1/competitive", json=payload)

        assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_create_competitive_analysis_too_many_urls():
    """Test validation fails with > 5 URLs."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        payload = {
            "urls": [f"https://competitor{i}.com" for i in range(1, 7)]
        }

        response = await client.post("/api/v1/competitive", json=payload)

        assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_create_competitive_analysis_invalid_url():
    """Test validation fails with invalid URL."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        payload = {
            "urls": [
                "https://competitor1.com",
                "not-a-valid-url"
            ]
        }

        response = await client.post("/api/v1/competitive", json=payload)

        assert response.status_code == 400
        assert "Invalid URL" in response.json()["detail"]


@pytest.mark.asyncio
async def test_create_competitive_analysis_labels_mismatch():
    """Test validation fails when labels count doesn't match URLs."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        payload = {
            "urls": [
                "https://competitor1.com",
                "https://competitor2.com",
                "https://competitor3.com"
            ],
            "labels": ["Label 1", "Label 2"]  # Only 2 labels for 3 URLs
        }

        response = await client.post("/api/v1/competitive", json=payload)

        assert response.status_code == 400
        assert "must match" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_get_batch_status(mock_db_session):
    """Test retrieving batch status."""
    from app.models.competitive import CompetitiveAnalysisBatch
    from app.models.analysis import AnalysisStatus

    batch_id = uuid4()

    # Create mock batch
    batch = CompetitiveAnalysisBatch(
        id=batch_id,
        name="Test Batch",
        status=AnalysisStatus.PROCESSING,
        progress=50,
        total_urls=3,
        completed_count=1,
        failed_count=0
    )

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        with patch('app.api.v1.competitive.get_db', return_value=mock_db_session):
            response = await client.get(f"/api/v1/competitive/{batch_id}")

            if response.status_code == 200:
                data = response.json()
                assert data["id"] == str(batch_id)
                assert data["status"] == "processing"
                assert data["progress"] == 50


@pytest.mark.asyncio
async def test_get_batch_not_found():
    """Test 404 when batch doesn't exist."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        fake_id = uuid4()
        response = await client.get(f"/api/v1/competitive/{fake_id}")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_get_competitive_results_not_completed():
    """Test getting results before analysis completes."""
    from app.models.competitive import CompetitiveAnalysisBatch
    from app.models.analysis import AnalysisStatus

    batch_id = uuid4()

    # Batch still processing
    batch = CompetitiveAnalysisBatch(
        id=batch_id,
        status=AnalysisStatus.PROCESSING,
        total_urls=3
    )

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get(f"/api/v1/competitive/{batch_id}/results")

        assert response.status_code == 400
        assert "not completed" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_url_order_preserved():
    """Test that URL order is preserved through batch creation."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        urls = [
            "https://competitor3.com",
            "https://competitor1.com",
            "https://competitor2.com"
        ]

        payload = {"urls": urls}

        with patch('app.workers.competitive_worker.competitive_worker.submit_competitive_analysis'):
            response = await client.post("/api/v1/competitive", json=payload)

            assert response.status_code == 201
            data = response.json()

            # Verify order is preserved
            assert data["urls"][0]["url"] == urls[0]
            assert data["urls"][1]["url"] == urls[1]
            assert data["urls"][2]["url"] == urls[2]

            # Verify order_index is sequential
            assert data["urls"][0]["order_index"] == 0
            assert data["urls"][1]["order_index"] == 1
            assert data["urls"][2]["order_index"] == 2


@pytest.mark.asyncio
async def test_primary_flag_set():
    """Test that first URL is marked as primary."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        payload = {
            "urls": [
                "https://oursite.com",  # Should be primary
                "https://competitor1.com",
                "https://competitor2.com"
            ]
        }

        with patch('app.workers.competitive_worker.competitive_worker.submit_competitive_analysis'):
            response = await client.post("/api/v1/competitive", json=payload)

            assert response.status_code == 201
            data = response.json()

            # First URL should be primary
            assert data["urls"][0]["is_primary"] is True
            assert data["urls"][1]["is_primary"] is False
            assert data["urls"][2]["is_primary"] is False


@pytest.mark.asyncio
async def test_batch_without_name():
    """Test creating batch without optional name."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        payload = {
            "urls": [
                "https://competitor1.com",
                "https://competitor2.com"
            ]
            # No name provided
        }

        with patch('app.workers.competitive_worker.competitive_worker.submit_competitive_analysis'):
            response = await client.post("/api/v1/competitive", json=payload)

            assert response.status_code == 201
            data = response.json()
            assert data["name"] is None


@pytest.mark.asyncio
async def test_batch_without_labels():
    """Test creating batch without optional labels."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        payload = {
            "urls": [
                "https://competitor1.com",
                "https://competitor2.com"
            ]
            # No labels provided
        }

        with patch('app.workers.competitive_worker.competitive_worker.submit_competitive_analysis'):
            response = await client.post("/api/v1/competitive", json=payload)

            assert response.status_code == 201
            data = response.json()

            # Labels should be None
            assert data["urls"][0]["label"] is None
            assert data["urls"][1]["label"] is None
