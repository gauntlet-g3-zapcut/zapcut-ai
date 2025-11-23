"""
Database migration script: Add images field and migrate existing brand image data.

This script:
1. Creates a backup of the brands table
2. Adds the 'images' JSON column to brands and campaigns tables
3. Migrates existing product_image_1_url and product_image_2_url to the new images array
4. Verifies the migration
5. (Optional) Drops old columns after confirmation

Run with: python -m scripts.migrate_images
"""

import uuid
import logging
from datetime import datetime
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker
from app.config import settings
from app.models.brand import Brand
from app.models.campaign import Campaign

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def extract_filename_from_url(url: str) -> str:
    """Extract filename from S3 URL."""
    if not url:
        return ""
    # Extract filename from URL path
    parts = url.split('/')
    return parts[-1] if parts else "unknown"


def create_backup_table(engine):
    """Create backup of brands table."""
    logger.info("Step 1: Creating backup of brands table...")

    with engine.connect() as conn:
        # Check if backup already exists
        result = conn.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'brands_backup'
            );
        """))
        backup_exists = result.scalar()

        if backup_exists:
            logger.warning("Backup table 'brands_backup' already exists. Skipping backup creation.")
            logger.warning("If you want to create a fresh backup, drop the old one first:")
            logger.warning("  DROP TABLE brands_backup;")
            return

        # Create backup
        conn.execute(text("CREATE TABLE brands_backup AS SELECT * FROM brands;"))
        conn.commit()

        # Verify backup
        result = conn.execute(text("SELECT COUNT(*) FROM brands_backup;"))
        count = result.scalar()
        logger.info(f"✅ Backup created successfully with {count} brands")


def add_images_columns(engine):
    """Add images JSON column to brands and campaigns tables."""
    logger.info("Step 2: Adding images column to tables...")

    with engine.connect() as conn:
        inspector = inspect(engine)

        # Check and add images column to brands
        brands_columns = [col['name'] for col in inspector.get_columns('brands')]
        if 'images' not in brands_columns:
            logger.info("Adding 'images' column to brands table...")
            conn.execute(text("ALTER TABLE brands ADD COLUMN images JSON;"))
            conn.commit()
            logger.info("✅ Added 'images' column to brands table")
        else:
            logger.info("'images' column already exists in brands table")

        # Check and add images column to campaigns
        campaigns_columns = [col['name'] for col in inspector.get_columns('campaigns')]
        if 'images' not in campaigns_columns:
            logger.info("Adding 'images' column to campaigns table...")
            conn.execute(text("ALTER TABLE campaigns ADD COLUMN images JSON DEFAULT '[]'::json;"))
            conn.commit()
            logger.info("✅ Added 'images' column to campaigns table")
        else:
            logger.info("'images' column already exists in campaigns table")


def migrate_brand_images(session):
    """Migrate existing brand image URLs to new images array."""
    logger.info("Step 3: Migrating brand image data...")

    brands = session.query(Brand).all()
    logger.info(f"Found {len(brands)} brands to migrate")

    migrated_count = 0
    skipped_count = 0

    for brand in brands:
        # Skip if already migrated (images field is not empty)
        if brand.images and len(brand.images) > 0:
            logger.debug(f"Brand {brand.id} already migrated, skipping...")
            skipped_count += 1
            continue

        images = []

        # Migrate product_image_1_url
        if brand.product_image_1_url:
            images.append({
                "id": str(uuid.uuid4()),
                "url": brand.product_image_1_url,
                "filename": extract_filename_from_url(brand.product_image_1_url),
                "uploaded_at": brand.created_at.isoformat() if brand.created_at else datetime.utcnow().isoformat(),
                "size_bytes": 0,  # Unknown, set to 0
                "order": 0,
                "caption": "",
                "is_primary": True
            })

        # Migrate product_image_2_url
        if brand.product_image_2_url:
            images.append({
                "id": str(uuid.uuid4()),
                "url": brand.product_image_2_url,
                "filename": extract_filename_from_url(brand.product_image_2_url),
                "uploaded_at": brand.created_at.isoformat() if brand.created_at else datetime.utcnow().isoformat(),
                "size_bytes": 0,
                "order": 1,
                "caption": "",
                "is_primary": False
            })

        # Update brand with new images array
        brand.images = images
        migrated_count += 1

        logger.debug(f"Migrated brand {brand.id}: {len(images)} images")

    session.commit()
    logger.info(f"✅ Migrated {migrated_count} brands, skipped {skipped_count} already migrated brands")


def verify_migration(session):
    """Verify the migration was successful."""
    logger.info("Step 4: Verifying migration...")

    brands = session.query(Brand).all()
    errors = []

    for brand in brands:
        old_image_1 = brand.product_image_1_url
        old_image_2 = brand.product_image_2_url
        new_images = brand.images or []

        # Calculate expected image count
        expected_count = (1 if old_image_1 else 0) + (1 if old_image_2 else 0)

        # Check image count matches
        if len(new_images) != expected_count:
            errors.append(f"Brand {brand.id}: Expected {expected_count} images, got {len(new_images)}")
            continue

        # Check URLs are preserved
        image_urls = [img['url'] for img in new_images]

        if old_image_1 and old_image_1 not in image_urls:
            errors.append(f"Brand {brand.id}: product_image_1_url not found in new images")

        if old_image_2 and old_image_2 not in image_urls:
            errors.append(f"Brand {brand.id}: product_image_2_url not found in new images")

        # Check primary image is set correctly
        primary_images = [img for img in new_images if img.get('is_primary')]
        if len(new_images) > 0 and len(primary_images) != 1:
            errors.append(f"Brand {brand.id}: Should have exactly 1 primary image, got {len(primary_images)}")

    if errors:
        logger.error("❌ Migration verification failed with errors:")
        for error in errors:
            logger.error(f"  - {error}")
        return False
    else:
        logger.info(f"✅ Migration verified successfully for {len(brands)} brands")
        return True


def drop_old_columns(engine):
    """Drop old product_image columns (run this manually after confirming migration)."""
    logger.info("Step 5 (OPTIONAL): Dropping old columns...")
    logger.warning("⚠️  This step is DESTRUCTIVE and cannot be undone!")
    logger.warning("⚠️  Make sure you've tested the migration thoroughly before running this.")

    response = input("Are you sure you want to drop product_image_1_url and product_image_2_url columns? (yes/no): ")

    if response.lower() != 'yes':
        logger.info("Skipping column drop. Old columns will remain in the database.")
        return

    with engine.connect() as conn:
        logger.info("Dropping product_image_1_url column...")
        conn.execute(text("ALTER TABLE brands DROP COLUMN product_image_1_url;"))

        logger.info("Dropping product_image_2_url column...")
        conn.execute(text("ALTER TABLE brands DROP COLUMN product_image_2_url;"))

        conn.commit()
        logger.info("✅ Old columns dropped successfully")


def rollback_migration(engine):
    """Rollback migration by restoring from backup."""
    logger.warning("⚠️  ROLLBACK: Restoring brands table from backup...")

    response = input("Are you sure you want to rollback? This will restore the backup table. (yes/no): ")

    if response.lower() != 'yes':
        logger.info("Rollback cancelled.")
        return

    with engine.connect() as conn:
        # Check if backup exists
        result = conn.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'brands_backup'
            );
        """))
        backup_exists = result.scalar()

        if not backup_exists:
            logger.error("❌ Backup table 'brands_backup' does not exist. Cannot rollback.")
            return

        # Drop current brands table and restore from backup
        conn.execute(text("DROP TABLE brands;"))
        conn.execute(text("ALTER TABLE brands_backup RENAME TO brands;"))
        conn.commit()

        logger.info("✅ Rollback completed. Brands table restored from backup.")


def main():
    """Main migration function."""
    logger.info("=" * 60)
    logger.info("IMAGE MIGRATION SCRIPT")
    logger.info("=" * 60)

    # Create database engine
    engine = create_engine(settings.DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Step 1: Create backup
        create_backup_table(engine)

        # Step 2: Add images columns
        add_images_columns(engine)

        # Step 3: Migrate brand images
        migrate_brand_images(session)

        # Step 4: Verify migration
        verification_passed = verify_migration(session)

        if verification_passed:
            logger.info("=" * 60)
            logger.info("✅ MIGRATION COMPLETED SUCCESSFULLY")
            logger.info("=" * 60)
            logger.info("")
            logger.info("Next steps:")
            logger.info("1. Test your application thoroughly")
            logger.info("2. Monitor for any issues")
            logger.info("3. After 1-2 weeks of successful testing:")
            logger.info("   - Re-run this script with --drop-columns flag to remove old columns")
            logger.info("   - Or manually run: python -m scripts.migrate_images --drop-columns")
            logger.info("")
            logger.info("Backup table 'brands_backup' will remain for safety.")
            logger.info("To remove it later: DROP TABLE brands_backup;")
        else:
            logger.error("=" * 60)
            logger.error("❌ MIGRATION FAILED VERIFICATION")
            logger.error("=" * 60)
            logger.error("Please review errors above and fix before proceeding.")
            logger.error("To rollback: python -m scripts.migrate_images --rollback")

    except Exception as e:
        logger.error(f"❌ Migration failed with error: {e}", exc_info=True)
        logger.error("To rollback: python -m scripts.migrate_images --rollback")

    finally:
        session.close()
        engine.dispose()


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        if sys.argv[1] == "--drop-columns":
            engine = create_engine(settings.DATABASE_URL)
            drop_old_columns(engine)
            engine.dispose()
        elif sys.argv[1] == "--rollback":
            engine = create_engine(settings.DATABASE_URL)
            rollback_migration(engine)
            engine.dispose()
        else:
            print("Usage:")
            print("  python -m scripts.migrate_images           # Run migration")
            print("  python -m scripts.migrate_images --drop-columns  # Drop old columns")
            print("  python -m scripts.migrate_images --rollback      # Rollback migration")
    else:
        main()
