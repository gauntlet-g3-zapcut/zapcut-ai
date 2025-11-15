# UI/UX Guidelines

## Design Philosophy

### Core Principles

#### 1. Single-Page Agent Experience
**Inspiration**: ChatGPT  
**Principle**: The entire app should feel like conversing with an intelligent assistant, not navigating through complex menus.

- No multi-step wizards
- No navigation bar with 10+ options
- One continuous conversation from login to published video
- Context persists throughout the session

#### 2. Progressive Disclosure
**Principle**: Show only what's needed at each stage.

- Don't overwhelm with all options upfront
- Reveal features as user advances through workflow
- Hide complexity behind intelligent defaults

#### 3. Glass Morphism Aesthetic
**Principle**: Modern, premium, ethereal feel with depth and layers.

- Frosted glass panels with backdrop blur
- Subtle shadows and borders
- Layered interface with depth perception
- Light plays through semi-transparent surfaces

#### 4. Brand Identity
**Primary Colors**:
- ⚡ **Bright Yellow** (`#FFEB3B`, `#FDD835`) - Lightning bolt highlight, CTAs
- 🖱️ **White Cursor** (`#FFFFFF`, `#F5F5F5`) - Backgrounds, text
- **Black** (`#000000`, `#1A1A1A`) - Primary text, strong contrast elements

**Accent Colors**:
- **Gray Scale**: `#E0E0E0`, `#BDBDBD`, `#757575`, `#424242`
- **Success Green**: `#4CAF50`
- **Warning Orange**: `#FF9800`
- **Error Red**: `#F44336`

---

## Visual Design System

### Typography

#### Font Stack
```css
--font-primary: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
--font-display: 'Cal Sans', 'Inter', sans-serif; /* For headings */
--font-mono: 'JetBrains Mono', 'Fira Code', monospace; /* For code/technical */
```

#### Font Sizes
```css
--text-xs: 0.75rem;    /* 12px - Labels, captions */
--text-sm: 0.875rem;   /* 14px - Body, UI elements */
--text-base: 1rem;     /* 16px - Default body */
--text-lg: 1.125rem;   /* 18px - Chat messages */
--text-xl: 1.25rem;    /* 20px - Subheadings */
--text-2xl: 1.5rem;    /* 24px - Section headings */
--text-3xl: 1.875rem;  /* 30px - Page titles */
--text-4xl: 2.25rem;   /* 36px - Hero text */
```

#### Font Weights
```css
--font-normal: 400;
--font-medium: 500;
--font-semibold: 600;
--font-bold: 700;
```

---

### Color Palette

#### Primary Palette
```css
/* Yellow - Lightning bolt accent */
--yellow-bright: #FFEB3B;
--yellow-dark: #FDD835;
--yellow-glow: rgba(255, 235, 59, 0.3);

/* White/Light - Cursor, backgrounds */
--white: #FFFFFF;
--white-soft: #F5F5F5;
--white-glass: rgba(255, 255, 255, 0.1);

/* Black/Dark - Text, contrast */
--black: #000000;
--black-soft: #1A1A1A;
--black-glass: rgba(0, 0, 0, 0.4);
```

#### Gray Scale
```css
--gray-50: #FAFAFA;
--gray-100: #F5F5F5;
--gray-200: #E0E0E0;
--gray-300: #BDBDBD;
--gray-400: #9E9E9E;
--gray-500: #757575;
--gray-600: #616161;
--gray-700: #424242;
--gray-800: #212121;
--gray-900: #121212;
```

#### Semantic Colors
```css
--success: #4CAF50;
--success-light: #81C784;
--success-dark: #388E3C;

--warning: #FF9800;
--warning-light: #FFB74D;
--warning-dark: #F57C00;

--error: #F44336;
--error-light: #E57373;
--error-dark: #D32F2F;

--info: #2196F3;
--info-light: #64B5F6;
--info-dark: #1976D2;
```

---

### Glass Morphism Components

#### Glass Panel
```css
.glass-panel {
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.18);
  border-radius: 16px;
  box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.15);
}
```

#### Glass Card (Elevated)
```css
.glass-card {
  background: rgba(255, 255, 255, 0.15);
  backdrop-filter: blur(30px);
  border: 1px solid rgba(255, 255, 255, 0.25);
  border-radius: 20px;
  box-shadow: 
    0 8px 32px 0 rgba(31, 38, 135, 0.15),
    inset 0 1px 0 0 rgba(255, 255, 255, 0.3);
}
```

#### Glass Button (Primary)
```css
.glass-button-primary {
  background: linear-gradient(135deg, rgba(255, 235, 59, 0.9), rgba(253, 216, 53, 0.9));
  backdrop-filter: blur(10px);
  border: 2px solid rgba(255, 255, 255, 0.4);
  border-radius: 12px;
  box-shadow: 
    0 4px 16px 0 rgba(255, 235, 59, 0.4),
    inset 0 1px 0 0 rgba(255, 255, 255, 0.5);
  color: var(--black);
  font-weight: 600;
  transition: all 0.3s ease;
}

.glass-button-primary:hover {
  transform: translateY(-2px);
  box-shadow: 
    0 6px 24px 0 rgba(255, 235, 59, 0.6),
    inset 0 1px 0 0 rgba(255, 255, 255, 0.6);
}
```

---

## Layout Structure

### Single-Page App Layout
```
┌─────────────────────────────────────────────────────────┐
│  Top Bar (Fixed)                                        │
│  Logo | Project Name                   User Menu        │
├─────────────────────────────────────────────────────────┤
│ Left │         Center Chat Area        │ Right Panel    │
│ Side │                                 │  (Collapsible) │
│ bar  │  ┌─────────────────────────┐   │                │
│      │  │ System: Welcome! ...    │   │  Scenes List   │
│      │  └─────────────────────────┘   │  ─────────     │
│ Pro- │                                 │  Scene 1       │
│ ject │  ┌─────────────────────────┐   │  Scene 2       │
│ List │  │ User: Create ad for ... │   │  Scene 3       │
│      │  └─────────────────────────┘   │  ...           │
│      │                                 │                │
│      │  ┌─────────────────────────┐   │  Video Preview │
│      │  │ System: Great! Now ...  │   │  [Player]      │
│      │  └─────────────────────────┘   │                │
│      │                                 │  Actions       │
│      │  ┌──────────────────────┐      │  Download      │
│      │  │ Input: [Type...]     │      │  Post to X     │
│      │  └──────────────────────┘      │  ...           │
└──────┴─────────────────────────────────┴────────────────┘
```

### Responsive Breakpoints
```css
--breakpoint-mobile: 640px;
--breakpoint-tablet: 768px;
--breakpoint-desktop: 1024px;
--breakpoint-wide: 1280px;
```

**Mobile** (<768px):
- Hide left sidebar (collapse to hamburger menu)
- Full-width chat area
- Right panel becomes bottom sheet

**Tablet** (768px-1024px):
- Left sidebar visible but narrow
- Chat area 60% width
- Right panel 25% width

**Desktop** (1024px+):
- Left sidebar 240px fixed
- Chat area fluid, centered
- Right panel 320px fixed

---

## Component Guidelines

### 1. Chat Messages

#### System Message (AI)
```jsx
<div className="message message-system">
  <div className="avatar">
    <Lightning className="icon-yellow" />
  </div>
  <div className="message-bubble glass-panel">
    <p className="message-text">
      Hi! I'm your Zapcut assistant. Let's create your first AI-generated video ad.
    </p>
  </div>
  <div className="message-time">Just now</div>
</div>
```

**Styling**:
- Avatar: Yellow lightning bolt icon
- Bubble: Glass panel with white text
- Animation: Fade in from bottom + slight scale

#### User Message
```jsx
<div className="message message-user">
  <div className="message-bubble glass-panel-user">
    <p className="message-text">
      Create a modern ad for Luna Coffee
    </p>
  </div>
  <div className="avatar">
    <User className="icon-white" />
  </div>
  <div className="message-time">Just now</div>
</div>
```

**Styling**:
- Avatar: User initials or profile image
- Bubble: Darker glass panel, right-aligned
- Animation: Slide in from right

---

### 2. Input Field

#### Chat Input
```jsx
<div className="chat-input-container glass-panel">
  <textarea 
    className="chat-input"
    placeholder="Describe your video ad..."
    rows={1}
  />
  <button className="send-button glass-button-primary">
    <Send className="icon" />
  </button>
</div>
```

**Behavior**:
- Auto-resize as user types
- Max 5 lines before scrolling
- Enter to send, Shift+Enter for new line
- Send button glows on hover

---

### 3. Progress Indicator

#### Generation Progress
```jsx
<div className="progress-container glass-panel">
  <div className="progress-header">
    <Lightning className="icon-yellow pulse" />
    <h3>Generating your video...</h3>
  </div>
  
  <div className="progress-bar">
    <div className="progress-fill" style={{width: '60%'}} />
  </div>
  
  <div className="progress-steps">
    <div className="step completed">
      <Check className="icon-success" />
      <span>Creative Bible</span>
    </div>
    <div className="step completed">
      <Check className="icon-success" />
      <span>Reference Images</span>
    </div>
    <div className="step active">
      <Loader className="icon-yellow spin" />
      <span>Scene 3 of 5</span>
    </div>
    <div className="step pending">
      <Clock className="icon-gray" />
      <span>Music</span>
    </div>
    <div className="step pending">
      <Clock className="icon-gray" />
      <span>Composition</span>
    </div>
  </div>
  
  <div className="progress-stats">
    <span>Elapsed: 2m 35s</span>
    <span>Est. remaining: 2m 10s</span>
  </div>
</div>
```

**Styling**:
- Glass panel with subtle pulse animation
- Progress bar with yellow gradient fill
- Checkmarks fade in on completion
- Active step has spinning loader

---

### 4. Video Preview

#### Video Player
```jsx
<div className="video-preview-container glass-card">
  <div className="video-player">
    <video 
      src={videoUrl} 
      controls 
      className="video-element"
    />
  </div>
  
  <div className="video-controls">
    <button className="control-button">
      <Play className="icon" />
    </button>
    <div className="timeline">
      <div className="timeline-fill" />
    </div>
    <div className="volume-control">
      <Volume2 className="icon" />
      <input type="range" min="0" max="100" />
    </div>
  </div>
  
  <div className="video-actions">
    <button className="glass-button-primary">
      <Download className="icon" />
      Download MP4
    </button>
    <button className="glass-button-secondary">
      <Share2 className="icon" />
      Post to X
    </button>
  </div>
</div>
```

**Styling**:
- Elevated glass card
- Custom video controls matching glass theme
- Yellow hover states on buttons
- Smooth transitions on all interactions

---

### 5. Scene List (Right Panel)

#### Scene Card
```jsx
<div className="scene-card glass-panel">
  <div className="scene-header">
    <span className="scene-number">Scene 1</span>
    <span className="scene-duration">6s</span>
  </div>
  
  <div className="scene-thumbnail">
    <img src={thumbnailUrl} alt="Scene 1" />
  </div>
  
  <div className="scene-info">
    <h4 className="scene-title">Product Reveal</h4>
    <p className="scene-description">
      Close-up of Luna Coffee bottle...
    </p>
  </div>
  
  <button className="scene-edit-button">
    <Edit3 className="icon" />
    Edit Scene
  </button>
</div>
```

**Styling**:
- Stacked vertically with spacing
- Hover effect: lift + glow
- Active scene: yellow border
- Click to expand/edit

---

## Iconography

### Icon Library: Lucide React
**Why**: Clean, modern, consistent stroke weight, perfect for glass morphism.

### Common Icons
```jsx
import {
  Lightning,      // Brand icon, loading states
  User,           // User avatar
  Send,           // Send message
  Check,          // Completed steps
  Clock,          // Pending steps
  Loader,         // Loading spinner
  Play,           // Video controls
  Pause,
  Volume2,
  Download,       // Download video
  Share2,         // Share/publish
  Edit3,          // Edit scene
  Trash2,         // Delete
  Settings,       // Settings
  ChevronDown,    // Expand/collapse
  X,              // Close/cancel
  AlertCircle,    // Warnings
  AlertTriangle,  // Errors
  Info,           // Information
  Image,          // Image upload
  Film,           // Video
  Music,          // Audio
  Palette,        // Creative Bible
  Sparkles        // AI generation
} from 'lucide-react';
```

---

## Animation Guidelines

### Timing Functions
```css
--ease-out: cubic-bezier(0.16, 1, 0.3, 1);
--ease-in: cubic-bezier(0.7, 0, 0.84, 0);
--ease-in-out: cubic-bezier(0.87, 0, 0.13, 1);
```

### Standard Animations

#### Fade In
```css
@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
```

#### Pulse (Lightning bolt)
```css
@keyframes pulse {
  0%, 100% {
    opacity: 1;
    transform: scale(1);
  }
  50% {
    opacity: 0.7;
    transform: scale(0.95);
  }
}
```

#### Glow (Hover states)
```css
@keyframes glow {
  0%, 100% {
    box-shadow: 0 0 10px var(--yellow-glow);
  }
  50% {
    box-shadow: 0 0 20px var(--yellow-glow);
  }
}
```

---

## Accessibility

### Keyboard Navigation
- Tab order follows visual flow: Left → Center → Right
- Enter to send messages
- Esc to close modals
- Arrow keys to navigate scene list

### Screen Readers
- Semantic HTML: `<main>`, `<aside>`, `<nav>`, `<article>`
- ARIA labels on icon-only buttons
- Live regions for progress updates
- Alt text on all images

### Color Contrast
- Text on glass panels: WCAG AA minimum (4.5:1)
- Yellow CTAs on white: 3:1+ (large text exception)
- Error/warning text: 7:1+ for readability

### Reduced Motion
```css
@media (prefers-reduced-motion: reduce) {
  * {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

---

## Micro-Interactions

### Button Press
- Scale down to 0.95 on press
- Bounce back on release
- Ripple effect from click point

### Card Hover
- Lift 4px with shadow
- Border glow (yellow for active, white for neutral)
- Smooth 300ms transition

### Input Focus
- Yellow ring (2px)
- Subtle scale up (1.02)
- Placeholder fades out

### Loading States
- Skeleton screens for content loading
- Spinner for short operations (<5s)
- Progress bar for long operations (>5s)

---

## Error States

### Error Message
```jsx
<div className="error-message glass-panel-error">
  <AlertCircle className="icon-error" />
  <div className="error-content">
    <h4 className="error-title">Generation Failed</h4>
    <p className="error-description">
      Scene 3 couldn't be generated. We're retrying...
    </p>
  </div>
  <button className="error-action">Retry Now</button>
</div>
```

**Styling**:
- Red-tinted glass panel
- Error icon pulsing
- Clear action button

---

## Empty States

### No Projects Yet
```jsx
<div className="empty-state">
  <Lightning className="icon-yellow-large" />
  <h3>No projects yet</h3>
  <p>Create your first video ad to get started</p>
  <button className="glass-button-primary">
    Create Project
  </button>
</div>
```

**Styling**:
- Centered content
- Large icon (64px)
- Inviting CTA

---

**Last Updated**: November 15, 2025  
**Status**: Active  
**Next Review**: December 1, 2025

