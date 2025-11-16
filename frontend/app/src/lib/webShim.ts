// Web-compatible shim for Electron APIs
// This provides browser-based alternatives when running in a web environment

import type {
    MediaMeta,
    PreviewResult,
    ExportSettings,
    ExportResult,
    ProgressEvent,
    DisplayDevice,
    ListDevices,
    IngestRequest,
    IngestResult,
    GenerateImageResult,
} from './bindings';

// Export fileStore for use in other modules
export const fileStore = new Map<string, File>();

// Generate a unique ID for file references
let fileIdCounter = 0;

// Web-compatible file dialog using HTML5 File API
async function openFileDialogWeb(): Promise<{ filePaths: string[] }> {
    return new Promise((resolve, reject) => {
        try {
            // Ensure we're in a browser environment
            if (typeof document === 'undefined' || typeof document.createElement === 'undefined') {
                reject(new Error('File dialog requires a browser environment'));
                return;
            }

            const input = document.createElement('input');
            input.type = 'file';
            input.multiple = true;
            input.accept = 'video/*,audio/*,image/*,.mp4,.mov,.mp3,.wav,.jpg,.jpeg,.png';

            let resolved = false;

            const cleanup = () => {
                if (input.parentNode) {
                    try {
                        document.body.removeChild(input);
                    } catch (e) {
                        // Ignore cleanup errors
                    }
                }
            };

            input.onchange = (e) => {
                if (resolved) return;
                resolved = true;

                try {
                    const files = (e.target as HTMLInputElement).files;
                    if (!files || files.length === 0) {
                        cleanup();
                        resolve({ filePaths: [] });
                        return;
                    }

                    const filePaths: string[] = [];
                    Array.from(files).forEach((file) => {
                        const fileId = `web-file-${fileIdCounter++}`;
                        fileStore.set(fileId, file);
                        filePaths.push(fileId);
                    });

                    cleanup();
                    resolve({ filePaths });
                } catch (error) {
                    cleanup();
                    reject(error);
                }
            };

            input.oncancel = () => {
                if (resolved) return;
                resolved = true;
                cleanup();
                resolve({ filePaths: [] });
            };

            // Handle errors
            input.onerror = () => {
                if (resolved) return;
                resolved = true;
                cleanup();
                reject(new Error('File input error'));
            };

            // Add to DOM temporarily (some browsers require this)
            input.style.display = 'none';
            input.style.position = 'fixed';
            input.style.top = '-1000px';
            input.style.left = '-1000px';

            try {
                document.body.appendChild(input);

                // Use setTimeout to ensure the input is in the DOM before clicking
                setTimeout(() => {
                    try {
                        input.click();
                    } catch (error) {
                        if (!resolved) {
                            resolved = true;
                            cleanup();
                            reject(new Error('Failed to trigger file dialog. Please ensure file access is allowed.'));
                        }
                    }
                }, 0);
            } catch (error) {
                if (!resolved) {
                    resolved = true;
                    cleanup();
                    reject(new Error('Failed to create file input. Please check browser permissions.'));
                }
            }
        } catch (error) {
            reject(error instanceof Error ? error : new Error('Unknown error creating file dialog'));
        }
    });
}

// Get media metadata using Web APIs
async function getMediaMetadataWeb(fileIdOrUrl: string): Promise<MediaMeta> {
    // Try to get file from store first (by fileId or blob URL)
    let file = fileStore.get(fileIdOrUrl);
    let url: string;
    let mimeType: string = '';

    if (file) {
        // File found in store - use it directly
        url = URL.createObjectURL(file);
        mimeType = file.type;
    } else if (fileIdOrUrl.startsWith('blob:')) {
        // Already a blob URL - try to get file from store using blob URL as key
        file = fileStore.get(fileIdOrUrl);
        if (file) {
            url = fileIdOrUrl; // Reuse existing blob URL
            mimeType = file.type;
        } else {
            // Blob URL but no file in store - try to determine type from fetch
            url = fileIdOrUrl;
            try {
                const response = await fetch(url, { method: 'HEAD' });
                mimeType = response.headers.get('content-type') || '';
            } catch {
                // Fallback: try to guess from URL or use video as default
                mimeType = 'video/mp4';
            }
        }
    } else {
        throw new Error(`File not found: ${fileIdOrUrl}`);
    }

    return new Promise((resolve, reject) => {
        if (mimeType.startsWith('video/') || (!mimeType && !file?.type)) {
            // Default to video if unknown
            const video = document.createElement('video');
            video.preload = 'metadata';

            video.onloadedmetadata = () => {
                resolve({
                    duration_ms: Math.round(video.duration * 1000),
                    width: video.videoWidth,
                    height: video.videoHeight,
                    has_audio: true,
                });
                if (file) URL.revokeObjectURL(video.src);
            };

            video.onerror = () => {
                reject(new Error('Failed to load video metadata'));
                if (file) URL.revokeObjectURL(video.src);
            };

            video.src = url;
        } else if (mimeType.startsWith('audio/')) {
            const audio = document.createElement('audio');
            audio.preload = 'metadata';

            audio.onloadedmetadata = () => {
                resolve({
                    duration_ms: Math.round(audio.duration * 1000),
                    has_audio: true,
                });
                if (file) URL.revokeObjectURL(audio.src);
            };

            audio.onerror = () => {
                reject(new Error('Failed to load audio metadata'));
                if (file) URL.revokeObjectURL(audio.src);
            };

            audio.src = url;
        } else if (mimeType.startsWith('image/')) {
            const img = document.createElement('img');

            img.onload = () => {
                resolve({
                    duration_ms: 0,
                    width: img.width,
                    height: img.height,
                });
                if (file) URL.revokeObjectURL(img.src);
            };

            img.onerror = () => {
                reject(new Error('Failed to load image'));
                if (file) URL.revokeObjectURL(img.src);
            };

            img.src = url;
        } else {
            resolve({
                duration_ms: 0,
            });
        }
    });
}

// Ingest files for web (create object URLs)
async function ingestFilesWeb(request: IngestRequest): Promise<IngestResult[]> {
    // Use browser-compatible ingestion service
    const { ingestFilesBrowser } = await import('./browserIngest');
    return ingestFilesBrowser(request.file_paths);
}

// Save blob using browser download API
async function saveBlobToFileWeb(blobData: ArrayBuffer, suggestedFilename: string): Promise<{ success: boolean; path: string }> {
    try {
        const blob = new Blob([blobData]);
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = suggestedFilename || 'download';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

        return {
            success: true,
            path: suggestedFilename,
        };
    } catch (error) {
        console.error('Failed to save file:', error);
        return {
            success: false,
            path: '',
        };
    }
}

// List capture devices using MediaDevices API
async function listCaptureDevicesWeb(): Promise<ListDevices> {
    try {
        const devices = await navigator.mediaDevices.enumerateDevices();
        const audioInputs = devices
            .filter(d => d.kind === 'audioinput')
            .map(d => d.label || d.deviceId);

        // For displays, we can't enumerate them in browsers
        // But we can use getDisplayMedia for screen capture
        const displays: DisplayDevice[] = [];

        return {
            displays,
            audio_inputs: audioInputs,
        };
    } catch (error) {
        console.error('Failed to list devices:', error);
        return {
            displays: [],
            audio_inputs: [],
        };
    }
}

// Stub implementations for features that require backend support
async function applyEditsWeb(): Promise<{ success: boolean }> {
    console.warn('applyEdits not available in web mode - requires backend');
    return { success: false };
}

async function generatePreviewWeb(_projectJson: string, _atMs: number): Promise<PreviewResult> {
    // For web, we can generate previews using canvas
    // This is a simplified version - full implementation would use ffmpeg.wasm
    throw new Error('Preview generation requires ffmpeg.wasm support (coming soon)');
}

// Progress callback storage
let exportProgressCallback: ((event: ProgressEvent) => void) | null = null;

async function exportProjectWeb(projectJson: string, settings: ExportSettings): Promise<ExportResult> {
    // Import and use the web export service
    const { exportProjectWeb: exportProject, setExportProgressCallback } = await import('./webExport');
    
    // Set up progress callback
    setExportProgressCallback((event) => {
        if (exportProgressCallback) {
            exportProgressCallback(event);
        }
    });
    
    try {
        return await exportProject(projectJson, settings);
    } finally {
        // Clear progress callback after export
        setExportProgressCallback(null);
    }
}

function onExportProgressWeb(callback: (event: ProgressEvent) => void): () => void {
    exportProgressCallback = callback;
    return () => {
        exportProgressCallback = null;
    };
}

async function startScreenRecordWeb(): Promise<{ recordingId: string; outPath: string }> {
    throw new Error('Screen recording requires backend support');
}

async function stopScreenRecordWeb(): Promise<string> {
    throw new Error('Screen recording requires backend support');
}

function onStartRecordingWeb(): () => void {
    return () => { }; // No-op
}

function onStopRecordingWeb(): () => void {
    return () => { }; // No-op
}

async function revealInFinderWeb(): Promise<{ success: boolean }> {
    console.warn('revealInFinder not available in web mode');
    return { success: false };
}

async function deleteFileWeb(): Promise<{ success: boolean }> {
    console.warn('deleteFile not available in web mode');
    return { success: false };
}

async function generateCosmicImageWeb(_prompt: string): Promise<GenerateImageResult> {
    // This would need to call a backend API
    throw new Error('Image generation requires backend API');
}

// Initialize web shim if running in browser
export function initWebShim(): void {
    // Safety check
    if (typeof window === 'undefined') {
        console.warn('initWebShim called but window is undefined');
        return;
    }
    
    // If Electron API already exists, don't override it
    if ((window as any).electronAPI) {
        console.log('Electron API already exists, skipping web shim initialization');
        return;
    }

    // Check if we're in Electron environment
    const isElectronEnv = typeof navigator !== 'undefined' && navigator.userAgent.includes('Electron');
    if (isElectronEnv) {
        console.log('Electron environment detected, skipping web shim');
        return;
    }

    console.log('Initializing web-compatible shim for Electron APIs');

    // Mark that web shim is initialized
    (window as any).__WEB_SHIM_INITIALIZED = true;

    // Create web-compatible Electron API immediately
    const api = {
        getMediaMetadata: getMediaMetadataWeb,
        applyEdits: applyEditsWeb,
        generatePreview: generatePreviewWeb,
        exportProject: exportProjectWeb,
        ingestFiles: ingestFilesWeb,
        openFileDialog: openFileDialogWeb,
        saveBlobToFile: saveBlobToFileWeb,
        listCaptureDevices: listCaptureDevicesWeb,
        startScreenRecord: startScreenRecordWeb,
        stopScreenRecord: stopScreenRecordWeb,
        onExportProgress: onExportProgressWeb,
        onStartRecording: onStartRecordingWeb,
        onStopRecording: onStopRecordingWeb,
        revealInFinder: revealInFinderWeb,
        deleteFile: deleteFileWeb,
        generateImage: generateCosmicImageWeb,
    };
    
    // Set the API on window
    (window as any).electronAPI = api;

    // Verify it was set correctly
    if (!(window as any).electronAPI) {
        console.error('CRITICAL: Failed to set electronAPI on window object!');
        return;
    }
    
    if (typeof (window as any).electronAPI.openFileDialog !== 'function') {
        console.error('CRITICAL: openFileDialog is not a function after initialization!');
        return;
    }

    console.log('Web shim initialized successfully', {
        hasOpenFileDialog: typeof (window as any).electronAPI.openFileDialog === 'function',
        userAgent: navigator.userAgent,
        electronAPIExists: typeof (window as any).electronAPI !== 'undefined',
        allFunctions: Object.keys((window as any).electronAPI),
    });
}

// CRITICAL: Initialize shim immediately when module loads
// This ensures it's available before any other code runs
(function initializeWebShimImmediately() {
    if (typeof window === 'undefined') return;
    
    // Don't initialize if Electron is detected
    if (typeof navigator !== 'undefined' && navigator.userAgent.includes('Electron')) {
        return;
    }
    
    // Initialize immediately - this should set window.electronAPI
    initWebShim();
    
    // Verify it was set
    if (!(window as any).electronAPI) {
        console.error('CRITICAL: Web shim failed to initialize on module load!');
        // Try one more time
        setTimeout(() => {
            initWebShim();
            if (!(window as any).electronAPI) {
                console.error('CRITICAL: Web shim still failed after retry!');
            }
        }, 100);
    }
    
    // Also ensure it's available after DOM loads (for safety)
    if (typeof document !== 'undefined') {
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => {
                if (!(window as any).electronAPI) {
                    console.warn('Web shim missing on DOMContentLoaded, reinitializing...');
                    initWebShim();
                }
            });
        } else {
            // DOM already loaded, ensure shim is there
            if (!(window as any).electronAPI) {
                console.warn('Web shim missing after DOM load, reinitializing...');
                initWebShim();
            }
        }
    }
    
    // Log final status
    if ((window as any).electronAPI) {
        console.log('Web shim module initialization complete', {
            apiExists: true,
            hasOpenFileDialog: typeof (window as any).electronAPI.openFileDialog === 'function',
        });
    } else {
        console.error('Web shim module initialization FAILED - API not set!');
    }
})();

