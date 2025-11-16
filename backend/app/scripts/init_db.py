"""Create all database tables"""
from app.database import get_engine, Base
from app.models.user import User
from app.models.brand import Brand
from app.models.creative_bible import CreativeBible
from app.models.campaign import Campaign

print("Creating all database tables...")
engine = get_engine()
Base.metadata.create_all(bind=engine)
print("✅ Tables created successfully!")
print(f"Tables: {', '.join(Base.metadata.tables.keys())}")

