# Backend Structure

## Clean Implementation from Scratch

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration from env vars
│   ├── database.py          # SQLAlchemy setup
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── brand.py
│   │   ├── campaign.py
│   │   └── creative_bible.py
│   └── api/
│       ├── __init__.py
│       ├── auth.py          # Authentication routes
│       ├── brands.py        # Brand CRUD
│       ├── campaigns.py     # Campaign management
│       └── chat.py          # Chat/storyline routes
├── requirements.txt         # Python dependencies
├── Dockerfile              # Docker image for Fly.io
├── fly.toml                # Fly.io configuration
├── .dockerignore
├── .gitignore
├── README.md
└── DEPLOY.md               # Deployment guide
```

## Key Features

- ✅ Clean, simple structure
- ✅ No duplicate code
- ✅ Single source of truth
- ✅ Structured logging
- ✅ Fly.io ready
- ✅ Docker containerized
- ✅ Health checks configured

## API Endpoints

### Public
- `GET /` - Root
- `GET /health` - Health check
- `GET /cors-info` - CORS config
- `POST /init-db` - Initialize database

### Authentication
- `POST /api/auth/verify` - Verify token
- `GET /api/auth/me` - Get current user

### Brands
- `GET /api/brands` - List brands
- `POST /api/brands` - Create brand
- `GET /api/brands/{id}` - Get brand

### Campaigns
- `POST /api/campaigns` - Create campaign
- `GET /api/campaigns/{id}` - Get campaign
- `GET /api/campaigns/{id}/status` - Get status

### Chat
- `POST /api/brands/{id}/campaign-answers` - Submit answers
- `GET /api/brands/{id}/storyline/{creative_bible_id}` - Get storyline

