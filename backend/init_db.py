"""Initialize database with tables."""

import asyncio
from app.database import engine, Base
from app.models import analysis, competitive


async def init_db():
    """Create all database tables."""
    async with engine.begin() as conn:
        # Drop all tables (for dev only!)
        await conn.run_sync(Base.metadata.drop_all)

        # Create all tables
        await conn.run_sync(Base.metadata.create_all)

    print("✅ Database tables created successfully!")
    print("Tables created:")
    print("  - analysis_requests")
    print("  - analysis_results")
    print("  - competitive_analysis_batches")
    print("  - competitive_analysis_urls")
    print("  - comparison_results")


if __name__ == "__main__":
    asyncio.run(init_db())
