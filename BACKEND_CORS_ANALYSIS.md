# Backend Implementation & CORS Issue Analysis

## Executive Summary

This report analyzes the backend FastAPI implementation, focusing on the CORS (Cross-Origin Resource Sharing) issue that occurred when the backend returned a 500 Internal Server Error. The root cause was an unhandled exception (`KeyError: 'asyncio'` in the anyio library) that prevented CORS headers from being sent to the client, resulting in a CORS error in the browser.

---

## Table of Contents

1. [Backend Architecture Overview](#backend-architecture-overview)
2. [CORS Configuration](#cors-configuration)
3. [Request Flow & Middleware Order](#request-flow--middleware-order)
4. [Root Cause Analysis](#root-cause-analysis)
5. [The CORS Issue Explained](#the-cors-issue-explained)
6. [Solutions Implemented](#solutions-implemented)
7. [Recommendations](#recommendations)

---

## Backend Architecture Overview

### Technology Stack

- **Framework**: FastAPI 0.109.0
- **ASGI Server**: Uvicorn 0.27.0 (with standard extras)
- **Database**: PostgreSQL (via SQLAlchemy 2.0.25)
- **Authentication**: Supabase JWT tokens (RS256 via JWKS, HS256 via JWT secret)
- **Task Queue**: Celery 5.3.4 with Redis
- **Deployment**: Railway (using Nixpacks)

### Application Structure

```
backend/
├── app/
│   ├── main.py              # FastAPI app initialization, CORS config
│   ├── config.py            # Settings and environment variables
│   ├── database.py           # Database connection and session management
│   ├── api/
│   │   ├── auth.py          # Authentication & JWT verification
│   │   ├── brands.py        # Brand management endpoints
│   │   ├── campaigns.py     # Campaign endpoints
│   │   └── chat.py          # Chat/AI endpoints
│   ├── models/              # SQLAlchemy models
│   └── services/            # Business logic services
├── requirements.txt         # Python dependencies
└── start.sh                 # Railway startup script
```

### Key Components

#### 1. Application Initialization (`app/main.py`)

```python
# FastAPI app creation
app = FastAPI(title="AdCraft API", version="1.0.0")

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)

# Router registration
app.include_router(auth.router)
app.include_router(brands.router)
app.include_router(chat.router)
app.include_router(campaigns.router)
```

#### 2. Authentication Flow (`app/api/auth.py`)

The authentication system uses Supabase JWT tokens with dual algorithm support:

- **RS256 (Modern)**: Verified using JWKS (JSON Web Key Set) from Supabase
- **HS256 (Legacy)**: Verified using `SUPABASE_JWT_SECRET` environment variable

**Token Verification Process:**
1. Extract token from `Authorization: Bearer <token>` header
2. Decode JWT header to determine algorithm (RS256 or HS256)
3. Verify token signature using appropriate method
4. Validate token claims (expiration, audience, issuer)
5. Return decoded token data or raise `HTTPException(401)`

**User Resolution:**
- Extract `sub` (user ID) from verified token
- Query database for existing user by `supabase_uid`
- Create new user if not found
- Return `User` object for use in route handlers

#### 3. Database Configuration (`app/config.py`)

The settings system uses Pydantic Settings with environment variable support:

- **Database URL**: Can be set directly or constructed from Supabase credentials
- **CORS Origins**: Configurable via `CORS_ORIGINS` environment variable
- **Supabase Config**: URL, service role key, DB password, JWT secret

---

## CORS Configuration

### Current CORS Setup

```python
# Default origins (hardcoded)
default_origins = [
    "https://app.zapcut.video",  # Production frontend
    "http://localhost:5173",     # Local development
    "http://localhost:5175",
    "http://localhost:3000",
]

# Merge with environment variable origins
env_origins = settings.cors_origins_list
cors_origins = list(set(default_origins + env_origins))

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,  # Allows cookies/auth headers
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],     # Allows all headers
    expose_headers=["*"],     # Exposes all headers to client
    max_age=3600,           # Cache preflight for 1 hour
)
```

### CORS Headers Sent

When a request is allowed, FastAPI's CORSMiddleware adds these headers:

```
Access-Control-Allow-Origin: https://app.zapcut.video
Access-Control-Allow-Credentials: true
Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS, PATCH
Access-Control-Allow-Headers: *
Access-Control-Expose-Headers: *
Access-Control-Max-Age: 3600
```

### Preflight Requests (OPTIONS)

For CORS preflight requests (OPTIONS), the middleware:
1. Intercepts the request before it reaches route handlers
2. Returns a 200 OK response with CORS headers
3. Does not execute the actual route handler

---

## Request Flow & Middleware Order

### Normal Request Flow

```
1. Client sends request
   ↓
2. Uvicorn receives request
   ↓
3. FastAPI application receives request
   ↓
4. CORSMiddleware processes request
   ├─ If OPTIONS: Return 200 with CORS headers (preflight)
   └─ If other method: Continue to next middleware
   ↓
5. Exception handling middleware (if any)
   ↓
6. Route handler execution
   ├─ Dependency injection (auth, database)
   ├─ Business logic
   └─ Return response
   ↓
7. CORSMiddleware adds CORS headers to response
   ↓
8. Response sent to client
```

### Middleware Execution Order

FastAPI middleware executes in **reverse order** of registration:

1. **Last registered** → **First executed** (request phase)
2. **First registered** → **Last executed** (response phase)

In our case:
- CORSMiddleware is registered first
- It executes last in the response phase
- This ensures CORS headers are added to all responses

### Exception Handling Flow

When an exception occurs:

```
1. Exception raised in route handler or dependency
   ↓
2. FastAPI's exception handler catches it
   ↓
3. Exception handler creates error response
   ↓
4. CORSMiddleware should add CORS headers
   ↓
5. Error response sent to client
```

**Problem**: If the exception occurs in middleware or before the response is created, CORS headers may not be added.

---

## Root Cause Analysis

### The AnyIO KeyError Issue

**Error Message:**
```
KeyError: 'asyncio'
  File "/opt/venv/lib/python3.12/site-packages/anyio/_core/_eventloop.py", line 162, in get_async_backend
    return loaded_backends[asynclib_name]
```

**What Happened:**

1. **Python 3.12 Compatibility Issue**: The anyio library version (likely < 4.3.0) was incompatible with Python 3.12.7 used on Railway.

2. **Exception Location**: The error occurred during async event loop initialization, which happens:
   - During request processing
   - In the ASGI middleware stack
   - Before route handlers execute
   - Before CORS headers can be added

3. **Impact on CORS**: When the exception occurred:
   - FastAPI's exception handler tried to create an error response
   - The exception happened in the async infrastructure layer
   - The response creation process failed
   - CORS headers were never added to the response
   - Browser received a response without CORS headers
   - Browser blocked the response with CORS error

### Why CORS Headers Were Missing

**Technical Explanation:**

1. **Exception in ASGI Layer**: The `KeyError: 'asyncio'` occurred in the anyio library, which is used by Starlette (FastAPI's underlying framework) for async operations.

2. **Response Creation Failure**: When an exception occurs in the ASGI middleware stack:
   - The normal response flow is interrupted
   - FastAPI's exception handler attempts to create an error response
   - However, if the exception occurs in the async infrastructure, the response creation itself may fail
   - The CORSMiddleware's response phase never executes

3. **Browser Behavior**: When the browser receives a response without CORS headers:
   - The browser checks for `Access-Control-Allow-Origin` header
   - If missing, the browser blocks the response
   - The browser shows a CORS error in the console
   - The actual HTTP status (500) may not be visible to the client

### Error Sequence

```
1. Frontend sends: GET /api/brands/ with Authorization header
   ↓
2. Backend receives request
   ↓
3. CORSMiddleware processes request (request phase)
   ↓
4. Route handler dependency injection starts
   ├─ verify_token() called
   ├─ JWT verification attempts
   └─ AnyIO async operation triggered
   ↓
5. ❌ KeyError: 'asyncio' in anyio library
   ↓
6. Exception propagates to FastAPI exception handler
   ↓
7. Exception handler tries to create 500 response
   ↓
8. ❌ Response creation fails or CORS middleware skipped
   ↓
9. Response sent without CORS headers
   ↓
10. Browser blocks response → CORS error shown
```

---

## The CORS Issue Explained

### What is CORS?

**Cross-Origin Resource Sharing (CORS)** is a security mechanism implemented by web browsers that restricts web pages from making requests to a different domain than the one that served the web page.

### Why CORS Exists

- **Security**: Prevents malicious websites from making unauthorized requests to other domains
- **Same-Origin Policy**: Browsers enforce that requests must be from the same origin (protocol + domain + port)
- **Exception**: CORS allows cross-origin requests when the server explicitly permits them

### CORS Requirements

For a cross-origin request to succeed:

1. **Preflight Request (OPTIONS)**: For certain requests, browser sends OPTIONS request first
   - Server must respond with 200 OK
   - Server must include CORS headers
   - Browser checks headers before sending actual request

2. **Actual Request**: Browser sends the actual request
   - Server must include `Access-Control-Allow-Origin` header
   - Header must match the request's `Origin` header
   - For credentialed requests, `Access-Control-Allow-Credentials: true` required

3. **Response Headers**: Server must include:
   - `Access-Control-Allow-Origin: <origin>` (or `*` for non-credentialed requests)
   - `Access-Control-Allow-Credentials: true` (if using cookies/auth)
   - `Access-Control-Allow-Methods: <methods>` (for preflight)
   - `Access-Control-Allow-Headers: <headers>` (for preflight)

### Our Specific CORS Issue

**Error Message:**
```
Access to fetch at 'https://zapcut-ai-production.up.railway.app/api/brands/' 
from origin 'http://localhost:5173' has been blocked by CORS policy: 
No 'Access-Control-Allow-Origin' header is present on the requested resource.
```

**What This Means:**

1. **Request Origin**: `http://localhost:5173` (frontend)
2. **Target Origin**: `https://zapcut-ai-production.up.railway.app` (backend)
3. **Cross-Origin**: Different origins (different protocol, domain, port)
4. **Missing Header**: Response did not include `Access-Control-Allow-Origin`
5. **Browser Action**: Browser blocked the response

**Why the Header Was Missing:**

- The 500 Internal Server Error occurred before CORS headers could be added
- The exception in the anyio library prevented normal response processing
- FastAPI's exception handler may not have properly invoked CORS middleware
- The response was sent without CORS headers

---

## Solutions Implemented

### 1. Fixed AnyIO Compatibility Issue

**Problem**: anyio < 4.3.0 incompatible with Python 3.12

**Solution**: Updated `requirements.txt`:
```python
anyio>=4.3.0
sniffio>=1.3.0
```

**Result**: Resolved the `KeyError: 'asyncio'` that was causing 500 errors

### 2. Improved Error Handling

**Problem**: Unhandled exceptions could prevent CORS headers

**Solution**: Added comprehensive error handling in `app/api/auth.py`:

```python
async def get_current_user(...):
    try:
        # User resolution logic
        ...
    except HTTPException:
        raise  # Re-raise HTTP exceptions (they include proper status codes)
    except Exception as e:
        # Log error
        print(f"❌ get_current_user error: {type(e).__name__}: {e}", file=sys.stderr)
        # Return proper HTTPException (ensures CORS headers are added)
        raise HTTPException(
            status_code=500,
            detail="Internal server error during authentication"
        )
```

**Result**: All exceptions now return proper HTTPException responses, which go through CORS middleware

### 3. Enhanced JWT Verification Error Handling

**Problem**: JWT verification errors could cause unhandled exceptions

**Solution**: Added specific exception handling for JWT operations:

```python
try:
    decoded_token = jwt.decode(...)
except jwt.ExpiredSignatureError:
    raise HTTPException(status_code=401, detail="Token has expired")
except jwt.InvalidSignatureError:
    raise HTTPException(status_code=401, detail="Invalid token signature")
except jwt.DecodeError as e:
    raise HTTPException(status_code=401, detail=f"Token decode error: {str(e)}")
except jwt.InvalidTokenError as e:
    raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")
except Exception as e:
    # Log and return proper error
    raise HTTPException(status_code=401, detail=f"Failed to verify token: {str(e)}")
```

**Result**: All JWT errors return proper HTTPException responses with CORS headers

---

## Recommendations

### 1. Add Global Exception Handler

**Current State**: FastAPI has default exception handling, but we should add a custom handler to ensure CORS headers are always added.

**Recommendation**: Add a global exception handler:

```python
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler that ensures CORS headers are always added"""
    # Log the error
    print(f"❌ Unhandled exception: {type(exc).__name__}: {exc}", file=sys.stderr)
    
    # Create error response
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "type": type(exc).__name__
        }
    )
    # CORS headers will be added by CORSMiddleware in response phase
```

**Benefits**:
- Ensures all exceptions return proper responses
- CORS headers are always added via middleware
- Better error logging and debugging

### 2. Add CORS Preflight Handler

**Current State**: CORSMiddleware handles OPTIONS requests automatically.

**Recommendation**: Add explicit OPTIONS handler for debugging:

```python
@app.options("/{full_path:path}")
async def options_handler(request: Request):
    """Explicit OPTIONS handler for CORS preflight"""
    return {"status": "ok"}
```

**Benefits**:
- Explicit control over preflight responses
- Better debugging capabilities
- Can add custom headers if needed

### 3. Add Request Logging Middleware

**Recommendation**: Add middleware to log all requests and responses:

```python
from starlette.middleware.base import BaseHTTPMiddleware
import time

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        
        print(f"{request.method} {request.url.path} - {response.status_code} - {process_time:.3f}s")
        return response

app.add_middleware(LoggingMiddleware)  # Add before CORSMiddleware
```

**Benefits**:
- Track request/response times
- Debug CORS issues
- Monitor API usage

### 4. Add Health Check Endpoint

**Current State**: We have `/health` endpoint.

**Recommendation**: Enhance it to check dependencies:

```python
@app.get("/health")
async def health():
    """Health check endpoint"""
    checks = {
        "status": "healthy",
        "database": "unknown",
        "supabase": "unknown",
    }
    
    # Check database
    try:
        db = next(get_db())
        db.execute("SELECT 1")
        checks["database"] = "connected"
    except:
        checks["database"] = "disconnected"
        checks["status"] = "degraded"
    
    # Check Supabase
    if settings.SUPABASE_URL:
        checks["supabase"] = "configured"
    
    status_code = 200 if checks["status"] == "healthy" else 503
    return JSONResponse(content=checks, status_code=status_code)
```

### 5. Environment Variable Validation

**Recommendation**: Add startup validation for required environment variables:

```python
@app.on_event("startup")
async def startup_event():
    """Validate required environment variables on startup"""
    required_vars = [
        "SUPABASE_URL",
        "SUPABASE_SERVICE_ROLE_KEY",
        "DATABASE_URL",
    ]
    
    missing = [var for var in required_vars if not getattr(settings, var, None)]
    if missing:
        print(f"⚠️  WARNING: Missing environment variables: {missing}")
        # Don't exit - allow graceful degradation
```

### 6. CORS Configuration Improvements

**Current State**: CORS origins are hardcoded and merged with environment variables.

**Recommendation**: 
- Use environment variable for all origins in production
- Add origin validation
- Add CORS debug endpoint

```python
@app.get("/cors-info")
async def cors_info():
    """Debug endpoint to check CORS configuration"""
    return {
        "cors_origins": cors_origins,
        "request_origin": request.headers.get("origin"),
        "allowed": request.headers.get("origin") in cors_origins,
    }
```

### 7. Add Response Headers Middleware

**Recommendation**: Add security headers to all responses:

```python
from starlette.middleware.base import BaseHTTPMiddleware

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        return response

app.add_middleware(SecurityHeadersMiddleware)  # Add after CORSMiddleware
```

---

## Testing CORS Configuration

### Manual Testing

1. **Test Preflight Request**:
```bash
curl -X OPTIONS https://zapcut-ai-production.up.railway.app/api/brands/ \
  -H "Origin: http://localhost:5173" \
  -H "Access-Control-Request-Method: GET" \
  -v
```

**Expected Response**:
```
HTTP/1.1 200 OK
Access-Control-Allow-Origin: http://localhost:5173
Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS, PATCH
Access-Control-Allow-Headers: *
Access-Control-Allow-Credentials: true
```

2. **Test Actual Request**:
```bash
curl -X GET https://zapcut-ai-production.up.railway.app/api/brands/ \
  -H "Origin: http://localhost:5173" \
  -H "Authorization: Bearer <token>" \
  -v
```

**Expected Response**:
```
HTTP/1.1 200 OK
Access-Control-Allow-Origin: http://localhost:5173
Access-Control-Allow-Credentials: true
```

3. **Test Error Response**:
```bash
curl -X GET https://zapcut-ai-production.up.railway.app/api/brands/ \
  -H "Origin: http://localhost:5173" \
  -H "Authorization: Bearer invalid_token" \
  -v
```

**Expected Response**:
```
HTTP/1.1 401 Unauthorized
Access-Control-Allow-Origin: http://localhost:5173
Access-Control-Allow-Credentials: true
```

### Automated Testing

Add pytest tests for CORS:

```python
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_cors_preflight():
    response = client.options(
        "/api/brands/",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        }
    )
    assert response.status_code == 200
    assert "Access-Control-Allow-Origin" in response.headers
    assert response.headers["Access-Control-Allow-Origin"] == "http://localhost:5173"

def test_cors_actual_request():
    response = client.get(
        "/api/brands/",
        headers={"Origin": "http://localhost:5173"}
    )
    assert "Access-Control-Allow-Origin" in response.headers
```

---

## Conclusion

The CORS issue was caused by an unhandled exception (`KeyError: 'asyncio'` in anyio) that prevented CORS headers from being added to error responses. The fix involved:

1. **Updating dependencies** to resolve Python 3.12 compatibility issues
2. **Improving error handling** to ensure all exceptions return proper HTTPException responses
3. **Enhancing JWT verification** with specific exception handling

The backend CORS configuration is correct and should work properly now that the underlying exception issue is resolved. All responses (including errors) should now include CORS headers, allowing the frontend to receive and handle responses properly.

**Key Takeaway**: When debugging CORS issues, always check:
1. Is the server actually sending CORS headers? (Check network tab)
2. Are exceptions preventing CORS headers from being added?
3. Is the origin in the allowed origins list?
4. Are credentials being used correctly?

---

## Appendix: FastAPI CORS Middleware Documentation

For more information, see:
- [FastAPI CORS Documentation](https://fastapi.tiangolo.com/tutorial/cors/)
- [Starlette CORSMiddleware](https://www.starlette.io/middleware/#corsmiddleware)
- [MDN CORS Guide](https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS)

