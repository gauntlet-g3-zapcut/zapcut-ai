# Story 5.5 Validation Guide: Product Image Overlays

## 30-Second Quick Test
1. Create brand with product_image_1_url and product_image_2_url
2. Generate campaign video
3. Download final video
4. Play video and verify:
   - Product 1 appears at ~5 seconds (bottom-right, 200px wide)
   - Product 2 appears at ~15 seconds (bottom-right, 200px wide)
   - Images disappear after 3 seconds

## Automated Tests
```python
# Test add_product_overlays function
import tempfile
from app.tasks.video_generation import add_product_overlays

with tempfile.TemporaryDirectory() as temp_dir:
    input_video = "test_input.mp4"
    output_video = "test_output.mp4"
    product_images = [
        "https://example.com/product1.jpg",
        "https://example.com/product2.jpg"
    ]

    add_product_overlays(input_video, output_video, product_images, temp_dir)

    # Verify output video exists
    assert os.path.exists(output_video)

    # Check video properties with ffprobe
    # Should have overlays encoded
```

## Manual Validation Steps

### Test Product Overlay Display
1. **Create Brand with Product Images:**
   ```bash
   curl -X POST http://localhost:8000/api/brands/ \
     -F "title=Test Brand" \
     -F "description=Test Description" \
     -F "product_image_1=@/path/to/product1.jpg" \
     -F "product_image_2=@/path/to/product2.jpg"
   ```

2. **Generate Campaign:**
   - Trigger campaign generation
   - Wait for completion

3. **Download and Inspect Video:**
   ```bash
   wget {final_video_url} -O final_video.mp4

   # Play with timestamp display
   ffplay -vf "drawtext=text='%{pts\:hms}':fontsize=30:x=10:y=10" final_video.mp4
   ```

4. **Verify Overlays:**
   - At 5.0s: Product 1 should appear bottom-right
   - At 8.0s: Product 1 should disappear
   - At 15.0s: Product 2 should appear bottom-right
   - At 18.0s: Product 2 should disappear

### Test FFmpeg Filter
1. **Manual FFmpeg Command:**
   ```bash
   # With both products
   ffmpeg -i input.mp4 \
     -i product1.png -i product2.png \
     -filter_complex "[1:v]scale=200:-1[ovr1]; \
       [0:v][ovr1]overlay=W-w-20:H-h-20:enable='between(t,5,8)'[v1]; \
       [2:v]scale=200:-1[ovr2]; \
       [v1][ovr2]overlay=W-w-20:H-h-20:enable='between(t,15,18)'[v2]" \
     -map "[v2]" -map 0:a \
     -c:v libx264 -preset medium -crf 23 -c:a copy \
     output.mp4
   ```

2. **Verify:**
   - Video encodes successfully
   - Overlays appear at correct times
   - Images scaled to 200px width
   - Aspect ratio preserved

### Test Edge Cases

#### No Product Images
```python
product_images = None
# Expected: Video created without overlays (normal processing)
```

#### One Product Image
```python
product_images = ["https://example.com/product1.jpg"]
# Expected: Only product 1 overlay at 5-8s
# Expected: No product 2 overlay
```

#### Invalid Image URL
```python
product_images = ["https://invalid-url.com/404.jpg"]
# Expected: Error caught gracefully
# Expected: Video created without that overlay
```

#### Large Image Files
```python
# Test with 5MB+ images
# Expected: Images downloaded and scaled correctly
# Expected: Encoding completes (may be slower)
```

#### Different Image Formats
```python
# Test with: JPG, PNG, WEBP, GIF
# Expected: All formats handled by FFmpeg
```

### Test Positioning and Scaling
1. **Verify Bottom-Right Position:**
   - Overlay formula: `W-w-20:H-h-20`
   - W = video width, w = overlay width
   - H = video height, h = overlay height
   - 20px padding from edges

2. **Verify 200px Width:**
   - Scale formula: `scale=200:-1`
   - Width = 200px
   - Height = auto (maintains aspect ratio)

3. **Test Different Video Resolutions:**
   - 1080p (1920x1080)
   - 720p (1280x720)
   - 4K (3840x2160)
   - Expected: Overlays positioned correctly relative to video size

## Performance Testing
1. **Time Overlay Processing:**
   ```bash
   time ffmpeg ... # Run overlay command
   ```
   - Expected: <10 seconds for 30-second video
   - Expected: Proportional to video length

2. **Check File Size:**
   ```bash
   ls -lh output_with_overlays.mp4
   ```
   - Expected: Similar size to input (minimal increase)

## Acceptance Criteria Checklist
- [x] Product image 1 appears at 5s for 3 seconds
- [x] Product image 2 appears at 15s for 3 seconds
- [x] Images scaled to 200px width, positioned bottom-right
- [x] Images maintain aspect ratio
- [x] Missing product images handled gracefully
- [x] FFmpeg command builds correctly
- [x] Video re-encodes with H.264 codec
- [x] Audio stream preserved

## Rollback Plan
```bash
# Revert code changes
git checkout HEAD~1 -- backend/app/tasks/video_generation.py

# Videos generated before rollback still have overlays
# Videos generated after rollback won't have overlays

# No database changes needed
```

## Files Modified
- `backend/app/tasks/video_generation.py`
  - Added `add_product_overlays()` function
  - Updated `compose_video()` to accept product_images parameter
  - Extract product images from brand object
  - Call add_product_overlays after music mixing

## FFmpeg Technical Details

### Overlay Filter Syntax
```
overlay=x:y:enable='between(t,start,end)'
```
- `x=W-w-20`: X position (20px from right edge)
- `y=H-h-20`: Y position (20px from bottom edge)
- `enable='between(t,5,8)'`: Show overlay from 5s to 8s

### Filter Complex Flow
```
[1:v]scale=200:-1[ovr1]              # Scale product 1 to 200px
[0:v][ovr1]overlay=...[v1]           # Overlay on video
[2:v]scale=200:-1[ovr2]              # Scale product 2 to 200px
[v1][ovr2]overlay=...[v2]            # Overlay on previous result
```

## Known Limitations
- Fixed timestamps (5s and 15s) - not configurable per brand
- Fixed size (200px) - not configurable
- Fixed position (bottom-right) - not configurable
- Max 2 products - additional products ignored
- Image downloads must succeed (no retry logic)
- Re-encodes video (slower than stream copy)

## Future Enhancements
- Make timestamps configurable in creative bible
- Make size/position configurable
- Support more than 2 products
- Add fade in/out transitions
- Add drop shadow or border effects
- Support animated overlays (GIFs)
