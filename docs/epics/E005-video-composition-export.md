# Epic E005: Video Composition & Export

## Overview
Implement FFmpeg-based video composition pipeline that stitches generated scenes, adds audio, applies text overlays, and exports professional-quality MP4 files optimized for social media.

## Business Value
- Produces final deliverable (video file)
- Ensures professional quality output (1080p, 30fps)
- Optimizes file size for fast downloads/uploads
- Adds brand elements (text overlays, logos)
- Supports multiple export formats/aspect ratios

## Success Criteria
- [ ] All 5 scenes stitched with smooth 0.5s crossfades
- [ ] Audio synced properly with zero drift
- [ ] Text overlays appear at correct timestamps
- [ ] Output: H.264, 1080p, 30fps, <50MB
- [ ] Composition completes in <45 seconds
- [ ] Files uploaded to S3 with public CDN URLs
- [ ] Thumbnail generated for preview
- [ ] Support for 16:9, 9:16, 1:1 aspect ratios

## Dependencies
- Multi-agent video generation (E004)
- S3 storage infrastructure
- FFmpeg binary installed on workers
- Generated scenes and music from APIs

## Priority
**P0 - MVP Critical**

## Estimated Effort
**5-7 days** (2 backend engineers)

## Related Stories
- S029: FFmpeg Scene Stitching
- S030: Audio Mixing & Synchronization
- S031: Text Overlay Rendering
- S032: Video Encoding & Optimization
- S033: Thumbnail Generation
- S034: S3 Upload & CDN Distribution
- S035: Multiple Aspect Ratio Support

## Technical Implementation

### FFmpeg Pipeline
```bash
# 1. Stitch scenes with crossfades
ffmpeg -i scene1.mp4 -i scene2.mp4 -i scene3.mp4 -i scene4.mp4 -i scene5.mp4 \
  -filter_complex "\
    [0:v]setpts=PTS-STARTPTS[v0]; \
    [1:v]setpts=PTS-STARTPTS[v1]; \
    [v0][v1]xfade=transition=fade:duration=0.5:offset=5.5[v01]; \
    [v01][2:v]xfade=transition=fade:duration=0.5:offset=11.5[v012]; \
    [v012][3:v]xfade=transition=fade:duration=0.5:offset=17.5[v0123]; \
    [v0123][4:v]xfade=transition=fade:duration=0.5:offset=23.5[vout]" \
  -map "[vout]" intermediate.mp4

# 2. Add audio
ffmpeg -i intermediate.mp4 -i music.mp3 \
  -c:v copy -c:a aac -b:a 192k -shortest final_no_text.mp4

# 3. Add text overlays
ffmpeg -i final_no_text.mp4 \
  -vf "drawtext=text='Luna Coffee':fontsize=48:fontcolor=white:x=(w-text_w)/2:y=100:enable='between(t,24,30)', \
       drawtext=text='Your Morning Ritual':fontsize=32:fontcolor=white:x=(w-text_w)/2:y=160:enable='between(t,24,30)', \
       drawtext=text='Learn More':fontsize=36:fontcolor=white:x=(w-text_w)/2:y=h-150:enable='between(t,27,30)'" \
  -c:a copy final.mp4

# 4. Generate thumbnail
ffmpeg -i final.mp4 -ss 00:00:15 -vframes 1 -vf scale=1280:720 thumbnail.jpg
```

### Encoding Settings
```python
VIDEO_SETTINGS = {
    'codec': 'libx264',
    'preset': 'medium',  # Balance speed vs file size
    'crf': 23,           # Quality (18-28, lower = better)
    'pixel_format': 'yuv420p',
    'profile': 'high',
    'level': '4.0',
    'max_bitrate': '5M',
    'bufsize': '10M',
    'fps': 30
}

AUDIO_SETTINGS = {
    'codec': 'aac',
    'bitrate': '192k',
    'sample_rate': 48000,
    'channels': 2
}
```

### Text Overlay Configuration
```python
TEXT_OVERLAYS = {
    'product_name': {
        'text': project.product_name,
        'fontsize': 48,
        'fontcolor': 'white',
        'position': 'top_center',
        'y_offset': 100,
        'start_time': 24,  # seconds
        'end_time': 30,
        'fade_in': 0.5,
        'fade_out': 0.5
    },
    'tagline': {
        'text': 'Your Morning Ritual',
        'fontsize': 32,
        'fontcolor': 'white',
        'position': 'top_center',
        'y_offset': 160,
        'start_time': 24,
        'end_time': 30
    },
    'cta': {
        'text': 'Learn More',
        'fontsize': 36,
        'fontcolor': 'white',
        'position': 'bottom_center',
        'y_offset': 150,
        'start_time': 27,
        'end_time': 30
    }
}
```

### Aspect Ratio Support
```python
ASPECT_RATIOS = {
    '16:9': {
        'width': 1920,
        'height': 1080,
        'platforms': ['YouTube', 'X/Twitter', 'LinkedIn', 'Desktop']
    },
    '9:16': {
        'width': 1080,
        'height': 1920,
        'platforms': ['TikTok', 'Instagram Stories', 'Reels']
    },
    '1:1': {
        'width': 1080,
        'height': 1080,
        'platforms': ['Instagram Feed', 'LinkedIn', 'Facebook']
    }
}

def resize_for_aspect_ratio(input_video, aspect_ratio):
    target = ASPECT_RATIOS[aspect_ratio]
    return ffmpeg.input(input_video).filter(
        'scale', 
        f"{target['width']}:{target['height']}", 
        force_original_aspect_ratio='decrease'
    ).filter('pad', target['width'], target['height'], '(ow-iw)/2', '(oh-ih)/2')
```

### S3 Upload Strategy
```python
async def upload_to_s3(local_path, ad_id, file_type):
    """Upload file to S3 with metadata and return CDN URL"""
    s3_key = f"ads/{ad_id}/{file_type}/{uuid.uuid4()}.mp4"
    
    # Upload with metadata
    s3_client.upload_file(
        local_path,
        bucket_name='zapcut-assets',
        s3_key=s3_key,
        ExtraArgs={
            'ContentType': 'video/mp4',
            'CacheControl': 'max-age=31536000',  # 1 year
            'Metadata': {
                'ad_id': ad_id,
                'generated_at': datetime.utcnow().isoformat()
            }
        }
    )
    
    # Return CloudFront URL
    cdn_url = f"https://cdn.zapcut.video/{s3_key}"
    return cdn_url
```

## Performance Optimization
- Use hardware acceleration where available (NVENC, Quick Sync)
- Process scenes in parallel before stitching
- Cache intermediate outputs
- Stream uploads to S3 (don't wait for full encoding)
- Generate thumbnails during encoding (single pass)

## Quality Checks
- [ ] Audio sync verification (compare timestamps)
- [ ] Visual quality spot check (no artifacts)
- [ ] File size validation (<50MB for 30s)
- [ ] Text readability check
- [ ] Aspect ratio correctness

## Error Handling
- Retry failed FFmpeg commands (3 attempts)
- Validate output file exists and is valid video
- Check file size is reasonable
- Verify audio track exists
- Fallback to no-text version if overlay fails

## Success Metrics
- Composition success rate: >95%
- Average composition time: <45 seconds
- File size: 30-45MB for 30s video
- Audio sync errors: 0%
- CDN delivery speed: <2 seconds to first byte

---
**Created**: 2025-11-15  
**Status**: Draft  
**Owner**: Backend Media Team
