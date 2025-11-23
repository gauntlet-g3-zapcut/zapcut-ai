# Epic 6: Editor Integration & Final Export

**Status:** Not Started
**Priority:** P0 (MVP)
**Estimated Effort:** 2 weeks
**Dependencies:** Epic 1-5

---

## Epic Overview

### Value Proposition
Users can seamlessly open AI-generated videos in the existing Zapcut editor for advanced editing and export final videos with professional quality.

### Success Criteria
- [ ] Generated video loads into Zapcut editor automatically
- [ ] Video appears on timeline ready for editing
- [ ] Product images available in asset library
- [ ] Audio tracks separated and editable
- [ ] User can make edits using full Zapcut capabilities
- [ ] User can export final video in multiple formats
- [ ] "Back to Brands" navigation functional
- [ ] Complete round-trip workflow works

### Demo Scenario
1. User clicks "Open in Editor" from completion screen (Epic 5)
2. Video downloads to local directory
3. Zapcut editor launches with video loaded
4. Video on timeline, audio tracks visible, product images in library
5. User makes edits (trim, add text, adjust audio)
6. User exports video as MP4
7. User clicks "Back to Brands" → Returns to dashboard

---

## User Stories

### Story 6.1: Download Generated Video to Local
**As a** user
**I want** the generated video downloaded to my computer
**So that** I can edit it in the local Zapcut editor

**Acceptance Criteria:**
- [ ] Click "Open in Editor" triggers download
- [ ] Video saved to: `~/Library/Application Support/Zapcut/generated-videos/{projectId}.mp4`
- [ ] Download progress indicator shown
- [ ] Download completes before editor opens
- [ ] Downloaded file is verified (not corrupted)

**Frontend:**
```typescript
const openInEditor = async () => {
  // Download video from S3
  const localPath = await downloadVideoToLocal(
    videoUrl,
    projectId
  )

  // Load into Zapcut
  await loadVideoInEditor(localPath)

  // Navigate to editor
  navigate(`/editor/${zapcutProjectId}`)
}

const downloadVideoToLocal = async (s3Url, projectId) => {
  const appDataPath = window.electron.app.getPath('userData')
  const videosDir = path.join(appDataPath, 'generated-videos')

  await fs.promises.mkdir(videosDir, { recursive: true })

  const response = await fetch(s3Url)
  const buffer = await response.arrayBuffer()

  const localPath = path.join(videosDir, `${projectId}.mp4`)
  await fs.promises.writeFile(localPath, Buffer.from(buffer))

  return localPath
}
```

**Backend:**
```python
# Return signed S3 URL for download
GET /api/projects/:projectId/video
Response: { url: "https://s3.amazonaws.com/..." }
```

**Tasks:**
- [ ] Implement download logic in Electron
- [ ] Create generated-videos directory
- [ ] Add download progress UI
- [ ] Test file download and verification

---

### Story 6.2: Load Video into Zapcut Editor
**As a** developer
**I want** to load the generated video into existing Zapcut editor
**So that** users can edit with full capabilities

**Acceptance Criteria:**
- [ ] Video loaded as asset using existing `addAssetsFromPaths` API
- [ ] Video automatically added to timeline
- [ ] Audio tracks separated and visible
- [ ] Zapcut project linked to AdProject via `zapcutProjectId`

**Frontend:**
```typescript
const loadVideoInEditor = async (localPath) => {
  const { addAssetsFromPaths } = useProjectStore.getState()

  // Add video as asset
  await addAssetsFromPaths([localPath])

  // Video appears in library and timeline
  // Existing Zapcut logic handles this
}

// Link projects
const linkProjects = async (adProjectId, zapcutProjectId) => {
  await fetch(`/api/projects/${adProjectId}/link-zapcut`, {
    method: 'POST',
    body: JSON.stringify({ zapcutProjectId })
  })
}
```

**Backend:**
```python
POST /api/projects/:projectId/link-zapcut
Body: { zapcutProjectId: string }

UPDATE ad_projects
SET zapcut_project_id = ?
WHERE id = ?;
```

**Database:**
```sql
-- Already exists in ad_projects table
-- zapcut_project_id VARCHAR(255)
```

**Tasks:**
- [ ] Test addAssetsFromPaths with generated video
- [ ] Implement project linking
- [ ] Test video loads on timeline
- [ ] Test audio tracks visible

---

### Story 6.3: Load Product Images into Asset Library
**As a** user
**I want** brand product images available in the editor
**So that** I can use them in edits

**Acceptance Criteria:**
- [ ] Product images downloaded alongside video
- [ ] Images loaded into Zapcut asset library
- [ ] Images visible in library panel
- [ ] Images draggable to timeline

**Frontend:**
```typescript
const loadBrandAssets = async (brandId) => {
  const brand = await getBrand(brandId)

  // Download product images
  const localImagePaths = await downloadProductImages(brand.product_images)

  // Load into Zapcut
  await addAssetsFromPaths(localImagePaths)
}
```

**Tasks:**
- [ ] Download product images
- [ ] Load into asset library
- [ ] Test images appear in library

---

### Story 6.4: "Back to Brands" Navigation
**As a** user
**I want** to return to brands dashboard from editor
**So that** I can start a new project

**Acceptance Criteria:**
- [ ] "Back to Brands" button in TopBar
- [ ] Click navigates to /brands
- [ ] Unsaved changes prompt confirmation dialog
- [ ] Navigation preserves editor state (Zustand persist)

**Frontend:**
```typescript
// Update TopBar.tsx
<TopBar>
  <BackButton onClick={() => navigate('/brands')}>
    ← Back to Brands
  </BackButton>

  {/* Existing export button */}
  <ExportButton />
</TopBar>

// Confirmation if unsaved
const handleBack = () => {
  if (hasUnsavedChanges) {
    showConfirmDialog({
      title: 'Unsaved Changes',
      message: 'You have unsaved changes. Continue?',
      onConfirm: () => navigate('/brands')
    })
  } else {
    navigate('/brands')
  }
}
```

**Tasks:**
- [ ] Add "Back to Brands" button to TopBar
- [ ] Implement confirmation dialog
- [ ] Test navigation works
- [ ] Test state preservation

---

### Story 6.5: Video Export
**As a** user
**I want** to export my edited video
**So that** I can use it for my ads

**Acceptance Criteria:**
- [ ] Existing Zapcut export functionality works
- [ ] Can export as MP4 (H.264)
- [ ] Can select resolution (720p, 1080p)
- [ ] Can select quality settings
- [ ] Export progress shown
- [ ] Export saves to user-selected location

**Frontend:**
```typescript
// Existing Zapcut export logic
// No changes needed - already functional

// Export settings
{
  format: 'mp4',
  codec: 'h264',
  resolution: '1920x1080',
  framerate: 30,
  quality: 'high'
}
```

**Tasks:**
- [ ] Test export with generated video
- [ ] Verify export quality
- [ ] Test multiple formats

---

### Story 6.6: Round-Trip Workflow
**As a** user
**I want** a seamless workflow from ad creation to final export
**So that** I can efficiently create and refine videos

**Acceptance Criteria:**
- [ ] Complete flow: Auth → Brand → Chat → Script → Generation → Editor → Export
- [ ] Can return to dashboard from editor and start new project
- [ ] Can edit existing projects
- [ ] All data persists correctly

**End-to-End Test:**
1. Sign up
2. Create brand
3. Start chat
4. Generate script
5. Generate video
6. Open in editor
7. Make edits
8. Export video
9. Return to dashboard
10. Create second video

**Tasks:**
- [ ] Test complete workflow
- [ ] Fix any integration issues
- [ ] Verify data persistence

---

### Story 6.7: Download Final Video (Alternative to Editor)
**As a** user
**I want** to download the generated video without editing
**So that** I can use it immediately

**Acceptance Criteria:**
- [ ] "Download Video" button on completion screen
- [ ] Downloads MP4 file
- [ ] File named: `{brandName}-ad-{timestamp}.mp4`
- [ ] Downloaded file plays correctly

**Frontend:**
```typescript
const downloadVideo = async () => {
  const response = await fetch(videoUrl)
  const blob = await response.blob()
  const url = window.URL.createObjectURL(blob)

  const a = document.createElement('a')
  a.href = url
  a.download = `${brandName}-ad-${Date.now()}.mp4`
  a.click()
}
```

**Tasks:**
- [ ] Implement download button
- [ ] Test file download
- [ ] Test file plays correctly

---

## Database Schema

```sql
-- No new tables needed
-- Use existing zapcut_project_id in ad_projects
```

---

## API Endpoints

```
GET /api/projects/:projectId/video  -- Get video URL for download
POST /api/projects/:projectId/link-zapcut  -- Link to Zapcut project
```

---

## Frontend Routes

```
/editor/:projectId → Existing Zapcut EditorPage (with modifications)
```

---

## Testing Strategy

### Integration Tests
- Download video to local directory
- Load video into Zapcut editor
- Load product images into library
- Navigation from editor to dashboard
- Complete round-trip workflow

### Manual QA
- Video quality verification
- Audio sync verification
- Export format testing
- Cross-platform testing (macOS, Windows)

---

## Definition of Done

- [ ] All user stories completed
- [ ] Generated videos load correctly in Zapcut
- [ ] Product images available in editor
- [ ] "Back to Brands" navigation works
- [ ] Export functionality verified
- [ ] Download video works
- [ ] Complete round-trip workflow tested
- [ ] Code deployed to staging
- [ ] Demo scenario executable

---

## Dependencies

**External:**
- Existing Zapcut editor codebase
- Electron file system APIs

**Internal:**
- Epic 5 (need generated video)
- Existing Zapcut editor (use as-is)

---

## Risks & Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| Zapcut API incompatible | High | Review existing code early, plan adapters if needed |
| Large file downloads slow | Medium | Show progress, allow background download |
| Editor state conflicts | Medium | Clear separation between ad pipeline and editor state |

---

## References

- **PRD:** Section 3.6 (Video Editor Integration)
- **Technical Architecture:** Section 8 (Video Asset Loading)
- **UI Spec:** Screen 11 (Zapcut Editor)

---

## Notes

- Leverage existing Zapcut editor capabilities
- Minimal modifications to editor code
- Focus on seamless data flow from pipeline to editor
- Round-trip workflow is key success metric
