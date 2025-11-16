// Browser-compatible FFmpeg service using ffmpeg.wasm
import { FFmpeg } from '@ffmpeg/ffmpeg';
import { toBlobURL } from '@ffmpeg/util';

let ffmpegInstance: FFmpeg | null = null;
let isLoaded = false;
let isLoading = false;

/**
 * Get or initialize FFmpeg instance
 */
export async function getFFmpeg(): Promise<FFmpeg> {
  if (ffmpegInstance && isLoaded) {
    return ffmpegInstance;
  }

  if (isLoading) {
    // Wait for existing load to complete
    while (isLoading) {
      await new Promise(resolve => setTimeout(resolve, 100));
    }
    if (ffmpegInstance && isLoaded) {
      return ffmpegInstance;
    }
  }

  isLoading = true;

  try {
    const ffmpeg = new FFmpeg();
    
    // Load FFmpeg core
    const baseURL = 'https://unpkg.com/@ffmpeg/core@0.12.6/dist/esm';
    await ffmpeg.load({
      coreURL: await toBlobURL(`${baseURL}/ffmpeg-core.js`, 'text/javascript'),
      wasmURL: await toBlobURL(`${baseURL}/ffmpeg-core.wasm`, 'application/wasm'),
    });

    ffmpegInstance = ffmpeg;
    isLoaded = true;
    
    console.log('FFmpeg.wasm loaded successfully');
    return ffmpeg;
  } catch (error) {
    isLoading = false;
    console.error('Failed to load FFmpeg.wasm:', error);
    throw new Error(`Failed to initialize FFmpeg: ${error instanceof Error ? error.message : 'Unknown error'}`);
  } finally {
    isLoading = false;
  }
}

/**
 * Write file to FFmpeg virtual filesystem
 */
export async function writeFile(name: string, data: Uint8Array | string | Blob | File): Promise<void> {
  const ffmpeg = await getFFmpeg();
  // Convert File/Blob to Uint8Array if needed
  let fileData: Uint8Array | string;
  if (data instanceof File || data instanceof Blob) {
    fileData = await fileToUint8Array(data);
  } else {
    fileData = data;
  }
  await ffmpeg.writeFile(name, fileData);
}

/**
 * Read file from FFmpeg virtual filesystem
 */
export async function readFile(name: string): Promise<Uint8Array> {
  const ffmpeg = await getFFmpeg();
  const result = await ffmpeg.readFile(name);
  // Convert to Uint8Array if it's a string
  if (typeof result === 'string') {
    return new TextEncoder().encode(result);
  }
  return result;
}

/**
 * Delete file from FFmpeg virtual filesystem
 */
export async function deleteFile(name: string): Promise<void> {
  const ffmpeg = await getFFmpeg();
  await ffmpeg.deleteFile(name);
}

/**
 * List files in FFmpeg virtual filesystem
 */
export async function listDir(path: string = '/'): Promise<string[]> {
  const ffmpeg = await getFFmpeg();
  const result = await ffmpeg.listDir(path);
  // Convert FSNode[] to string[]
  return result.map(node => typeof node === 'string' ? node : node.name);
}

/**
 * Execute FFmpeg command
 */
export async function executeFFmpeg(args: string[]): Promise<void> {
  const ffmpeg = await getFFmpeg();
  await ffmpeg.exec(args);
}

/**
 * Get file as Blob from FFmpeg virtual filesystem
 */
export async function readFileAsBlob(name: string, mimeType?: string): Promise<Blob> {
  const data = await readFile(name);
  return new Blob([data], { type: mimeType });
}

/**
 * Convert File/Blob to Uint8Array
 */
export async function fileToUint8Array(file: File | Blob): Promise<Uint8Array> {
  const arrayBuffer = await file.arrayBuffer();
  return new Uint8Array(arrayBuffer);
}

/**
 * Get progress callback for FFmpeg operations
 */
export function onProgress(callback: (progress: { ratio: number }) => void): () => void {
  if (!ffmpegInstance) {
    return () => {};
  }
  
  const progressHandler = (event: { progress: number }) => {
    callback({ ratio: event.progress });
  };
  
  ffmpegInstance.on('progress', progressHandler);
  
  return () => {
    if (ffmpegInstance) {
      ffmpegInstance.off('progress', progressHandler);
    }
  };
}

