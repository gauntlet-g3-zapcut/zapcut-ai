# Epic E007: Infrastructure & Deployment

## Overview
Set up production-ready AWS infrastructure using Terraform (IaC), implement CI/CD pipelines, configure monitoring/logging, and deploy Zapcut API and worker services.

## Business Value
- Enables reliable, scalable production deployment
- Automates infrastructure provisioning
- Reduces operational overhead
- Supports rapid iteration through CI/CD
- Provides observability for debugging and optimization

## Success Criteria
- [ ] All AWS resources provisioned via Terraform
- [ ] PostgreSQL RDS instance running and accessible
- [ ] S3 buckets configured with CDN (CloudFront)
- [ ] AWS Cognito User Pool configured
- [ ] Elastic Beanstalk hosting FastAPI application
- [ ] Celery workers running on EC2 with auto-scaling
- [ ] CI/CD pipeline deploying on git push to main
- [ ] Monitoring dashboards in CloudWatch/Datadog
- [ ] Centralized logging with searchable logs
- [ ] Alert rules configured for critical failures

## Dependencies
- AWS account with appropriate IAM permissions
- GitHub repository for code
- Domain name for application (zapcut.video)

## Priority
**P0 - MVP Critical**

## Estimated Effort
**7-10 days** (1 DevOps engineer + 1 backend engineer)

## Related Stories
- S044: Terraform AWS Infrastructure Setup
- S045: PostgreSQL RDS Configuration
- S046: S3 Buckets & CloudFront CDN
- S047: AWS Cognito Setup
- S048: Elastic Beanstalk Application Deployment
- S049: Celery Worker EC2 Auto-Scaling Group
- S050: GitHub Actions CI/CD Pipeline
- S051: CloudWatch Monitoring & Dashboards
- S052: Centralized Logging Setup
- S053: Alert Rules & On-Call Configuration

## AWS Architecture

```
Internet
    │
    ├─> CloudFront CDN (cdn.zapcut.video)
    │       └─> S3 Bucket (zapcut-assets)
    │
    ├─> Route 53 DNS
    │       ├─> app.zapcut.video → Elastic Beanstalk ALB
    │       └─> api.zapcut.video → Elastic Beanstalk ALB
    │
    └─> Elastic Beanstalk (API)
            ├─> EC2 Auto Scaling Group (2-10 instances)
            ├─> Application Load Balancer
            └─> FastAPI containers
    
Backend Services:
    ├─> RDS PostgreSQL (Multi-AZ)
    ├─> ElastiCache Redis (replication group)
    ├─> SQS (video generation queue)
    └─> EC2 Auto Scaling Group (Celery workers)

Security:
    ├─> Cognito User Pool
    ├─> AWS Secrets Manager (API keys, DB passwords)
    ├─> VPC with private/public subnets
    └─> Security Groups & NACLs

Monitoring:
    ├─> CloudWatch Logs & Metrics
    ├─> CloudWatch Alarms
    └─> Datadog (optional)
```

## Terraform Configuration

### Directory Structure
```
infrastructure/
├── main.tf
├── variables.tf
├── outputs.tf
├── modules/
│   ├── vpc/
│   ├── rds/
│   ├── s3/
│   ├── cognito/
│   ├── elasticbeanstalk/
│   ├── ec2-workers/
│   └── monitoring/
├── environments/
│   ├── staging/
│   │   ├── terraform.tfvars
│   │   └── backend.tf
│   └── production/
│       ├── terraform.tfvars
│       └── backend.tf
```

### Key Resources

**VPC & Networking**
```hcl
module "vpc" {
  source = "./modules/vpc"
  
  cidr_block = "10.0.0.0/16"
  
  public_subnets  = ["10.0.1.0/24", "10.0.2.0/24"]
  private_subnets = ["10.0.10.0/24", "10.0.11.0/24"]
  database_subnets = ["10.0.20.0/24", "10.0.21.0/24"]
  
  enable_nat_gateway = true
  single_nat_gateway = false  # Multi-AZ for production
}
```

**RDS PostgreSQL**
```hcl
module "rds" {
  source = "./modules/rds"
  
  identifier = "zapcut-db-${var.environment}"
  engine_version = "16.1"
  instance_class = var.environment == "production" ? "db.r6g.large" : "db.t3.micro"
  
  allocated_storage = 100
  max_allocated_storage = 500
  
  multi_az = var.environment == "production"
  backup_retention_period = 7
  
  vpc_id = module.vpc.vpc_id
  subnet_ids = module.vpc.database_subnet_ids
}
```

**S3 & CloudFront**
```hcl
module "cdn" {
  source = "./modules/s3"
  
  bucket_name = "zapcut-assets-${var.environment}"
  
  enable_versioning = true
  enable_encryption = true
  
  cors_rules = [{
    allowed_headers = ["*"]
    allowed_methods = ["GET", "HEAD"]
    allowed_origins = ["https://app.zapcut.video"]
    max_age_seconds = 3000
  }]
  
  cloudfront_enabled = true
  cloudfront_aliases = ["cdn.zapcut.video"]
  acm_certificate_arn = var.acm_certificate_arn
}
```

## CI/CD Pipeline

### GitHub Actions Workflow

```yaml
name: Deploy Production

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

env:
  AWS_REGION: us-east-1
  EB_APPLICATION_NAME: zapcut-api
  EB_ENVIRONMENT_NAME: zapcut-api-production

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_DB: zapcut_test
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python 3.11
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
          pip install pytest pytest-cov
      
      - name: Run tests
        env:
          DATABASE_URL: postgresql://test:test@localhost:5432/zapcut_test
        run: |
          cd backend
          pytest --cov=app tests/
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3

  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python 3.11
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Run linters
        run: |
          cd backend
          pip install ruff mypy black
          ruff check app/
          mypy app/
          black --check app/

  build-and-deploy:
    needs: [test, lint]
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ${{ env.AWS_REGION }}
      
      - name: Build application
        run: |
          cd backend
          zip -r ../deploy.zip . -x '*.git*' '*__pycache__*' '*.pyc'
      
      - name: Deploy to Elastic Beanstalk
        uses: einaregilsson/beanstalk-deploy@v21
        with:
          aws_access_key: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws_secret_key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          application_name: ${{ env.EB_APPLICATION_NAME }}
          environment_name: ${{ env.EB_ENVIRONMENT_NAME }}
          version_label: ${{ github.sha }}
          region: ${{ env.AWS_REGION }}
          deployment_package: deploy.zip
          wait_for_deployment: true
          wait_for_environment_recovery: 300
      
      - name: Notify deployment
        if: success()
        run: |
          echo "Deployment successful!"
          # Send Slack notification, etc.

  deploy-workers:
    needs: [test, lint]
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ${{ env.AWS_REGION }}
      
      - name: Build worker AMI
        run: |
          # Use Packer to build AMI with latest worker code
          packer build -var "version=${{ github.sha }}" worker-ami.pkr.hcl
      
      - name: Update Auto Scaling Group
        run: |
          # Update launch template with new AMI
          # Trigger rolling update of worker instances
          aws autoscaling update-auto-scaling-group \
            --auto-scaling-group-name zapcut-workers-production \
            --launch-template LaunchTemplateName=zapcut-worker,Version='$Latest'
```

## Monitoring & Alerting

### CloudWatch Dashboards
```python
# Dashboard: Zapcut Production Overview
DASHBOARD_WIDGETS = [
    # API Metrics
    {
        "type": "metric",
        "properties": {
            "metrics": [
                ["AWS/ApplicationELB", "TargetResponseTime", {"stat": "Average"}],
                [".", "RequestCount", {"stat": "Sum"}],
                [".", "HTTPCode_Target_5XX_Count", {"stat": "Sum"}],
            ],
            "period": 300,
            "title": "API Performance"
        }
    },
    
    # Video Generation
    {
        "type": "metric",
        "properties": {
            "metrics": [
                ["Zapcut", "VideoGenerationDuration", {"stat": "Average"}],
                [".", "VideoGenerationSuccessRate", {"stat": "Average"}],
                [".", "VideoGenerationFailures", {"stat": "Sum"}],
            ],
            "period": 300,
            "title": "Video Generation"
        }
    },
    
    # Database
    {
        "type": "metric",
        "properties": {
            "metrics": [
                ["AWS/RDS", "CPUUtilization", {"dbinstance": "zapcut-db-production"}],
                [".", "DatabaseConnections"],
                [".", "FreeableMemory"],
            ],
            "period": 300,
            "title": "Database Health"
        }
    },
    
    # Cost
    {
        "type": "metric",
        "properties": {
            "metrics": [
                ["Zapcut", "CostPerVideo", {"stat": "Average"}],
                [".", "TotalDailySpend", {"stat": "Sum"}],
            ],
            "period": 86400,  # Daily
            "title": "Cost Metrics"
        }
    }
]
```

### Alert Rules
```python
ALARMS = [
    {
        "name": "high-api-error-rate",
        "metric": "HTTPCode_Target_5XX_Count",
        "threshold": 10,
        "period": 300,  # 5 minutes
        "evaluation_periods": 2,
        "action": "sns:us-east-1:123456789:zapcut-critical-alerts"
    },
    {
        "name": "video-generation-failures",
        "metric": "VideoGenerationSuccessRate",
        "threshold": 0.85,  # < 85% success rate
        "comparison": "LessThanThreshold",
        "period": 1800,  # 30 minutes
        "evaluation_periods": 1,
        "action": "sns:us-east-1:123456789:zapcut-alerts"
    },
    {
        "name": "high-database-cpu",
        "metric": "CPUUtilization",
        "threshold": 80,
        "period": 300,
        "evaluation_periods": 3,
        "action": "sns:us-east-1:123456789:zapcut-alerts"
    },
    {
        "name": "worker-queue-backlog",
        "metric": "ApproximateNumberOfMessagesVisible",
        "threshold": 50,
        "period": 600,  # 10 minutes
        "evaluation_periods": 2,
        "action": "sns:us-east-1:123456789:zapcut-alerts"
    }
]
```

## Logging Strategy

### Structured Logging
```python
import structlog

logger = structlog.get_logger()

# Example usage
logger.info(
    "video_generation_started",
    ad_id=ad_id,
    user_id=user_id,
    project_id=project_id,
    duration_target=30
)

logger.error(
    "sora_generation_failed",
    ad_id=ad_id,
    scene_index=3,
    error=str(e),
    retry_count=retry_count
)
```

### Log Aggregation
- All application logs → CloudWatch Logs
- Group by service: `/aws/elasticbeanstalk/zapcut-api/`, `/celery/workers/`
- Retention: 30 days for production, 7 days for staging
- Export to S3 for long-term storage (90 days)

## Security

### Secrets Management
```hcl
resource "aws_secretsmanager_secret" "api_keys" {
  name = "zapcut/${var.environment}/api-keys"
  
  secret_string = jsonencode({
    anthropic_api_key = var.anthropic_api_key
    openai_api_key = var.openai_api_key
    replicate_api_token = var.replicate_api_token
  })
}

# Access in application
import boto3

secrets_client = boto3.client('secretsmanager')
secret = secrets_client.get_secret_value(SecretId='zapcut/production/api-keys')
api_keys = json.loads(secret['SecretString'])
```

### IAM Roles
- EC2 instance role for workers (S3 read/write, SQS, Secrets Manager)
- Elastic Beanstalk service role (EC2, ELB, Auto Scaling, CloudWatch)
- Lambda role for maintenance tasks (RDS snapshots, S3 cleanup)

## Success Metrics
- Deployment success rate: >95%
- Deployment time: <10 minutes
- Infrastructure provisioning time: <30 minutes (first time)
- Zero-downtime deployments: 100%
- Mean time to recovery (MTTR): <30 minutes

---
**Created**: 2025-11-15  
**Status**: Draft  
**Owner**: DevOps + Backend Team
