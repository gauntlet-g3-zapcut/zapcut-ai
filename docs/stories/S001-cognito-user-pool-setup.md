# Story S001: AWS Cognito User Pool Setup

## Epic
[E001: User Authentication & Authorization](../Epics/E001-authentication-authorization.md)

## Story
**As a** platform engineer  
**I want to** provision and configure an AWS Cognito User Pool  
**So that** users can securely create accounts and authenticate

## Priority
**P0 - MVP Critical**

## Size
**M** (1-2 days)

## Description
Set up AWS Cognito User Pool using Terraform to handle user registration, authentication, and session management. This is the foundation for all user authentication in Zapcut.

## Acceptance Criteria
- [ ] Cognito User Pool created via Terraform
- [ ] Password policy configured (8+ chars, mixed case, symbols)
- [ ] Email verification enabled
- [ ] Custom attributes added (first_name, last_name, company_name)
- [ ] MFA optional (not required for MVP)
- [ ] App client configured with appropriate OAuth scopes
- [ ] Hosted UI customized with Zapcut branding
- [ ] User pool ID and client ID exported as Terraform outputs

## Technical Details

### Terraform Configuration
```hcl
# infrastructure/modules/cognito/main.tf

resource "aws_cognito_user_pool" "zapcut_users" {
  name = "zapcut-user-pool-${var.environment}"
  
  # Email as username
  username_attributes      = ["email"]
  auto_verified_attributes = ["email"]
  
  # Password policy
  password_policy {
    minimum_length                   = 8
    require_lowercase                = true
    require_numbers                  = true
    require_symbols                  = true
    require_uppercase                = true
    temporary_password_validity_days = 7
  }
  
  # Account recovery
  account_recovery_setting {
    recovery_mechanism {
      name     = "verified_email"
      priority = 1
    }
  }
  
  # Custom attributes
  schema {
    name                     = "first_name"
    attribute_data_type      = "String"
    developer_only_attribute = false
    mutable                  = true
    required                 = false
    
    string_attribute_constraints {
      min_length = 1
      max_length = 100
    }
  }
  
  schema {
    name                     = "last_name"
    attribute_data_type      = "String"
    developer_only_attribute = false
    mutable                  = true
    required                 = false
    
    string_attribute_constraints {
      min_length = 1
      max_length = 100
    }
  }
  
  schema {
    name                     = "company_name"
    attribute_data_type      = "String"
    developer_only_attribute = false
    mutable                  = true
    required                 = false
    
    string_attribute_constraints {
      min_length = 1
      max_length = 200
    }
  }
  
  # Email configuration
  email_configuration {
    email_sending_account = "COGNITO_DEFAULT"  # Use SES for production
  }
  
  # User pool add-ons
  user_pool_add_ons {
    advanced_security_mode = "ENFORCED"  # Protect against compromised credentials
  }
  
  tags = {
    Environment = var.environment
    Project     = "zapcut"
  }
}

# App client for web application
resource "aws_cognito_user_pool_client" "zapcut_web_client" {
  name         = "zapcut-web-client"
  user_pool_id = aws_cognito_user_pool.zapcut_users.id
  
  # OAuth settings
  allowed_oauth_flows_user_pool_client = true
  allowed_oauth_flows                  = ["code", "implicit"]
  allowed_oauth_scopes                 = ["email", "openid", "profile"]
  
  # Callback URLs
  callback_urls = [
    "https://app.zapcut.video/auth/callback",
    "http://localhost:3000/auth/callback"  # Dev environment
  ]
  
  logout_urls = [
    "https://zapcut.video",
    "http://localhost:3000"
  ]
  
  # Token validity
  access_token_validity  = 60   # minutes
  id_token_validity      = 60   # minutes
  refresh_token_validity = 30   # days
  
  # Prevent client secret (public client)
  generate_secret = false
  
  # Supported identity providers
  supported_identity_providers = ["COGNITO"]
  
  # Read/write permissions
  read_attributes = [
    "email",
    "email_verified",
    "custom:first_name",
    "custom:last_name",
    "custom:company_name"
  ]
  
  write_attributes = [
    "email",
    "custom:first_name",
    "custom:last_name",
    "custom:company_name"
  ]
}

# Hosted UI domain
resource "aws_cognito_user_pool_domain" "zapcut_domain" {
  domain       = "zapcut-${var.environment}"
  user_pool_id = aws_cognito_user_pool.zapcut_users.id
}

# Outputs
output "user_pool_id" {
  value = aws_cognito_user_pool.zapcut_users.id
}

output "user_pool_arn" {
  value = aws_cognito_user_pool.zapcut_users.arn
}

output "client_id" {
  value = aws_cognito_user_pool_client.zapcut_web_client.id
}

output "hosted_ui_url" {
  value = "https://${aws_cognito_user_pool_domain.zapcut_domain.domain}.auth.${var.aws_region}.amazoncognito.com"
}
```

### Custom Branding (Optional for MVP)
```hcl
resource "aws_cognito_user_pool_ui_customization" "zapcut_ui" {
  client_id = aws_cognito_user_pool_client.zapcut_web_client.id
  user_pool_id = aws_cognito_user_pool.zapcut_users.id
  
  # Custom CSS
  css = file("${path.module}/cognito-ui-custom.css")
  
  # Logo
  image_file = filebase64("${path.module}/zapcut-logo.png")
}
```

## Testing Plan

### Manual Testing
1. **Provision Infrastructure**
   ```bash
   cd infrastructure/environments/staging
   terraform init
   terraform apply -target=module.cognito
   ```

2. **Verify User Pool**
   - Navigate to AWS Console → Cognito → User Pools
   - Confirm user pool exists with correct settings
   - Verify custom attributes present

3. **Test Hosted UI**
   - Open hosted UI URL in browser
   - Verify sign-up flow works
   - Attempt weak password (should fail)
   - Complete registration with strong password
   - Verify email confirmation received

4. **Test Token Generation**
   ```bash
   # Use AWS CLI to initiate auth flow
   aws cognito-idp initiate-auth \
     --auth-flow USER_PASSWORD_AUTH \
     --client-id <CLIENT_ID> \
     --auth-parameters USERNAME=test@example.com,PASSWORD=TestPassword123!
   
   # Verify JWT tokens returned
   ```

### Automated Testing
```python
# tests/integration/test_cognito_setup.py
import boto3
import pytest

@pytest.fixture
def cognito_client():
    return boto3.client('cognito-idp', region_name='us-east-1')

def test_user_pool_exists(cognito_client):
    """Verify user pool is created with correct config"""
    user_pools = cognito_client.list_user_pools(MaxResults=50)
    
    zapcut_pool = next(
        (p for p in user_pools['UserPools'] if 'zapcut' in p['Name'].lower()),
        None
    )
    
    assert zapcut_pool is not None
    assert zapcut_pool['Name'] == 'zapcut-user-pool-staging'

def test_password_policy(cognito_client):
    """Verify password policy is enforced"""
    # Try to sign up with weak password
    with pytest.raises(Exception) as exc:
        cognito_client.sign_up(
            ClientId=CLIENT_ID,
            Username='weak@example.com',
            Password='weak',
            UserAttributes=[
                {'Name': 'email', 'Value': 'weak@example.com'}
            ]
        )
    
    assert 'PasswordTooShort' in str(exc.value) or 'InvalidPassword' in str(exc.value)

def test_custom_attributes(cognito_client):
    """Verify custom attributes can be set"""
    # Sign up user with custom attributes
    response = cognito_client.sign_up(
        ClientId=CLIENT_ID,
        Username='test@example.com',
        Password='TestPassword123!',
        UserAttributes=[
            {'Name': 'email', 'Value': 'test@example.com'},
            {'Name': 'custom:first_name', 'Value': 'John'},
            {'Name': 'custom:last_name', 'Value': 'Doe'},
            {'Name': 'custom:company_name', 'Value': 'Acme Inc'}
        ]
    )
    
    assert response['UserSub'] is not None
```

## Dependencies
- AWS account with appropriate IAM permissions
- Terraform >= 1.5
- `aws` provider >= 5.0

## Risks & Mitigations
- **Risk**: Cognito rate limits during testing
  - **Mitigation**: Use separate dev/staging/prod user pools
- **Risk**: Email delivery failures
  - **Mitigation**: Configure SES for production, use COGNITO_DEFAULT for MVP
- **Risk**: User pool cannot be deleted if users exist
  - **Mitigation**: Add lifecycle policy to prevent accidental deletion

## Definition of Done
- [ ] Terraform code merged to `main` branch
- [ ] Staging user pool provisioned and verified
- [ ] Production user pool provisioned
- [ ] Outputs documented in team wiki
- [ ] Manual testing completed successfully
- [ ] Integration tests passing in CI

## Related Stories
- S002: Email/Password Authentication Flow
- S003: Google OAuth Integration
- S047: AWS Cognito Setup (Infrastructure Epic)

---
**Created**: 2025-11-15  
**Assigned To**: DevOps Team  
**Status**: Ready
