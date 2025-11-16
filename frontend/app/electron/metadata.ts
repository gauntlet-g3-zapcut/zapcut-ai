import ffmpeg from 'fluent-ffmpeg';
import { MediaMetadata } from './types';

/**
 * Probe media file and extract metadata
 */
export async function probeMedia(inputPath: string): Promise<MediaMetadata> {
  return new Promise((resolve, reject) => {
    ffmpeg.ffprobe(inputPath, (err, metadata) => {
      if (err) {
        reject(new Error(`ffprobe failed: ${err.message}`));
        return;
      }

      // Initialize result
      const result: MediaMetadata = {
        duration_ms: 0,
        width: null,
        height: null,
        has_audio: null,
        codec_video: null,
        codec_audio: null,
        rotation_deg: null,
      };

      // Extract duration from format
      if (metadata.format && metadata.format.duration) {
        result.duration_ms = Math.round(metadata.format.duration * 1000);
      }

      // Process streams
      if (metadata.streams) {
        for (const stream of metadata.streams) {
          if (stream.codec_type === 'video') {
            result.width = stream.width || null;
            result.height = stream.height || null;
            result.codec_video = stream.codec_name || null;
            
            // Check for rotation in stream tags or metadata
            if (stream.tags && stream.tags.rotate) {
              result.rotation_deg = parseInt(stream.tags.rotate, 10);
            }
            
            // If duration not in format, try to get from video stream
            if (!result.duration_ms && stream.duration) {
              result.duration_ms = Math.round(parseFloat(stream.duration) * 1000);
            }
          } else if (stream.codec_type === 'audio') {
            result.has_audio = true;
            result.codec_audio = stream.codec_name || null;
          }
        }
      }

      resolve(result);
    });
  });
}

/**
 * Extract a poster frame from video at specified timestamp
 */
export async function extractPosterFrame(inputPath: string, atMs: number, outputPath: string): Promise<string> {
  return new Promise((resolve, reject) => {
    const timestamp = atMs / 1000; // Convert to seconds
    
    ffmpeg(inputPath)
      .seekInput(timestamp)
      .frames(1)
      .outputOptions(['-q:v 5'])
      .output(outputPath)
      .on('end', () => {
        resolve(`file://${outputPath}`);
      })
      .on('error', (err: Error) => {
        reject(new Error(`ffmpeg frame extraction failed: ${err.message}`));
      })
      .run();
  });
}

