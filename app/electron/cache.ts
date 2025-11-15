import * as path from 'path';
import * as fs from 'fs-extra';
import { App } from 'electron';

/**
 * Cache directory management - matches Rust CacheDirs structure
 */
export class CacheDirs {
  base: string;
  mediaDir: string;
  thumbDir: string;
  previews: string;
  segments: string;
  renders: string;
  captures: string;

  constructor(app: App) {
    const appDataPath = app.getPath('appData');
    const appName = 'com.zapcut.studio';
    
    this.base = path.join(appDataPath, appName, 'cache');
    this.mediaDir = path.join(this.base, 'media');
    this.thumbDir = path.join(this.base, 'thumbnails');
    this.previews = path.join(this.base, 'previews');
    this.segments = path.join(this.base, 'segments');
    this.renders = path.join(appDataPath, appName, 'projects');
    this.captures = path.join(this.base, 'captures');
  }

  /**
   * Ensure all cache directories exist
   */
  async ensureDirectories(): Promise<void> {
    await fs.ensureDir(this.mediaDir);
    await fs.ensureDir(this.thumbDir);
    await fs.ensureDir(this.previews);
    await fs.ensureDir(this.segments);
    await fs.ensureDir(this.renders);
    await fs.ensureDir(this.captures);
  }

  /**
   * Get preview file path for a specific plan and timestamp
   */
  previewFile(planId: string, atMs: number): string {
    const filename = `${planId}_${atMs}.jpg`;
    return path.join(this.previews, filename);
  }

  /**
   * Get concat list path for export
   */
  concatListPath(planId: string): string {
    return path.join(this.segments, `${planId}_concat.txt`);
  }

  /**
   * Get segment path for export
   */
  segmentPath(index: number): string {
    return path.join(this.segments, `segment_${String(index).padStart(4, '0')}.mp4`);
  }

  /**
   * Get render output path
   */
  renderOutputPath(planId: string, ext: string): string {
    const timestamp = Math.floor(Date.now() / 1000);
    return path.join(this.renders, `${planId}_${timestamp}.${ext}`);
  }

  /**
   * Get render output path with custom filename
   */
  renderOutputPathWithFilename(filename: string, ext: string): string {
    // Sanitize filename to remove path separators and invalid characters
    const sanitizedFilename = filename.replace(/[\/\\:*?"<>|]/g, '_');
    return path.join(this.renders, `${sanitizedFilename}.${ext}`);
  }

  /**
   * Get capture output path
   */
  captureOutputPath(ext: string): string {
    const timestamp = Math.floor(Date.now() / 1000);
    return path.join(this.captures, `capture_${timestamp}.${ext}`);
  }
}

