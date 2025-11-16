// Web export service using ffmpeg.wasm
import { getFFmpeg, writeFile, deleteFile, fileToUint8Array, readFileAsBlob } from './ffmpegWasm';
import { fileStore } from './webShim';
import type { ExportSettings, ExportResult, ProgressEvent } from './bindings';

interface ProjectJson {
  id: string;
  assets?: Record<string, any>;
  clips?: Record<string, any>;
  tracks?: Record<string, any>;
  canvasNodes?: Record<string, any>;
}

interface SeqClip {
  srcPath: string;
  inMs: number;
  outMs: number;
  startMs: number;
  endMs: number;
  assetWidth?: number;
  assetHeight?: number;
}

interface EditPlan {
  id: string;
  mainTrack: SeqClip[];
}

let progressCallback: ((event: ProgressEvent) => void) | null = null;

/**
 * Set progress callback for export operations
 */
export function setExportProgressCallback(callback: ((event: ProgressEvent) => void) | null): void {
  progressCallback = callback;
}

/**
 * Report progress to callback if available
 */
function reportProgress(phase: string, current: number, total: number, message: string): void {
  if (progressCallback) {
    progressCallback({ phase, current, total, message });
  }
}

/**
 * Get file from fileStore or fetch from URL
 */
async function getFileData(srcPath: string): Promise<Uint8Array> {
  // Check if it's a file ID in fileStore (e.g., "web-file-0")
  let file = fileStore.get(srcPath);
  if (file) {
    return await fileToUint8Array(file);
  }

  // Check if it's a blob URL - also check fileStore with blob URL as key
  if (srcPath.startsWith('blob:')) {
    file = fileStore.get(srcPath);
    if (file) {
      return await fileToUint8Array(file);
    }
    // Fetch from blob URL if not in store
    try {
      const response = await fetch(srcPath);
      const blob = await response.blob();
      return await fileToUint8Array(blob);
    } catch (error) {
      throw new Error(`Failed to load blob URL: ${srcPath} - ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  // Check if it's a file:// URL
  if (srcPath.startsWith('file://')) {
    const fileId = srcPath.substring(7);
    file = fileStore.get(fileId);
    if (file) {
      return await fileToUint8Array(file);
    }
  }

  // Check if it's a media:// URL (used in Electron/web)
  if (srcPath.startsWith('media://')) {
    const fileId = srcPath.substring(8);
    file = fileStore.get(fileId);
    if (file) {
      return await fileToUint8Array(file);
    }
  }

  // Try to fetch from URL (http/https)
  if (srcPath.startsWith('http://') || srcPath.startsWith('https://')) {
    try {
      const response = await fetch(srcPath);
      const blob = await response.blob();
      return await fileToUint8Array(blob);
    } catch (error) {
      throw new Error(`Failed to fetch from URL: ${srcPath} - ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  // Last resort: try fileStore with the path as-is (might be an object URL)
  file = fileStore.get(srcPath);
  if (file) {
    return await fileToUint8Array(file);
  }

  throw new Error(`Failed to load file: ${srcPath} - file not found in store and not a valid URL`);
}

/**
 * Check if file is an image based on extension or MIME type
 */
function isImageFile(filePath: string, file?: File): boolean {
  if (file) {
    return file.type.startsWith('image/');
  }
  const ext = filePath.toLowerCase().split('.').pop() || '';
  return ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp'].includes(ext);
}

/**
 * Build EditPlan from project JSON
 */
function buildPlan(projectJsonString: string): EditPlan {
  let parsed: ProjectJson;
  try {
    parsed = JSON.parse(projectJsonString);
  } catch (e) {
    throw new Error(`Invalid project JSON: ${(e as Error).message}`);
  }

  const { id, assets = {}, clips = {}, tracks = {} } = parsed;

  if (!id) {
    throw new Error('Project JSON missing id field');
  }

  const mainTrack: SeqClip[] = [];

  // Process clips by track role
  for (const [, track] of Object.entries(tracks)) {
    const trackObj = track as any;
    if (!trackObj.clipOrder || !Array.isArray(trackObj.clipOrder)) {
      continue;
    }

    // Only process main track for now (simplified export)
    if (trackObj.role !== 'main') {
      continue;
    }

    for (const clipId of trackObj.clipOrder) {
      const clip = clips[clipId];
      if (!clip) continue;

      const asset = assets[(clip as any).assetId];
      if (!asset) continue;

      const clipObj = clip as any;

      // Validate clip timing
      if (clipObj.outMs <= clipObj.inMs) {
        throw new Error(`Clip ${clipId} has invalid timing: out <= in`);
      }

      // Get source path - try multiple possible fields
      const assetSrc = (asset as any).src || (asset as any).file_path || (asset as any).url;
      if (!assetSrc) {
        throw new Error(`Asset ${(clip as any).assetId} missing source path`);
      }

      const seqClip: SeqClip = {
        srcPath: assetSrc,
        inMs: clipObj.inMs,
        outMs: clipObj.outMs,
        startMs: clipObj.startMs,
        endMs: clipObj.endMs,
      };

      // Attach asset metadata for aspect ratio preservation
      if ((asset as any).width && (asset as any).height) {
        seqClip.assetWidth = (asset as any).width;
        seqClip.assetHeight = (asset as any).height;
      }

      mainTrack.push(seqClip);
    }
  }

  // Sort main track by start time
  mainTrack.sort((a, b) => a.startMs - b.startMs);

  return {
    id,
    mainTrack,
  };
}

/**
 * Create a black video segment using ffmpeg.wasm
 */
async function createBlackSegment(
  outputPath: string,
  durationSec: number,
  width: number,
  height: number
): Promise<void> {
  const ffmpeg = await getFFmpeg();

  // Use color filter to create black video
  const args = [
    '-f', 'lavfi',
    '-i', `color=c=black:s=${width}x${height}:r=30:d=${durationSec}`,
    '-f', 'lavfi',
    '-i', `anullsrc=r=48000:cl=stereo`,
    '-c:v', 'libx264',
    '-preset', 'ultrafast',
    '-crf', '23',
    '-pix_fmt', 'yuv420p',
    '-c:a', 'aac',
    '-shortest',
    '-y',
    outputPath,
  ];

  await ffmpeg.exec(args);
}

/**
 * Convert image to video segment
 */
async function convertImageToVideoSegment(
  inputPath: string,
  outputPath: string,
  durationSec: number,
  targetWidth: number | null,
  targetHeight: number | null,
  assetWidth: number | undefined,
  assetHeight: number | undefined,
  bitrate: number
): Promise<void> {
  const ffmpeg = await getFFmpeg();

  const args: string[] = [
    '-loop', '1',
    '-framerate', '30',
    '-i', inputPath,
    '-t', durationSec.toString(),
  ];

  // Apply scaling with aspect ratio preservation if target resolution is specified
  if (targetWidth && targetHeight) {
    if (assetWidth && assetHeight && assetWidth > 0 && assetHeight > 0) {
      const assetAspect = assetWidth / assetHeight;
      const targetAspect = targetWidth / targetHeight;

      let scaleWidth: number, scaleHeight: number;
      if (assetAspect > targetAspect) {
        scaleWidth = targetWidth;
        scaleHeight = Math.round(targetWidth / assetAspect);
      } else {
        scaleHeight = targetHeight;
        scaleWidth = Math.round(targetHeight * assetAspect);
      }

      const padX = Math.round((targetWidth - scaleWidth) / 2);
      const padY = Math.round((targetHeight - scaleHeight) / 2);

      args.push(
        '-vf',
        `scale=${scaleWidth}:${scaleHeight}:force_original_aspect_ratio=decrease,pad=${targetWidth}:${targetHeight}:${padX}:${padY}:color=black`
      );
    } else {
      args.push('-vf', `scale=${targetWidth}:${targetHeight}`);
    }
  }

  args.push(
    '-c:v', 'libx264',
    '-preset', 'veryfast',
    '-crf', '23',
    '-b:v', `${bitrate}k`,
    '-pix_fmt', 'yuv420p',
    '-y',
    outputPath
  );

  await ffmpeg.exec(args);
}

/**
 * Trim a video segment
 */
async function trimSegment(
  inputPath: string,
  outputPath: string,
  startSec: number,
  durationSec: number,
  copyCodec: boolean,
  targetWidth: number | null,
  targetHeight: number | null,
  bitrate: number
): Promise<void> {
  const ffmpeg = await getFFmpeg();

  const args: string[] = [
    '-ss', startSec.toString(),
    '-i', inputPath,
    '-t', durationSec.toString(),
  ];

  if (copyCodec) {
    args.push('-c', 'copy');
  } else {
    if (targetWidth && targetHeight) {
      args.push('-vf', `scale=${targetWidth}:${targetHeight}`);
    }
    args.push(
      '-c:v', 'libx264',
      '-c:a', 'aac',
      '-preset', 'veryfast',
      '-crf', '23',
      '-b:v', `${bitrate}k`,
      '-b:a', '192k',
    );
  }

  args.push('-y', outputPath);

  await ffmpeg.exec(args);
}

/**
 * Concatenate video segments
 */
async function concatenateSegments(
  concatListPath: string,
  outputPath: string,
  copyCodec: boolean,
  targetWidth: number | null,
  targetHeight: number | null,
  bitrate: number
): Promise<void> {
  const ffmpeg = await getFFmpeg();

  const args: string[] = [
    '-f', 'concat',
    '-safe', '0',
    '-i', concatListPath,
  ];

  if (copyCodec) {
    args.push('-c', 'copy');
  } else {
    if (targetWidth && targetHeight) {
      args.push('-vf', `scale=${targetWidth}:${targetHeight}`);
    }
    args.push(
      '-c:v', 'libx264',
      '-c:a', 'aac',
      '-preset', 'veryfast',
      '-crf', '23',
      '-b:v', `${bitrate}k`,
      '-b:a', '192k',
    );
  }

  args.push('-y', outputPath);

  await ffmpeg.exec(args);
}

/**
 * Export project using ffmpeg.wasm
 */
export async function exportProjectWeb(
  projectJson: string,
  settings: ExportSettings
): Promise<ExportResult> {
  // Ensure FFmpeg is loaded
  await getFFmpeg();

  // Parse project JSON
  const plan = buildPlan(projectJson);

  // Determine target resolution
  const targetWidth = settings.width || 1920;
  const targetHeight = settings.height || 1080;
  const useSourceResolution = targetWidth === -1 || targetHeight === -1;
  const bitrate = settings.bitrate || 5000;
  const format = settings.format || 'mp4';

  // Calculate total steps
  const gapCount = plan.mainTrack.length > 0 ? plan.mainTrack.length - 1 : 0;
  const total = plan.mainTrack.length + gapCount + 2;
  let current = 0;

  const segmentPaths: string[] = [];
  let segmentIndex = 0;

  reportProgress('segment', current, total, 'Starting export...');

  // Step 1: Process each clip and gaps between them
  for (let idx = 0; idx < plan.mainTrack.length; idx++) {
    const clip = plan.mainTrack[idx];

    // Add gap before this clip (if not the first clip)
    if (idx > 0) {
      const prevClip = plan.mainTrack[idx - 1];
      const gapDurationMs = clip.startMs - prevClip.endMs;

      if (gapDurationMs > 0) {
        try {
          reportProgress('segment', current, total, `Creating gap ${idx}/${gapCount}`);

          const gapPath = `gap_${segmentIndex}.mp4`;
          const gapWidth = useSourceResolution ? 1920 : targetWidth;
          const gapHeight = useSourceResolution ? 1080 : targetHeight;

          await createBlackSegment(gapPath, gapDurationMs / 1000, gapWidth, gapHeight);
          segmentPaths.push(gapPath);
          segmentIndex++;
          current++;
        } catch (err) {
          console.warn(`Failed to create gap segment: ${(err as Error).message}`);
          // Continue without the gap
        }
      }
    }

    // Process clip
    reportProgress('segment', current, total, `Processing clip ${idx + 1}/${plan.mainTrack.length}`);

    const segPath = `segment_${segmentIndex}.mp4`;
    const startSec = clip.inMs / 1000;
    const durationSec = (clip.outMs - clip.inMs) / 1000;

    // Determine file extension for input path
    let fileExt = '.mp4';
    const file = fileStore.get(clip.srcPath);
    if (file) {
      // Get extension from File object
      const fileName = file.name;
      const extMatch = fileName.match(/\.([^.]+)$/);
      if (extMatch) {
        fileExt = '.' + extMatch[1].toLowerCase();
      }
    } else if (clip.srcPath.includes('.')) {
      // Get extension from path
      fileExt = clip.srcPath.substring(clip.srcPath.lastIndexOf('.')).toLowerCase();
    }

    // Load file data into FFmpeg virtual filesystem
    const inputPath = `input_${segmentIndex}${fileExt}`;
    const fileData = await getFileData(clip.srcPath);
    await writeFile(inputPath, fileData);

    // Check if this is an image file
    const isImage = isImageFile(clip.srcPath, file);

    if (isImage) {
      // Convert image to video segment
      await convertImageToVideoSegment(
        inputPath,
        segPath,
        durationSec,
        useSourceResolution ? null : targetWidth,
        useSourceResolution ? null : targetHeight,
        clip.assetWidth,
        clip.assetHeight,
        bitrate
      );
    } else {
      // Handle video clips
      const needsScaling = !useSourceResolution;

      if (needsScaling) {
        await trimSegment(inputPath, segPath, startSec, durationSec, false, targetWidth, targetHeight, bitrate);
      } else {
        try {
          await trimSegment(inputPath, segPath, startSec, durationSec, true, null, null, bitrate);
        } catch (err) {
          console.log(`Codec copy failed for segment ${idx}, transcoding...`);
          await trimSegment(inputPath, segPath, startSec, durationSec, false, null, null, bitrate);
        }
      }
    }

    segmentPaths.push(segPath);
    segmentIndex++;
    current++;

    // Clean up input file
    try {
      await deleteFile(inputPath);
    } catch (err) {
      // Ignore cleanup errors
    }
  }

  // Step 2: Create concat list file
  reportProgress('concat', current, total, 'Preparing concatenation');

  const concatPath = 'concat_list.txt';
  const concatContent = segmentPaths.map(segPath => `file '${segPath}'`).join('\n');
  await writeFile(concatPath, concatContent);

  current++;

  // Step 3: Concatenate segments
  reportProgress('finalize', current, total, 'Writing final output');

  const ext = format === 'mov' ? 'mov' : 'mp4';
  const outputPath = `output.${ext}`;

  try {
    await concatenateSegments(concatPath, outputPath, true, null, null, bitrate);
  } catch (err) {
    console.log('Concat with copy failed, re-encoding...');
    await concatenateSegments(concatPath, outputPath, false, targetWidth, targetHeight, bitrate);
  }

  current++;

  // Step 4: Read output file
  const blob = await readFileAsBlob(outputPath, `video/${ext}`);
  const blobUrl = URL.createObjectURL(blob);

  // Calculate duration
  const firstClipStart = plan.mainTrack.length > 0 ? plan.mainTrack[0].startMs : 0;
  const lastClipEnd = plan.mainTrack.length > 0 ? plan.mainTrack[plan.mainTrack.length - 1].endMs : 0;
  const durationMs = lastClipEnd - firstClipStart;

  // Clean up temporary files
  try {
    for (const segPath of segmentPaths) {
      await deleteFile(segPath);
    }
    await deleteFile(concatPath);
    await deleteFile(outputPath);
  } catch (err) {
    console.warn('Failed to clean up temporary files:', err);
  }

  // Trigger download
  const filename = settings.filename || `export_${Date.now()}.${ext}`;
  const a = document.createElement('a');
  a.href = blobUrl;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);

  // Return result
  return {
    path: blobUrl,
    duration_ms: durationMs,
    size_bytes: blob.size,
  };
}

