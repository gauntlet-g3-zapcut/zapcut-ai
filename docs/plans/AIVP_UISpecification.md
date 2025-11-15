# Frontend Specification - AI Video Generation Pipeline
**Date:** 2025-11-15
**Status:** Complete
**Related:** PRD-AI-Video-Generation-Pipeline.md, 2025-11-15-technical-architecture-decisions.md

---

## Table of Contents

1. [Overview](#overview)
2. [Tech Stack](#tech-stack)
3. [Design System](#design-system)
4. [Application Architecture](#application-architecture)
5. [Complete UI Flows](#complete-ui-flows)
6. [Screen Specifications](#screen-specifications)
7. [Component Library](#component-library)
8. [State Management](#state-management)
9. [API Integration](#api-integration)
10. [File Structure](#file-structure)

---

## Overview

### Application Type
**Electron Desktop Application** with cloud backend integration

### Key Characteristics
- Hybrid architecture: Cloud features + local video editor
- Modern glassmorphism design
- Responsive layout (desktop-first)
- Real-time progress tracking
- Seamless editor integration

### User Journey
```
Landing → Auth → Brands Dashboard → Chat → Script Review →
Video Generation → Video Editor (Zapcut)
```

---

## Tech Stack

### Core Framework
- **Electron**: Desktop application wrapper
- **React 18+**: UI framework
- **TypeScript**: Type safety
- **Vite**: Build tool (existing)

### Styling
- **TailwindCSS**: Utility-first CSS
- **Glassmorphism**: Custom design system
- **CSS Variables**: Theme management

### State Management
- **Zustand**: Global state (existing)
  - `authStore`: User authentication state
  - `brandStore`: Brand data (cloud-synced)
  - `adProjectStore`: Ad project data (cloud-synced)
  - `generationStore`: Video generation progress
  - `projectStore`: Zapcut editor state (existing, local)
  - `uiStore`: UI state (existing)

### UI Components
- **Lucide React**: Icon library
- **Custom components**: Glassmorphism design system
- **shadcn/ui base**: Button, Dialog, Input (existing)

### Data Fetching
- **Fetch API**: HTTP requests to backend
- **Polling**: Generation progress updates (5s interval)

### Routing
- **React Router DOM**: Client-side routing
- Routes:
  - `/` - Landing page
  - `/login` - Login page
  - `/signup` - Signup page
  - `/brands` - Brands dashboard
  - `/brands/:brandId/chat` - Chat interface
  - `/brands/:brandId/projects/:projectId/script` - Script review
  - `/brands/:brandId/projects/:projectId/generate` - Generation status
  - `/editor/:projectId` - Zapcut editor (existing)

---

## Design System

### Brand Colors

```typescript
// tailwind.config.js
export default {
  theme: {
    extend: {
      colors: {
        // Primary
        'lightning-yellow': '#FFEB3B',
        'lightning-yellow-dark': '#FFC107',

        // Backgrounds
        'cosmic-dark': '#0A0E27',
        'mid-navy': '#1A2332',
        'dark-navy': '#0F1419',

        // Accents
        'light-blue': '#4FC3F7',
        'light-blue-dark': '#0288D1',

        // Neutrals
        'glass-white': 'rgba(255, 255, 255, 0.05)',
        'glass-border': 'rgba(255, 255, 255, 0.1)',
      }
    }
  }
}
```

### Typography

```css
/* Font Stack */
font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
             "Helvetica Neue", Arial, sans-serif;

/* Sizes */
--text-xs: 0.75rem;     /* 12px */
--text-sm: 0.875rem;    /* 14px */
--text-base: 1rem;      /* 16px */
--text-lg: 1.125rem;    /* 18px */
--text-xl: 1.25rem;     /* 20px */
--text-2xl: 1.5rem;     /* 24px */
--text-3xl: 1.875rem;   /* 30px */
--text-4xl: 2.25rem;    /* 36px */

/* Weights */
--font-normal: 400;
--font-medium: 500;
--font-semibold: 600;
--font-bold: 700;
```

### Glassmorphism Components

```css
/* Glass Card */
.glass-card {
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
}

/* Glass Input */
.glass-input {
  background: rgba(255, 255, 255, 0.08);
  backdrop-filter: blur(8px);
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 8px;
  color: #FFFFFF;
  padding: 12px 16px;
  transition: all 0.3s ease;
}

.glass-input:focus {
  border-color: #FFEB3B;
  outline: none;
  box-shadow: 0 0 0 2px rgba(255, 235, 59, 0.2);
}

/* Primary Button */
.btn-primary {
  background: linear-gradient(135deg, #FFEB3B 0%, #FFC107 100%);
  color: #0A0E27;
  font-weight: 600;
  border-radius: 8px;
  padding: 12px 24px;
  box-shadow: 0 4px 16px rgba(255, 235, 59, 0.3);
  border: none;
  cursor: pointer;
  transition: all 0.3s ease;
}

.btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(255, 235, 59, 0.4);
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
}

/* Secondary Button */
.btn-secondary {
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(8px);
  color: #FFFFFF;
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 8px;
  padding: 12px 24px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.btn-secondary:hover {
  background: rgba(255, 255, 255, 0.15);
  border-color: rgba(255, 255, 255, 0.3);
}
```

### Spacing Scale

```typescript
// Tailwind spacing (using existing scale)
const spacing = {
  xs: '4px',
  sm: '8px',
  md: '16px',
  lg: '24px',
  xl: '32px',
  '2xl': '48px',
  '3xl': '64px',
}
```

---

## Application Architecture

### Layout Structure

```
┌─────────────────────────────────────────────────────┐
│                    TopBar (60px)                    │
├──────┬────────────────────────────────────┬─────────┤
│ Left │                                    │  Right  │
│ Rail │         Main Content Area          │  Rail   │
│(60px)│                                    │ (60px)  │
│      │                                    │         │
├──────┴────────────────────────────────────┴─────────┤
│              Timeline (320px - Editor only)         │
└─────────────────────────────────────────────────────┘
```

### Navigation Flow

**Unauthenticated:**
```
Landing Page → Login/Signup → Brands Dashboard
```

**Authenticated:**
```
Brands Dashboard →
  ├─ Create Brand → Brand Modal → Chat Interface
  └─ Click Brand → Chat Interface → Script Review →
                   Generation Status → Editor
```

---

## Complete UI Flows

### Flow 1: First-Time User Journey

```
┌─────────────────────────────────────────────────┐
│ 1. LANDING PAGE                                 │
│                                                 │
│ [Hero Section]                                  │
│ "Create Professional Video Ads with AI"        │
│                                                 │
│ [Features Grid]                                 │
│ - AI-Powered Script Generation                  │
│ - Professional Voiceover & Music                │
│ - Brand-Specific Styling                        │
│                                                 │
│ Action: Click "Login" (top-right) ─────────────┐│
└─────────────────────────────────────────────────┘│
                                                   │
┌──────────────────────────────────────────────────▼┐
│ 2. LOGIN PAGE                                    │
│                                                  │
│ [Glass Card - Center]                            │
│ Email: [________________]                        │
│ Password: [________________]                     │
│                                                  │
│ [Login Button - Yellow]                          │
│ Don't have an account? Sign up                   │
│                                                  │
│ OR                                               │
│                                                  │
│ [Continue with Google]                           │
│                                                  │
│ Action: Login ──────────────────────────────────┐│
└──────────────────────────────────────────────────┘│
                                                    │
┌───────────────────────────────────────────────────▼┐
│ 3. BRANDS DASHBOARD (Empty State)                 │
│                                                    │
│ [Left Sidebar]                                     │
│ - User: John Doe                                   │
│ - Brands (active)                                  │
│ - Settings                                         │
│                                                    │
│ [Main Area - Empty State]                          │
│ ┌────────────────────────────────────────┐         │
│ │  [Illustration - Empty Box]            │         │
│ │                                        │         │
│ │  No brands yet                         │         │
│ │  Create your first brand to get started│         │
│ │                                        │         │
│ │  [Create Brand Button - Yellow]        │         │
│ └────────────────────────────────────────┘         │
│                                                    │
│ Action: Click "Create Brand" ──────────────────────┐│
└────────────────────────────────────────────────────┘│
                                                      │
┌─────────────────────────────────────────────────────▼┐
│ 4. CREATE BRAND MODAL                               │
│                                                     │
│ [Glass Modal - 600px width]                         │
│ ┌─────────────────────────────────────────────┐     │
│ │ Create Brand                           [X]  │     │
│ ├─────────────────────────────────────────────┤     │
│ │                                             │     │
│ │ Brand Title * (required)                    │     │
│ │ [________________________]                  │     │
│ │                                             │     │
│ │ Brand Description * (required)              │     │
│ │ [________________________]                  │     │
│ │ [________________________]                  │     │
│ │ [________________________]                  │     │
│ │ 500 characters max                          │     │
│ │                                             │     │
│ │ Product Images * (min 2, max 10)            │     │
│ │ ┌──────┐ ┌──────┐ ┌──────┐                 │     │
│ │ │ IMG1 │ │ IMG2 │ │  +   │                 │     │
│ │ └──────┘ └──────┘ └──────┘                 │     │
│ │ Drag & drop or click to upload              │     │
│ │                                             │     │
│ │ ▼ Brand Guidelines (Optional)               │     │
│ │                                             │     │
│ │ [Cancel]  [Create Brand - Yellow] ────────┐ │     │
│ └───────────────────────────────────────────┘ │     │
└───────────────────────────────────────────────┘     │
                                                      │
Action: Fill form + Upload 2 images + Click "Create"│
                                                      │
┌─────────────────────────────────────────────────────▼┐
│ 5. BRANDS DASHBOARD (With Brand)                    │
│                                                      │
│ [Header]                                             │
│ Brands                    [Create Brand - Yellow]    │
│                                                      │
│ [Brand Grid - 2-3 columns]                           │
│ ┌─────────────────┐                                  │
│ │  [Product Img]  │                                  │
│ │                 │                                  │
│ │  Acme Shoes     │                                  │
│ │  Created 2 mins │                                  │
│ │  0 projects     │                                  │
│ └─────────────────┘                                  │
│                                                      │
│ Action: Click brand card ──────────────────────────┐ │
└────────────────────────────────────────────────────┘ │
                                                       │
┌──────────────────────────────────────────────────────▼┐
│ 6. CHAT INTERFACE                                    │
│                                                      │
│ [Header]                                             │
│ ← Back to Brands    Acme Shoes    Step 1 of 3       │
│                                                      │
│ [Chat Messages - Scrollable]                         │
│ ┌────────────────────────────────────────────┐       │
│ │ [AI Avatar] Hi! I'm excited to help you    │       │
│ │             create an amazing ad for        │       │
│ │             Acme Shoes.                     │       │
│ │                                             │       │
│ │             To get started, could you tell  │       │
│ │             me what you want to achieve?    │       │
│ │                                             │       │
│ │                                   [You]     │       │
│ │                          We want to promote │       │
│ │                          our new running    │       │
│ │                          shoe line to       │       │
│ │                          young athletes     │       │
│ └────────────────────────────────────────────┘       │
│                                                      │
│ [Input Area]                                         │
│ [________________________] [Send →]                  │
│                                                      │
│ Interaction: User answers 5 AI questions ──────────┐ │
└────────────────────────────────────────────────────┘ │
                                                       │
After 5 questions answered...                         │
                                                       │
┌──────────────────────────────────────────────────────▼┐
│ 7. CHAT → SCRIPT TRANSITION                         │
│                                                      │
│ [Chat Messages]                                      │
│ ┌────────────────────────────────────────────┐       │
│ │ [AI Avatar] Perfect! I have everything I   │       │
│ │             need. Let me create a          │       │
│ │             storyline for your ad...       │       │
│ │                                             │       │
│ │             [Loading Animation]             │       │
│ │             Generating script...            │       │
│ └────────────────────────────────────────────┘       │
│                                                      │
│ Auto-navigate after 3-5 seconds ────────────────────┐│
└─────────────────────────────────────────────────────┘│
                                                       │
┌──────────────────────────────────────────────────────▼┐
│ 8. SCRIPT REVIEW PAGE                                │
│                                                      │
│ [Header]                                             │
│ ← Back    Acme Shoes - Script Review    Step 2 of 3 │
│                                                      │
│ [Storyline Section - Glass Card]                     │
│ ┌────────────────────────────────────────────┐       │
│ │ 📝 Storyline                              │       │
│ │                                            │       │
│ │ "Follow a young runner as they discover   │       │
│ │  the perfect shoe for their morning run.  │       │
│ │  From city streets to mountain trails,    │       │
│ │  Acme Shoes keeps them moving forward."   │       │
│ └────────────────────────────────────────────┘       │
│                                                      │
│ [Scenes Section - Scrollable]                        │
│ ┌────────────────────────────────────────────┐       │
│ │ Scene 1          Duration: 5s              │       │
│ │ ────────────────────────────────────       │       │
│ │ Visual: Runner lacing up Acme Shoes in     │       │
│ │         morning light, close-up on shoe    │       │
│ │                                             │       │
│ │ Voiceover: "Every journey starts with      │       │
│ │            the right first step."           │       │
│ │                                             │       │
│ │ ▼ Show Sora Prompt                          │       │
│ └────────────────────────────────────────────┘       │
│                                                      │
│ ┌────────────────────────────────────────────┐       │
│ │ Scene 2          Duration: 10s             │       │
│ │ ...                                         │       │
│ └────────────────────────────────────────────┘       │
│                                                      │
│ [Actions - Bottom Fixed]                             │
│ [Regenerate Script]  [Approve & Generate Video →]    │
│                                                      │
│ Action: Click "Approve & Generate Video" ──────────┐ │
└────────────────────────────────────────────────────┘ │
                                                       │
┌──────────────────────────────────────────────────────▼┐
│ 9. VIDEO GENERATION STATUS                          │
│                                                      │
│ [Full Screen - Glass Overlay]                        │
│                                                      │
│            [⚡ Lightning Bolt Animation]              │
│                                                      │
│         Your ad is being created...                  │
│                                                      │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 45%                  │
│                                                      │
│       Generating Scene 2 of 3                        │
│                                                      │
│       About 3 minutes remaining                      │
│                                                      │
│ [Current Steps - Checkmarks]                         │
│ ✅ Scene 1 generated                                 │
│ ⏳ Scene 2 generating...                             │
│ ⏸️  Scene 3 pending                                  │
│ ⏸️  Creating voiceover                               │
│ ⏸️  Composing music                                  │
│ ⏸️  Finalizing video                                 │
│                                                      │
│ Polling every 5 seconds for updates...               │
│                                                      │
│ When complete, auto-navigate ──────────────────────┐ │
└────────────────────────────────────────────────────┘ │
                                                       │
┌──────────────────────────────────────────────────────▼┐
│ 10. GENERATION COMPLETE                              │
│                                                      │
│            [✅ Success Animation]                     │
│                                                      │
│              Your ad is ready!                       │
│                                                      │
│ [Video Preview - 400px width]                        │
│ ┌────────────────────────────────────┐               │
│ │                                    │               │
│ │   [Generated Video Playing]        │               │
│ │                                    │               │
│ │   ▶️  0:15 / 0:15                  │               │
│ └────────────────────────────────────┘               │
│                                                      │
│ [Actions]                                            │
│ [Download Video]  [Open in Editor - Yellow →]        │
│                                                      │
│ Action: Click "Open in Editor" ────────────────────┐ │
└────────────────────────────────────────────────────┘ │
                                                       │
┌──────────────────────────────────────────────────────▼┐
│ 11. ZAPCUT VIDEO EDITOR                              │
│                                                      │
│ [Existing Zapcut UI]                                 │
│ - Generated video loaded as asset                    │
│ - Video on timeline                                  │
│ - Audio tracks visible                               │
│ - Product images in library                          │
│                                                      │
│ User can now:                                        │
│ - Edit timeline (trim, split, rearrange)             │
│ - Add effects/transitions                            │
│ - Adjust audio levels                                │
│ - Add text overlays                                  │
│ - Export final video                                 │
│                                                      │
│ [Top Bar]                                            │
│ ← Back to Brands    [Export Button]                  │
└─────────────────────────────────────────────────────┘
```

### Flow 2: Returning User - Second Video

```
┌──────────────────────────────────────────────────┐
│ BRANDS DASHBOARD (Returning User)                │
│                                                  │
│ [Brand Grid]                                     │
│ ┌─────────────────┐                              │
│ │  [Product Img]  │                              │
│ │                 │                              │
│ │  Acme Shoes     │                              │
│ │  Created 2 days │                              │
│ │  1 project      │ ← First video completed     │
│ │                 │                              │
│ │  [Notification Badge]                          │
│ │  "Custom brand style ready!"                   │
│ └─────────────────┘                              │
│                                                  │
│ Click brand card ─────────────────────────────┐  │
└──────────────────────────────────────────────┘  │
                                                  │
┌─────────────────────────────────────────────────▼┐
│ LORA PREVIEW MODAL (One-time)                   │
│                                                 │
│ [Glass Modal - 800px width]                     │
│ ┌─────────────────────────────────────────┐     │
│ │ 🎨 Your Custom Brand Style is Ready!    │     │
│ ├─────────────────────────────────────────┤     │
│ │                                         │     │
│ │ Compare the difference:                 │     │
│ │                                         │     │
│ │ ┌──────────────┐  ┌──────────────┐      │     │
│ │ │   Standard   │  │  Your Style  │      │     │
│ │ │              │  │              │      │     │
│ │ │  [Sample]    │  │  [Sample]    │      │     │
│ │ │   Frame      │  │   Frame      │      │     │
│ │ └──────────────┘  └──────────────┘      │     │
│ │                                         │     │
│ │ Your custom style ensures all future    │     │
│ │ videos maintain consistent brand look.  │     │
│ │                                         │     │
│ │ Use this style for future ads?          │     │
│ │                                         │     │
│ │ [No, use standard]  [Yes, use my style] │     │
│ └─────────────────────────────────────────┘     │
│                                                 │
│ User decision saved → Proceeds to chat ─────────┤
└─────────────────────────────────────────────────┘
```

### Flow 3: Pricing/Paywall (After 2 Free Videos)

```
┌──────────────────────────────────────────────────┐
│ CHAT INTERFACE (3rd Video Attempt)               │
│                                                  │
│ User starts typing message...                    │
│                                                  │
│ → Trigger: Paywall modal appears                 │
└──────────────────────────────────────────────────┘
                ↓
┌─────────────────────────────────────────────────┐
│ PRICING MODAL (Blocking)                        │
│                                                 │
│ [Glass Modal - 900px width]                     │
│ ┌─────────────────────────────────────────┐     │
│ │ Choose your plan to continue creating   │     │
│ ├─────────────────────────────────────────┤     │
│ │                                         │     │
│ │ You've used your 2 free videos! 🎉      │     │
│ │                                         │     │
│ │ ┌─────────────┐  ┌──────────────┐       │     │
│ │ │ PAY AS YOU GO│  │SUBSCRIPTION │       │     │
│ │ ├─────────────┤  ├──────────────┤       │     │
│ │ │ $5 per video│  │   Starter    │       │     │
│ │ │             │  │   $29/month  │       │     │
│ │ │ 30s max     │  │              │       │     │
│ │ │ 1080p       │  │ 10 videos    │       │     │
│ │ │             │  │ 30s max      │       │     │
│ │ │ [Buy Credits│  │ 1080p        │       │     │
│ │ │    $5/ea]   │  │              │       │     │
│ │ │             │  │ [Subscribe]  │ ⭐     │     │
│ │ │  OR         │  │ Most Popular │       │     │
│ │ │             │  │              │       │     │
│ │ │ Save with   │  │   Pro        │       │     │
│ │ │ credit packs│  │   $79/month  │       │     │
│ │ │             │  │              │       │     │
│ │ │ $40 = 10    │  │ 30 videos    │       │     │
│ │ │ ($4 each)   │  │ 60s max      │       │     │
│ │ └─────────────┘  └──────────────┘       │     │
│ │                                         │     │
│ │ All plans include:                      │     │
│ │ ✓ AI script generation                  │     │
│ │ ✓ Professional voiceover & music        │     │
│ │ ✓ Custom brand style                    │     │
│ │ ✓ Full editor access                    │     │
│ │                                         │     │
│ │              [Continue →]               │     │
│ └─────────────────────────────────────────┘     │
└─────────────────────────────────────────────────┘
```

---

## Screen Specifications

### Screen 1: Landing Page

**Route:** `/`

**Purpose:** Marketing page to attract and convert users

**Layout:**
```
┌─────────────────────────────────────────────┐
│ [TopBar - Transparent overlay]              │
│ Logo               [Features] [Pricing] [Login]
├─────────────────────────────────────────────┤
│                                             │
│          [Hero Section - Full viewport]     │
│                                             │
│  Create Professional Video Ads with AI      │
│       in Minutes, Not Hours                 │
│                                             │
│  [Get Started Free →]                       │
│                                             │
├─────────────────────────────────────────────┤
│                                             │
│  [Features Grid - 3 columns]                │
│  ┌──────┐  ┌──────┐  ┌──────┐              │
│  │  AI  │  │Voice │  │Brand │              │
│  │Script│  │ Over │  │Style │              │
│  └──────┘  └──────┘  └──────┘              │
│                                             │
├─────────────────────────────────────────────┤
│  [Social Proof]                             │
│  "Join 1000+ businesses creating ads..."    │
│                                             │
└─────────────────────────────────────────────┘
```

**Components:**
- `<LandingHero />`
- `<FeaturesGrid />`
- `<SocialProof />`
- `<Footer />`

**State:** None (static page)

**Actions:**
- Click "Login" → Navigate to `/login`
- Click "Get Started" → Navigate to `/signup`

---

### Screen 2: Login Page

**Route:** `/login`

**Purpose:** User authentication

**Layout:**
```
┌─────────────────────────────────────────────┐
│        [Cosmic Background - Full screen]    │
│                                             │
│             [Glass Card - Center]           │
│                                             │
│          ⚡ Welcome Back                     │
│                                             │
│  Email                                      │
│  [_________________________]                │
│                                             │
│  Password                                   │
│  [_________________________]                │
│  Forgot password?                           │
│                                             │
│  [Login →]                                  │
│                                             │
│  ──────────── OR ────────────               │
│                                             │
│  [Continue with Google]                     │
│                                             │
│  Don't have an account? Sign up             │
│                                             │
└─────────────────────────────────────────────┘
```

**Components:**
- `<AuthLayout>`
  - `<GlassCard>`
    - `<LoginForm>`
      - `<GlassInput name="email" />`
      - `<GlassInput type="password" name="password" />`
      - `<PrimaryButton>Login</PrimaryButton>`
      - `<GoogleAuthButton />`

**State:**
```typescript
const [email, setEmail] = useState('');
const [password, setPassword] = useState('');
const [isLoading, setIsLoading] = useState(false);
const [error, setError] = useState('');
```

**API Integration:**
```typescript
POST /api/auth/login
Body: { email, password }
Response: { token, user: { id, name, email, subscription_tier } }
```

**Actions:**
1. User fills email + password
2. Click "Login" → POST to `/api/auth/login`
3. On success:
   - Store token in localStorage
   - Update authStore
   - Navigate to `/brands`
4. On error: Display error message

**Validation:**
- Email: Required, valid format
- Password: Required, min 8 chars

---

### Screen 3: Brands Dashboard

**Route:** `/brands`

**Purpose:** View and manage brands, starting point for ad creation

**Layout:**
```
┌────┬────────────────────────────────────────┬────┐
│Left│           Main Content Area            │Right│
│Rail│                                        │Rail│
│    │  [Header]                              │    │
│    │  Brands         [Create Brand →]       │    │
│    │                                        │    │
│ 👤 │  [Brand Grid - 2-3 columns]            │    │
│    │  ┌────────────┐  ┌────────────┐        │ ⚙️  │
│Bra │  │[Prod Img]  │  │[Prod Img]  │        │    │
│nds │  │            │  │            │        │Set │
│    │  │Acme Shoes  │  │TechGadget  │        │ting│
│Set │  │2 days ago  │  │1 week ago  │        │s   │
│ting│  │3 projects  │  │1 project   │        │    │
│s   │  └────────────┘  └────────────┘        │    │
│    │                                        │    │
│    │  [Empty State - if no brands]          │    │
│    │  ┌─────────────────────────────┐       │    │
│    │  │  [Empty Box Illustration]   │       │    │
│    │  │                             │       │    │
│    │  │  No brands yet              │       │    │
│    │  │  Create your first brand    │       │    │
│    │  │  to get started             │       │    │
│    │  │                             │       │    │
│    │  │  [Create Brand →]           │       │    │
│    │  └─────────────────────────────┘       │    │
└────┴────────────────────────────────────────┴────┘
```

**Components:**
- `<DashboardLayout>`
  - `<LeftSidebar>`
    - `<UserProfile />`
    - `<NavItem active>Brands</NavItem>`
    - `<NavItem>Settings</NavItem>`
  - `<MainContent>`
    - `<PageHeader>`
      - `<h1>Brands</h1>`
      - `<PrimaryButton onClick={openCreateBrandModal}>Create Brand</PrimaryButton>`
    - `<BrandGrid>`
      - `<BrandCard />` (repeated)
    - `<EmptyState>` (conditional)

**State:**
```typescript
// brandStore (Zustand)
interface BrandStore {
  brands: Brand[];
  isLoading: boolean;
  fetchBrands: () => Promise<void>;
  createBrand: (data: CreateBrandDTO) => Promise<Brand>;
}

// Local state
const [showCreateModal, setShowCreateModal] = useState(false);
```

**API Integration:**
```typescript
GET /api/brands
Response: Brand[]

interface Brand {
  id: string;
  title: string;
  description: string;
  product_images: string[];
  created_at: string;
  project_count: number;
  lora_model_status?: 'none' | 'training' | 'ready';
}
```

**Actions:**
1. On mount: Fetch brands (`GET /api/brands`)
2. Click "Create Brand" → Open `<CreateBrandModal>`
3. Click brand card → Navigate to `/brands/{brandId}/chat`
4. Display LoRA notification badge if `lora_model_status === 'ready'` and not yet approved

**Responsive Behavior:**
- 3 columns on large screens (1920px+)
- 2 columns on medium screens (1024px-1919px)
- 1 column on small screens (<1024px)

---

### Screen 4: Create Brand Modal

**Component:** `<CreateBrandModal>`

**Purpose:** Collect brand information and product images

**Layout:**
```
[Glass Modal Overlay - Full screen dimmed]

      ┌─────────────────────────────────────┐
      │ Create Brand                   [X]  │
      ├─────────────────────────────────────┤
      │                                     │
      │ Brand Title *                       │
      │ [_____________________________]     │
      │                                     │
      │ Brand Description * (500 char max)  │
      │ [_____________________________]     │
      │ [_____________________________]     │
      │ [_____________________________]     │
      │ 450/500 characters                  │
      │                                     │
      │ Product Images * (2-10 images)      │
      │ ┌────────┐ ┌────────┐ ┌────────┐   │
      │ │ [IMG1] │ │ [IMG2] │ │   +    │   │
      │ │  [X]   │ │  [X]   │ │  Add   │   │
      │ └────────┘ └────────┘ └────────┘   │
      │ JPG, PNG, WEBP • Max 10MB each      │
      │                                     │
      │ ▼ Brand Guidelines (Optional)       │
      │   ┌─────────────────────────────┐   │
      │   │ Brand Colors                │   │
      │   │ [Color Picker]              │   │
      │   │                             │   │
      │   │ Tone of Voice               │   │
      │   │ [_______________________]   │   │
      │   └─────────────────────────────┘   │
      │                                     │
      │ [Cancel]      [Create Brand →]      │
      │               (Disabled if invalid) │
      └─────────────────────────────────────┘
```

**Components:**
- `<Modal>`
  - `<GlassCard>`
    - `<Form onSubmit={handleCreateBrand}>`
      - `<GlassInput name="title" required />`
      - `<GlassTextarea name="description" required maxLength={500} />`
      - `<ImageUploader min={2} max={10} />`
      - `<Accordion title="Brand Guidelines">`
        - `<ColorPicker />`
        - `<GlassInput name="tone" />`
      - `<SecondaryButton onClick={close}>Cancel</SecondaryButton>`
      - `<PrimaryButton type="submit" disabled={!isValid}>Create Brand</PrimaryButton>`

**State:**
```typescript
interface CreateBrandFormState {
  title: string;
  description: string;
  productImages: File[];
  brandGuidelines: {
    colors: string[];
    tone: string;
  };
}

const [formData, setFormData] = useState<CreateBrandFormState>({
  title: '',
  description: '',
  productImages: [],
  brandGuidelines: { colors: [], tone: '' }
});

const [isUploading, setIsUploading] = useState(false);
const [errors, setErrors] = useState<Record<string, string>>({});
```

**Validation:**
```typescript
const isValid =
  formData.title.length > 0 &&
  formData.description.length > 0 &&
  formData.description.length <= 500 &&
  formData.productImages.length >= 2 &&
  formData.productImages.length <= 10;
```

**API Integration:**
```typescript
// Step 1: Upload images
POST /api/upload (multipart/form-data)
Files: productImages[]
Response: { urls: string[] }

// Step 2: Create brand
POST /api/brands
Body: {
  title: string;
  description: string;
  product_images: string[]; // URLs from step 1
  brand_guidelines: {
    colors: string[];
    tone: string;
  };
}
Response: Brand
```

**Actions:**
1. User fills form
2. User uploads 2+ images (previews shown)
3. Click "Create Brand":
   - Validate form
   - Upload images to S3 (via `/api/upload`)
   - Create brand record (POST `/api/brands`)
   - Close modal
   - Refresh brand list
   - Navigate to `/brands/{brandId}/chat`

**Error Handling:**
- Image upload fails: Show error, allow retry
- Brand creation fails: Show error message
- Validation errors: Inline error messages

---

### Screen 5: Chat Interface

**Route:** `/brands/:brandId/chat`

**Purpose:** Conversational AI to gather ad requirements

**Layout:**
```
┌─────────────────────────────────────────────────┐
│ [Header]                                        │
│ ← Back to Brands   [Brand Icon] Acme Shoes      │
│                             Step 1 of 3: Details│
└─────────────────────────────────────────────────┘
│                                                 │
│ [Chat Messages - Scrollable]                    │
│ ┌───────────────────────────────────────────┐   │
│ │                                           │   │
│ │  [AI Avatar]  Hi! I'm excited to help... │   │
│ │               (Left-aligned, glass card)  │   │
│ │                                           │   │
│ │                                   [You]   │   │
│ │         We want to promote our... (Right) │   │
│ │                                           │   │
│ │  [AI]  Great! Who is your target...      │   │
│ │                                           │   │
│ │                                   [You]   │   │
│ │                   Young athletes... (Right)   │
│ │                                           │   │
│ │  [Typing indicator...]                    │   │
│ │                                           │   │
│ └───────────────────────────────────────────┘   │
│                                                 │
│ [Input Area - Fixed Bottom]                     │
│ ┌───────────────────────────────────────────┐   │
│ │ [______________________________] [Send →] │   │
│ │ Type your message...                      │   │
│ └───────────────────────────────────────────┘   │
└─────────────────────────────────────────────────┘
```

**Components:**
- `<ChatLayout>`
  - `<ChatHeader>`
    - `<BackButton to="/brands" />`
    - `<BrandInfo brand={brand} />`
    - `<ProgressIndicator currentStep={1} totalSteps={3} />`
  - `<ChatMessages>`
    - `<MessageBubble />` (repeated)
      - `<AssistantMessage>` (left, yellow tint)
      - `<UserMessage>` (right, white tint)
    - `<TypingIndicator>` (conditional)
  - `<ChatInput>`
    - `<GlassInput onSubmit={sendMessage} />`
    - `<IconButton icon="send" />`

**State:**
```typescript
// adProjectStore (Zustand)
interface AdProjectStore {
  currentProject: AdProject | null;
  messages: ChatMessage[];
  isAIResponding: boolean;
  sendMessage: (content: string) => Promise<void>;
  questionCount: number; // Track questions asked (max 5)
}

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}
```

**API Integration:**
```typescript
// Create new ad project (on first load)
POST /api/brands/{brandId}/projects
Response: { id: string, brand_id: string, status: 'chat' }

// Send message and get AI response
POST /api/projects/{projectId}/chat
Body: { message: string }
Response: {
  message: {
    role: 'assistant',
    content: string
  },
  question_count: number,
  is_complete: boolean // true after 5 questions
}
```

**Conversation Flow:**
1. **Initial Message** (Auto-sent on mount):
   ```
   Hi! I'm excited to help you create an amazing ad for [Brand Name].
   To get started, could you tell me a bit about what you want to achieve
   with this ad?
   ```

2. **Question 1-5**: AI asks follow-up questions based on user responses
   - Target audience
   - Ad platform (Instagram, Facebook, TikTok, YouTube)
   - Ad duration (15s, 30s, 60s)
   - Key message / USP
   - Call-to-action

3. **Completion Message**:
   ```
   Perfect! I have everything I need. Let me create a storyline for your ad...
   [Loading animation]
   ```

4. **Auto-navigate** after 3 seconds → `/brands/{brandId}/projects/{projectId}/script`

**Actions:**
1. User types message in input
2. Press Enter or click Send
3. Add user message to UI immediately
4. Show typing indicator
5. POST to `/api/projects/{projectId}/chat`
6. Add AI response to UI
7. After 5 questions: Show completion message → Navigate to script review

**UX Details:**
- Auto-scroll to latest message
- Disable input while AI is responding
- Character limit: 500 chars per message
- Enter to send, Shift+Enter for new line

---

### Screen 6: Script Review

**Route:** `/brands/:brandId/projects/:projectId/script`

**Purpose:** Review and approve AI-generated ad script

**Layout:**
```
┌─────────────────────────────────────────────────┐
│ [Header]                                        │
│ ← Back   [Brand Icon] Acme Shoes - Script Review│
│                             Step 2 of 3: Script │
└─────────────────────────────────────────────────┘
│                                                 │
│ [Storyline Section - Glass Card]                │
│ ┌───────────────────────────────────────────┐   │
│ │ 📝 Storyline                              │   │
│ │                                           │   │
│ │ "Follow a young runner as they discover   │   │
│ │  the perfect shoe for their morning run.  │   │
│ │  From city streets to mountain trails,    │   │
│ │  Acme Shoes keeps them moving forward."   │   │
│ │                                           │   │
│ └───────────────────────────────────────────┘   │
│                                                 │
│ [Scenes - Scrollable]                           │
│ ┌───────────────────────────────────────────┐   │
│ │ ┌─────────────────────────────────────┐   │   │
│ │ │ Scene 1             Duration: 5s    │   │   │
│ │ ├─────────────────────────────────────┤   │   │
│ │ │ 🎬 Visual Description               │   │   │
│ │ │ Close-up of runner lacing up Acme   │   │   │
│ │ │ Shoes in golden morning light.      │   │   │
│ │ │                                     │   │   │
│ │ │ 🎙️ Voiceover                         │   │   │
│ │ │ "Every journey starts with the      │   │   │
│ │ │  right first step."                 │   │   │
│ │ │                                     │   │   │
│ │ │ ▼ Show Sora Prompt                  │   │   │
│ │ │   ┌─────────────────────────────┐   │   │   │
│ │ │   │ Cinematic close-up shot of  │   │   │
│ │ │   │ athletic hands tying bright │   │   │
│ │ │   │ red running shoes, warm...  │   │   │
│ │ │   └─────────────────────────────┘   │   │   │
│ │ └─────────────────────────────────────┘   │   │
│ │                                           │   │
│ │ ┌─────────────────────────────────────┐   │   │
│ │ │ Scene 2             Duration: 10s   │   │   │
│ │ └─────────────────────────────────────┘   │   │
│ │                                           │   │
│ │ ┌─────────────────────────────────────┐   │   │
│ │ │ Scene 3             Duration: 15s   │   │   │
│ │ └─────────────────────────────────────┘   │   │
│ └───────────────────────────────────────────┘   │
│                                                 │
│ [Actions - Fixed Bottom]                        │
│ ┌───────────────────────────────────────────┐   │
│ │ [Regenerate Script]  [Approve & Generate →│   │
│ └───────────────────────────────────────────┘   │
└─────────────────────────────────────────────────┘
```

**Components:**
- `<ScriptReviewLayout>`
  - `<ScriptHeader>`
    - `<BackButton />`
    - `<BrandInfo />`
    - `<ProgressIndicator currentStep={2} />`
  - `<StorylineCard>`
    - Storyline text (2-3 sentences)
  - `<ScenesList>`
    - `<SceneCard />` (repeated for each scene)
      - Scene number & duration
      - Visual description
      - Voiceover text
      - `<Accordion title="Show Sora Prompt">`
        - Detailed visual prompt
  - `<ActionBar>`
    - `<SecondaryButton onClick={regenerateScript}>Regenerate Script</SecondaryButton>`
    - `<PrimaryButton onClick={approveAndGenerate}>Approve & Generate Video →</PrimaryButton>`

**State:**
```typescript
interface Script {
  id: string;
  storyline: string;
  scenes: Scene[];
}

interface Scene {
  sceneNumber: number;
  description: string;
  duration: number;
  visualPrompt: string;
  voiceoverText?: string;
  audioPrompt?: string;
}

// adProjectStore
const script = useAdProjectStore(state => state.script);
const isRegenerating = useAdProjectStore(state => state.isRegenerating);
```

**API Integration:**
```typescript
// Fetch script (generated during chat transition)
GET /api/projects/{projectId}/script
Response: Script

// Regenerate script
POST /api/projects/{projectId}/script/regenerate
Response: Script

// Approve and start generation
POST /api/projects/{projectId}/generate-video
Response: { status: 'processing', job_id: string }
```

**Actions:**
1. **On Mount**: Fetch script (GET `/api/projects/{projectId}/script`)
2. **Regenerate Script**:
   - Show loading state
   - POST to `/api/projects/{projectId}/script/regenerate`
   - Replace script with new version
3. **Approve & Generate Video**:
   - POST to `/api/projects/{projectId}/generate-video`
   - Navigate to `/brands/{brandId}/projects/{projectId}/generate`

**UX Details:**
- Accordion for Sora prompts (collapsed by default)
- Smooth scroll to top on regenerate
- Disable buttons during regeneration
- Show loading skeleton while fetching script

---

### Screen 7: Video Generation Status

**Route:** `/brands/:brandId/projects/:projectId/generate`

**Purpose:** Real-time progress tracking for video generation

**Layout:**
```
┌─────────────────────────────────────────────────┐
│           [Full Screen - Glass Overlay]         │
│                                                 │
│                                                 │
│            [⚡ Lightning Bolt Animation]         │
│                 (Pulsing yellow)                │
│                                                 │
│         Your ad is being created...             │
│                                                 │
│                                                 │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 45%       │
│                                                 │
│                                                 │
│          Generating Scene 2 of 3                │
│                                                 │
│        About 3 minutes remaining                │
│                                                 │
│                                                 │
│  [Progress Steps - Vertical]                    │
│  ✅ Scene 1 generated                           │
│  ⏳ Scene 2 generating...    ← Active           │
│  ⏸️  Scene 3 pending                            │
│  ⏸️  Creating voiceover                         │
│  ⏸️  Composing music                            │
│  ⏸️  Adding sound effects                       │
│  ⏸️  Finalizing video                           │
│                                                 │
│                                                 │
│  [Note: This process takes 6-8 minutes]         │
│  You can close this window and return later.    │
│                                                 │
└─────────────────────────────────────────────────┘
```

**Components:**
- `<GenerationStatusLayout>`
  - `<AnimatedIcon type="lightning" pulsing />`
  - `<Title>Your ad is being created...</Title>`
  - `<ProgressBar value={progress} />`
  - `<CurrentStep>{currentStep}</CurrentStep>`
  - `<TimeRemaining>{estimatedTime}</TimeRemaining>`
  - `<ProgressSteps>`
    - `<StepItem status="completed" />` ✅
    - `<StepItem status="active" />` ⏳
    - `<StepItem status="pending" />` ⏸️

**State:**
```typescript
interface GenerationStatus {
  status: 'processing' | 'completed' | 'failed';
  progress: number; // 0-100
  currentStep: string;
  estimatedTimeRemaining: number; // seconds
  steps: GenerationStep[];
  videoUrl?: string;
  errorMessage?: string;
}

interface GenerationStep {
  name: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
}
```

**API Integration:**
```typescript
// Poll for status every 5 seconds
GET /api/projects/{projectId}/generation-status
Response: GenerationStatus
```

**Polling Logic:**
```typescript
useEffect(() => {
  const pollInterval = setInterval(async () => {
    const status = await fetchGenerationStatus(projectId);

    setGenerationStatus(status);

    if (status.status === 'completed') {
      clearInterval(pollInterval);
      // Auto-navigate to completion screen
      navigate('completion');
    } else if (status.status === 'failed') {
      clearInterval(pollInterval);
      // Show error modal
      showErrorModal(status.errorMessage);
    }
  }, 5000); // Poll every 5 seconds

  return () => clearInterval(pollInterval);
}, [projectId]);
```

**Progress Calculation:**
```typescript
// Backend calculates progress based on completed jobs
const steps = [
  'Scene 1 generated',
  'Scene 2 generated',
  'Scene 3 generated',
  'Voiceover created',
  'Music composed',
  'Sound effects added',
  'Video finalized'
];

const progress = (completedSteps / totalSteps) * 100;
```

**Actions:**
1. **On Mount**: Start polling for status
2. **Every 5 seconds**: Fetch latest status
3. **On Completion**: Stop polling, show success screen
4. **On Failure**: Stop polling, show error modal

**UX Details:**
- Smooth progress bar animation
- Active step highlighted with animation
- Can close and return (generation continues server-side)
- Estimated time updates based on actual progress

---

### Screen 8: Generation Complete

**Component:** `<GenerationCompleteScreen>`

**Purpose:** Show generated video and provide next actions

**Layout:**
```
┌─────────────────────────────────────────────────┐
│                                                 │
│                                                 │
│            [✅ Success Animation]                │
│                 (Checkmark)                     │
│                                                 │
│              Your ad is ready!                  │
│                                                 │
│                                                 │
│  [Video Preview - 600px width, 16:9]            │
│  ┌─────────────────────────────────────────┐    │
│  │                                         │    │
│  │                                         │    │
│  │      [Generated Video Player]           │    │
│  │                                         │    │
│  │                                         │    │
│  │  ▶️  0:00 / 0:15                        │    │
│  └─────────────────────────────────────────┘    │
│                                                 │
│                                                 │
│  [Video Info]                                   │
│  Duration: 15 seconds                           │
│  Resolution: 1080p                              │
│  File size: 12.4 MB                             │
│                                                 │
│                                                 │
│  [Actions - Two buttons]                        │
│  ┌──────────────────┐  ┌──────────────────┐    │
│  │  Download Video  │  │ Open in Editor → │    │
│  │   (Secondary)    │  │    (Primary)     │    │
│  └──────────────────┘  └──────────────────┘    │
│                                                 │
│  ← Back to Brands                               │
│                                                 │
└─────────────────────────────────────────────────┘
```

**Components:**
- `<SuccessLayout>`
  - `<SuccessAnimation>`
  - `<Title>Your ad is ready!</Title>`
  - `<VideoPlayer src={videoUrl} controls />`
  - `<VideoInfo>`
    - Duration, resolution, file size
  - `<ActionButtons>`
    - `<SecondaryButton onClick={downloadVideo}>Download Video</SecondaryButton>`
    - `<PrimaryButton onClick={openInEditor}>Open in Editor →</PrimaryButton>`

**State:**
```typescript
const videoUrl = useAdProjectStore(state => state.currentProject?.final_video_url);
const isDownloading = useState(false);
```

**Actions:**
1. **Download Video**:
   - Get signed S3 URL from backend
   - Trigger browser download
   ```typescript
   const downloadVideo = async () => {
     const response = await fetch(videoUrl);
     const blob = await response.blob();
     const url = window.URL.createObjectURL(blob);
     const a = document.createElement('a');
     a.href = url;
     a.download = `${brandName}_ad_${Date.now()}.mp4`;
     a.click();
   };
   ```

2. **Open in Editor**:
   - Download video to local temp folder
   - Load into Zapcut editor
   - Navigate to editor
   ```typescript
   const openInEditor = async () => {
     // Step 1: Download video
     const localPath = await downloadVideoToLocal(videoUrl, projectId);

     // Step 2: Load into Zapcut
     const { addAssetsFromPaths } = useProjectStore.getState();
     await addAssetsFromPaths([localPath]);

     // Step 3: Navigate to editor
     navigate(`/editor/${zapcutProjectId}`);
   };
   ```

**Download to Local Implementation:**
```typescript
const downloadVideoToLocal = async (
  s3Url: string,
  projectId: string
): Promise<string> => {
  // Use Electron's app data directory
  const appDataPath = window.electron.app.getPath('userData');
  const videosDir = path.join(appDataPath, 'generated-videos');

  // Ensure directory exists
  await fs.promises.mkdir(videosDir, { recursive: true });

  // Download file
  const response = await fetch(s3Url);
  const buffer = await response.arrayBuffer();

  // Save locally
  const localPath = path.join(videosDir, `${projectId}.mp4`);
  await fs.promises.writeFile(localPath, Buffer.from(buffer));

  return localPath;
};
```

---

### Screen 9: Zapcut Editor (Integrated)

**Route:** `/editor/:projectId`

**Purpose:** Edit generated video with full Zapcut capabilities

**Layout:** (Existing Zapcut UI)

**Integration Points:**

1. **Pre-populated Assets:**
   ```typescript
   // On editor load for generated video
   useEffect(() => {
     const loadGeneratedAssets = async () => {
       const project = await getAdProject(projectId);

       // Load generated video
       await addAssetsFromPaths([project.local_video_path]);

       // Load product images
       const brand = await getBrand(project.brand_id);
       await addAssetsFromPaths(brand.product_images_local);
     };

     loadGeneratedAssets();
   }, [projectId]);
   ```

2. **Modified Top Bar:**
   ```typescript
   // Add "Back to Brands" button
   <TopBar>
     <BackButton to="/brands">← Back to Brands</BackButton>
     {/* Existing export button */}
     <ExportButton />
   </TopBar>
   ```

3. **Project Linking:**
   ```typescript
   // Link Zapcut project to AdProject
   interface AdProject {
     zapcut_project_id: string; // Links to local Zustand project
   }
   ```

**No other changes needed** - user gets full Zapcut editing capabilities

---

## Component Library

### Core Components

#### 1. GlassCard

```typescript
interface GlassCardProps {
  children: React.ReactNode;
  className?: string;
  padding?: 'sm' | 'md' | 'lg';
}

const GlassCard: React.FC<GlassCardProps> = ({
  children,
  className = '',
  padding = 'md'
}) => {
  const paddingClasses = {
    sm: 'p-4',
    md: 'p-6',
    lg: 'p-8'
  };

  return (
    <div className={`glass-card ${paddingClasses[padding]} ${className}`}>
      {children}
    </div>
  );
};
```

#### 2. GlassInput

```typescript
interface GlassInputProps {
  name: string;
  type?: 'text' | 'email' | 'password' | 'number';
  placeholder?: string;
  value: string;
  onChange: (value: string) => void;
  required?: boolean;
  error?: string;
  icon?: React.ReactNode;
}

const GlassInput: React.FC<GlassInputProps> = ({
  name,
  type = 'text',
  placeholder,
  value,
  onChange,
  required,
  error,
  icon
}) => {
  return (
    <div className="flex flex-col gap-1">
      <div className="relative">
        {icon && (
          <div className="absolute left-3 top-1/2 -translate-y-1/2 text-white/50">
            {icon}
          </div>
        )}
        <input
          type={type}
          name={name}
          placeholder={placeholder}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          required={required}
          className={`glass-input w-full ${icon ? 'pl-10' : ''} ${error ? 'border-red-500' : ''}`}
        />
      </div>
      {error && (
        <span className="text-xs text-red-400">{error}</span>
      )}
    </div>
  );
};
```

#### 3. PrimaryButton

```typescript
interface ButtonProps {
  children: React.ReactNode;
  onClick?: () => void;
  disabled?: boolean;
  loading?: boolean;
  type?: 'button' | 'submit';
  icon?: React.ReactNode;
}

const PrimaryButton: React.FC<ButtonProps> = ({
  children,
  onClick,
  disabled,
  loading,
  type = 'button',
  icon
}) => {
  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled || loading}
      className="btn-primary flex items-center gap-2"
    >
      {loading ? (
        <LoadingSpinner size="sm" />
      ) : icon}
      {children}
    </button>
  );
};
```

#### 4. BrandCard

```typescript
interface BrandCardProps {
  brand: Brand;
  onClick: () => void;
  showNotification?: boolean;
}

const BrandCard: React.FC<BrandCardProps> = ({
  brand,
  onClick,
  showNotification
}) => {
  return (
    <div
      onClick={onClick}
      className="glass-card p-0 cursor-pointer hover:scale-105 transition-transform relative"
    >
      {showNotification && (
        <div className="absolute top-2 right-2 bg-lightning-yellow text-cosmic-dark text-xs px-2 py-1 rounded-full">
          New!
        </div>
      )}

      <div className="aspect-video bg-mid-navy overflow-hidden rounded-t-xl">
        <img
          src={brand.product_images[0]}
          alt={brand.title}
          className="w-full h-full object-cover"
        />
      </div>

      <div className="p-4">
        <h3 className="text-lg font-semibold text-white mb-1">
          {brand.title}
        </h3>
        <p className="text-sm text-white/60 mb-2">
          Created {formatDistanceToNow(new Date(brand.created_at))} ago
        </p>
        <p className="text-sm text-white/40">
          {brand.project_count} {brand.project_count === 1 ? 'project' : 'projects'}
        </p>
      </div>
    </div>
  );
};
```

#### 5. MessageBubble

```typescript
interface MessageBubbleProps {
  message: ChatMessage;
  isUser: boolean;
}

const MessageBubble: React.FC<MessageBubbleProps> = ({ message, isUser }) => {
  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
      {!isUser && (
        <div className="w-8 h-8 rounded-full bg-lightning-yellow flex items-center justify-center mr-2 shrink-0">
          <Sparkles className="w-4 h-4 text-cosmic-dark" />
        </div>
      )}

      <div
        className={`max-w-[70%] p-4 rounded-2xl ${
          isUser
            ? 'bg-white/10 text-white'
            : 'bg-lightning-yellow/10 text-white border border-lightning-yellow/20'
        }`}
      >
        <p className="text-sm whitespace-pre-wrap">{message.content}</p>
        <span className="text-xs text-white/40 mt-2 block">
          {format(new Date(message.timestamp), 'h:mm a')}
        </span>
      </div>

      {isUser && (
        <div className="w-8 h-8 rounded-full bg-light-blue flex items-center justify-center ml-2 shrink-0">
          <User className="w-4 h-4 text-white" />
        </div>
      )}
    </div>
  );
};
```

#### 6. SceneCard

```typescript
interface SceneCardProps {
  scene: Scene;
  sceneNumber: number;
}

const SceneCard: React.FC<SceneCardProps> = ({ scene, sceneNumber }) => {
  const [showPrompt, setShowPrompt] = useState(false);

  return (
    <div className="glass-card mb-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-lg font-semibold text-white">
          Scene {sceneNumber}
        </h3>
        <span className="text-sm text-white/60 bg-white/10 px-3 py-1 rounded-full">
          {scene.duration}s
        </span>
      </div>

      <div className="space-y-3">
        <div>
          <h4 className="text-sm font-medium text-white/80 mb-1 flex items-center gap-2">
            <Film className="w-4 h-4" /> Visual Description
          </h4>
          <p className="text-white/90">{scene.description}</p>
        </div>

        {scene.voiceoverText && (
          <div>
            <h4 className="text-sm font-medium text-white/80 mb-1 flex items-center gap-2">
              <Mic className="w-4 h-4" /> Voiceover
            </h4>
            <p className="text-white/70 italic">"{scene.voiceoverText}"</p>
          </div>
        )}

        <button
          onClick={() => setShowPrompt(!showPrompt)}
          className="text-sm text-light-blue flex items-center gap-1"
        >
          <ChevronDown className={`w-4 h-4 transition-transform ${showPrompt ? 'rotate-180' : ''}`} />
          {showPrompt ? 'Hide' : 'Show'} Sora Prompt
        </button>

        {showPrompt && (
          <div className="bg-cosmic-dark/50 p-3 rounded-lg">
            <p className="text-sm text-white/60 font-mono">
              {scene.visualPrompt}
            </p>
          </div>
        )}
      </div>
    </div>
  );
};
```

#### 7. ProgressBar

```typescript
interface ProgressBarProps {
  value: number; // 0-100
  showPercentage?: boolean;
}

const ProgressBar: React.FC<ProgressBarProps> = ({ value, showPercentage = true }) => {
  return (
    <div className="w-full">
      <div className="h-2 bg-white/10 rounded-full overflow-hidden">
        <div
          className="h-full bg-gradient-to-r from-lightning-yellow to-light-blue transition-all duration-500 ease-out"
          style={{ width: `${value}%` }}
        />
      </div>
      {showPercentage && (
        <p className="text-right text-sm text-white/60 mt-1">{value}%</p>
      )}
    </div>
  );
};
```

---

## State Management

### Auth Store

```typescript
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface User {
  id: string;
  email: string;
  name: string;
  subscription_tier: 'free' | 'starter' | 'pro' | 'agency';
  credits: number;
  free_videos_used: number;
}

interface AuthStore {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;

  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
}

export const useAuthStore = create<AuthStore>()(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      isAuthenticated: false,

      login: async (email, password) => {
        const response = await fetch(`${API_BASE}/api/auth/login`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email, password })
        });

        if (!response.ok) {
          throw new Error('Login failed');
        }

        const data = await response.json();

        set({
          user: data.user,
          token: data.token,
          isAuthenticated: true
        });
      },

      logout: () => {
        set({
          user: null,
          token: null,
          isAuthenticated: false
        });
      },

      refreshUser: async () => {
        const { token } = get();
        if (!token) return;

        const response = await fetch(`${API_BASE}/api/auth/me`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });

        if (response.ok) {
          const user = await response.json();
          set({ user });
        }
      }
    }),
    {
      name: 'zapcut-auth-storage',
      partialize: (state) => ({
        user: state.user,
        token: state.token,
        isAuthenticated: state.isAuthenticated
      })
    }
  )
);
```

### Brand Store

```typescript
import { create } from 'zustand';

interface Brand {
  id: string;
  user_id: string;
  title: string;
  description: string;
  product_images: string[];
  brand_guidelines?: {
    colors: string[];
    tone: string;
  };
  created_at: string;
  project_count: number;
  lora_model?: {
    status: 'none' | 'training' | 'ready' | 'failed';
    preview_image_url?: string;
    user_approved: boolean;
  };
}

interface BrandStore {
  brands: Brand[];
  isLoading: boolean;
  error: string | null;

  fetchBrands: () => Promise<void>;
  createBrand: (data: CreateBrandDTO) => Promise<Brand>;
  getBrandById: (id: string) => Brand | undefined;
  approveLoRA: (brandId: string, approved: boolean) => Promise<void>;
}

export const useBrandStore = create<BrandStore>((set, get) => ({
  brands: [],
  isLoading: false,
  error: null,

  fetchBrands: async () => {
    set({ isLoading: true, error: null });
    try {
      const { token } = useAuthStore.getState();
      const response = await fetch(`${API_BASE}/api/brands`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (!response.ok) throw new Error('Failed to fetch brands');

      const brands = await response.json();
      set({ brands, isLoading: false });
    } catch (error) {
      set({ error: error.message, isLoading: false });
    }
  },

  createBrand: async (data) => {
    const { token } = useAuthStore.getState();

    // Step 1: Upload images
    const formData = new FormData();
    data.productImages.forEach((file) => {
      formData.append('files', file);
    });

    const uploadResponse = await fetch(`${API_BASE}/api/upload`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}` },
      body: formData
    });

    const { urls } = await uploadResponse.json();

    // Step 2: Create brand
    const brandResponse = await fetch(`${API_BASE}/api/brands`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        title: data.title,
        description: data.description,
        product_images: urls,
        brand_guidelines: data.brandGuidelines
      })
    });

    const brand = await brandResponse.json();
    set({ brands: [...get().brands, brand] });
    return brand;
  },

  getBrandById: (id) => {
    return get().brands.find((b) => b.id === id);
  },

  approveLoRA: async (brandId, approved) => {
    const { token } = useAuthStore.getState();
    await fetch(`${API_BASE}/api/brands/${brandId}/lora/approve`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ approved })
    });

    // Update local state
    set({
      brands: get().brands.map((b) =>
        b.id === brandId
          ? { ...b, lora_model: { ...b.lora_model!, user_approved: approved } }
          : b
      )
    });
  }
}));
```

### Ad Project Store

```typescript
import { create } from 'zustand';

interface AdProjectStore {
  currentProject: AdProject | null;
  messages: ChatMessage[];
  script: Script | null;
  generationStatus: GenerationStatus | null;
  isLoading: boolean;

  createProject: (brandId: string) => Promise<AdProject>;
  sendMessage: (projectId: string, content: string) => Promise<void>;
  fetchScript: (projectId: string) => Promise<void>;
  regenerateScript: (projectId: string) => Promise<void>;
  startGeneration: (projectId: string) => Promise<void>;
  fetchGenerationStatus: (projectId: string) => Promise<GenerationStatus>;
}

export const useAdProjectStore = create<AdProjectStore>((set, get) => ({
  currentProject: null,
  messages: [],
  script: null,
  generationStatus: null,
  isLoading: false,

  createProject: async (brandId) => {
    const { token } = useAuthStore.getState();
    const response = await fetch(`${API_BASE}/api/brands/${brandId}/projects`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });

    const project = await response.json();
    set({ currentProject: project, messages: [] });
    return project;
  },

  sendMessage: async (projectId, content) => {
    const userMessage: ChatMessage = {
      id: generateId(),
      role: 'user',
      content,
      timestamp: new Date()
    };

    set({ messages: [...get().messages, userMessage], isLoading: true });

    const { token } = useAuthStore.getState();
    const response = await fetch(`${API_BASE}/api/projects/${projectId}/chat`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ message: content })
    });

    const data = await response.json();

    const assistantMessage: ChatMessage = {
      id: generateId(),
      role: 'assistant',
      content: data.message.content,
      timestamp: new Date()
    };

    set({
      messages: [...get().messages, assistantMessage],
      isLoading: false
    });

    return data;
  },

  fetchScript: async (projectId) => {
    const { token } = useAuthStore.getState();
    const response = await fetch(`${API_BASE}/api/projects/${projectId}/script`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });

    const script = await response.json();
    set({ script });
  },

  regenerateScript: async (projectId) => {
    set({ isLoading: true });
    const { token } = useAuthStore.getState();
    const response = await fetch(`${API_BASE}/api/projects/${projectId}/script/regenerate`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}` }
    });

    const script = await response.json();
    set({ script, isLoading: false });
  },

  startGeneration: async (projectId) => {
    const { token } = useAuthStore.getState();
    await fetch(`${API_BASE}/api/projects/${projectId}/generate-video`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}` }
    });
  },

  fetchGenerationStatus: async (projectId) => {
    const { token } = useAuthStore.getState();
    const response = await fetch(`${API_BASE}/api/projects/${projectId}/generation-status`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });

    const status = await response.json();
    set({ generationStatus: status });
    return status;
  }
}));
```

---

## API Integration

### API Client Setup

```typescript
// lib/api.ts
const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

class APIClient {
  private getHeaders(): HeadersInit {
    const { token } = useAuthStore.getState();
    return {
      'Content-Type': 'application/json',
      ...(token && { 'Authorization': `Bearer ${token}` })
    };
  }

  async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const response = await fetch(`${API_BASE}${endpoint}`, {
      ...options,
      headers: {
        ...this.getHeaders(),
        ...options.headers
      }
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || 'Request failed');
    }

    return response.json();
  }

  async get<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: 'GET' });
  }

  async post<T>(endpoint: string, data?: any): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: JSON.stringify(data)
    });
  }

  async put<T>(endpoint: string, data: any): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'PUT',
      body: JSON.stringify(data)
    });
  }

  async delete<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: 'DELETE' });
  }
}

export const api = new APIClient();
```

### Environment Variables

```bash
# .env
VITE_API_BASE_URL=http://localhost:8000  # Development
# VITE_API_BASE_URL=https://api.zapcut.com  # Production
```

---

## File Structure

```
app/
├── src/
│   ├── components/
│   │   ├── ui/             # Existing shadcn components
│   │   │   ├── button.tsx
│   │   │   ├── card.tsx
│   │   │   ├── dialog.tsx
│   │   │   └── input.tsx
│   │   │
│   │   ├── glass/          # NEW: Glassmorphism components
│   │   │   ├── GlassCard.tsx
│   │   │   ├── GlassInput.tsx
│   │   │   ├── GlassButton.tsx
│   │   │   └── GlassModal.tsx
│   │   │
│   │   ├── auth/           # NEW: Authentication components
│   │   │   ├── LoginForm.tsx
│   │   │   ├── SignupForm.tsx
│   │   │   └── AuthLayout.tsx
│   │   │
│   │   ├── brands/         # NEW: Brand management
│   │   │   ├── BrandCard.tsx
│   │   │   ├── BrandGrid.tsx
│   │   │   ├── CreateBrandModal.tsx
│   │   │   ├── ImageUploader.tsx
│   │   │   └── LoRAPreviewModal.tsx
│   │   │
│   │   ├── chat/           # NEW: Chat interface
│   │   │   ├── ChatLayout.tsx
│   │   │   ├── ChatMessages.tsx
│   │   │   ├── MessageBubble.tsx
│   │   │   ├── ChatInput.tsx
│   │   │   └── TypingIndicator.tsx
│   │   │
│   │   ├── script/         # NEW: Script review
│   │   │   ├── ScriptReviewLayout.tsx
│   │   │   ├── StorylineCard.tsx
│   │   │   ├── SceneCard.tsx
│   │   │   └── ScenesList.tsx
│   │   │
│   │   ├── generation/     # NEW: Video generation
│   │   │   ├── GenerationStatusLayout.tsx
│   │   │   ├── ProgressBar.tsx
│   │   │   ├── ProgressSteps.tsx
│   │   │   ├── AnimatedIcon.tsx
│   │   │   └── GenerationCompleteScreen.tsx
│   │   │
│   │   ├── shared/         # Shared components
│   │   │   ├── Sidebar.tsx
│   │   │   ├── TopBar.tsx
│   │   │   ├── ProgressIndicator.tsx
│   │   │   ├── LoadingSpinner.tsx
│   │   │   └── EmptyState.tsx
│   │   │
│   │   ├── LeftRail.tsx    # Existing
│   │   ├── RightRail.tsx   # Existing
│   │   └── ...             # Other existing components
│   │
│   ├── pages/              # NEW: Page components
│   │   ├── LandingPage.tsx
│   │   ├── LoginPage.tsx
│   │   ├── SignupPage.tsx
│   │   ├── BrandsDashboard.tsx
│   │   ├── ChatPage.tsx
│   │   ├── ScriptReviewPage.tsx
│   │   ├── GenerationStatusPage.tsx
│   │   └── EditorPage.tsx  # Existing App.tsx refactored
│   │
│   ├── store/
│   │   ├── authStore.ts         # NEW: Authentication state
│   │   ├── brandStore.ts        # NEW: Brand management state
│   │   ├── adProjectStore.ts    # NEW: Ad project state
│   │   ├── projectStore.ts      # Existing: Zapcut editor state
│   │   ├── playbackStore.ts     # Existing
│   │   └── uiStore.ts           # Existing
│   │
│   ├── lib/
│   │   ├── api.ts               # NEW: API client
│   │   ├── utils.ts             # Existing utilities
│   │   ├── bindings.ts          # Existing Electron bindings
│   │   └── ...                  # Other existing libs
│   │
│   ├── types/
│   │   ├── index.ts             # Existing editor types
│   │   ├── auth.ts              # NEW: Auth types
│   │   ├── brand.ts             # NEW: Brand types
│   │   └── adProject.ts         # NEW: Ad project types
│   │
│   ├── App.tsx              # Main app with routing
│   ├── main.tsx             # Entry point
│   └── globals.css          # Global styles + glassmorphism
│
├── electron/
│   ├── main.ts              # Existing
│   ├── preload.ts           # Existing + new IPC for downloads
│   └── ...
│
├── public/
├── package.json
├── vite.config.ts
└── tailwind.config.js       # Updated with custom colors
```

---

## Implementation Checklist

### Phase 1: Foundation (Week 1)
- [ ] Set up React Router DOM
- [ ] Create glassmorphism design system (CSS)
- [ ] Build core glass components (Card, Input, Button)
- [ ] Set up Zustand stores (auth, brand, adProject)
- [ ] Create API client utility
- [ ] Set up environment variables

### Phase 2: Authentication (Week 1-2)
- [ ] Build LandingPage component
- [ ] Build LoginPage component
- [ ] Build SignupPage component
- [ ] Implement authStore logic
- [ ] Add protected route wrapper
- [ ] Test auth flow end-to-end

### Phase 3: Brand Management (Week 2-3)
- [ ] Build BrandsDashboard page
- [ ] Build BrandCard component
- [ ] Build CreateBrandModal
- [ ] Build ImageUploader component
- [ ] Implement brandStore logic
- [ ] Test brand creation flow

### Phase 4: Chat Interface (Week 3-4)
- [ ] Build ChatPage layout
- [ ] Build MessageBubble component
- [ ] Build ChatInput component
- [ ] Build TypingIndicator component
- [ ] Implement chat message handling
- [ ] Test 5-question conversation flow

### Phase 5: Script Review (Week 4-5)
- [ ] Build ScriptReviewPage layout
- [ ] Build StorylineCard component
- [ ] Build SceneCard component
- [ ] Build ScenesList component
- [ ] Implement script regeneration
- [ ] Test script approval flow

### Phase 6: Video Generation (Week 5-6)
- [ ] Build GenerationStatusPage
- [ ] Build ProgressBar component
- [ ] Build ProgressSteps component
- [ ] Build AnimatedIcon component
- [ ] Implement polling logic (5s interval)
- [ ] Build GenerationCompleteScreen
- [ ] Test generation status updates

### Phase 7: Editor Integration (Week 6-7)
- [ ] Implement video download to local
- [ ] Update Zapcut editor entry point
- [ ] Add "Back to Brands" button to TopBar
- [ ] Test asset loading from generated video
- [ ] Test full flow: generation → editor

### Phase 8: Pricing & Paywall (Week 7)
- [ ] Build PricingModal component
- [ ] Implement free video counter
- [ ] Add paywall triggers
- [ ] Implement credit/subscription checks
- [ ] Test upgrade flows

### Phase 9: LoRA Preview (Week 7-8)
- [ ] Build LoRAPreviewModal
- [ ] Implement side-by-side comparison
- [ ] Add approval logic
- [ ] Test LoRA notification badge

### Phase 10: Polish & Testing (Week 8-9)
- [ ] Error handling for all API calls
- [ ] Loading states for all async operations
- [ ] Form validation for all inputs
- [ ] Responsive design adjustments
- [ ] Accessibility improvements (ARIA labels, keyboard nav)
- [ ] End-to-end testing
- [ ] Performance optimization

---

**Document Complete**
**Ready for Implementation**
