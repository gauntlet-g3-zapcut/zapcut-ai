"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const electron_1 = require("electron");
/**
 * Expose protected methods to renderer process via context bridge
 */
electron_1.contextBridge.exposeInMainWorld('electronAPI', {
    // Media operations
    getMediaMetadata: (path) => electron_1.ipcRenderer.invoke('get-media-metadata', path),
    applyEdits: (projectJson) => electron_1.ipcRenderer.invoke('apply-edits', projectJson),
    generatePreview: (projectJson, atMs) => electron_1.ipcRenderer.invoke('generate-preview', projectJson, atMs),
    exportProject: (projectJson, settings) => electron_1.ipcRenderer.invoke('export-project', projectJson, settings),
    // File ingestion
    ingestFiles: (request) => electron_1.ipcRenderer.invoke('ingest-files', request),
    // File dialog
    openFileDialog: () => electron_1.ipcRenderer.invoke('open-file-dialog'),
    // Save blob to file
    saveBlobToFile: (blobData, filePath) => electron_1.ipcRenderer.invoke('save-blob-to-file', blobData, filePath),
    // Reveal file in Finder/Explorer
    revealInFinder: (filePath) => electron_1.ipcRenderer.invoke('reveal-in-finder', filePath),
    // Delete file
    deleteFile: (filePath) => electron_1.ipcRenderer.invoke('delete-file', filePath),
    // AI Image Generation
    generateImage: (prompt) => electron_1.ipcRenderer.invoke('generate-image', prompt),
    // Screen recording
    listCaptureDevices: () => electron_1.ipcRenderer.invoke('list-capture-devices'),
    startScreenRecord: (settings) => electron_1.ipcRenderer.invoke('start-screen-record', settings),
    stopScreenRecord: (recordingId) => electron_1.ipcRenderer.invoke('stop-screen-record', recordingId),
    // Progress events
    onExportProgress: (callback) => {
        const listener = (_event, data) => callback(data);
        electron_1.ipcRenderer.on('export-progress', listener);
        // Return cleanup function
        return () => {
            electron_1.ipcRenderer.removeListener('export-progress', listener);
        };
    },
    // Screen recording events
    onStartRecording: (callback) => {
        const listener = (_event, data) => callback(data);
        electron_1.ipcRenderer.on('start-recording', listener);
        // Return cleanup function
        return () => {
            electron_1.ipcRenderer.removeListener('start-recording', listener);
        };
    },
    onStopRecording: (callback) => {
        const listener = (_event, data) => callback(data);
        electron_1.ipcRenderer.on('stop-recording', listener);
        // Return cleanup function
        return () => {
            electron_1.ipcRenderer.removeListener('stop-recording', listener);
        };
    },
});
//# sourceMappingURL=preload.js.map