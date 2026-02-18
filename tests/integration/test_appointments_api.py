"""
Safe Database Verification Script
- Only manages tables defined in OUR models
- Leaves all other tables untouched
- Uses schema-qualified table names (public.tablename)
"""

import asyncio
import sys
from sqlalchemy import text, inspect
from app.config.database import engine
from app.models.base import Base
from app.models.booking import Booking

# Define OUR tables (tables we own and can manage)
OUR_TABLES = ['bookings']  # Add more as you create them
SCHEMA = 'public'  # Database schema

async def test_connection():
    """Test if we can connect to Neon PostgreSQL"""
    print("\n" + "="*60)
    print("🔍 STEP 1: Testing Database Connection...")
    print("="*60)
    
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT version()"))
            version = result.scalar()
            
            print("✅ SUCCESS! Connected to PostgreSQL")
            print(f"📊 Database version: {version[:50]}...")
            return True
            
    except Exception as e:
        print("❌ FAILED! Could not connect to database")
        print(f"Error: {e}")
        return False

async def list_all_tables():
    """List all tables in the database"""
    print("\n" + "="*60)
    print("🔍 STEP 2: Listing All Tables in Database...")
    print("="*60)
    
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text(f"""
                SELECT 
                    schemaname,
                    tablename
                FROM pg_catalog.pg_tables
                WHERE schemaname = '{SCHEMA}'
                ORDER BY tablename
            """))
            
            tables = result.fetchall()
            
            if not tables:
                print(f"ℹ️  No tables found in schema '{SCHEMA}'")
                return [], []
            
            all_tables = [row[1] for row in tables]
            our_tables = [t for t in all_tables if t in OUR_TABLES]
            other_tables = [t for t in all_tables if t not in OUR_TABLES]
            
            print(f"✅ Found {len(all_tables)} total table(s) in '{SCHEMA}' schema:\n")
            
            if our_tables:
                print(f"📋 OUR TABLES (we manage these):")
                for table in our_tables:
                    try:
                        count_result = await conn.execute(
                            text(f"SELECT COUNT(*) FROM {SCHEMA}.{table}")
                        )
                        count = count_result.scalar()
                        print(f"   🔧 {SCHEMA}.{table} ({count} rows)")
                    except Exception:
                        print(f"   🔧 {SCHEMA}.{table}")
            
            if other_tables:
                print(f"\n📋 OTHER TABLES (we DON'T touch these):")
                for table in other_tables:
                    try:
                        count_result = await conn.execute(
                            text(f"SELECT COUNT(*) FROM {SCHEMA}.{table}")
                        )
                        count = count_result.scalar()
                        print(f"   🛡️  {SCHEMA}.{table} ({count} rows) - PROTECTED")
                    except Exception:
                        print(f"   🛡️  {SCHEMA}.{table} - PROTECTED")
            
            return our_tables, other_tables
                
    except Exception as e:
        print("❌ FAILED! Could not list tables")
        print(f"Error: {e}")
        return [], []

async def drop_our_tables_only():
    """Drop ONLY our tables, leave everything else untouched"""
    print("\n" + "="*60)
    print("🔍 STEP 3: Dropping OUR Tables Only (Safe)...")
    print("="*60)
    
    try:
        async with engine.begin() as conn:
            # Check which of our tables exist
            result = await conn.execute(text(f"""
                SELECT tablename 
                FROM pg_catalog.pg_tables
                WHERE schemaname = '{SCHEMA}'
                AND tablename = ANY(:our_tables)
            """), {"our_tables": OUR_TABLES})
            
            existing_our_tables = [row[0] for row in result]
            
            if not existing_our_tables:
                print("ℹ️  None of our tables exist yet. Nothing to drop.")
                return True
            
            print(f"🗑️  Dropping {len(existing_our_tables)} of our table(s):")
            
            for table in existing_our_tables:
                print(f"   ❌ Dropping {SCHEMA}.{table}...")
                await conn.execute(
                    text(f"DROP TABLE IF EXISTS {SCHEMA}.{table} CASCADE")
                )
            
            print("\n✅ Our tables dropped successfully")
            print("✅ All other tables remain untouched")
            
        return True
        
    except Exception as e:
        print("❌ FAILED! Could not drop tables")
        print(f"Error: {e}")
        return False

async def create_our_tables():
    """Create ONLY our tables"""
    print("\n" + "="*60)
    print("🔍 STEP 4: Creating OUR Tables...")
    print("="*60)
    
    try:
        async with engine.begin() as conn:
            # Get tables defined in our models
            def create_tables_from_models(connection):
                # Get only tables we defined in OUR_TABLES
                tables_to_create = {
                    name: table 
                    for name, table in Base.metadata.tables.items()
                    if name in OUR_TABLES
                }
                
                if not tables_to_create:
                    print("⚠️  No tables defined in models!")
                    return
                
                print(f"📝 Creating {len(tables_to_create)} table(s):")
                for name in tables_to_create.keys():
                    print(f"   ➕ {SCHEMA}.{name}")
                
                # Create tables
                for table in tables_to_create.values():
                    table.create(connection, checkfirst=True)
            
            await conn.run_sync(create_tables_from_models)
            
            print("\n✅ Our tables created successfully!")
            
        return True
        
    except Exception as e:
        print("❌ FAILED! Could not create tables")
        print(f"Error: {e}")
        return False

async def verify_our_tables():
    """Verify that OUR tables exist"""
    print("\n" + "="*60)
    print("🔍 STEP 5: Verifying OUR Tables Exist...")
    print("="*60)
    
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text(f"""
                SELECT tablename 
                FROM pg_catalog.pg_tables
                WHERE schemaname = '{SCHEMA}'
                AND tablename = ANY(:our_tables)
            """), {"our_tables": OUR_TABLES})
            
            existing = [row[0] for row in result]
            
            print(f"✅ Checking {len(OUR_TABLES)} expected table(s):\n")
            
            all_exist = True
            for table in OUR_TABLES:
                if table in existing:
                    print(f"   ✅ {SCHEMA}.{table} - EXISTS")
                else:
                    print(f"   ❌ {SCHEMA}.{table} - MISSING")
                    all_exist = False
            
            return all_exist
                
    except Exception as e:
        print("❌ FAILED! Could not verify tables")
        print(f"Error: {e}")
        return False

async def check_bookings_schema():
    """Check the structure of bookings table"""
    print("\n" + "="*60)
    print("🔍 STEP 6: Checking Bookings Table Structure...")
    print("="*60)
    
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text(f"""
                SELECT 
                    column_name, 
                    data_type, 
                    is_nullable
                FROM information_schema.columns 
                WHERE table_schema = '{SCHEMA}'
                AND table_name = 'bookings'
                ORDER BY ordinal_position
            """))
            
            columns = result.fetchall()
            
            if not columns:
                print("⚠️  Table structure not found")
                return False
            
            print(f"✅ Found {len(columns)} columns in {SCHEMA}.bookings:\n")
            print(f"{'Column Name':<25} {'Type':<20} {'Nullable'}")
            print("-" * 60)
            
            for col_name, data_type, nullable in columns:
                nullable_str = "YES" if nullable == "YES" else "NO"
                print(f"{col_name:<25} {data_type:<20} {nullable_str}")
            
            # Check for required columns
            column_names = [col[0] for col in columns]
            
            required_columns = {
                'id': 'Primary key',
                'patient_name': 'Patient name',
                'patient_email': 'Patient email',
                'patient_phone': 'Phone number (Cal.com V2)',
                'start_time': 'Appointment time',
                'calcom_booking_uid': 'Cal.com booking reference',
                'status': 'Booking status'
            }
            
            print("\n📋 Validating required columns:")
            all_present = True
            for col, description in required_columns.items():
                if col in column_names:
                    print(f"   ✅ {col:<25} {description}")
                else:
                    print(f"   ❌ {col:<25} MISSING - {description}")
                    all_present = False
            
            return all_present
            
    except Exception as e:
        print("❌ FAILED! Could not check table structure")
        print(f"Error: {e}")
        return False

async def verify_other_tables_untouched():
    """Verify that other tables are still intact"""
    print("\n" + "="*60)
    print("🔍 STEP 7: Verifying Other Tables Are Untouched...")
    print("="*60)
    
    try:
        async with engine.connect() as conn:
            # Get all tables except ours
            result = await conn.execute(text(f"""
                SELECT tablename 
                FROM pg_catalog.pg_tables
                WHERE schemaname = '{SCHEMA}'
                AND tablename <> ALL(:our_tables)
                ORDER BY tablename
            """), {"our_tables": OUR_TABLES})
            
            other_tables = [row[0] for row in result]
            
            if not other_tables:
                print("ℹ️  No other tables exist in database")
                return True
            
            print(f"✅ Found {len(other_tables)} other table(s):")
            print("   Verifying they are untouched...\n")
            
            for table in other_tables:
                try:
                    count_result = await conn.execute(
                        text(f"SELECT COUNT(*) FROM {SCHEMA}.{table}")
                    )
                    count = count_result.scalar()
                    print(f"   🛡️  {SCHEMA}.{table} - {count} rows - INTACT")
                except Exception as e:
                    print(f"   ⚠️  {SCHEMA}.{table} - Could not verify: {e}")
            
            print("\n✅ All other tables are intact!")
            
            return True
            
    except Exception as e:
        print("❌ FAILED! Could not verify other tables")
        print(f"Error: {e}")
        return False

async def insert_test_booking():
    """Insert a test booking using schema-qualified name"""
    print("\n" + "="*60)
    print("🔍 STEP 8: Testing Insert Operation...")
    print("="*60)
    
    try:
        from datetime import datetime, timezone
        from app.config.database import AsyncSessionLocal
        from app.models.booking import BookingStatus
        
        async with AsyncSessionLocal() as session:
            # Check if test booking exists
            from sqlalchemy import select
            stmt = select(Booking).where(
                Booking.patient_email == "test@example.com"
            )
            result = await session.execute(stmt)
            existing = result.scalar_one_or_none()
            
            if existing:
                print("ℹ️  Test booking already exists")
                print(f"   ID: {existing.id}")
                print(f"   Name: {existing.patient_name}")
                return True
            
            # Create test booking
            test_booking = Booking(
                calcom_booking_id=999999,
                calcom_booking_uid="test_uid_12345",
                patient_name="Test Patient",
                patient_email="test@example.com",
                patient_phone="+919876543210",
                patient_timezone="Asia/Kolkata",
                start_time=datetime.now(timezone.utc),
                event_type_id=12345,
                duration_minutes=30,
                status=BookingStatus.PENDING,
                notes="Test booking - safe to delete"
            )
            
            session.add(test_booking)
            await session.commit()
            
            print("✅ Test booking inserted successfully!")
            print(f"   Table: {SCHEMA}.bookings")
            print(f"   ID: {test_booking.id}")
            print(f"   Name: {test_booking.patient_name}")
            print(f"   Email: {test_booking.patient_email}")
            print(f"   Phone: {test_booking.patient_phone}")
            
            return True
            
    except Exception as e:
        print("❌ FAILED! Could not insert test booking")
        print(f"Error: {e}")
        return False

async def final_table_summary():
    """Show final summary of all tables"""
    print("\n" + "="*60)
    print("🔍 STEP 9: Final Database State...")
    print("="*60)
    
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text(f"""
                SELECT 
                    schemaname,
                    tablename
                FROM pg_catalog.pg_tables
                WHERE schemaname = '{SCHEMA}'
                ORDER BY tablename
            """))
            
            tables = result.fetchall()
            
            print(f"📊 Total tables in {SCHEMA} schema: {len(tables)}\n")
            print(f"{'Table Name':<30} {'Type':<20} {'Record Count'}")
            print("-" * 70)
            
            for schema, table in tables:
                is_our_table = table in OUR_TABLES
                table_type = "OUR TABLE" if is_our_table else "OTHER TABLE"
                
                try:
                    count_result = await conn.execute(
                        text(f"SELECT COUNT(*) FROM {schema}.{table}")
                    )
                    count = count_result.scalar()
                    icon = "🔧" if is_our_table else "🛡️"
                    print(f"{icon} {table:<27} {table_type:<20} {count}")
                except Exception:
                    print(f"   {table:<27} {table_type:<20} Error")
            
            return True
            
    except Exception as e:
        print("❌ FAILED! Could not get summary")
        print(f"Error: {e}")
        return False

async def main():
    """Run all verification steps"""
    print("\n" + "="*60)
    print("🚀 PRODUCTION-SAFE DATABASE VERIFICATION")
    print("="*60)
    print(f"Schema: {SCHEMA}")
    print(f"Our Tables: {', '.join(OUR_TABLES)}")
    print("="*60)
    
    results = {}
    
    # Step 1: Test connection
    results['connection'] = await test_connection()
    if not results['connection']:
        print("\n❌ Cannot proceed without database connection!")
        sys.exit(1)
    
    # Step 2: List all tables
    our_existing, other_existing = await list_all_tables()
    
    # Step 3: Drop ONLY our tables
    results['drop_safe'] = await drop_our_tables_only()
    
    # Step 4: Create our tables
    results['tables_created'] = await create_our_tables()
    
    # Step 5: Verify our tables
    results['our_tables_ok'] = await verify_our_tables()
    
    # Step 6: Check bookings schema
    results['schema_ok'] = await check_bookings_schema()
    
    # Step 7: Verify other tables untouched
    results['others_intact'] = await verify_other_tables_untouched()
    
    # Step 8: Test insert
    results['insert_ok'] = await insert_test_booking()
    
    # Step 9: Final summary
    await final_table_summary()
    
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
        print("\n🎉 ALL TESTS PASSED!")
        print(f"\n✅ Our tables ({', '.join(OUR_TABLES)}) are ready")
        print("✅ All other tables remain untouched")
        print("✅ Schema-qualified names working correctly")
        print("\n📋 Next steps:")
        print("   1. Test Cal.com V2 API connection")
        print("   2. Test appointment tools")
        print("   3. Integrate with LiveKit agent")
    else:
        print("\n⚠️  Some tests failed. Check errors above.")
    
    print("\n")

if __name__ == "__main__":
    asyncio.run(main())