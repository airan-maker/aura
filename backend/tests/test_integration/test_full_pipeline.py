"""
Integration tests for full analysis pipeline
"""

import pytest
import asyncio
from app.services.orchestrator import AnalysisOrchestrator
from app.models.analysis import AnalysisRequest, AnalysisStatus
from app.database import AsyncSessionLocal
import uuid


@pytest.mark.asyncio
async def test_full_pipeline_example_com():
    """Test complete analysis pipeline with example.com"""

    # Create request
    async with AsyncSessionLocal() as db:
        request = AnalysisRequest(
            url="https://example.com",
            status=AnalysisStatus.PENDING,
            progress=0
        )
        db.add(request)
        await db.commit()
        await db.refresh(request)
        request_id = str(request.id)

    # Run orchestrator
    orchestrator = AnalysisOrchestrator()
    result = await orchestrator.run_analysis(request_id)

    # Verify results
    assert result is not None
    assert result['seo_score'] > 0
    assert result['seo_score'] <= 100
    assert result['aeo_score'] > 0
    assert result['aeo_score'] <= 100

    # Verify SEO metrics
    assert 'seo_metrics' in result
    assert 'meta_tags' in result['seo_metrics']
    assert 'headings' in result['seo_metrics']
    assert 'performance' in result['seo_metrics']

    # Verify AEO metrics
    assert 'aeo_metrics' in result
    assert 'what_it_does' in result['aeo_metrics']
    assert 'clarity_score' in result['aeo_metrics']

    # Verify recommendations
    assert 'recommendations' in result
    assert len(result['recommendations']) > 0

    # Check request status
    async with AsyncSessionLocal() as db:
        from sqlalchemy import select
        stmt = select(AnalysisRequest).where(AnalysisRequest.id == uuid.UUID(request_id))
        result_req = await db.execute(stmt)
        updated_request = result_req.scalar_one()

        assert updated_request.status == AnalysisStatus.COMPLETED
        assert updated_request.progress == 100
        assert updated_request.completed_at is not None


@pytest.mark.asyncio
async def test_pipeline_with_invalid_url():
    """Test pipeline with invalid URL"""

    async with AsyncSessionLocal() as db:
        request = AnalysisRequest(
            url="https://this-domain-definitely-does-not-exist-12345678.com",
            status=AnalysisStatus.PENDING,
            progress=0
        )
        db.add(request)
        await db.commit()
        await db.refresh(request)
        request_id = str(request.id)

    # Run orchestrator - should fail gracefully
    orchestrator = AnalysisOrchestrator()
    result = await orchestrator.run_analysis(request_id)

    # Should return None on error
    assert result is None

    # Check request status is FAILED
    async with AsyncSessionLocal() as db:
        from sqlalchemy import select
        stmt = select(AnalysisRequest).where(AnalysisRequest.id == uuid.UUID(request_id))
        result_req = await db.execute(stmt)
        updated_request = result_req.scalar_one()

        assert updated_request.status == AnalysisStatus.FAILED
        assert updated_request.error_message is not None


@pytest.mark.asyncio
async def test_pipeline_progress_updates():
    """Test that progress is updated correctly throughout pipeline"""

    async with AsyncSessionLocal() as db:
        request = AnalysisRequest(
            url="https://example.com",
            status=AnalysisStatus.PENDING,
            progress=0
        )
        db.add(request)
        await db.commit()
        await db.refresh(request)
        request_id = str(request.id)

    progress_updates = []

    async def progress_callback(req_id, progress, step):
        progress_updates.append({
            'progress': progress,
            'step': step
        })

    orchestrator = AnalysisOrchestrator()
    orchestrator.progress_callback = progress_callback

    await orchestrator.run_analysis(request_id)

    # Verify progress updates occurred
    assert len(progress_updates) > 0

    # Verify progress increased monotonically
    prev_progress = -1
    for update in progress_updates:
        assert update['progress'] >= prev_progress
        prev_progress = update['progress']

    # Verify final progress is 100
    assert progress_updates[-1]['progress'] == 100


@pytest.mark.asyncio
async def test_concurrent_analyses():
    """Test running multiple analyses concurrently"""

    urls = [
        "https://example.com",
        "https://www.ietf.org",
        "https://www.w3.org"
    ]

    request_ids = []

    # Create requests
    async with AsyncSessionLocal() as db:
        for url in urls:
            request = AnalysisRequest(
                url=url,
                status=AnalysisStatus.PENDING,
                progress=0
            )
            db.add(request)
            await db.commit()
            await db.refresh(request)
            request_ids.append(str(request.id))

    # Run analyses concurrently
    orchestrator = AnalysisOrchestrator()
    tasks = [orchestrator.run_analysis(req_id) for req_id in request_ids]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Verify all completed successfully
    for result in results:
        if isinstance(result, Exception):
            pytest.fail(f"Analysis failed with exception: {result}")
        assert result is not None
        assert 'seo_score' in result
        assert 'aeo_score' in result


@pytest.mark.asyncio
async def test_analysis_duration_tracking():
    """Test that analysis duration is tracked correctly"""

    async with AsyncSessionLocal() as db:
        request = AnalysisRequest(
            url="https://example.com",
            status=AnalysisStatus.PENDING,
            progress=0
        )
        db.add(request)
        await db.commit()
        await db.refresh(request)
        request_id = str(request.id)

    orchestrator = AnalysisOrchestrator()
    result = await orchestrator.run_analysis(request_id)

    # Verify duration is tracked
    assert result is not None
    assert 'analysis_duration' in result
    assert result['analysis_duration'] > 0
    assert result['analysis_duration'] < 300  # Should complete within 5 minutes


@pytest.mark.asyncio
async def test_screenshot_capture():
    """Test that screenshots are captured and saved"""

    async with AsyncSessionLocal() as db:
        request = AnalysisRequest(
            url="https://example.com",
            status=AnalysisStatus.PENDING,
            progress=0
        )
        db.add(request)
        await db.commit()
        await db.refresh(request)
        request_id = str(request.id)

    orchestrator = AnalysisOrchestrator()
    result = await orchestrator.run_analysis(request_id)

    # Verify screenshot path is saved
    from sqlalchemy import select
    from app.models.analysis import AnalysisResult

    async with AsyncSessionLocal() as db:
        stmt = select(AnalysisResult).where(AnalysisResult.request_id == uuid.UUID(request_id))
        result_obj = await db.execute(stmt)
        analysis_result = result_obj.scalar_one()

        assert analysis_result.screenshot_path is not None
        assert len(analysis_result.screenshot_path) > 0

        # Verify screenshot file exists
        import os
        assert os.path.exists(analysis_result.screenshot_path)
