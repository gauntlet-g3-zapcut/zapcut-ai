# Fly.io Deployment Guide

## Prerequisites

1. Install Fly CLI:
```bash
curl -L https://fly.io/install.sh | sh
```

2. Login to Fly.io:
```bash
fly auth login
```

## Initial Deployment

### 1. Create App

```bash
cd backend
fly apps create zapcut-api
```

### 2. Deploy Redis (Required for Celery)

Deploy managed Redis via Upstash:

```bash
fly redis create
```

This will prompt for:
- Organization
- Database name (e.g., `zapcut-redis`)
- Primary region (e.g., `iad`)
- Eviction policy (optional)

After creation, get the connection URL:

```bash
fly redis status zapcut-redis
```

### 3. Set Environment Variables

Set all required secrets:

```bash
fly secrets set DATABASE_URL="postgresql://user:pass@host:5432/db"
fly secrets set SUPABASE_URL="https://your-project.supabase.co"
fly secrets set SUPABASE_SERVICE_ROLE_KEY="your-service-role-key"
fly secrets set SUPABASE_JWT_SECRET="your-jwt-secret"  # Optional, for HS256
fly secrets set OPENAI_API_KEY="your-openai-key"
fly secrets set REPLICATE_API_TOKEN="your-replicate-token"
fly secrets set REDIS_URL="redis://default:password@host:port"  # From fly redis status
fly secrets set CORS_ORIGINS="http://localhost:5173,https://app.zapcut.video"
```

### 4. Create PostgreSQL Database

```bash
# Create database
fly postgres create --name zapcut-db --region iad

# Attach to app
fly postgres attach zapcut-db --app zapcut-api
```

This will automatically set `DATABASE_URL` secret.

### 5. Deploy

```bash
fly deploy
```

### 6. Initialize Database

After deployment, initialize the database tables:

```bash
curl -X POST https://zapcut-api.fly.dev/init-db
```

Or use Fly CLI:

```bash
fly ssh console -C "curl -X POST http://localhost:8000/init-db"
```

## Updating Secrets

```bash
fly secrets set KEY="value"
```

View current secrets:

```bash
fly secrets list
```

## Viewing Logs

```bash
fly logs
```

## Scaling

```bash
# Scale to 2 instances
fly scale count 2

# Scale memory
fly scale memory 512
```

## Health Checks

Fly.io automatically checks `/health` endpoint every 30 seconds (configured in `fly.toml`).

## Troubleshooting

### Check app status:
```bash
fly status
```

### SSH into app:
```bash
fly ssh console
```

### View app info:
```bash
fly info
```

### Restart app:
```bash
fly apps restart zapcut-api
```

## Custom Domain

1. Add domain in Fly.io dashboard
2. Update DNS records as instructed
3. Fly.io will automatically provision SSL certificate

## Monitoring

- View metrics in Fly.io dashboard
- Set up alerts for health check failures
- Monitor logs with `fly logs`

