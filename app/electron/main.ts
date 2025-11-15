import { app, BrowserWindow, ipcMain, desktopCapturer, screen, dialog, protocol, shell } from 'electron';
import * as path from 'path';
import * as fs from 'fs';
import * as https from 'https';
// @ts-ignore - no types available
const squirrelStartup = require('electron-squirrel-startup');
import { ChildProcess } from 'child_process';

// Load environment variables from .env file
// Load from project root (one level up from electron directory)
require('dotenv').config({ path: path.join(__dirname, '..', '.env') });

import { configureFfmpeg } from './ffmpeg';
import { CacheDirs } from './cache';
import { probeMedia, extractPosterFrame } from './metadata';
import { buildPlan, findVisibleClip } from './editPlan';
import { executeExportJob } from './export';
import { ingestFiles } from './ingest';
import {
  ExportSettings,
  ExportResult,
  ListDevicesResult,
  RecordSettings,
  RecordingInfo,
  IngestRequest,
  IngestResult,
  GenerateImageResult,
} from './types';

// Handle Squirrel events on Windows
if (squirrelStartup) {
  app.quit();
}

let mainWindow: BrowserWindow | null = null;
let cacheDirs: CacheDirs | null = null;
let isQuitting = false;
let isCleaningUp = false; // Prevent multiple cleanup calls
let activeProcesses = new Set<ChildProcess>(); // Track active FFmpeg processes
let activeRecordings = new Map<string, RecordingInfo>(); // Track active screen recordings

/**
 * Create the main application window
 */
function createWindow(): void {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    title: 'Zapcut: AI Video Ads Generator & Editor',
    icon: path.join(__dirname, '../build-resources/icons/zapcut-app-icon-transparent.png'),
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js'),
    },
    show: false, // Don't show until ready
  });

  // Show window when ready to prevent visual flash
  mainWindow.once('ready-to-show', () => {
    mainWindow?.show();
    console.log('Electron window is ready and visible');
  });

  // Check if running in dev mode
  const isDev = process.argv.includes('--dev');

  if (isDev) {
    // Load from Vite dev server
    // Wait a bit for Vite to be ready, then load
    setTimeout(() => {
      mainWindow?.loadURL('http://localhost:3000').catch((err) => {
        console.error('Failed to load Vite dev server:', err);
        console.log('Make sure Vite is running on http://localhost:3000');
      });
    }, 1000);
    mainWindow.webContents.openDevTools();
  } else {
    // Load from built files
    if (app.isPackaged) {
      // In packaged app, use the path relative to ASAR root
      mainWindow.loadFile('dist/index.html');
    } else {
      // In development, use relative path from main.js
      mainWindow.loadFile(path.join(__dirname, '../dist/index.html'));
    }
  }

  // Handle window closed event
  mainWindow.on('close', (event: Electron.Event) => {
    if (!isQuitting) {
      event.preventDefault();
      mainWindow?.hide();
      
      // On macOS, keep app running when window is closed
      if (process.platform === 'darwin') {
        return;
      }
    }
    
    // Only cleanup if not already quitting (to avoid double cleanup)
    if (!isQuitting) {
      cleanup();
      // Force quit after cleanup
      setTimeout(() => {
        app.quit();
      }, 1000);
    }
  });

  // Handle window closed (after close event)
  mainWindow.on('closed', () => {
    mainWindow = null;
  });

  // Handle window minimize to tray (optional)
  mainWindow.on('minimize', (event: Electron.Event) => {
    if (process.platform === 'darwin') {
      event.preventDefault();
      mainWindow?.hide();
    }
  });
}

/**
 * Cleanup function for graceful shutdown
 */
function cleanup(): void {
  if (isCleaningUp) {
    console.log('Cleanup already in progress, skipping...');
    return;
  }
  
  isCleaningUp = true;
  console.log('Cleaning up resources...');
  
  // Cancel any ongoing operations
  if (mainWindow && !mainWindow.isDestroyed()) {
    mainWindow.webContents.send('app-shutting-down');
  }
  
  // Stop all active screen recordings
  if (activeRecordings.size > 0) {
    console.log(`Stopping ${activeRecordings.size} active recordings...`);
    for (const [recordingId, recording] of activeRecordings) {
      try {
        console.log(`Stopping recording ${recordingId}`);
        // Note: In a real implementation, you'd stop the actual recording here
        // For now, we just clean up the tracking
      } catch (error) {
        console.error(`Error stopping recording ${recordingId}:`, error);
      }
    }
    activeRecordings.clear();
  }
  
  // Kill all active FFmpeg processes
  if (activeProcesses.size > 0) {
    console.log(`Terminating ${activeProcesses.size} active processes...`);
    const processes = Array.from(activeProcesses);
    activeProcesses.clear(); // Clear immediately to prevent re-tracking
    
    for (const process of processes) {
      try {
        if (process && !process.killed) {
          console.log(`Killing process ${process.pid}`);
          process.kill('SIGTERM');
        }
      } catch (error) {
        console.error('Error killing process:', error);
      }
    }
    
    // Force kill any remaining processes after 3 seconds
    setTimeout(() => {
      for (const process of processes) {
        try {
          if (process && !process.killed) {
            console.log(`Force killing process ${process.pid}`);
            process.kill('SIGKILL');
          }
        } catch (error) {
          console.error('Error force killing process:', error);
        }
      }
    }, 3000);
  }
  
  console.log('Cleanup completed');
}

/**
 * Initialize application
 */
async function initialize(): Promise<void> {
  // Configure FFmpeg paths
  configureFfmpeg();

  // Initialize cache directories
  cacheDirs = new CacheDirs(app);
  await cacheDirs.ensureDirectories();

  // Register custom protocol for serving local media files
  protocol.registerFileProtocol('media', (request, callback) => {
    try {
      // Extract file path from media:// URL
      let url = request.url.substring('media://'.length);
      
      // Add leading slash if missing (protocol strips it)
      if (!url.startsWith('/')) {
        url = '/' + url;
      }
      
      // Decode URI component to handle spaces and special characters
      const filePath = decodeURIComponent(url);
      
      console.log(`[media://] Request for: ${request.url}`);
      console.log(`[media://] Decoded path: ${filePath}`);
      
      // Security check: ensure the file exists and is readable
      if (!fs.existsSync(filePath)) {
        console.error(`[media://] File not found: ${filePath}`);
        callback({ error: -6 }); // NET::ERR_FILE_NOT_FOUND
        return;
      }
      
      console.log(`[media://] File exists, serving: ${filePath}`);
      callback({ path: filePath });
    } catch (error) {
      console.error('[media://] Error serving media file:', error);
      callback({ error: -2 }); // NET::ERR_FAILED
    }
  });

  // Create window
  createWindow();
}

// Register protocol scheme as privileged BEFORE app is ready
protocol.registerSchemesAsPrivileged([
  {
    scheme: 'media',
    privileges: {
      bypassCSP: true,
      stream: true,
      supportFetchAPI: true,
      standard: true,
      secure: true
    }
  }
]);

// App lifecycle
app.whenReady().then(initialize);

// Handle window-all-closed
app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    cleanup();
    app.quit();
  }
});

// Handle activate (macOS)
app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  } else if (mainWindow) {
    mainWindow.show();
  }
});

// Handle before-quit
app.on('before-quit', (event) => {
  if (!isQuitting) {
    isQuitting = true;
    event.preventDefault(); // Prevent immediate quit
    cleanup();
    
    // Force quit after cleanup completes
    setTimeout(() => {
      console.log('Force quitting after cleanup...');
      app.exit(0);
    }, 2000);
  }
});

// Handle will-quit (redundant with before-quit, but kept for safety)
app.on('will-quit', () => {
  if (!isCleaningUp) {
    cleanup();
  }
});

// Handle app termination (removed - not a valid event in Electron)

// Handle uncaught exceptions
process.on('uncaughtException', (error) => {
  console.error('Uncaught Exception:', error);
  cleanup();
  
  // Don't exit immediately, let user save work
  if (mainWindow && !mainWindow.isDestroyed()) {
    mainWindow.webContents.send('app-error', {
      type: 'uncaughtException',
      message: error.message,
      stack: error.stack
    });
  }
});

// Handle unhandled promise rejections
process.on('unhandledRejection', (reason, promise) => {
  console.error('Unhandled Rejection at:', promise, 'reason:', reason);
  cleanup();
  
  if (mainWindow && !mainWindow.isDestroyed()) {
    mainWindow.webContents.send('app-error', {
      type: 'unhandledRejection',
      message: reason?.toString() || 'Unknown error',
      promise: promise.toString()
    });
  }
});

// Handle SIGTERM (force quit)
process.on('SIGTERM', () => {
  console.log('Received SIGTERM, shutting down gracefully...');
  cleanup();
  // Force quit after 5 seconds
  setTimeout(() => {
    console.log('Force quitting after timeout...');
    process.exit(0);
  }, 5000);
});

// Handle SIGINT (Ctrl+C)
process.on('SIGINT', () => {
  console.log('Received SIGINT, shutting down gracefully...');
  cleanup();
  // Force quit after 5 seconds
  setTimeout(() => {
    console.log('Force quitting after timeout...');
    process.exit(0);
  }, 5000);
});

// Handle SIGUSR1 (macOS)
process.on('SIGUSR1', () => {
  console.log('Received SIGUSR1, shutting down gracefully...');
  cleanup();
  app.quit();
});

// Handle SIGUSR2 (macOS)
process.on('SIGUSR2', () => {
  console.log('Received SIGUSR2, shutting down gracefully...');
  cleanup();
  app.quit();
});

/**
 * Track an active FFmpeg process for cleanup
 */
function trackProcess(process: ChildProcess): void {
  activeProcesses.add(process);
  
  // Remove from tracking when process ends
  process.on('exit', () => {
    activeProcesses.delete(process);
  });
  
  process.on('error', () => {
    activeProcesses.delete(process);
  });
}

/**
 * Stop tracking a process
 */
function untrackProcess(process: ChildProcess): void {
  activeProcesses.delete(process);
}

// ===== IPC Handlers =====

/**
 * List available capture devices (displays and audio inputs)
 */
ipcMain.handle('list-capture-devices', async (): Promise<ListDevicesResult> => {
  try {
    const sources = await desktopCapturer.getSources({
      types: ['screen', 'window'],
      thumbnailSize: { width: 150, height: 150 }
    });
    
    const displays = sources.map((source, index) => ({
      id: source.id,
      name: source.name,
      thumbnail: source.thumbnail.toDataURL(),
      index: index
    }));
    
    // For now, we'll return empty audio inputs since we're not implementing audio recording yet
    const audioInputs: string[] = [];
    
    return {
      displays,
      audio_inputs: audioInputs
    };
  } catch (error) {
    throw new Error(`Failed to list capture devices: ${(error as Error).message}`);
  }
});

/**
 * Start screen recording
 */
ipcMain.handle('start-screen-record', async (event, settings: RecordSettings): Promise<{ recordingId: string; outPath: string }> => {
  try {
    const { fps = 30, display_index = 0, audio_index = 0 } = settings;
    
    // Get available sources
    const sources = await desktopCapturer.getSources({
      types: ['screen', 'window'],
      thumbnailSize: { width: 150, height: 150 }
    });
    
    if (display_index >= sources.length) {
      throw new Error(`Display index ${display_index} out of range. Available displays: ${sources.length}`);
    }
    
    const source = sources[display_index];
    const recordingId = `recording_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    
    // Generate output path
    const outputPath = path.join(
      cacheDirs ? cacheDirs.captures : app.getPath('temp'),
      `screen_recording_${recordingId}.webm`
    );
    
    // Store recording info
    activeRecordings.set(recordingId, {
      source,
      outputPath,
      startTime: Date.now(),
      settings: { fps, display_index, audio_index }
    });
    
    console.log(`Started screen recording ${recordingId} to ${outputPath}`);
    
    // Send the source info to the renderer process to start recording
    event.sender.send('start-recording', {
      recordingId,
      sourceId: source.id,
      outputPath,
      settings: { fps, display_index, audio_index }
    });
    
    return {
      recordingId,
      outPath: outputPath
    };
  } catch (error) {
    throw new Error(`Failed to start screen recording: ${(error as Error).message}`);
  }
});

/**
 * Stop screen recording
 */
ipcMain.handle('stop-screen-record', async (event, recordingId: string): Promise<string> => {
  try {
    const recording = activeRecordings.get(recordingId);
    if (!recording) {
      throw new Error(`Recording ${recordingId} not found`);
    }
    
    // Send stop signal to renderer process
    event.sender.send('stop-recording', { recordingId });
    
    // Remove from active recordings
    activeRecordings.delete(recordingId);
    
    console.log(`Stopped screen recording ${recordingId}`);
    
    return recording.outputPath;
  } catch (error) {
    throw new Error(`Failed to stop screen recording: ${(error as Error).message}`);
  }
});

/**
 * Get media metadata
 */
ipcMain.handle('get-media-metadata', async (event, filePath: string) => {
  try {
    const metadata = await probeMedia(filePath);
    return metadata;
  } catch (error) {
    throw new Error(`Failed to get metadata: ${error}`);
  }
});

/**
 * Generate preview frame
 */
ipcMain.handle('generate-preview', async (event, projectJson: string, atMs: number): Promise<{ url: string; ts: number }> => {
  try {
    const plan = buildPlan(projectJson);
    const visibleClip = findVisibleClip(plan, atMs);
    
    if (!visibleClip) {
      throw new Error('No clip visible at this time');
    }

    // Calculate timestamp relative to clip source
    const relativeMs = atMs - visibleClip.startMs + visibleClip.inMs;
    const outputPath = cacheDirs!.previewFile(plan.id, atMs);
    
    const url = await extractPosterFrame(visibleClip.srcPath, relativeMs, outputPath);
    
    return {
      url,
      ts: atMs,
    };
  } catch (error) {
    throw new Error(`Failed to generate preview: ${error}`);
  }
});

/**
 * Export project
 */
ipcMain.handle('export-project', async (event, projectJson: string, settings: ExportSettings): Promise<ExportResult> => {
  try {
    const plan = buildPlan(projectJson);
    const result = await executeExportJob(plan, settings, cacheDirs!, mainWindow, trackProcess);
    return result;
  } catch (error) {
    throw new Error(`Failed to export project: ${error}`);
  }
});

/**
 * Convert WebM to MP4 using ffmpeg
 */
function convertWebmToMp4(inputPath: string, outputPath: string): Promise<string> {
  return new Promise((resolve, reject) => {
    const ffmpeg = require('fluent-ffmpeg');
    
    console.log(`Converting WebM to MP4: ${inputPath} -> ${outputPath}`);
    
    const command = ffmpeg(inputPath)
      .videoCodec('libx264')
      .audioCodec('aac')
      .outputOptions([
        '-preset fast',
        '-crf 23',
        '-movflags +faststart'
      ])
      .output(outputPath)
      .on('start', (commandLine: string) => {
        console.log('FFmpeg command:', commandLine);
      })
      .on('progress', (progress: any) => {
        if (progress.percent) {
          console.log(`Conversion progress: ${Math.round(progress.percent)}%`);
        }
      })
      .on('end', () => {
        console.log('WebM to MP4 conversion completed');
        resolve(outputPath);
      })
      .on('error', (err: Error) => {
        console.error('Conversion error:', err);
        reject(new Error(`FFmpeg conversion failed: ${err.message}`));
      });
    
    // Track the process
    const process = command.run();
    trackProcess(process);
  });
}

/**
 * Convert WebM audio to MP3 using ffmpeg
 */
function convertWebmToMp3(inputPath: string, outputPath: string): Promise<string> {
  return new Promise((resolve, reject) => {
    const ffmpeg = require('fluent-ffmpeg');
    
    console.log(`Converting WebM audio to MP3: ${inputPath} -> ${outputPath}`);
    
    const command = ffmpeg(inputPath)
      .audioCodec('libmp3lame')
      .audioBitrate('192k')
      .audioChannels(2)
      .audioFrequency(44100)
      .output(outputPath)
      .on('start', (commandLine: string) => {
        console.log('FFmpeg command:', commandLine);
      })
      .on('progress', (progress: any) => {
        if (progress.percent) {
          console.log(`Conversion progress: ${Math.round(progress.percent)}%`);
        }
      })
      .on('end', () => {
        console.log('WebM to MP3 conversion completed');
        resolve(outputPath);
      })
      .on('error', (err: Error) => {
        console.error('Conversion error:', err);
        reject(new Error(`FFmpeg audio conversion failed: ${err.message}`));
      });
    
    // Track the process
    const process = command.run();
    trackProcess(process);
  });
}

/**
 * Save blob data to file (converts WebM to MP4 for video, MP3 for audio)
 */
ipcMain.handle('save-blob-to-file', async (event, blobData: ArrayBuffer, filename: string): Promise<{ success: boolean; path: string }> => {
  try {
    const buffer = Buffer.from(blobData);
    
    // Construct full path in cache/media directory
    const webmPath = path.join(cacheDirs!.mediaDir, filename);
    
    // Save the blob to the webm file
    await fs.promises.writeFile(webmPath, buffer);
    console.log(`Saved WebM recording to: ${webmPath}`);
    
    // Check if it's a microphone recording (audio-only) by filename
    if (filename.startsWith('microphone_recording_')) {
      // For audio recordings, convert to MP3
      const mp3Filename = filename.replace('.webm', '.mp3');
      const mp3Path = path.join(cacheDirs!.mediaDir, mp3Filename);
      
      await convertWebmToMp3(webmPath, mp3Path);
      
      // Delete the original WebM file
      await fs.promises.unlink(webmPath);
      console.log(`Deleted temporary WebM file: ${webmPath}`);
      
      return { success: true, path: mp3Path };
    } else {
      // For video recordings (webcam/screen), convert to MP4
      const mp4Filename = filename.replace('.webm', '.mp4');
      const mp4Path = path.join(cacheDirs!.mediaDir, mp4Filename);
      
      await convertWebmToMp4(webmPath, mp4Path);
      
      // Delete the original WebM file
      await fs.promises.unlink(webmPath);
      console.log(`Deleted temporary WebM file: ${webmPath}`);
      
      return { success: true, path: mp4Path };
    }
  } catch (error) {
    throw new Error(`Failed to save blob to file: ${(error as Error).message}`);
  }
});

/**
 * Ingest files
 */
ipcMain.handle('ingest-files', async (event, request: IngestRequest): Promise<IngestResult[]> => {
  try {
    const { file_paths } = request;
    const results = await ingestFiles(file_paths, cacheDirs!);
    return results;
  } catch (error) {
    throw new Error(`Failed to ingest files: ${error}`);
  }
});

/**
 * Apply edits to project (placeholder implementation)
 */
ipcMain.handle('apply-edits', async (event, projectJson: string): Promise<{ success: boolean }> => {
  try {
    // For now, this is a placeholder - in a real implementation,
    // this would process the project JSON and apply any pending edits
    console.log('Apply edits called with project:', JSON.parse(projectJson));
    return { success: true };
  } catch (error) {
    throw new Error(`Failed to apply edits: ${(error as Error).message}`);
  }
});

/**
 * Open file dialog to select media files
 */
ipcMain.handle('open-file-dialog', async (): Promise<{ filePaths: string[] }> => {
  try {
    if (!mainWindow) {
      console.error('Cannot open file dialog: mainWindow is null');
      throw new Error('Application window is not available');
    }
    
    const result = await dialog.showOpenDialog(mainWindow, {
      properties: ['openFile', 'multiSelections'],
      filters: [
        { name: 'Media Files', extensions: ['mp4', 'mov', 'avi', 'mkv', 'webm', 'mp3', 'wav', 'aac', 'flac', 'ogg', 'jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp'] },
        { name: 'Video Files', extensions: ['mp4', 'mov', 'avi', 'mkv', 'webm'] },
        { name: 'Audio Files', extensions: ['mp3', 'wav', 'aac', 'flac', 'ogg'] },
        { name: 'Image Files', extensions: ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp'] },
        { name: 'All Files', extensions: ['*'] }
      ]
    });
    
    if (!result.canceled && result.filePaths.length > 0) {
      return { filePaths: result.filePaths };
    }
    
    return { filePaths: [] };
  } catch (error) {
    console.error('Error opening file dialog:', error);
    throw new Error(`Failed to open file dialog: ${(error as Error).message}`);
  }
});

/**
 * Open/reveal file in Finder (macOS), Explorer (Windows), or Files (Linux)
 */
ipcMain.handle('reveal-in-finder', async (event, filePath: string): Promise<{ success: boolean }> => {
  try {
    shell.showItemInFolder(filePath);
    return { success: true };
  } catch (error) {
    console.error('Error revealing file in finder:', error);
    throw new Error(`Failed to reveal file: ${(error as Error).message}`);
  }
});

/**
 * Delete a file
 */
ipcMain.handle('delete-file', async (event, filePath: string): Promise<{ success: boolean }> => {
  try {
    await fs.promises.unlink(filePath);
    console.log(`Deleted file: ${filePath}`);
    return { success: true };
  } catch (error: any) {
    // If file doesn't exist, consider it a success
    if (error.code === 'ENOENT') {
      console.log(`File already deleted: ${filePath}`);
      return { success: true };
    }
    console.error('Error deleting file:', error);
    throw new Error(`Failed to delete file: ${error.message}`);
  }
});

/**
 * Download image from URL and save to file
 */
async function downloadImage(url: string, outputPath: string): Promise<string> {
  return new Promise((resolve, reject) => {
    const file = fs.createWriteStream(outputPath);
    
    https.get(url, (response) => {
      if (response.statusCode !== 200) {
        reject(new Error(`Failed to download image: ${response.statusCode}`));
        return;
      }
      
      response.pipe(file);
      
      file.on('finish', () => {
        file.close();
        resolve(outputPath);
      });
    }).on('error', (err) => {
      fs.unlink(outputPath, () => {}); // Delete the file on error
      reject(err);
    });
  });
}

/**
 * Generate cosmic image using OpenAI DALL-E API
 */
ipcMain.handle('generate-image', async (event, userPrompt: string): Promise<GenerateImageResult> => {
  try {
    const apiKey = process.env.VITE_OPENAI_API_KEY || process.env.OPENAI_API_KEY;
    
    if (!apiKey) {
      throw new Error('OpenAI API key not found. Please set VITE_OPENAI_API_KEY or OPENAI_API_KEY environment variable.');
    }

    // Combine user prompt with cosmic system prompt
    const fullPrompt = `Create a cosmic/celestial themed image featuring ${userPrompt}. The image should have a space, nebula, starfield, or celestial aesthetic. The style should be artistic and visually striking.`;

    // Call OpenAI DALL-E API
    const requestData = JSON.stringify({
      model: 'dall-e-3',
      prompt: fullPrompt,
      size: '1024x1024',
      quality: 'standard',
      n: 1
    });

    const options = {
      hostname: 'api.openai.com',
      path: '/v1/images/generations',
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${apiKey}`,
        'Content-Length': Buffer.byteLength(requestData)
      }
    };

    // Make API request
    const apiResponse = await new Promise<any>((resolve, reject) => {
      const req = https.request(options, (res) => {
        let data = '';
        
        res.on('data', (chunk) => {
          data += chunk;
        });
        
        res.on('end', () => {
          if (res.statusCode !== 200) {
            reject(new Error(`OpenAI API error: ${res.statusCode} - ${data}`));
            return;
          }
          
          try {
            const json = JSON.parse(data);
            resolve(json);
          } catch (error) {
            reject(new Error(`Failed to parse API response: ${(error as Error).message}`));
          }
        });
      });
      
      req.on('error', (error) => {
        reject(new Error(`API request failed: ${error.message}`));
      });
      
      req.write(requestData);
      req.end();
    });

    // Extract image URL from response
    if (!apiResponse.data || !apiResponse.data[0] || !apiResponse.data[0].url) {
      throw new Error('Invalid API response: missing image URL');
    }

    const imageUrl = apiResponse.data[0].url;
    
    // Generate filename for saved image
    const timestamp = Date.now();
    const filename = `cosmic_${timestamp}.png`;
    const outputPath = path.join(cacheDirs!.mediaDir, filename);
    
    // Ensure media directory exists
    await fs.promises.mkdir(cacheDirs!.mediaDir, { recursive: true });
    
    // Download and save image
    await downloadImage(imageUrl, outputPath);
    
    console.log(`Generated cosmic image saved to: ${outputPath}`);
    
    return { success: true, path: outputPath };
  } catch (error) {
    console.error('Error generating image:', error);
    throw new Error(`Failed to generate image: ${(error as Error).message}`);
  }
});

