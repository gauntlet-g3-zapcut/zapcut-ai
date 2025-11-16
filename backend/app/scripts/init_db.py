"""
Initialize database tables for ZapCut AI.
Creates all tables defined in SQLAlchemy models.
"""
from app.database import Base, engine
from app.models import User, Brand, CreativeBible, Campaign, GenerationJob
from sqlalchemy import text, inspect

print("=" * 80)
print("ZAPCUT AI - DATABASE INITIALIZATION")
print("=" * 80)

# Import all models to ensure they're registered with Base
print("\n✓ Models imported:")
print(f"  - User")
print(f"  - Brand")
print(f"  - CreativeBible")
print(f"  - Campaign")
print(f"  - GenerationJob")

# Check existing tables
inspector = inspect(engine)
existing_tables = inspector.get_table_names()
print(f"\nExisting tables: {existing_tables}")

# Create all tables
print("\nCreating tables...")
Base.metadata.create_all(bind=engine)

# Verify tables were created
inspector = inspect(engine)
new_tables = inspector.get_table_names()

print("\n" + "=" * 80)
print("TABLES CREATED SUCCESSFULLY")
print("=" * 80)

for table in sorted(new_tables):
    is_new = "NEW" if table not in existing_tables else "EXISTING"
    print(f"\n[{is_new}] {table}")
    
    # Show columns
    columns = inspector.get_columns(table)
    for col in columns:
        nullable = "NULL" if col.get("nullable") else "NOT NULL"
        default = f" DEFAULT {col.get('default')}" if col.get('default') else ""
        print(f"  - {col['name']}: {col['type']} {nullable}{default}")
    
    # Show indexes
    indexes = inspector.get_indexes(table)
    if indexes:
        print(f"  Indexes:")
        for idx in indexes:
            print(f"    - {idx['name']}: {idx['column_names']}")

print("\n" + "=" * 80)
print(f"Total tables: {len(new_tables)}")
print("Database initialization complete!")
print("=" * 80)
