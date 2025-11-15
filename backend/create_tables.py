#!/usr/bin/env python3
"""
Create all database tables on Railway
"""
import sys
sys.path.insert(0, '/Users/nat/adcraft/backend')

from app.database import engine, Base
from app.models import user, brand, creative_bible, campaign

def create_tables():
    print("Creating all database tables...")
    Base.metadata.create_all(bind=engine)
    print("✅ All tables created successfully!")

if __name__ == "__main__":
    create_tables()

