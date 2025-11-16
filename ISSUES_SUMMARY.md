# Issues Summary - Campaign Answers Submission Timeout

## Overview
The application is experiencing a timeout error when users attempt to submit campaign answers via the "Continue to Storyline" button. The request times out after 30 seconds, preventing users from proceeding to the storyline generation step.

## Timeline of Changes
1. **Before**: System was working with basic video generation using asyncio
2. **Migration**: Migrated to Celery + Redis for background task processing
3. **After Migration**: Brands loading issue appeared (fixed), now campaign answers submission is timing out

## Current Issue: Campaign Answers Submission Timeout

### Error Message
```
Failed to submit answers: Request timed out. Please check your connection.
```

### Frontend Code (Working)
```typescript
// frontend/src/pages/BrandChat.jsx
const handleSubmit = async () => {
  const allAnswered = QUESTIONS.every(q => answers[q.id])
  if (!allAnswered) {
    alert("Please answer all questions before continuing.")
    return
  }

  setLoading(true)
  try {
    console.log("Submitting answers:", { brandId, answers })
    const response = await api.submitCampaignAnswers(brandId, answers)
    console.log("Submit response:", response)
    if (!response?.creative_bible_id) {
      throw new Error("Invalid response: missing creative_bible_id")
    }
    navigate(`/brands/${brandId}/storyline/${response.creative_bible_id}`)
  } catch (error) {
    console.error("Failed to submit answers:", error)
    const errorMessage = error instanceof Error ? error.message : "Unknown error occurred"
    alert(`Failed to submit answers: ${errorMessage}. Please check the console for details.`)
  } finally {
    setLoading(false)
  }
}
```

### API Request Function
```typescript
// frontend/src/services/api.ts
async function apiRequest<T = unknown>(endpoint: string, options: RequestOptions = {}, retryCount = 0): Promise<T> {
  const maxRetries = 1
  const token = await getAuthToken()
  
  const url = `${API_URL}${endpoint}`
  console.log(`[API] Making request to: ${url}`)

  // Add timeout to prevent hanging requests
  const controller = new AbortController()
  const timeoutId = setTimeout(() => controller.abort(), 30000) // 30 second timeout

  try {
    const response = await fetch(url, {
      ...options,
      signal: controller.signal,
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
        ...options.headers,
      },
    })
    
    clearTimeout(timeoutId)

    // Handle 401 Unauthorized - might be due to invalid token
    if (response.status === 401 && retryCount < maxRetries) {
      // Try refreshing the session and retrying once
      console.warn("Received 401, attempting to refresh session and retry...")
      try {
        const { data: refreshData, error: refreshError } = await supabase.auth.refreshSession()
        if (!refreshError && refreshData.session) {
          // Retry the request with the new token
          return apiRequest<T>(endpoint, options, retryCount + 1)
        }
      } catch (refreshErr) {
        console.error("Failed to refresh session:", refreshErr)
      }
      // If refresh fails, sign out and throw error
      await supabase.auth.signOut()
      throw new Error("Session expired. Please log in again.")
    }

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: "An error occurred" })) as { detail?: string; message?: string }
      console.error(`[API] Request failed: ${response.status}`, error)
      throw new Error(error.detail || error.message || "Request failed")
    }

    const data = await response.json()
    console.log(`[API] Request successful:`, data)
    return data as T
  } catch (error: unknown) {
    clearTimeout(timeoutId)
    if (error instanceof Error && error.name === 'AbortError') {
      console.error(`[API] Request timeout: ${url}`)
      throw new Error("Request timed out. Please check your connection.")
    }
    throw error
  }
}

// API method for submitting campaign answers
submitCampaignAnswers: <T = unknown>(brandId: string, answers: unknown) => apiRequest<T>(`/api/brands/${brandId}/campaign-answers`, {
  method: "POST",
  body: JSON.stringify({ answers }),
}),
```

### Backend Endpoint
```python
# backend/app/api/chat.py
@router.post("/{brand_id}/campaign-answers")
async def submit_campaign_answers(
    brand_id: str,
    campaign_answers: CampaignAnswers,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Submit campaign answers."""
    logger.info(f"[CAMPAIGN-ANSWERS] Received request for brand: {brand_id}, user: {current_user.id}")
    logger.info(f"[CAMPAIGN-ANSWERS] Answers keys: {list(campaign_answers.answers.keys())}")
    
    try:
        brand_uuid = uuid.UUID(brand_id)
    except ValueError as e:
        logger.error(f"Invalid brand ID format: {brand_id}, error: {e}")
        raise HTTPException(status_code=400, detail="Invalid brand ID")
    
    brand = db.query(Brand).filter(
        Brand.id == brand_uuid,
        Brand.user_id == current_user.id
    ).first()
    
    if not brand:
        logger.warning(f"Brand not found: {brand_id} for user: {current_user.id}")
        raise HTTPException(status_code=404, detail="Brand not found")
    
    # Validate answers
    required_keys = ["style", "audience", "emotion", "pacing", "colors"]
    missing_keys = [key for key in required_keys if key not in campaign_answers.answers]
    if missing_keys:
        logger.error(f"Missing required answer keys: {missing_keys}. Received keys: {list(campaign_answers.answers.keys())}")
        raise HTTPException(status_code=400, detail=f"All questions must be answered. Missing: {', '.join(missing_keys)}")
    
    try:
        logger.info(f"[CAMPAIGN-ANSWERS] Creating creative bible for brand: {brand_id}")
        # Create creative bible
        creative_bible = CreativeBible(
            brand_id=brand.id,
            name=f"campaign_{uuid.uuid4().hex[:8]}",
            creative_bible={},
            reference_image_urls={},
            conversation_history=campaign_answers.answers,
            created_at=datetime.utcnow().isoformat()
        )
        logger.info(f"[CAMPAIGN-ANSWERS] CreativeBible object created, adding to session")
        db.add(creative_bible)
        logger.info(f"[CAMPAIGN-ANSWERS] Committing to database...")
        db.commit()
        logger.info(f"[CAMPAIGN-ANSWERS] Commit successful, refreshing object...")
        db.refresh(creative_bible)
        
        logger.info(f"[CAMPAIGN-ANSWERS] Created creative bible: {creative_bible.id} for brand: {brand_id}")
        
        return {
            "creative_bible_id": str(creative_bible.id),
            "message": "Campaign preferences saved successfully"
        }
    except Exception as e:
        logger.error(f"[CAMPAIGN-ANSWERS] Error creating creative bible: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to save campaign answers: {str(e)}")
```

### CreativeBible Model
```python
# backend/app/models/creative_bible.py
class CreativeBible(Base):
    """Creative Bible model."""
    __tablename__ = "creative_bibles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    brand_id = Column(UUID(as_uuid=True), ForeignKey("brands.id"), nullable=False)
    name = Column(String, nullable=False)
    creative_bible = Column(JSON, nullable=False, default=dict)
    reference_image_urls = Column(JSON, nullable=False, default=dict)
    conversation_history = Column(JSON, nullable=True)
    created_at = Column(String, nullable=False)
    
    # Relationships
    campaigns = relationship("Campaign", back_populates="creative_bible")
```

## Symptoms

1. **Frontend**: Request times out after 30 seconds
2. **Backend Logs**: No `[CAMPAIGN-ANSWERS]` logs appear, suggesting request never reaches backend
3. **Fly.io Proxy**: Multiple proxy errors in logs:
   ```
   [PM01] machines API returned an error: "rate limit exceeded"
   [PM01] machines API returned an error: "machine ID ... lease currently held by ..."
   [PR03] could not find a good candidate within 1 attempts at load balancing
   ```

## Environment Details

### Deployment
- **Platform**: Fly.io
- **App Name**: zapcut-api
- **Region**: iad (US East)
- **Machines**: 2 machines running (one may be stopped)

### Infrastructure
- **Backend**: FastAPI (Python 3.11)
- **Database**: PostgreSQL (Supabase)
- **Task Queue**: Celery + Redis (Upstash)
- **Frontend**: React + Vite
- **Auth**: Supabase Auth

### Configuration
```python
# backend/app/config.py
class Settings(BaseSettings):
    DATABASE_URL: Optional[str] = None
    SUPABASE_URL: Optional[str] = None
    SUPABASE_SERVICE_ROLE_KEY: Optional[str] = None
    SUPABASE_JWT_SECRET: Optional[str] = None
    REDIS_URL: Optional[str] = None  # Upstash Redis with SSL
    OPENAI_API_KEY: Optional[str] = None
    REPLICATE_API_TOKEN: Optional[str] = None
```

## Previous Issues (Resolved)

### 1. Brands Not Loading
**Issue**: Brands endpoint was not returning data after Celery migration
**Fix**: Fixed indentation bug in `apiRequest` function - 401 handling was outside try block
**Status**: ✅ Resolved

### 2. Excessive Logging
**Issue**: Backend generating too many logs per second
**Fix**: Reduced logging verbosity, only log important events
**Status**: ✅ Resolved

### 3. Frontend Refresh Crash
**Issue**: App crashed when refreshing during video generation
**Fix**: Added proper cleanup in `useEffect` hooks, validation, and error handling
**Status**: ✅ Resolved

## Current Investigation Points

### 1. Request Not Reaching Backend
- No backend logs appear when request is made
- Suggests Fly.io proxy is blocking/dropping requests
- Proxy errors indicate connectivity issues

### 2. Possible Causes
- **Network/Proxy**: Fly.io proxy having issues connecting to machines
- **Authentication**: Request might be hanging during token verification
- **Database**: Database connection might be slow or hanging
- **CORS**: Preflight request might be failing silently

### 3. Database Status
- User confirmed database exists
- Tables should be initialized
- No database connection errors in logs

## Questions to Investigate

1. **Is the request reaching the backend?**
   - Check if `[CAMPAIGN-ANSWERS] Received request` appears in logs
   - If not, the issue is network/proxy related

2. **Is authentication working?**
   - Check if `get_current_user` dependency is completing
   - Verify token is valid and not expired

3. **Is the database operation hanging?**
   - Check if logs stop at "Committing to database..."
   - Verify database connection pool isn't exhausted

4. **Is CORS blocking the request?**
   - Check browser console for CORS errors
   - Verify preflight OPTIONS request succeeds

## Recommended Debugging Steps

1. **Check Browser Console**
   - Look for `[API] Making request to: ...` log
   - Check Network tab for request status
   - Verify request is actually being sent

2. **Check Backend Logs**
   ```bash
   fly logs --app zapcut-api | grep CAMPAIGN-ANSWERS
   ```

3. **Test Endpoint Directly**
   ```bash
   curl -X POST https://zapcut-api.fly.dev/api/brands/{brandId}/campaign-answers \
     -H "Authorization: Bearer {token}" \
     -H "Content-Type: application/json" \
     -d '{"answers": {"style": "test", "audience": "test", "emotion": "test", "pacing": "test", "colors": "test"}}'
   ```

4. **Check Fly.io Status**
   ```bash
   fly status --app zapcut-api
   fly logs --app zapcut-api --no-tail | tail -50
   ```

## Potential Solutions

### Solution 1: Increase Timeout (Temporary)
```typescript
// frontend/src/services/api.ts
const timeoutId = setTimeout(() => controller.abort(), 60000) // 60 seconds
```

### Solution 2: Add Request Retry Logic
```typescript
// Add exponential backoff retry for network errors
```

### Solution 3: Fix Fly.io Proxy Issues
- Restart the app: `fly apps restart zapcut-api`
- Check machine health: `fly status --app zapcut-api`
- Scale machines if needed

### Solution 4: Add Request Middleware Logging
```python
# Add middleware to log all incoming requests
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Incoming request: {request.method} {request.url}")
    response = await call_next(request)
    return response
```

### Solution 5: Database Connection Pooling
```python
# Check database connection pool settings
# Ensure pool isn't exhausted
```

## Code Changes Made During Investigation

1. **Added detailed logging** to backend endpoint
2. **Improved error messages** in frontend
3. **Added validation** for response structure
4. **Fixed indentation bug** in apiRequest (for brands issue)

## Error Scenarios

### Scenario 1: Request Never Sent
**Symptoms**: No `[API] Making request to:` in browser console
**Cause**: JavaScript error before fetch call
**Fix**: Check browser console for JavaScript errors

### Scenario 2: Request Sent but No Response
**Symptoms**: `[API] Making request to:` appears, but request shows "pending" in Network tab
**Cause**: Network/proxy issue, request not reaching backend
**Fix**: Check Fly.io proxy status, restart app

### Scenario 3: Request Reaches Backend but Hangs
**Symptoms**: Backend logs show `[CAMPAIGN-ANSWERS] Received request` but no completion
**Cause**: Database operation hanging, authentication hanging, or infinite loop
**Fix**: Check database connection, add more granular logging

### Scenario 4: CORS Preflight Failure
**Symptoms**: OPTIONS request fails in Network tab
**Cause**: CORS configuration issue
**Fix**: Verify CORS settings in `backend/app/main.py`

## Next Steps

1. **Immediate**: Check browser console and network tab to see if request is being sent
2. **Short-term**: Verify backend is receiving requests (check logs)
3. **Medium-term**: Fix Fly.io proxy/connectivity issues
4. **Long-term**: Add request monitoring and better error handling

## Debugging Commands

```bash
# Check app status
fly status --app zapcut-api

# View recent logs
fly logs --app zapcut-api --no-tail | tail -100

# Filter for campaign-answers logs
fly logs --app zapcut-api | grep -i "campaign-answers"

# Check machine health
fly machine list --app zapcut-api

# Restart app
fly apps restart zapcut-api

# SSH into machine to debug
fly ssh console --app zapcut-api
```

## Related Files

- `frontend/src/pages/BrandChat.jsx` - Frontend component
- `frontend/src/services/api.ts` - API client
- `backend/app/api/chat.py` - Backend endpoint
- `backend/app/models/creative_bible.py` - Database model
- `backend/app/api/auth.py` - Authentication
- `backend/app/database.py` - Database connection
- `backend/start.sh` - Startup script (runs Celery + FastAPI)

## Deployment Info

- **Startup Script**: `backend/start.sh` runs both Celery worker and FastAPI
- **Celery Config**: `backend/app/celery_app.py` - Uses Upstash Redis with SSL
- **Fly.io Config**: `backend/fly.toml` - Health checks on `/health` endpoint

