"""Pytest configuration and shared fixtures."""

import os
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

# Add backend directory to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Set test environment variables before any imports
# Use SQLite for testing (no need for PostgreSQL server)
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("OPENAI_API_KEY", "test-key-12345")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-testing-only")
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("ALLOWED_ORIGINS", '["http://localhost:3000"]')
os.environ.setdefault("CRAWLER_TIMEOUT", "30000")
os.environ.setdefault("MAX_CONCURRENT_ANALYSES", "3")

# Import after setting environment variables
from app.database import Base


# Configure pytest-asyncio
def pytest_configure(config):
    """Configure pytest settings."""
    config.addinivalue_line(
        "markers", "asyncio: mark test as an asyncio test"
    )


@pytest.fixture(scope="session")
def anyio_backend():
    """Configure anyio backend for async tests."""
    return "asyncio"


@pytest.fixture
async def test_db_engine():
    """Create a test database engine."""
    # Use in-memory SQLite for fast tests
    # Note: SQLite doesn't support all PostgreSQL features, but works for basic tests
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        poolclass=NullPool,
        echo=False,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
async def test_db_session(test_db_engine):
    """Create a test database session."""
    async_session = async_sessionmaker(
        test_db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session() as session:
        yield session
        await session.rollback()


@pytest.fixture
def mock_db_session():
    """Create a mock database session for unit tests."""
    session = AsyncMock(spec=AsyncSession)
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.refresh = AsyncMock()
    session.close = AsyncMock()
    session.execute = AsyncMock()
    session.add = MagicMock()
    return session


@pytest.fixture
def mock_openai_client():
    """Create a mock OpenAI client."""
    client = MagicMock()

    # Mock chat completion response
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = '{"insights": "test insights", "opportunities": [], "threats": []}'

    client.chat.completions.create = AsyncMock(return_value=mock_response)

    return client


@pytest.fixture
def mock_playwright():
    """Create a mock Playwright instance."""
    playwright = MagicMock()
    browser = MagicMock()
    context = MagicMock()
    page = MagicMock()

    # Set up the mock chain
    playwright.chromium.launch = AsyncMock(return_value=browser)
    browser.new_context = AsyncMock(return_value=context)
    context.new_page = AsyncMock(return_value=page)
    page.goto = AsyncMock()
    page.content = AsyncMock(return_value="<html><body>Test content</body></html>")
    page.close = AsyncMock()
    context.close = AsyncMock()
    browser.close = AsyncMock()

    return playwright


@pytest.fixture(autouse=True)
def reset_singletons():
    """Reset singleton instances between tests."""
    # Clear any cached instances
    from app.workers import analysis_worker, competitive_worker

    # Reset worker tasks
    if hasattr(analysis_worker, 'analysis_worker'):
        analysis_worker.analysis_worker.tasks.clear()

    if hasattr(competitive_worker, 'competitive_worker'):
        competitive_worker.competitive_worker.tasks.clear()

    yield

    # Cleanup after test
    if hasattr(analysis_worker, 'analysis_worker'):
        analysis_worker.analysis_worker.tasks.clear()

    if hasattr(competitive_worker, 'competitive_worker'):
        competitive_worker.competitive_worker.tasks.clear()


@pytest.fixture
def sample_url():
    """Provide a sample URL for testing."""
    return "https://example.com"


@pytest.fixture
def sample_urls():
    """Provide sample URLs for competitive analysis testing."""
    return [
        "https://competitor1.com",
        "https://competitor2.com",
        "https://competitor3.com",
    ]


@pytest.fixture
def sample_html():
    """Provide sample HTML content for testing."""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <title>Test Page</title>
        <meta name="description" content="Test description">
        <meta name="keywords" content="test, keywords">
    </head>
    <body>
        <h1>Welcome to Test Page</h1>
        <p>This is a test paragraph with some content.</p>
        <a href="/page1">Link 1</a>
        <a href="/page2">Link 2</a>
    </body>
    </html>
    """


@pytest.fixture
def sample_seo_metrics():
    """Provide sample SEO metrics for testing."""
    return {
        "category_scores": {
            "meta_tags": 85.0,
            "performance": 90.0,
            "content_quality": 75.0,
            "mobile_optimization": 80.0,
            "technical_seo": 88.0,
        },
        "metrics": {
            "title": "Test Page",
            "description": "Test description",
            "h1_count": 1,
            "word_count": 150,
            "internal_links": 5,
            "external_links": 2,
            "images": 3,
            "ssl_enabled": True,
            "mobile_friendly": True,
        },
        "issues": [
            "Missing alt text on 1 image",
            "Page load time could be improved",
        ],
    }


@pytest.fixture
def sample_aeo_metrics():
    """Provide sample AEO metrics for testing."""
    return {
        "clarity_score": 78.5,
        "structured_data_score": 85.0,
        "faq_score": 70.0,
        "entities": ["Test Company", "Product Name"],
        "topics": ["technology", "innovation"],
        "question_answering_potential": 75.0,
    }
