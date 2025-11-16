# Story 5.6 Validation Guide: Enhanced FFmpeg Video Composition

## 30-Second Quick Test
1. Generate campaign with voiceovers and music
2. Download final video
3. Play and verify:
   - Crossfade transitions between scenes (not hard cuts)
   - Voiceover audible at full volume
   - Music audible in background at lower volume (~30%)
   - Professional quality: 1080p, 30fps, smooth playback

## Automated Tests
```bash
# Test video properties
ffprobe final_video.mp4

# Expected output:
# - Video: h264, yuv420p, 1920x1080, 30 fps
# - Audio: aac, 192 kb/s
# - Duration: ~30 seconds

# Test for crossfades (manual inspection)
ffplay final_video.mp4
# Look for smooth fades at ~5s, ~11s, ~17s, ~23s
```

## Manual Validation Steps

### Test Crossfade Transitions
1. **Generate Video:**
   - Create campaign with 5 scenes
   - Wait for completion

2. **Inspect Transitions:**
   ```bash
   # Play with frame-by-frame control
   ffplay -vf "drawtext=text='%{pts\:hms}':x=10:y=10:fontsize=30" final_video.mp4
   ```

3. **Verify Crossfades:**
   - Scene 1 → 2: Fade at ~5 seconds (1-second crossfade)
   - Scene 2 → 3: Fade at ~11 seconds
   - Scene 3 → 4: Fade at ~17 seconds
   - Scene 4 → 5: Fade at ~23 seconds
   - Smooth blend, not abrupt cut

### Test Audio Mixing
1. **Extract Audio:**
   ```bash
   ffmpeg -i final_video.mp4 -vn -acodec copy audio.aac
   ```

2. **Play and Verify:**
   ```bash
   ffplay audio.aac
   ```
   - Voiceover clear and prominent
   - Music audible in background
   - Music not overpowering voiceover
   - No audio clipping or distortion

3. **Inspect Audio Levels:**
   ```bash
   ffmpeg -i final_video.mp4 -af "volumedetect" -f null /dev/null
   ```
   - Check mean_volume and max_volume
   - Should be well-balanced

### Test Individual Functions

#### create_crossfade_video()
```python
from app.tasks.video_generation import create_crossfade_video

scene_files = [
    "/tmp/scene_1.mp4",
    "/tmp/scene_2.mp4",
    "/tmp/scene_3.mp4"
]

output = "/tmp/crossfaded.mp4"
create_crossfade_video(scene_files, output, crossfade_duration=1.0)

# Verify output exists
assert os.path.exists(output)

# Check duration (should be: total_scenes * duration - (num_fades * fade_duration))
# 3 scenes * 6s - 2 fades * 1s = 16 seconds
```

#### concatenate_audio()
```python
from app.tasks.video_generation import concatenate_audio

audio_files = [
    "/tmp/vo_1.mp3",
    "/tmp/vo_2.mp3",
    "/tmp/vo_3.mp3"
]

output = "/tmp/concatenated.mp3"
concatenate_audio(audio_files, output)

# Verify output
assert os.path.exists(output)
```

#### mix_audio_tracks()
```python
from app.tasks.video_generation import mix_audio_tracks

voiceover = "/tmp/voiceover_full.mp3"
music = "/tmp/music.mp3"
output = "/tmp/mixed.mp3"

mix_audio_tracks(voiceover, music, output, voiceover_volume=1.0, music_volume=0.3)

# Verify output
assert os.path.exists(output)

# Play and verify mix
ffplay output
```

#### combine_video_audio()
```python
from app.tasks.video_generation import combine_video_audio

video = "/tmp/crossfaded.mp4"
audio = "/tmp/mixed.mp3"
output = "/tmp/final.mp4"

combine_video_audio(video, audio, output)

# Verify output
assert os.path.exists(output)

# Check has both video and audio
ffprobe output
```

### Test Edge Cases

#### No Voiceover
```python
voiceover_urls = None
# Expected: Only music in audio track (at 30% volume)
```

#### No Music
```python
music_url = None
# Expected: Only voiceover in audio track (at 100% volume)
```

#### No Audio at All
```python
voiceover_urls = None
music_url = None
# Expected: Silent video or original scene audio preserved
```

#### Single Scene
```python
# Only 1 scene in video_urls
# Expected: No crossfades, just single scene with audio
```

#### Mismatched Durations
- Voiceover longer than video
- Music shorter than video
- Expected: Audio truncated/extended to match video duration

### Test Video Quality
1. **Resolution:**
   ```bash
   ffprobe -v error -select_streams v:0 -show_entries stream=width,height final_video.mp4
   # Expected: 1920x1080 (or original scene resolution)
   ```

2. **Frame Rate:**
   ```bash
   ffprobe -v error -select_streams v:0 -show_entries stream=r_frame_rate final_video.mp4
   # Expected: 30/1 (30 fps)
   ```

3. **Codec:**
   ```bash
   ffprobe -v error -select_streams v:0 -show_entries stream=codec_name final_video.mp4
   # Expected: h264
   ```

4. **Pixel Format:**
   ```bash
   ffprobe -v error -select_streams v:0 -show_entries stream=pix_fmt final_video.mp4
   # Expected: yuv420p (compatible with most players)
   ```

### Performance Testing
1. **Composition Time:**
   ```bash
   time {run compose_video()}
   ```
   - Expected: 30-90 seconds for 30-second video
   - Crossfades are CPU-intensive

2. **File Size:**
   ```bash
   ls -lh final_video.mp4
   ```
   - Expected: 10-50 MB for 30-second 1080p video
   - CRF 23 provides good quality/size balance

## Acceptance Criteria Checklist
- [x] Scenes transition with 1-second crossfade (not hard cut)
- [x] Voiceover audible at 100% volume
- [x] Music audible underneath at 30% volume
- [x] Product images overlay correctly (from Story 5.5)
- [x] Final video: H.264, 1080p, 30fps, smooth playback
- [x] Composition completes in ~60 seconds
- [x] Audio mixing uses proper volume levels
- [x] Voiceover concatenation works correctly
- [x] No audio/video sync issues

## Rollback Plan
```bash
# Revert to simple concat (no crossfades, basic audio)
git checkout HEAD~1 -- backend/app/tasks/video_generation.py

# Or restore previous compose_video function
# Videos will use simple concatenation instead of crossfades
```

## Files Modified
- `backend/app/tasks/video_generation.py`
  - Added `create_crossfade_video()` - xfade filter for N scenes
  - Added `concatenate_audio()` - join voiceover files
  - Added `mix_audio_tracks()` - mix voiceover + music (100% + 30%)
  - Added `combine_video_audio()` - merge video + mixed audio
  - Updated `compose_video()` to use all new functions
  - Pass voiceover_urls to compose_video from campaign

## FFmpeg Technical Details

### Crossfade Filter (xfade)
```bash
# 2 scenes example
ffmpeg -i scene1.mp4 -i scene2.mp4 \
  -filter_complex "[0:v][1:v]xfade=transition=fade:duration=1:offset=5[vout]" \
  -map "[vout]" output.mp4
```

Offset calculation:
- Scene 1 duration: 6 seconds
- Crossfade duration: 1 second
- Offset: 6 - 1 = 5 seconds

### Audio Mixing (amix)
```bash
ffmpeg -i voiceover.mp3 -i music.mp3 \
  -filter_complex "[0:a]volume=1.0[a1];[1:a]volume=0.3[a2];[a1][a2]amix=inputs=2:duration=first[aout]" \
  -map "[aout]" mixed.mp3
```

Volume levels:
- voiceover: 1.0 (100%, no change)
- music: 0.3 (30%, reduced)
- duration=first: Use voiceover duration

### Video + Audio Combination
```bash
ffmpeg -i video.mp4 -i audio.mp3 \
  -c:v copy \  # Copy video stream (no re-encode)
  -c:a aac -b:a 192k \  # Encode audio to AAC, 192kbps
  -map 0:v:0 -map 1:a:0 \  # Use video from input 0, audio from input 1
  -shortest \  # End when shortest stream ends
  output.mp4
```

## Known Limitations
- Crossfade offset assumes 6-second scenes (not dynamic)
- Cannot handle variable scene durations automatically
- Re-encodes video (slower, quality loss possible)
- Crossfades may not work if scenes have different resolutions
- Audio mixing always uses same volume ratios (not adjustable per scene)

## Future Enhancements
- Dynamic scene duration detection (ffprobe)
- Configurable crossfade duration per transition
- Different transition types (wipe, dissolve, slide)
- Dynamic volume adjustment based on content
- Normalization of audio levels
- Support for 4K/HDR video
- GPU-accelerated encoding
