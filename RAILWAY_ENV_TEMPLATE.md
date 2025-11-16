# Railway Environment Variables Template

Copy-paste these into Railway for each service.

## 1. Backend API Service

```bash
# Database Configuration
DATABASE_URL=postgresql://postgres:[PASSWORD]@db.[PROJECT_REF].supabase.co:5432/postgres
# OR leave blank and set these for auto-construction:
SUPABASE_URL=https://[PROJECT_REF].supabase.co
SUPABASE_DB_PASSWORD=[YOUR_DB_PASSWORD]

# Supabase Configuration
SUPABASE_SERVICE_ROLE_KEY=[YOUR_SERVICE_ROLE_KEY]

# Redis Configuration (Reference Railway Redis service)
REDIS_URL=${{Redis.REDIS_URL}}

# API Keys
OPENAI_API_KEY=[YOUR_OPENAI_KEY]
REPLICATE_API_TOKEN=[YOUR_REPLICATE_TOKEN]

# CORS Configuration (Update after frontend is deployed)
CORS_ORIGINS=https://app.zapcut.video,${{Frontend.RAILWAY_PUBLIC_DOMAIN}},http://localhost:5173

# Port (Railway sets this automatically, but can be explicit)
PORT=8000
```

---

## 2. Celery Worker Service

**Copy ALL variables from Backend API, except PORT and CORS_ORIGINS:**

```bash
# Database Configuration
DATABASE_URL=postgresql://postgres:[PASSWORD]@db.[PROJECT_REF].supabase.co:5432/postgres
# OR leave blank and set these:
SUPABASE_URL=https://[PROJECT_REF].supabase.co
SUPABASE_DB_PASSWORD=[YOUR_DB_PASSWORD]

# Supabase Configuration
SUPABASE_SERVICE_ROLE_KEY=[YOUR_SERVICE_ROLE_KEY]

# Redis Configuration
REDIS_URL=${{Redis.REDIS_URL}}

# API Keys
OPENAI_API_KEY=[YOUR_OPENAI_KEY]
REPLICATE_API_TOKEN=[YOUR_REPLICATE_TOKEN]
```

---

## 3. Frontend Service

```bash
# Backend API URL (Update with your actual backend Railway domain)
VITE_API_URL=https://[BACKEND_DOMAIN].railway.app

# Supabase Configuration
VITE_SUPABASE_URL=https://[PROJECT_REF].supabase.co
VITE_SUPABASE_ANON_KEY=[YOUR_SUPABASE_ANON_KEY]
```

---

## Railway Variable References

Railway allows you to reference other services using `${{ServiceName.VARIABLE}}`:

- **Redis URL**: `${{Redis.REDIS_URL}}`
- **Backend Domain**: `${{Backend.RAILWAY_PUBLIC_DOMAIN}}`
- **Frontend Domain**: `${{Frontend.RAILWAY_PUBLIC_DOMAIN}}`

### Example:
If your services are named:
- `backend-api`
- `celery-worker`
- `frontend-app`
- `redis`

Then use:
- `${{redis.REDIS_URL}}`
- `${{backend-api.RAILWAY_PUBLIC_DOMAIN}}`
- `${{frontend-app.RAILWAY_PUBLIC_DOMAIN}}`

**Note**: Railway auto-generates REDIS_URL when you create Redis service.

---

## Finding Your Credentials

### Supabase Credentials

1. Go to https://app.supabase.com
2. Select your project
3. Go to "Settings" → "API"

**You'll find:**
- `SUPABASE_URL`: "Project URL"
- `SUPABASE_ANON_KEY`: "Project API keys" → anon/public key
- `SUPABASE_SERVICE_ROLE_KEY`: "Project API keys" → service_role key

4. Go to "Settings" → "Database"

**You'll find:**
- `SUPABASE_DB_PASSWORD`: Your database password
- Full `DATABASE_URL`: Under "Connection string" → "URI"

### OpenAI API Key

1. Go to https://platform.openai.com
2. Click on your profile → "API Keys"
3. Create or copy your API key

### Replicate API Token

1. Go to https://replicate.com
2. Click on your profile → "API Tokens"
3. Create or copy your API token

---

## Deployment Order

1. **Create services in this order:**
   - Redis (first)
   - Backend API (second, references Redis)
   - Celery Worker (third, references Redis)
   - Frontend (last, references Backend)

2. **After each deployment, copy the domain:**
   - Backend → Copy domain → Update in Frontend's `VITE_API_URL`
   - Frontend → Copy domain → Update in Backend's `CORS_ORIGINS`

3. **Redeploy services after updating cross-references**

---

## Verification Checklist

After setting all environment variables:

### Backend API
- [ ] Can connect to Supabase PostgreSQL
- [ ] Can connect to Redis
- [ ] CORS includes frontend domain
- [ ] `/health` endpoint returns `{"status":"healthy"}`

### Celery Worker
- [ ] Logs show "Connected to redis"
- [ ] Logs show task registration
- [ ] Can connect to database

### Frontend
- [ ] Can load in browser
- [ ] API calls go to correct backend domain
- [ ] Supabase auth works
- [ ] No CORS errors in console

---

## Common Issues

### DATABASE_URL Format

**Correct:**
```
postgresql://postgres:password@db.xxxxx.supabase.co:5432/postgres
```

**Incorrect:**
```
postgres://postgres:password@db.xxxxx.supabase.co:5432/postgres  # Wrong schema
postgresql://postgres@db.xxxxx.supabase.co:5432/postgres  # Missing password
```

### Redis URL Format

Railway auto-generates this, but it should look like:
```
redis://default:[password]@[host]:6379
```

**Don't manually set this** - use `${{Redis.REDIS_URL}}`

### CORS Origins Format

**Correct:**
```
CORS_ORIGINS=https://frontend.railway.app,https://app.zapcut.video,http://localhost:5173
```

**Incorrect:**
```
CORS_ORIGINS=frontend.railway.app  # Missing https://
CORS_ORIGINS=https://frontend.railway.app/  # Trailing slash
CORS_ORIGINS="https://frontend.railway.app"  # Quotes (Railway adds them automatically)
```

---

## Production vs Development

### Development (Local)

```bash
# Backend .env
DATABASE_URL=postgresql://postgres:password@localhost:5432/adcraft
REDIS_URL=redis://localhost:6379/0
CORS_ORIGINS=http://localhost:5173,http://localhost:5174
API_URL=http://localhost:8000

# Frontend .env.local
VITE_API_URL=http://localhost:8000
```

### Production (Railway)

Use the variables from sections 1-3 above with:
- Railway-provided Redis URL
- Railway-provided public domains
- Production Supabase credentials

---

## Security Notes

1. **Never commit these values to git**
2. **Use Railway's environment variable UI** - they're encrypted
3. **Rotate keys regularly** (especially service role keys)
4. **Use different credentials for dev/prod**
5. **Don't share service role keys** - they have admin access

---

**Last Updated**: ___________
