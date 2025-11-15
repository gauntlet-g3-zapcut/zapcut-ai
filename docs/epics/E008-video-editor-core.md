# Epic E008: Video Editor Core

## Overview
Build core video editing functionality within Electron desktop application, including canvas-based preview, video playback engine, audio management, and clip manipulation on timeline.

## Business Value
- Enables manual video editing workflows
- Provides professional-grade editing capabilities
- Differentiates from web-only competitors
- Supports advanced users who need fine control
- Bridges gap between AI generation and manual editing

## Success Criteria
- [ ] Electron app launches on macOS/Windows/Linux
- [ ] Video files can be imported (drag-and-drop, file picker)
- [ ] Canvas preview displays video at correct resolution
- [ ] Playback works smoothly at 30fps (no dropped frames)
- [ ] Audio synchronized with video (zero drift)
- [ ] Multiple video/audio tracks supported
- [ ] Clips can be trimmed, split, moved on timeline
- [ ] Export to MP4 with custom settings

## Dependencies
- Electron framework setup
- FFmpeg binaries (bundled with app)
- React + TypeScript frontend
- Zustand state management
- Canvas rendering engine

## Priority
**P0 - Already Implemented** (Documentation/Maintenance)

## Estimated Effort
**Already Complete** (30+ days of prior work)

## Related Stories
- S054: Electron Main Process Setup
- S055: Video Ingestion & Metadata Extraction
- S056: Canvas Video Renderer
- S057: VideoPoolManager (Preloading)
- S058: AudioManager (Web Audio API)
- S059: Timeline Playback Synchronization
- S060: Clip Manipulation (Trim, Split, Move)
- S061: Export Pipeline

## Architecture

### Components

**1. Electron Main Process** (`electron/main.ts`)
- Application lifecycle management
- IPC handlers for video operations
- FFmpeg integration
- File system operations
- Window management

**2. Canvas Rendering System**
- `CanvasVideoRenderer.ts`: Core video frame rendering
- `CanvasCompositor.ts`: Composite multiple layers
- `CanvasEffects.ts`: Apply real-time effects
- Hardware-accelerated where possible

**3. Media Management**
- `VideoPoolManager.ts`: Preload and cache video elements
- `AudioManager.ts`: Web Audio API for precise sync
- Metadata extraction via FFmpeg

**4. State Management** (Zustand)
- `projectStore.ts`: Project, assets, timeline state
- `playbackStore.ts`: Playback position, playing state
- `uiStore.ts`: UI panels, modals, selections

## Key Technical Decisions

### Why Electron?
- Cross-platform desktop app (single codebase)
- Access to native APIs (file system, FFmpeg)
- Better performance than web for video processing
- Professional feel (menubar, native windows)

### Why Canvas over `<video>`?
- Frame-perfect control for effects/transitions
- Composite multiple videos simultaneously
- Apply real-time filters and transformations
- Export requires frame access anyway

### Video Preloading Strategy
```typescript
class VideoPoolManager {
  private pool: Map<string, HTMLVideoElement> = new Map();
  
  preload(assetId: string, url: string) {
    const video = document.createElement('video');
    video.src = url;
    video.preload = 'auto';
    video.load();
    this.pool.set(assetId, video);
  }
  
  get(assetId: string): HTMLVideoElement | null {
    return this.pool.get(assetId) || null;
  }
}
```

### Audio Synchronization
```typescript
class AudioManager {
  private context: AudioContext;
  private sources: Map<string, AudioBufferSourceNode> = new Map();
  
  async playAt(assetId: string, startTime: number) {
    const source = this.context.createBufferSource();
    source.buffer = await this.getAudioBuffer(assetId);
    source.connect(this.context.destination);
    source.start(this.context.currentTime, startTime);
    this.sources.set(assetId, source);
  }
  
  stop(assetId: string) {
    const source = this.sources.get(assetId);
    if (source) {
      source.stop();
      this.sources.delete(assetId);
    }
  }
}
```

### Canvas Compositor
```typescript
class CanvasCompositor {
  private canvas: HTMLCanvasElement;
  private ctx: CanvasRenderingContext2D;
  
  render(frame: number) {
    // Clear canvas
    this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
    
    // Get all clips at current frame
    const clips = this.getClipsAtFrame(frame);
    
    // Render each clip in layer order
    clips.forEach(clip => {
      const video = this.videoPool.get(clip.assetId);
      if (!video) return;
      
      // Calculate source time
      const clipTime = (frame - clip.startFrame) / 30;  // 30fps
      video.currentTime = clipTime;
      
      // Apply transforms
      this.ctx.save();
      this.ctx.globalAlpha = clip.opacity;
      this.ctx.translate(clip.x, clip.y);
      this.ctx.scale(clip.scaleX, clip.scaleY);
      this.ctx.rotate(clip.rotation);
      
      // Draw video frame
      this.ctx.drawImage(
        video,
        0, 0,
        clip.width, clip.height
      );
      
      // Apply effects
      this.applyEffects(clip.effects);
      
      this.ctx.restore();
    });
  }
}
```

## Performance Optimization

### Frame Dropping Prevention
- Maintain 60fps rendering loop (RAF)
- Seek video elements ahead of playhead
- Use Web Workers for heavy computations
- GPU acceleration via WebGL/Canvas

### Memory Management
- Limit video pool size (5-10 concurrent videos)
- Unload videos not visible in current timeline view
- Use OffscreenCanvas for background processing
- Clear audio buffers after playback

## Export Pipeline

```typescript
async function exportVideo(
  timeline: Timeline,
  outputPath: string,
  options: ExportOptions
) {
  // 1. Render all frames to images
  const frames: string[] = [];
  for (let frame = 0; frame < timeline.totalFrames; frame++) {
    const blob = await compositor.renderFrame(frame);
    const framePath = await saveFrameToTemp(blob, frame);
    frames.push(framePath);
  }
  
  // 2. Use FFmpeg to create video
  await ffmpeg.exec([
    '-framerate', '30',
    '-i', 'frame_%04d.png',
    '-i', 'audio.mp3',
    '-c:v', 'libx264',
    '-preset', options.preset,
    '-crf', options.quality.toString(),
    '-c:a', 'aac',
    '-b:a', '192k',
    outputPath
  ]);
  
  // 3. Cleanup temp files
  await cleanupFrames(frames);
}
```

## Existing Implementation Status

✅ **Complete**:
- Electron app setup
- Video ingestion & metadata
- Canvas rendering
- Basic playback
- Audio synchronization
- Timeline UI
- Export to MP4

🚧 **In Progress**:
- Effects system (partially complete)
- Transitions (basic crossfades only)
- Advanced text overlays

📋 **Planned**:
- Real-time collaboration
- Cloud project sync
- Plugin system

## Known Issues
- High memory usage with 4K videos
- Some audio codecs not supported
- Export can be slow for long videos (no hardware encoding yet)

---
**Created**: 2025-11-15  
**Status**: Implemented  
**Owner**: Desktop Team
