# Story 5.2 Validation Guide: Enhanced Job Queue & Tracking System

## 30-Second Quick Test
1. Run migration: `psql -d zapcut -f backend/migrations/001_add_generation_jobs.sql`
2. Check tables exist: `\dt generation_jobs` and `\d campaigns`
3. Import models: `python -c "from app.models import GenerationJob; print('OK')"`
4. Verify new campaign fields: `generation_stage`, `generation_progress`, `voiceover_urls`

## Automated Tests
```python
# Test in Python shell
from app.models import Campaign, GenerationJob
from app.database import SessionLocal

db = SessionLocal()

# Create test campaign
campaign = db.query(Campaign).first()
print(f"Stage: {campaign.generation_stage}")  # Should be 'not_started'
print(f"Progress: {campaign.generation_progress}")  # Should be 0

# Create test job
job = GenerationJob(
    campaign_id=campaign.id,
    job_type="scene_video",
    scene_number=1,
    status="pending"
)
db.add(job)
db.commit()

# Verify job created
assert job.id is not None
assert job.campaign_id == campaign.id
print(f"Job created: {job.id}")
```

## Manual Validation Steps

### Database Migration
1. **Run Migration:**
   ```bash
   cd backend
   psql $DATABASE_URL -f migrations/001_add_generation_jobs.sql
   ```

2. **Verify Tables:**
   ```sql
   -- Check generation_jobs table
   \d generation_jobs

   -- Should show columns: id, campaign_id, job_type, scene_number, status, etc.

   -- Check campaigns table updates
   \d campaigns

   -- Should show new columns: voiceover_urls, generation_stage, generation_progress
   ```

3. **Verify Indexes:**
   ```sql
   \di idx_generation_jobs_campaign
   \di idx_generation_jobs_status
   ```

### Model Testing
1. **Import Models:**
   ```python
   from app.models import Campaign, GenerationJob
   from app.database import SessionLocal
   ```

2. **Create Generation Job:**
   ```python
   db = SessionLocal()
   campaign = db.query(Campaign).first()

   job = GenerationJob(
       campaign_id=campaign.id,
       job_type="scene_video",
       scene_number=1,
       status="processing",
       input_params={"prompt": "test"},
       replicate_job_id="rep_123"
   )
   db.add(job)
   db.commit()
   ```

3. **Query Jobs:**
   ```python
   # Get jobs by campaign
   jobs = db.query(GenerationJob).filter(
       GenerationJob.campaign_id == campaign.id
   ).all()

   # Get pending jobs
   pending = db.query(GenerationJob).filter(
       GenerationJob.status == "pending"
   ).all()
   ```

4. **Test Cascade Delete:**
   ```python
   # Delete campaign should delete jobs
   db.delete(campaign)
   db.commit()

   # Jobs should be auto-deleted
   orphan_jobs = db.query(GenerationJob).filter(
       GenerationJob.campaign_id == campaign.id
   ).all()
   assert len(orphan_jobs) == 0
   ```

### Edge Cases
1. **NULL Values:**
   - scene_number can be NULL (for music/composite jobs)
   - replicate_job_id can be NULL (not started yet)
   - output_url can be NULL (not completed)

2. **JSONB Fields:**
   - input_params can store arbitrary JSON
   - voiceover_urls can store array of URLs

3. **Default Values:**
   - status defaults to 'pending'
   - generation_stage defaults to 'not_started'
   - generation_progress defaults to 0

## Acceptance Criteria Checklist
- [x] `generation_jobs` table created successfully
- [x] Job records can be created for each pipeline step
- [x] Jobs track start/end times and status
- [x] Failed jobs capture error messages
- [x] Campaign progress updates 0-100%
- [x] Indexes created for performance
- [x] Cascade delete works (deleting campaign deletes jobs)
- [x] Models import without errors

## Rollback Plan
```sql
-- Rollback migration
DROP TABLE IF EXISTS generation_jobs CASCADE;

ALTER TABLE campaigns
DROP COLUMN IF EXISTS voiceover_urls,
DROP COLUMN IF EXISTS generation_stage,
DROP COLUMN IF EXISTS generation_progress;
```

```bash
# Revert model changes
git checkout HEAD~1 -- backend/app/models/campaign.py
git checkout HEAD~1 -- backend/app/models/__init__.py
git rm backend/app/models/generation_job.py
```

## Files Modified
- `backend/app/models/generation_job.py` (NEW)
- `backend/app/models/campaign.py`
  - Added `voiceover_urls` column
  - Added `generation_stage` column
  - Added `generation_progress` column
  - Added `generation_jobs` relationship
- `backend/app/models/__init__.py`
  - Added GenerationJob import
- `backend/migrations/001_add_generation_jobs.sql` (NEW)

## Notes
- Migration must be run manually on database
- In production, use Alembic or similar migration tool
- Jobs will be created in Stories 5.3-5.6 during pipeline execution
- Progress tracking used in Story 5.8 for frontend UI
