"""
Database table creation script.
Run this script to create all tables defined in mysql_module/models.py
"""

import asyncio
from mysql_module.models import Base
from config.settings import settings


async def create_tables():
    """Create all database tables."""
    # Use sync URL for table creation
    sync_url = settings.mysql_sync_url
    
    print(f"Connecting to database: {settings.MYSQL_HOST}:{settings.MYSQL_PORT}/{settings.MYSQL_DATABASE}")
    print(f"Sync URL: {sync_url}")
    
    # Create engine with connect_args to set charset
    from sqlalchemy import create_engine
    
    engine = create_engine(
        sync_url,
        echo=True,
        connect_args={"charset": "utf8mb4"}
    )
    
    print("\nCreating tables...")
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    print("\n[SUCCESS] All tables created successfully!")
    
    # List all tables
    print("\n[INFO] Created tables:")
    for table_name in Base.metadata.tables.keys():
        print(f"  - {table_name}")
    
    engine.dispose()


if __name__ == "__main__":
    print("=" * 60)
    print("Database Table Creation Script")
    print("=" * 60)
    
    try:
        asyncio.run(create_tables())
    except Exception as e:
        print(f"\n[ERROR] Error creating tables: {e}")
        raise
