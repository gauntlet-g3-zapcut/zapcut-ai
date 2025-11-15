# Epic E006: Social Media Publishing

## Overview
Implement OAuth integrations with X (Twitter) and LinkedIn to enable one-click video publishing directly from Zapcut, including caption editing, post composition, and published post tracking.

## Business Value
- Streamlines workflow: generate → publish in <5 minutes
- Reduces friction (no manual download/upload)
- Tracks published posts for analytics
- Competitive differentiator (direct integration)
- Enables viral loop (brand visibility on socials)

## Success Criteria
- [ ] Users can connect X and LinkedIn accounts via OAuth
- [ ] One-click "Post to X" uploads video and creates tweet
- [ ] One-click "Post to LinkedIn" uploads video and creates post
- [ ] Users can edit captions before posting
- [ ] Confirmation modal prevents accidental posts
- [ ] Published post URLs displayed after success
- [ ] Post metadata stored for analytics

## Dependencies
- Video composition & export (E005)
- User authentication (E001)
- X/Twitter API v2 OAuth 2.0
- LinkedIn Marketing API OAuth 2.0

## Priority
**P1 - Post-MVP Polish**

## Estimated Effort
**4-6 days** (1 backend + 1 frontend engineer)

## Related Stories
- S036: X/Twitter OAuth Integration
- S037: LinkedIn OAuth Integration
- S038: X Video Upload API Client
- S039: LinkedIn Video Upload & Post Creation
- S040: Caption Editor UI Component
- S041: Post Confirmation Modal
- S042: Published Post Tracking
- S043: Social Account Management UI

## OAuth Flow

### X/Twitter OAuth 2.0 with PKCE
```python
# 1. Generate authorization URL
auth_url = twitter_oauth.get_authorization_url(
    redirect_uri="https://app.zapcut.video/auth/twitter/callback",
    scopes=["tweet.read", "tweet.write", "users.read", "offline.access"],
    code_challenge=generate_pkce_challenge()
)

# 2. User authorizes, Twitter redirects back with code
code = request.args.get('code')

# 3. Exchange code for access token
tokens = twitter_oauth.fetch_token(
    code=code,
    code_verifier=code_verifier
)

# 4. Store tokens in database
user.update(
    twitter_access_token=encrypt(tokens['access_token']),
    twitter_refresh_token=encrypt(tokens['refresh_token'])
)
```

### LinkedIn OAuth 2.0
```python
# Similar flow with LinkedIn-specific scopes
auth_url = linkedin_oauth.get_authorization_url(
    redirect_uri="https://app.zapcut.video/auth/linkedin/callback",
    scopes=["w_member_social", "r_basicprofile"],
)
```

## X/Twitter Video Publishing

```python
async def post_to_twitter(ad_id: str, caption: str, user_id: str):
    # 1. Get user's Twitter tokens
    user = User.get(user_id)
    access_token = decrypt(user.twitter_access_token)
    
    # 2. Download video from S3
    ad = GeneratedAd.get(ad_id)
    video_path = download_from_s3(ad.final_video_url)
    
    # 3. Upload video to Twitter Media API
    media_upload_url = "https://upload.twitter.com/1.1/media/upload.json"
    
    # INIT
    init_response = requests.post(
        media_upload_url,
        params={
            "command": "INIT",
            "media_type": "video/mp4",
            "media_category": "tweet_video",
            "total_bytes": os.path.getsize(video_path)
        },
        headers={"Authorization": f"Bearer {access_token}"}
    )
    media_id = init_response.json()['media_id_string']
    
    # APPEND (chunked upload)
    chunk_size = 5 * 1024 * 1024  # 5MB chunks
    with open(video_path, 'rb') as f:
        segment_index = 0
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            
            requests.post(
                media_upload_url,
                params={
                    "command": "APPEND",
                    "media_id": media_id,
                    "segment_index": segment_index
                },
                files={"media": chunk},
                headers={"Authorization": f"Bearer {access_token}"}
            )
            segment_index += 1
    
    # FINALIZE
    requests.post(
        media_upload_url,
        params={
            "command": "FINALIZE",
            "media_id": media_id
        },
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    # 4. Create tweet with video
    tweet_response = requests.post(
        "https://api.twitter.com/2/tweets",
        json={
            "text": caption,
            "media": {"media_ids": [media_id]}
        },
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    tweet_data = tweet_response.json()
    tweet_id = tweet_data['data']['id']
    tweet_url = f"https://twitter.com/user/status/{tweet_id}"
    
    # 5. Store published post record
    PublishedPost.create(
        ad_id=ad_id,
        user_id=user_id,
        platform="twitter",
        post_id=tweet_id,
        post_url=tweet_url,
        caption=caption
    )
    
    return tweet_url
```

## LinkedIn Video Publishing

```python
async def post_to_linkedin(ad_id: str, caption: str, user_id: str, visibility: str = "public"):
    # 1. Get user's LinkedIn tokens and profile
    user = User.get(user_id)
    access_token = decrypt(user.linkedin_access_token)
    
    # Get LinkedIn person URN
    profile = requests.get(
        "https://api.linkedin.com/v2/me",
        headers={"Authorization": f"Bearer {access_token}"}
    ).json()
    person_urn = f"urn:li:person:{profile['id']}"
    
    # 2. Register video upload
    register_response = requests.post(
        "https://api.linkedin.com/v2/assets?action=registerUpload",
        json={
            "registerUploadRequest": {
                "recipes": ["urn:li:digitalmediaRecipe:feedshare-video"],
                "owner": person_urn,
                "serviceRelationships": [{
                    "relationshipType": "OWNER",
                    "identifier": "urn:li:userGeneratedContent"
                }]
            }
        },
        headers={"Authorization": f"Bearer {access_token}"}
    ).json()
    
    upload_url = register_response['value']['uploadMechanism']['com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest']['uploadUrl']
    asset_urn = register_response['value']['asset']
    
    # 3. Upload video
    ad = GeneratedAd.get(ad_id)
    video_bytes = download_bytes_from_s3(ad.final_video_url)
    
    requests.put(
        upload_url,
        data=video_bytes,
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    # 4. Create post with video
    post_response = requests.post(
        "https://api.linkedin.com/v2/ugcPosts",
        json={
            "author": person_urn,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {"text": caption},
                    "shareMediaCategory": "VIDEO",
                    "media": [{
                        "status": "READY",
                        "media": asset_urn
                    }]
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": visibility.upper()
            }
        },
        headers={"Authorization": f"Bearer {access_token}"}
    ).json()
    
    post_id = post_response['id']
    post_url = f"https://www.linkedin.com/feed/update/{post_id}"
    
    # 5. Store published post record
    PublishedPost.create(
        ad_id=ad_id,
        user_id=user_id,
        platform="linkedin",
        post_id=post_id,
        post_url=post_url,
        caption=caption
    )
    
    return post_url
```

## UI Components

### Social Account Connection
```tsx
<SocialAccountsCard>
  <ConnectButton platform="twitter" connected={!!user.twitter_access_token}>
    {connected ? "✓ Connected to @username" : "Connect X (Twitter)"}
  </ConnectButton>
  
  <ConnectButton platform="linkedin" connected={!!user.linkedin_access_token}>
    {connected ? "✓ Connected to LinkedIn" : "Connect LinkedIn"}
  </ConnectButton>
</SocialAccountsCard>
```

### Post Composer Modal
```tsx
<PostModal video={generatedAd}>
  <VideoPreview url={generatedAd.final_video_url} />
  
  <CaptionEditor
    maxLength={280}  // Twitter limit
    defaultCaption={`Introducing ${project.product_name}...`}
    onChange={setCaption}
  />
  
  <PlatformSelector>
    ☐ Post to X (Twitter)
    ☐ Post to LinkedIn
  </PlatformSelector>
  
  <ButtonGroup>
    <Button variant="secondary" onClick={onCancel}>Cancel</Button>
    <Button variant="primary" onClick={handlePost}>Post Now</Button>
  </ButtonGroup>
</PostModal>
```

## Data Model

```sql
CREATE TABLE published_posts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  ad_id UUID NOT NULL REFERENCES generated_ads(id),
  user_id UUID NOT NULL REFERENCES users(id),
  
  -- Platform info
  platform VARCHAR(50) NOT NULL,  -- 'twitter', 'linkedin'
  post_id VARCHAR(255) NOT NULL,
  post_url TEXT NOT NULL,
  
  -- Content
  caption TEXT,
  
  -- Metadata
  published_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  
  -- Analytics (future)
  views INTEGER DEFAULT 0,
  likes INTEGER DEFAULT 0,
  comments INTEGER DEFAULT 0,
  shares INTEGER DEFAULT 0,
  
  CONSTRAINT valid_platform CHECK (platform IN ('twitter', 'linkedin', 'instagram', 'tiktok'))
);

CREATE INDEX idx_published_posts_ad_id ON published_posts(ad_id);
CREATE INDEX idx_published_posts_user_id ON published_posts(user_id);
CREATE INDEX idx_published_posts_platform ON published_posts(platform);
```

## Error Handling
- Token expiration: Auto-refresh if refresh token available
- Upload failures: Retry with exponential backoff (3 attempts)
- Caption too long: Truncate with "..." for Twitter
- Video too large: Show error, suggest download instead
- Network errors: Queue for retry

## Security Considerations
- Encrypt social tokens at rest (AES-256)
- Use PKCE for OAuth (prevents authorization code interception)
- Validate redirect URIs
- Implement CSRF tokens
- Rate limit post attempts (5/hour per platform)

## Success Metrics
- OAuth connection success rate: >95%
- Post publishing success rate: >98%
- Average time to publish: <30 seconds
- User adoption: >40% of users connect at least one social account

---
**Created**: 2025-11-15  
**Status**: Draft  
**Owner**: Backend + Frontend Team
