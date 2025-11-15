# Epic 2: Authentication & Brand Management

**Status:** Not Started
**Priority:** P0 (MVP)
**Estimated Effort:** 2-3 weeks
**Dependencies:** Epic 1 (Infrastructure must be deployed)

---

## Epic Overview

### Value Proposition
Users can securely create accounts, authenticate, and manage brand profiles with product images and guidelines, establishing the foundation for personalized AI-generated video content.

### Success Criteria
- [ ] Users can sign up with email/password or Google OAuth
- [ ] Users can log in and sessions persist across app restarts
- [ ] Users can create brands with name, description, and 2+ product images
- [ ] Users can view list of their brands
- [ ] Users can edit and delete brands
- [ ] All user data is isolated (users only see their own brands)
- [ ] Complete UI flows are functional and polished

### Demo Scenario
1. New user visits landing page
2. Clicks "Sign up" → Creates account with Google
3. Redirected to Brands Dashboard (empty state)
4. Clicks "Create Brand" → Uploads product images, fills form
5. Brand appears in dashboard
6. User logs out and logs back in → Brands persist
7. User edits brand → Changes save successfully

---

## Technical Stack

### Frontend (Electron + React)
- React Router for navigation
- Zustand for state management (authStore, brandStore)
- Glassmorphism UI components
- Lucide React icons
- Clerk for authentication UI

### Backend (FastAPI)
- FastAPI framework
- SQLAlchemy ORM
- JWT tokens for session management
- Pydantic models for validation
- Boto3 for S3 uploads

### Database (PostgreSQL)
- Users table
- Brands table
- PostgreSQL on RDS

### Storage
- S3 for product images
- CloudFront for image delivery

---

## User Stories

### Story 2.1: Landing Page & Navigation
**As a** new visitor
**I want** to see a clear value proposition and sign-in option
**So that** I understand the product and can get started

**Acceptance Criteria:**
- [ ] Landing page displays product name "Zapcut AI"
- [ ] Hero section with value proposition
- [ ] "Login" button in top-right corner
- [ ] Glassmorphism design matches design system
- [ ] Page is responsive (desktop-first)
- [ ] Clicking "Login" navigates to login page

**Frontend:**
```typescript
// Pages
- LandingPage.tsx
  - LandingHero component
  - Features grid
  - CTA button

// Routes
GET / → LandingPage
```

**Backend:** N/A (static page)
**Database:** N/A

**Tasks:**
- [ ] Create LandingPage component
- [ ] Create LandingHero component
- [ ] Add glassmorphism styling
- [ ] Add routing for `/` route
- [ ] Test navigation to login page

---

### Story 2.2: User Registration (Email/Password)
**As a** new user
**I want** to create an account with email and password
**So that** I can access the platform

**Acceptance Criteria:**
- [ ] Signup page with email, password, name fields
- [ ] Password requirements: min 8 chars, 1 uppercase, 1 number
- [ ] Form validation with inline errors
- [ ] Success redirects to brands dashboard
- [ ] Error messages for duplicate email
- [ ] Password is hashed before storage

**Frontend:**
```typescript
// Pages
- SignupPage.tsx
  - SignupForm component
  - GlassInput components
  - Validation logic

// State
authStore.signup(email, password, name)

// Routes
GET /signup → SignupPage
POST /api/auth/signup → Backend
```

**Backend:**
```python
# Endpoints
POST /api/auth/signup
Body: { email, password, name }
Response: { user: {...}, token: "..." }

# Logic
- Validate email format
- Validate password strength
- Hash password with bcrypt
- Create user record
- Generate JWT token
- Return user + token
```

**Database:**
```sql
INSERT INTO users (email, name, password_hash)
VALUES (?, ?, ?);
```

**Tasks:**
- [ ] Create SignupPage component
- [ ] Create signup API endpoint
- [ ] Add password hashing
- [ ] Add email validation
- [ ] Generate JWT tokens
- [ ] Test signup flow end-to-end
- [ ] Test duplicate email handling

---

### Story 2.3: User Authentication (Google OAuth)
**As a** new user
**I want** to sign in with Google
**So that** I don't have to create another password

**Acceptance Criteria:**
- [ ] "Sign in with Google" button on login page
- [ ] OAuth flow redirects to Google consent screen
- [ ] User grants permissions
- [ ] Account created/updated with Google profile
- [ ] User redirected to dashboard
- [ ] Session persists

**Frontend:**
```typescript
// Pages
- LoginPage.tsx
  - GoogleAuthButton component
  - OAuth callback handling

// State
authStore.loginWithGoogle()

// Routes
GET /login → LoginPage
GET /auth/callback → Handle OAuth callback
```

**Backend:**
```python
# Endpoints
GET /api/auth/google/login
→ Redirect to Google OAuth

GET /api/auth/google/callback
→ Exchange code for tokens
→ Get user profile from Google
→ Create/update user
→ Generate JWT
→ Redirect to frontend with token

# Logic
- OAuth 2.0 flow with Google
- Verify OAuth tokens
- Create user if doesn't exist
- Update user if exists
- Generate JWT session token
```

**Database:**
```sql
-- Insert or update user
INSERT INTO users (email, name, oauth_provider, oauth_id)
VALUES (?, ?, 'google', ?)
ON CONFLICT (email)
DO UPDATE SET name = EXCLUDED.name;
```

**Tasks:**
- [ ] Register app with Google OAuth
- [ ] Implement OAuth flow in backend
- [ ] Create GoogleAuthButton component
- [ ] Handle OAuth callback
- [ ] Test OAuth flow end-to-end
- [ ] Handle OAuth errors

---

### Story 2.4: User Login (Email/Password)
**As a** returning user
**I want** to log in with my credentials
**So that** I can access my account

**Acceptance Criteria:**
- [ ] Login page with email and password fields
- [ ] "Login" button submits form
- [ ] Success redirects to brands dashboard
- [ ] Error message for invalid credentials
- [ ] "Forgot password?" link (UI only for MVP)

**Frontend:**
```typescript
// Pages
- LoginPage.tsx
  - LoginForm component

// State
authStore.login(email, password)

// Routes
POST /api/auth/login → Backend
```

**Backend:**
```python
# Endpoints
POST /api/auth/login
Body: { email, password }
Response: { user: {...}, token: "..." }

# Logic
- Find user by email
- Verify password hash
- Generate JWT token
- Return user + token
```

**Database:**
```sql
SELECT id, email, name, password_hash, subscription_tier
FROM users
WHERE email = ?;
```

**Tasks:**
- [ ] Create LoginPage component
- [ ] Create login API endpoint
- [ ] Add password verification
- [ ] Test login flow
- [ ] Test invalid credentials
- [ ] Add "Forgot password" link (no functionality yet)

---

### Story 2.5: Session Management
**As a** user
**I want** my session to persist
**So that** I don't have to log in repeatedly

**Acceptance Criteria:**
- [ ] JWT token stored securely in localStorage
- [ ] Token included in all API requests
- [ ] Token expires after 7 days
- [ ] Expired token redirects to login
- [ ] Logout clears token
- [ ] Session persists across app restarts

**Frontend:**
```typescript
// State
authStore {
  user: User | null
  token: string | null
  isAuthenticated: boolean

  // Methods
  login()
  logout()
  refreshUser()
}

// API Client
Headers: { Authorization: `Bearer ${token}` }

// Routes
Protected routes require authStore.isAuthenticated
```

**Backend:**
```python
# Middleware
- Verify JWT on every request
- Extract user from token
- Attach user to request context

# Logic
- JWT expiration: 7 days
- Validate token signature
- Handle expired tokens
```

**Database:**
```sql
-- Token validation queries user table
SELECT id, email, name FROM users WHERE id = ?;
```

**Tasks:**
- [ ] Implement JWT generation
- [ ] Implement JWT verification middleware
- [ ] Create authStore with persistence
- [ ] Add token to API client headers
- [ ] Test token expiration
- [ ] Test logout clears session
- [ ] Test session persistence across restarts

---

### Story 2.6: Brands Dashboard (Empty State)
**As a** new user
**I want** to see an empty brands dashboard
**So that** I understand I need to create a brand

**Acceptance Criteria:**
- [ ] Dashboard shows after login
- [ ] Empty state illustration displayed
- [ ] "No brands yet" message
- [ ] "Create Brand" button (primary CTA)
- [ ] Left sidebar with user profile
- [ ] Navigation items: Brands (active), Settings

**Frontend:**
```typescript
// Pages
- BrandsDashboard.tsx
  - LeftSidebar component
  - EmptyState component
  - CreateBrandButton

// State
brandStore.fetchBrands()

// Routes
GET /brands → BrandsDashboard
GET /api/brands → Backend (returns [])
```

**Backend:**
```python
# Endpoints
GET /api/brands
Headers: { Authorization: Bearer <token> }
Response: Brand[]

# Logic
- Extract user from JWT
- Query brands for user
- Return empty array if none
```

**Database:**
```sql
SELECT * FROM brands
WHERE user_id = ?
ORDER BY created_at DESC;
```

**Tasks:**
- [ ] Create BrandsDashboard page
- [ ] Create EmptyState component
- [ ] Create LeftSidebar component
- [ ] Implement GET /api/brands endpoint
- [ ] Test empty state displays correctly
- [ ] Test protected route (requires auth)

---

### Story 2.7: Create Brand Flow
**As a** user
**I want** to create a brand profile
**So that** I can generate videos for my product

**Acceptance Criteria:**
- [ ] "Create Brand" button opens modal
- [ ] Modal has form with: title, description, product images
- [ ] Title is required (max 100 chars)
- [ ] Description is required (max 500 chars)
- [ ] Minimum 2 product images required
- [ ] Maximum 10 product images allowed
- [ ] Image formats: JPG, PNG, WEBP
- [ ] Max file size: 10MB per image
- [ ] Image preview shown after upload
- [ ] "Cancel" closes modal
- [ ] "Create Brand" saves and closes modal
- [ ] Validation errors shown inline

**Frontend:**
```typescript
// Components
- CreateBrandModal.tsx
  - GlassCard
  - GlassInput (title)
  - GlassTextarea (description)
  - ImageUploader component
  - Validation logic

// State
brandStore.createBrand({ title, description, productImages })

// Routes
POST /api/brands → Backend
POST /api/upload → Upload images first
```

**Backend:**
```python
# Endpoints
POST /api/upload
Content-Type: multipart/form-data
Files: productImages[]
Response: { urls: string[] }

POST /api/brands
Body: {
  title: string,
  description: string,
  product_images: string[] // S3 URLs from upload
}
Response: Brand

# Logic
1. Upload endpoint:
   - Validate file types
   - Validate file sizes
   - Upload to S3
   - Return S3 URLs

2. Create brand endpoint:
   - Validate required fields
   - Validate image count (2-10)
   - Create brand record
   - Link to user
```

**Database:**
```sql
-- Create brands table
CREATE TABLE brands (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    product_images TEXT[], -- Array of S3 URLs
    brand_guidelines JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_brands_user ON brands(user_id);

-- Insert brand
INSERT INTO brands (user_id, title, description, product_images)
VALUES (?, ?, ?, ?);
```

**Tasks:**
- [ ] Create CreateBrandModal component
- [ ] Create ImageUploader component
- [ ] Implement POST /api/upload endpoint
- [ ] Implement POST /api/brands endpoint
- [ ] Set up S3 bucket for uploads
- [ ] Add image validation
- [ ] Add form validation
- [ ] Test upload flow
- [ ] Test brand creation
- [ ] Test validation errors

---

### Story 2.8: Brands List View
**As a** user
**I want** to see all my brands
**So that** I can select one to work with

**Acceptance Criteria:**
- [ ] Brands displayed in grid (2-3 columns)
- [ ] Each brand card shows: thumbnail (first product image), title, creation date, project count
- [ ] Cards have glassmorphism styling
- [ ] Clicking card navigates to chat interface (Epic 3)
- [ ] Grid is responsive

**Frontend:**
```typescript
// Components
- BrandGrid.tsx
  - BrandCard component (repeated)

// State
const brands = useBrandStore(state => state.brands)

// Display
- First product image as thumbnail
- Brand title
- Created date (relative: "2 days ago")
- Project count: "3 projects"
```

**Backend:**
```python
# Endpoints (already created in 2.6)
GET /api/brands
Response: Brand[]

# Include project count in response
SELECT b.*, COUNT(p.id) as project_count
FROM brands b
LEFT JOIN ad_projects p ON p.brand_id = b.id
WHERE b.user_id = ?
GROUP BY b.id;
```

**Database:**
```sql
-- Query returns brands with project counts
```

**Tasks:**
- [ ] Create BrandGrid component
- [ ] Create BrandCard component
- [ ] Update GET /api/brands to include project count
- [ ] Add image loading states
- [ ] Test grid layout
- [ ] Test card click navigation

---

### Story 2.9: Edit Brand
**As a** user
**I want** to edit my brand details
**So that** I can keep information current

**Acceptance Criteria:**
- [ ] Brand card has "Edit" button (on hover or menu)
- [ ] Edit opens same modal as create, pre-filled
- [ ] Can change title, description
- [ ] Can add/remove product images
- [ ] Changes save to database
- [ ] Updated brand reflects in list immediately

**Frontend:**
```typescript
// Components
- EditBrandModal.tsx (reuse CreateBrandModal)
- BrandCard with edit button

// State
brandStore.updateBrand(brandId, updates)

// Routes
PUT /api/brands/:brandId → Backend
```

**Backend:**
```python
# Endpoints
PUT /api/brands/:brandId
Body: { title?, description?, product_images? }
Response: Brand

# Logic
- Validate user owns brand
- Update fields
- Return updated brand
```

**Database:**
```sql
UPDATE brands
SET title = ?, description = ?, product_images = ?, updated_at = NOW()
WHERE id = ? AND user_id = ?;
```

**Tasks:**
- [ ] Add edit button to BrandCard
- [ ] Reuse CreateBrandModal for editing
- [ ] Implement PUT /api/brands/:brandId endpoint
- [ ] Test edit flow
- [ ] Test authorization (can only edit own brands)

---

### Story 2.10: Delete Brand
**As a** user
**I want** to delete brands I no longer need
**So that** my dashboard stays organized

**Acceptance Criteria:**
- [ ] Brand card has "Delete" option (in menu)
- [ ] Confirmation dialog before delete
- [ ] Delete removes brand and all associated data
- [ ] Brand removed from list immediately
- [ ] Cannot delete if brand has active projects (Epic 3+)

**Frontend:**
```typescript
// Components
- DeleteConfirmDialog

// State
brandStore.deleteBrand(brandId)

// Routes
DELETE /api/brands/:brandId → Backend
```

**Backend:**
```python
# Endpoints
DELETE /api/brands/:brandId
Response: { success: true }

# Logic
- Validate user owns brand
- Check for active projects (Epic 3+)
- Delete brand record
- S3 cleanup (optional for MVP)
```

**Database:**
```sql
DELETE FROM brands
WHERE id = ? AND user_id = ?;

-- Cascade deletes handle related records
```

**Tasks:**
- [ ] Add delete button to BrandCard
- [ ] Create DeleteConfirmDialog
- [ ] Implement DELETE /api/brands/:brandId endpoint
- [ ] Test delete flow
- [ ] Test confirmation dialog
- [ ] Test authorization

---

## Database Schema

```sql
-- Migration 002: Add brands table

CREATE TABLE brands (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    product_images TEXT[] NOT NULL, -- Array of S3 URLs
    brand_guidelines JSONB, -- For future use
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    CONSTRAINT min_images CHECK (array_length(product_images, 1) >= 2),
    CONSTRAINT max_images CHECK (array_length(product_images, 1) <= 10)
);

CREATE INDEX idx_brands_user ON brands(user_id);
CREATE INDEX idx_brands_created ON brands(created_at DESC);
```

---

## API Endpoints

### Authentication
```
POST /api/auth/signup
POST /api/auth/login
GET /api/auth/google/login
GET /api/auth/google/callback
POST /api/auth/logout
GET /api/auth/me
```

### Brands
```
GET /api/brands
POST /api/brands
GET /api/brands/:brandId
PUT /api/brands/:brandId
DELETE /api/brands/:brandId
```

### Uploads
```
POST /api/upload
```

---

## Frontend Routes

```
/ → LandingPage (public)
/login → LoginPage (public)
/signup → SignupPage (public)
/brands → BrandsDashboard (protected)
```

---

## State Management

### authStore
```typescript
interface AuthStore {
  user: User | null
  token: string | null
  isAuthenticated: boolean

  login: (email, password) => Promise<void>
  signup: (email, password, name) => Promise<void>
  loginWithGoogle: () => Promise<void>
  logout: () => void
  refreshUser: () => Promise<void>
}
```

### brandStore
```typescript
interface BrandStore {
  brands: Brand[]
  isLoading: boolean

  fetchBrands: () => Promise<void>
  createBrand: (data) => Promise<Brand>
  updateBrand: (id, data) => Promise<Brand>
  deleteBrand: (id) => Promise<void>
  getBrandById: (id) => Brand | undefined
}
```

---

## Testing Strategy

### Frontend Tests
- Component tests for all pages
- Form validation tests
- State management tests
- Navigation tests

### Backend Tests
- API endpoint tests (signup, login, CRUD brands)
- Authentication middleware tests
- Image upload tests
- Authorization tests (users can't access others' brands)

### Integration Tests
- End-to-end: Signup → Create brand → View list
- End-to-end: Login → Edit brand → Delete brand
- OAuth flow test

---

## Definition of Done

- [ ] All user stories completed
- [ ] All acceptance criteria met
- [ ] Frontend UI matches design system
- [ ] All API endpoints tested
- [ ] Database migrations tested
- [ ] Authentication flows work (email + Google)
- [ ] Brand CRUD operations work
- [ ] Image uploads work
- [ ] Authorization enforced (users see only their brands)
- [ ] Code deployed to staging
- [ ] Smoke tests pass
- [ ] Demo scenario executable

---

## Dependencies

**External:**
- Google OAuth credentials
- AWS S3 bucket for images
- JWT secret key

**Internal:**
- Epic 1 (infrastructure) must be complete

---

## Risks & Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| OAuth integration complexity | Medium | Start with email/password, add OAuth after |
| S3 upload failures | Medium | Add retry logic, show clear errors |
| Image size/format issues | Low | Client-side validation before upload |

---

## References

- **PRD:** `/docs/plans/AIVP_PRD.md` - Sections 3.1, 3.2 (Auth & Brands)
- **UI Spec:** `/docs/plans/AIVP_UISpecification.md` - Screens 1-4
- **Design Decisions:** `/docs/plans/AIVP_DesignDecisions.md`
- **Related Epics:** Epic 3 (Chat will use brand context)
