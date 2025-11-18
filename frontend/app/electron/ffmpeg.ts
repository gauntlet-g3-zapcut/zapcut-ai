import * as path from 'path';
import { app } from 'electron';
import ffmpeg from 'fluent-ffmpeg';

/**
 * Resolve FFmpeg binary path based on environment
 */
export function resolveFfmpegPath(): string {
  if (app.isPackaged) {
    // Production: binaries are in resources
    return path.join(process.resourcesPath!, 'bin', 'macos', 'ffmpeg');
  } else {
    // Development: binaries are in electron/bin/macos
    return path.join(__dirname, 'bin', 'macos', 'ffmpeg');
  }
}

/**
 * Resolve FFprobe binary path based on environment
 */
export function resolveFfprobePath(): string {
  if (app.isPackaged) {
    return path.join(process.resourcesPath!, 'bin', 'macos', 'ffprobe');
  } else {
    return path.join(__dirname, 'bin', 'macos', 'ffprobe');
  }
}

/**
 * Configure fluent-ffmpeg to use bundled binaries
 */
export function configureFfmpeg(): { ffmpegPath: string; ffprobePath: string } {
  const ffmpegPath = resolveFfmpegPath();
  const ffprobePath = resolveFfprobePath();
  
  ffmpeg.setFfmpegPath(ffmpegPath);
  ffmpeg.setFfprobePath(ffprobePath);
  
  return { ffmpegPath, ffprobePath };
}

