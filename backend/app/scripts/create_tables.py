#!/usr/bin/env python3
"""
Create all database tables
"""
from app.database import get_engine, Base
from app.models import User, Brand, CreativeBible, Campaign

def create_tables():
    print("Creating all database tables...")
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
    print("✅ All tables created successfully!")
    print(f"Tables: {', '.join(Base.metadata.tables.keys())}")

if __name__ == "__main__":
    create_tables()

