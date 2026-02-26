"""
Database Connection and Schema Verification Test
- Tests database connectivity
- Verifies noavoice_ns schema exists
- Creates tables from models
- Lists all tables in schema
"""

import asyncio
import sys
from sqlalchemy import text
from app.config.database import engine, init_db
from app.config.settings import settings
from app.config.logging import app_logger, db_logger

async def test_connection():
    """Test if we can connect to PostgreSQL"""
    print("\n" + "="*60)
    print("🔍 Testing Database Connection...")
    print("="*60)
    
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT version()"))
            version = result.scalar()
            
            print("✅ Connected to PostgreSQL")
            print(f"📊 Database: {version[:50]}...")
            app_logger.info("Database connection successful")
            return True
            
    except Exception as e:
        print("❌ Connection failed!")
        print(f"Error: {e}")
        db_logger.error(f"Database connection failed: {e}", exc_info=True)
        return False


async def check_schema_exists():
    """Check if schema exists"""
    print("\n" + "="*60)
    print(f"🔍 Checking Schema '{settings.DB_SCHEMA}'...")
    print("="*60)
    
    try:
        async with engine.connect() as conn:
            result = await conn.execute(
                text(
                    f"SELECT schema_name FROM information_schema.schemata "
                    f"WHERE schema_name = '{settings.DB_SCHEMA}'"
                )
            )
            schema_exists = result.scalar() is not None
            
            if schema_exists:
                print(f"✅ Schema '{settings.DB_SCHEMA}' exists")
                db_logger.info(f"Schema '{settings.DB_SCHEMA}' verified")
                return True
            else:
                print(f"❌ Schema '{settings.DB_SCHEMA}' NOT FOUND")
                print(f"\nCreate it manually:")
                print(f"   CREATE SCHEMA {settings.DB_SCHEMA};")
                db_logger.error(f"Schema '{settings.DB_SCHEMA}' does not exist")
                return False
                
    except Exception as e:
        print("❌ Failed to check schema")
        print(f"Error: {e}")
        db_logger.error(f"Failed to check schema: {e}", exc_info=True)
        return False


async def create_tables():
    """Create tables in schema using init_db"""
    print("\n" + "="*60)
    print("🔍 Creating Tables in Schema...")
    print("="*60)
    
    try:
        await init_db()
        print("✅ Tables created or already exist")
        db_logger.info("Database tables initialized successfully")
        return True
        
    except Exception as e:
        print("❌ Failed to create tables")
        print(f"Error: {e}")
        db_logger.error(f"Failed to create tables: {e}", exc_info=True)
        return False


async def list_tables():
    """List all tables in the schema"""
    print("\n" + "="*60)
    print(f"🔍 Tables in '{settings.DB_SCHEMA}' Schema...")
    print("="*60)
    
    try:
        async with engine.connect() as conn:
            result = await conn.execute(
                text(
                    f"SELECT tablename FROM pg_catalog.pg_tables "
                    f"WHERE schemaname = '{settings.DB_SCHEMA}' "
                    f"ORDER BY tablename"
                )
            )
            
            tables = [row[0] for row in result.fetchall()]
            
            if not tables:
                print(f"ℹ️  No tables found in schema '{settings.DB_SCHEMA}'")
                return False
            
            print(f"✅ Found {len(tables)} table(s):\n")
            
            for table in tables:
                try:
                    count_result = await conn.execute(
                        text(f"SELECT COUNT(*) FROM {settings.DB_SCHEMA}.{table}")
                    )
                    count = count_result.scalar()
                    print(f"   ✅ {settings.DB_SCHEMA}.{table} ({count} rows)")
                except Exception:
                    print(f"   ✅ {settings.DB_SCHEMA}.{table}")
            
            db_logger.info(f"Found {len(tables)} tables in schema")
            return True
                
    except Exception as e:
        print("❌ Failed to list tables")
        print(f"Error: {e}")
        db_logger.error(f"Failed to list tables: {e}", exc_info=True)
        return False


async def main():
    """Run database verification"""
    print("\n" + "="*60)
    print("🚀 DATABASE VERIFICATION")
    print("="*60)
    print(f"Schema: {settings.DB_SCHEMA}")
    print("="*60)
    
    results = {}
    
    # Step 1: Test connection
    results['connection'] = await test_connection()
    if not results['connection']:
        print("\n❌ Cannot proceed without database connection!")
        sys.exit(1)
    
    # Step 2: Check schema exists
    results['schema_exists'] = await check_schema_exists()
    if not results['schema_exists']:
        print("\n❌ Schema does not exist. Please create it manually.")
        sys.exit(1)
    
    # Step 3: Create tables
    results['tables_created'] = await create_tables()
    
    # Step 4: List tables
    results['tables_listed'] = await list_tables()
    
    # Final summary
    print("\n" + "="*60)
    print("📊 VERIFICATION SUMMARY")
    print("="*60)
    for key, value in results.items():
        status = "✅ PASS" if value else "❌ FAIL"
        label = key.replace('_', ' ').title()
        print(f"{label:<30} {status}")
    print("="*60)
    
    if all(results.values()):
        print("\n🎉 DATABASE READY!")
        print(f"✅ Connected to PostgreSQL")
        print(f"✅ Schema '{settings.DB_SCHEMA}' verified")
        print(f"✅ Tables created successfully")
        print("\n")
    else:
        print("\n⚠️  Some verification steps failed. Check errors above.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())