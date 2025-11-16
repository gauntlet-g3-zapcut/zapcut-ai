// Browser-compatible file ingestion service
import type { IngestResult, MediaMeta } from './bindings';
import { fileStore } from './webShim';

// Get media metadata using Web APIs
async function getMediaMetadataWeb(fileIdOrUrl: string): Promise<MediaMeta> {
    const file = fileStore.get(fileIdOrUrl);
    let url: string;
    let mimeType: string = '';

    if (file) {
        url = URL.createObjectURL(file);
        mimeType = file.type;
    } else if (fileIdOrUrl.startsWith('blob:')) {
        url = fileIdOrUrl;
        try {
            const response = await fetch(url, { method: 'HEAD' });
            mimeType = response.headers.get('content-type') || '';
        } catch {
            mimeType = 'video/mp4';
        }
    } else {
        throw new Error(`File not found: ${fileIdOrUrl}`);
    }

    return new Promise((resolve, reject) => {
        if (mimeType.startsWith('video/') || (!mimeType && !file?.type)) {
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

// Get file extension from filename
function getFileExtension(filename: string): string {
    const parts = filename.split('.');
    return parts.length > 1 ? parts[parts.length - 1].toLowerCase() : '';
}

// Determine asset type from file
function getAssetType(file: File, metadata: MediaMeta | null = null): 'video' | 'audio' | 'image' {
    const ext = getFileExtension(file.name);
    const videoExts = ['mp4', 'mov', 'avi', 'mkv', 'm4v', 'webm'];
    const audioExts = ['mp3', 'wav', 'aac', 'flac', 'ogg', 'm4a'];
    const imageExts = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp'];

    // Check MIME type first
    if (file.type.startsWith('video/')) return 'video';
    if (file.type.startsWith('audio/')) return 'audio';
    if (file.type.startsWith('image/')) return 'image';

    // Fallback to extension
    if (videoExts.includes(ext)) return 'video';
    if (audioExts.includes(ext)) return 'audio';
    if (imageExts.includes(ext)) return 'image';

    // WebM can be video or audio - check metadata
    if (ext === 'webm' && metadata) {
        if (!metadata.width || !metadata.height) {
            return 'audio';
        }
        return 'video';
    }

    // Default to video for webm
    if (ext === 'webm') return 'video';

    return 'video'; // Default fallback
}

// Generate thumbnail for video using canvas
async function generateVideoThumbnail(file: File, atTime: number = 1): Promise<string> {
    return new Promise((resolve, reject) => {
        const video = document.createElement('video');
        video.preload = 'metadata';
        video.muted = true;
        video.playsInline = true;

        let hasSeeked = false;
        const videoUrl = URL.createObjectURL(file);

        video.onloadedmetadata = () => {
            // Seek to a frame (1 second or 10% of duration, whichever is smaller)
            const seekTime = Math.min(atTime, video.duration * 0.1);
            video.currentTime = seekTime;
        };

        video.onseeked = () => {
            if (hasSeeked) return; // Prevent multiple calls
            hasSeeked = true;
            const canvas = document.createElement('canvas');
            canvas.width = 320;
            canvas.height = 180;
            const ctx = canvas.getContext('2d');

            if (!ctx) {
                reject(new Error('Failed to get canvas context'));
                return;
            }

            // Calculate aspect ratio preserving dimensions
            const videoAspect = video.videoWidth / video.videoHeight;
            const canvasAspect = canvas.width / canvas.height;

            let drawWidth = canvas.width;
            let drawHeight = canvas.height;
            let offsetX = 0;
            let offsetY = 0;

            if (videoAspect > canvasAspect) {
                drawHeight = canvas.width / videoAspect;
                offsetY = (canvas.height - drawHeight) / 2;
            } else {
                drawWidth = canvas.height * videoAspect;
                offsetX = (canvas.width - drawWidth) / 2;
            }

            ctx.fillStyle = '#000';
            ctx.fillRect(0, 0, canvas.width, canvas.height);
            ctx.drawImage(video, offsetX, offsetY, drawWidth, drawHeight);

            canvas.toBlob((blob) => {
                if (blob) {
                    const url = URL.createObjectURL(blob);
                    resolve(url);
                    URL.revokeObjectURL(videoUrl);
                } else {
                    URL.revokeObjectURL(videoUrl);
                    reject(new Error('Failed to create thumbnail blob'));
                }
            }, 'image/jpeg', 0.8);
        };

        video.onerror = (e) => {
            console.error('Video thumbnail error:', e);
            URL.revokeObjectURL(videoUrl);
            reject(new Error('Failed to load video for thumbnail'));
        };

        // Set timeout for video loading
        const timeout = setTimeout(() => {
            if (!hasSeeked) {
                URL.revokeObjectURL(videoUrl);
                reject(new Error('Video thumbnail generation timeout'));
            }
        }, 10000); // 10 second timeout

        video.onloadeddata = () => {
            // Video data loaded, ready to seek
        };

        video.src = videoUrl;
        
        // Wrap resolve to clean up timeout
        const originalResolve = resolve;
        resolve = (value: string | PromiseLike<string>) => {
            clearTimeout(timeout);
            originalResolve(value);
        };
    });
}

// Generate thumbnail for image (resize)
async function generateImageThumbnail(file: File): Promise<string> {
    return new Promise((resolve, reject) => {
        const img = new Image();
        const imageUrl = URL.createObjectURL(file);

        img.onload = () => {
            const canvas = document.createElement('canvas');
            canvas.width = 320;
            canvas.height = 180;
            const ctx = canvas.getContext('2d');

            if (!ctx) {
                URL.revokeObjectURL(imageUrl);
                reject(new Error('Failed to get canvas context'));
                return;
            }

            // Calculate aspect ratio preserving dimensions
            const imgAspect = img.width / img.height;
            const canvasAspect = canvas.width / canvas.height;

            let drawWidth = canvas.width;
            let drawHeight = canvas.height;
            let offsetX = 0;
            let offsetY = 0;

            if (imgAspect > canvasAspect) {
                drawHeight = canvas.width / imgAspect;
                offsetY = (canvas.height - drawHeight) / 2;
            } else {
                drawWidth = canvas.height * imgAspect;
                offsetX = (canvas.width - drawWidth) / 2;
            }

            ctx.fillStyle = '#000';
            ctx.fillRect(0, 0, canvas.width, canvas.height);
            ctx.drawImage(img, offsetX, offsetY, drawWidth, drawHeight);

            canvas.toBlob((blob) => {
                if (blob) {
                    const url = URL.createObjectURL(blob);
                    resolve(url);
                    URL.revokeObjectURL(imageUrl);
                } else {
                    URL.revokeObjectURL(imageUrl);
                    reject(new Error('Failed to create thumbnail blob'));
                }
            }, 'image/jpeg', 0.8);
        };

        img.onerror = () => {
            URL.revokeObjectURL(imageUrl);
            reject(new Error('Failed to load image for thumbnail'));
        };

        img.src = imageUrl;
    });
}

/**
 * Ingest files for browser (using File objects)
 */
export async function ingestFilesBrowser(fileIds: string[]): Promise<IngestResult[]> {
    const results: IngestResult[] = [];

    for (const fileId of fileIds) {
        try {
            // Get file from store
            const file = fileStore.get(fileId);
            if (!file) {
                console.warn(`File not found in store: ${fileId}`);
                continue;
            }

            // Create object URL for the file
            const objectUrl = URL.createObjectURL(file);

            // Store file with both fileId and objectUrl as keys for later retrieval
            fileStore.set(objectUrl, file);

            // Extract metadata using the file directly (more reliable)
            let metadata: MediaMeta;
            try {
                // Use the fileId to get metadata (which uses the File object)
                metadata = await getMediaMetadataWeb(fileId);
            } catch (error) {
                console.error(`Failed to get metadata for ${file.name}:`, error);
                // Create minimal metadata based on file type
                if (file.type.startsWith('video/')) {
                    metadata = {
                        duration_ms: 0,
                        width: undefined,
                        height: undefined,
                        has_audio: true,
                    };
                } else if (file.type.startsWith('audio/')) {
                    metadata = {
                        duration_ms: 0,
                        has_audio: true,
                    };
                } else if (file.type.startsWith('image/')) {
                    metadata = {
                        duration_ms: 0,
                        width: undefined,
                        height: undefined,
                    };
                } else {
                    metadata = {
                        duration_ms: 0,
                        width: undefined,
                        height: undefined,
                    };
                }
            }

            // Determine asset type
            const assetType = getAssetType(file, metadata);

            // For images, set default duration to 5 seconds
            if (assetType === 'image' && metadata.duration_ms === 0) {
                metadata.duration_ms = 5000;
            }

            // Generate thumbnail
            let thumbnailUrl: string | null = null;
            try {
                if (assetType === 'video') {
                    thumbnailUrl = await generateVideoThumbnail(file);
                } else if (assetType === 'image') {
                    thumbnailUrl = await generateImageThumbnail(file);
                }
            } catch (thumbError) {
                console.warn(`Failed to generate thumbnail for ${file.name}:`, thumbError);
                // Continue without thumbnail
            }

            results.push({
                asset_id: objectUrl, // Use object URL as asset ID
                file_path: objectUrl,
                original_file_name: file.name,
                thumbnail_path: thumbnailUrl,
                file_size: file.size,
                metadata,
            });
        } catch (error) {
            console.error(`Error ingesting file ${fileId}:`, error);
            throw error;
        }
    }

    return results;
}

