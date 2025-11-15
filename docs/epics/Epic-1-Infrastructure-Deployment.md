# Epic 1: Infrastructure & Deployment Pipeline

**Status:** Not Started
**Priority:** P0 (Must complete before all other epics)
**Estimated Effort:** 1-2 weeks
**Dependencies:** None

---

## Epic Overview

### Value Proposition
Establish production-ready infrastructure and CI/CD pipeline so that every subsequent epic can be deployed, tested, and validated in production-like environments from day one.

### Success Criteria
- [ ] Backend API deployable to AWS with one command
- [ ] Frontend (Electron app) builds and packages successfully
- [ ] Database migrations run automatically on deployment
- [ ] CI/CD pipeline runs tests and deploys on merge to main
- [ ] Monitoring and logging infrastructure operational
- [ ] Development, staging, and production environments configured

### Demo Scenario
1. Push code to GitHub
2. CI/CD pipeline triggers automatically
3. Tests run in pipeline
4. On success, deploys to staging environment
5. Smoke tests verify deployment
6. Can promote to production with approval

---

## Technical Stack

### Infrastructure
- **Cloud Provider:** AWS
- **Compute:** ECS Fargate (backend API) or EC2
- **Database:** RDS PostgreSQL
- **Storage:** S3 (video assets, generated files)
- **Cache/Queue:** ElastiCache Redis
- **CDN:** CloudFront (for static assets)

### CI/CD
- **Pipeline:** GitHub Actions
- **Container Registry:** AWS ECR
- **IaC:** Terraform or AWS CDK

### Monitoring
- **Application Monitoring:** Sentry (errors)
- **Logs:** CloudWatch Logs
- **Metrics:** CloudWatch Metrics
- **Uptime:** UptimeRobot or Pingdom

---

## User Stories

### Story 1.1: AWS Infrastructure Setup
**As a** DevOps engineer
**I want** to provision all AWS resources via Infrastructure as Code
**So that** environments are reproducible and version-controlled

**Acceptance Criteria:**
- [ ] Terraform/CDK scripts create all AWS resources
- [ ] Resources include: VPC, subnets, security groups, RDS, S3, ECS cluster
- [ ] Scripts work idempotently (can run multiple times safely)
- [ ] State is stored remotely (Terraform Cloud or S3 backend)
- [ ] Variables configured for dev/staging/prod environments
- [ ] Documentation exists for running infrastructure setup

**Frontend:** N/A
**Backend:** N/A
**Database:**
- RDS PostgreSQL instance provisioned
- Connection string stored in Secrets Manager

**Tasks:**
- [ ] Install and configure Terraform/CDK
- [ ] Write IaC scripts for networking (VPC, subnets)
- [ ] Write IaC scripts for RDS PostgreSQL
- [ ] Write IaC scripts for S3 buckets
- [ ] Write IaC scripts for Redis (ElastiCache)
- [ ] Write IaC scripts for ECS cluster
- [ ] Configure remote state storage
- [ ] Test infrastructure provisioning
- [ ] Document infrastructure setup process

---

### Story 1.2: Backend API Deployment Pipeline
**As a** developer
**I want** the backend API to deploy automatically on merge
**So that** changes reach production quickly and reliably

**Acceptance Criteria:**
- [ ] GitHub Actions workflow builds Docker image
- [ ] Workflow pushes image to ECR
- [ ] Workflow deploys to ECS Fargate
- [ ] Health check endpoint verifies deployment
- [ ] Rollback mechanism in place for failed deployments
- [ ] Environment variables injected from Secrets Manager
- [ ] Deployment completes in < 10 minutes

**Frontend:** N/A
**Backend:**
- Health check endpoint: `GET /health`
- Returns: `{ "status": "healthy", "version": "1.0.0", "timestamp": "..." }`

**Database:**
- Migrations run automatically before deployment

**Tasks:**
- [ ] Create Dockerfile for FastAPI app
- [ ] Write GitHub Actions workflow for backend
- [ ] Configure ECR repository
- [ ] Create ECS task definition
- [ ] Create ECS service with load balancer
- [ ] Implement health check endpoint
- [ ] Configure secrets management
- [ ] Test deployment pipeline
- [ ] Add rollback mechanism
- [ ] Document deployment process

---

### Story 1.3: Database Migration System
**As a** developer
**I want** database schema changes to deploy automatically
**So that** database stays in sync with application code

**Acceptance Criteria:**
- [ ] Alembic configured for database migrations
- [ ] Migrations run automatically on deployment
- [ ] Migration status is logged
- [ ] Failed migrations block deployment
- [ ] Can rollback migrations if needed
- [ ] Migrations tested in staging before production

**Frontend:** N/A
**Backend:**
- Migration command integrated into deployment script

**Database:**
- Alembic migration history table created
- Initial migration creates base schema

**Tasks:**
- [ ] Install and configure Alembic
- [ ] Create initial migration (users table)
- [ ] Integrate migrations into deployment pipeline
- [ ] Add migration status logging
- [ ] Test migration rollback process
- [ ] Document migration workflow

---

### Story 1.4: Frontend Build & Package Pipeline
**As a** developer
**I want** Electron app to build and package automatically
**So that** we can distribute releases efficiently

**Acceptance Criteria:**
- [ ] GitHub Actions workflow builds Electron app
- [ ] Builds for macOS, Windows, Linux
- [ ] Auto-updates configured with electron-updater
- [ ] Code signing configured for macOS
- [ ] Installers uploaded to S3 or GitHub Releases
- [ ] Version numbers auto-incremented
- [ ] Build completes in < 15 minutes

**Frontend:**
- Vite production build configuration
- Electron packaging with electron-builder

**Backend:** N/A
**Database:** N/A

**Tasks:**
- [ ] Configure Vite for production builds
- [ ] Configure electron-builder
- [ ] Write GitHub Actions workflow for frontend
- [ ] Set up code signing certificates
- [ ] Configure auto-update mechanism
- [ ] Test builds on all platforms
- [ ] Document release process

---

### Story 1.5: Environment Configuration Management
**As a** developer
**I want** environment-specific configurations managed securely
**So that** secrets are never committed to code

**Acceptance Criteria:**
- [ ] AWS Secrets Manager stores all secrets
- [ ] Environment variables injected at runtime
- [ ] Separate configs for dev/staging/prod
- [ ] API keys for OpenAI, Replicate, Suno stored securely
- [ ] Database credentials stored securely
- [ ] Frontend can access backend API URL via env config

**Frontend:**
- Environment variables: `VITE_API_BASE_URL`

**Backend:**
- Environment variables loaded from AWS Secrets Manager
- Required vars: `DATABASE_URL`, `REDIS_URL`, `OPENAI_API_KEY`, `REPLICATE_API_KEY`, `SUNO_API_KEY`, `JWT_SECRET`

**Database:**
- Connection credentials stored in Secrets Manager

**Tasks:**
- [ ] Create Secrets Manager entries
- [ ] Configure backend to load from Secrets Manager
- [ ] Configure frontend environment variables
- [ ] Test environment switching
- [ ] Document secret management process

---

### Story 1.6: Monitoring & Logging Setup
**As an** operations engineer
**I want** comprehensive logging and monitoring
**So that** I can diagnose issues quickly

**Acceptance Criteria:**
- [ ] Sentry configured for error tracking
- [ ] CloudWatch Logs collecting application logs
- [ ] CloudWatch Metrics tracking API response times
- [ ] Uptime monitoring alerts on downtime
- [ ] Log retention policy configured (30 days)
- [ ] Dashboards created for key metrics

**Frontend:**
- Sentry SDK integrated for error reporting

**Backend:**
- Structured logging to CloudWatch
- Sentry SDK integrated
- Custom metrics emitted to CloudWatch

**Database:**
- Slow query logging enabled
- CloudWatch metrics for connections, CPU

**Tasks:**
- [ ] Set up Sentry project
- [ ] Integrate Sentry in frontend
- [ ] Integrate Sentry in backend
- [ ] Configure CloudWatch Logs groups
- [ ] Set up CloudWatch Metrics
- [ ] Create CloudWatch Dashboard
- [ ] Configure UptimeRobot monitoring
- [ ] Set up alerting rules
- [ ] Test error tracking flow
- [ ] Document monitoring setup

---

### Story 1.7: Smoke Tests & Deployment Verification
**As a** QA engineer
**I want** automated smoke tests after deployment
**So that** broken deployments are caught immediately

**Acceptance Criteria:**
- [ ] Smoke test script runs after deployment
- [ ] Tests verify: API health, database connectivity, Redis connectivity
- [ ] Failed smoke tests trigger rollback
- [ ] Tests complete in < 2 minutes
- [ ] Test results reported in deployment logs

**Frontend:**
- Basic app launch test

**Backend:**
- Smoke test endpoints:
  - `GET /health` - Returns 200
  - `GET /api/health/db` - Verifies DB connection
  - `GET /api/health/redis` - Verifies Redis connection

**Database:**
- Health check query: `SELECT 1`

**Tasks:**
- [ ] Write smoke test script
- [ ] Integrate into deployment pipeline
- [ ] Add rollback trigger on failure
- [ ] Test failure scenarios
- [ ] Document smoke test process

---

## Database Schema (Initial)

```sql
-- Migration 001: Initial schema

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255),
    password_hash VARCHAR(255),
    subscription_tier VARCHAR(50) DEFAULT 'free',
    credits INTEGER DEFAULT 0,
    free_videos_used INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_users_email ON users(email);
```

---

## API Endpoints

### Health Check Endpoints

```
GET /health
Response: { "status": "healthy", "version": "1.0.0" }

GET /api/health/db
Response: { "status": "healthy", "database": "connected" }

GET /api/health/redis
Response: { "status": "healthy", "redis": "connected" }
```

---

## Testing Strategy

### Infrastructure Tests
- Terraform validate and plan in CI
- Test infrastructure in dev environment first

### Deployment Tests
- Smoke tests run automatically
- Manual QA in staging before production

### Monitoring Tests
- Test error reporting by triggering sample error
- Verify alerts fire correctly

---

## Definition of Done

- [ ] All AWS infrastructure provisioned via IaC
- [ ] Backend API deploys automatically via CI/CD
- [ ] Database migrations run automatically
- [ ] Frontend builds and packages for all platforms
- [ ] Secrets managed securely (no hardcoded credentials)
- [ ] Monitoring and logging operational
- [ ] Smoke tests pass after deployment
- [ ] Documentation complete for all processes
- [ ] Team trained on deployment procedures

---

## Dependencies

**External:**
- AWS account with appropriate permissions
- GitHub repository
- Domain name for API (optional but recommended)
- SSL certificate (AWS Certificate Manager)

**Internal:**
- None (this is the foundation)

---

## Risks & Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| AWS costs higher than expected | High | Set billing alerts, use cost calculator upfront |
| Deployment pipeline failures | Medium | Thorough testing in dev, have manual deploy fallback |
| Secret leakage | High | Use AWS Secrets Manager, never commit secrets |
| Slow deployment times | Low | Optimize Docker builds with caching |

---

## References

- **PRD:** `/docs/plans/AIVP_PRD.md` - Section 2.1 (Tech Stack)
- **Technical Architecture:** `/docs/plans/AIVP_TechnicalArchitecture.md` - Section 7 (Deployment Architecture)
- **Related Epics:** All epics depend on this one

---

## Notes

- This epic must be **100% complete** before starting Epic 2
- Infrastructure should support scaling from day one
- Use AWS Free Tier where possible for cost optimization
- Consider Terraform modules for reusability across environments
