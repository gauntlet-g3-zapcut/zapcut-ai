import { contextBridge, ipcRenderer } from 'electron';
import {
  MediaMetadata,
  ExportSettings,
  ExportResult,
  ProgressEvent,
  ListDevicesResult,
  RecordSettings,
  IngestRequest,
  IngestResult,
  GenerateImageResult,
} from './types';

/**
 * Expose protected methods to renderer process via context bridge
 */
contextBridge.exposeInMainWorld('electronAPI', {
  // Media operations
  getMediaMetadata: (path: string): Promise<MediaMetadata> =>
    ipcRenderer.invoke('get-media-metadata', path),
  
  applyEdits: (projectJson: string): Promise<{ success: boolean }> =>
    ipcRenderer.invoke('apply-edits', projectJson),
  
  generatePreview: (projectJson: string, atMs: number): Promise<{ url: string; ts: number }> =>
    ipcRenderer.invoke('generate-preview', projectJson, atMs),
  
  exportProject: (projectJson: string, settings: ExportSettings): Promise<ExportResult> =>
    ipcRenderer.invoke('export-project', projectJson, settings),
  
  // File ingestion
  ingestFiles: (request: IngestRequest): Promise<IngestResult[]> =>
    ipcRenderer.invoke('ingest-files', request),
  
  // File dialog
  openFileDialog: (): Promise<{ filePaths: string[] }> =>
    ipcRenderer.invoke('open-file-dialog'),
  
  // Save blob to file
  saveBlobToFile: (blobData: ArrayBuffer, filePath: string): Promise<{ success: boolean; path: string }> =>
    ipcRenderer.invoke('save-blob-to-file', blobData, filePath),
  
  // Reveal file in Finder/Explorer
  revealInFinder: (filePath: string): Promise<{ success: boolean }> =>
    ipcRenderer.invoke('reveal-in-finder', filePath),
  
  // Delete file
  deleteFile: (filePath: string): Promise<{ success: boolean }> =>
    ipcRenderer.invoke('delete-file', filePath),
  
  // AI Image Generation
  generateImage: (prompt: string): Promise<GenerateImageResult> =>
    ipcRenderer.invoke('generate-image', prompt),
  
  // Screen recording
  listCaptureDevices: (): Promise<ListDevicesResult> =>
    ipcRenderer.invoke('list-capture-devices'),
  startScreenRecord: (settings: RecordSettings): Promise<{ recordingId: string; outPath: string }> =>
    ipcRenderer.invoke('start-screen-record', settings),
  stopScreenRecord: (recordingId: string): Promise<string> =>
    ipcRenderer.invoke('stop-screen-record', recordingId),
  
  // Progress events
  onExportProgress: (callback: (event: ProgressEvent) => void): (() => void) => {
    const listener = (_event: Electron.IpcRendererEvent, data: ProgressEvent) => callback(data);
    ipcRenderer.on('export-progress', listener);
    
    // Return cleanup function
    return () => {
      ipcRenderer.removeListener('export-progress', listener);
    };
  },
  
  // Screen recording events
  onStartRecording: (callback: (event: { recordingId: string; sourceId: string; outputPath: string; settings: RecordSettings }) => void): (() => void) => {
    const listener = (_event: Electron.IpcRendererEvent, data: { recordingId: string; sourceId: string; outputPath: string; settings: RecordSettings }) => callback(data);
    ipcRenderer.on('start-recording', listener);
    
    // Return cleanup function
    return () => {
      ipcRenderer.removeListener('start-recording', listener);
    };
  },
  
  onStopRecording: (callback: (event: { recordingId: string }) => void): (() => void) => {
    const listener = (_event: Electron.IpcRendererEvent, data: { recordingId: string }) => callback(data);
    ipcRenderer.on('stop-recording', listener);
    
    // Return cleanup function
    return () => {
      ipcRenderer.removeListener('stop-recording', listener);
    };
  },
});

