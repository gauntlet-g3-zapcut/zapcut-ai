import { useState, useEffect } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Upload } from "lucide-react";
import { useProjectStore } from "@/store/projectStore";
import { openFileDialog } from "@/lib/bindings";
import { waitForElectronAPI } from "@/lib/utils";

interface UploadModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onDuplicateDetected?: (filename: string) => void;
}

export function UploadModal({ open, onOpenChange, onDuplicateDetected }: UploadModalProps) {
  const [isUploading, setIsUploading] = useState(false);
  const [apiAvailable, setApiAvailable] = useState(false);
  const [isWebMode, setIsWebMode] = useState(false);
  const { addAssetsFromPaths, assets } = useProjectStore();

  // Check if API is available when modal opens
  useEffect(() => {
    if (open) {
      // Force initialization check
      const checkAPI = () => {
        // Check immediately if API exists (web shim or Electron)
        if (window.electronAPI && typeof window.electronAPI.openFileDialog === 'function') {
          setApiAvailable(true);
          // Check if it's web mode by checking if it's the shim (has web-specific behavior)
          setIsWebMode(typeof (window as any).__WEB_SHIM_INITIALIZED !== 'undefined' ||
            !navigator.userAgent.includes('Electron'));
          return true;
        }
        return false;
      };

      // Check immediately
      if (checkAPI()) {
        return;
      }

      // If not available, try to initialize web shim
      if (typeof (window as any).__WEB_SHIM_INITIALIZED === 'undefined') {
        // Import and initialize web shim dynamically
        import('@/lib/webShim').then(({ initWebShim }) => {
          initWebShim();
          if (checkAPI()) {
            return;
          }
          // Wait a bit more for initialization
          waitForElectronAPI(2000).then((available) => {
            setApiAvailable(available);
            setIsWebMode(available && !navigator.userAgent.includes('Electron'));
          });
        });
      } else {
        // Wait a bit for API to be ready
        waitForElectronAPI(2000).then((available) => {
          setApiAvailable(available);
          setIsWebMode(available && !navigator.userAgent.includes('Electron'));
        });
      }
    }
  }, [open]);

  // Browser-compatible function to extract filename from path
  const getFilename = (filePath: string): string => {
    // Handle both forward slashes (macOS/Linux) and backslashes (Windows)
    // Also handle object URLs (blob: or web-file-*)
    if (filePath.startsWith('blob:') || filePath.startsWith('web-file-')) {
      // For web files, try to get name from store or use the ID
      return filePath.includes('/') ? filePath.split('/').pop() || 'file' : filePath;
    }
    const parts = filePath.replace(/\\/g, '/').split('/');
    return parts[parts.length - 1];
  };

  const handleUploadClick = async () => {
    if (isUploading) return; // Prevent multiple clicks

    setIsUploading(true);
    try {
      // Always try to open file dialog - bindings.ts will handle initialization
      console.log('Opening file dialog...');
      const result = await openFileDialog();
      if (result.filePaths && result.filePaths.length > 0) {
        // Check for duplicates by filename
        const existingFilenames = new Set(assets.map(a => a.name));
        let hasDuplicates = false;

        for (const filePath of result.filePaths) {
          const filename = getFilename(filePath);
          if (existingFilenames.has(filename)) {
            hasDuplicates = true;
            onDuplicateDetected?.(filename);
            break;
          }
        }

        if (!hasDuplicates) {
          await addAssetsFromPaths(result.filePaths);
          onOpenChange(false);
        }
      }
    } catch (error) {
      console.error('Error selecting files:', error);
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      
      // Check if API exists for debugging
      const apiExists = typeof window.electronAPI !== 'undefined';
      const hasFunction = typeof window.electronAPI?.openFileDialog === 'function';
      const shimInitialized = typeof (window as any).__WEB_SHIM_INITIALIZED !== 'undefined';
      
      console.error('File dialog error details:', {
        errorMessage,
        apiExists,
        hasFunction,
        shimInitialized,
        userAgent: navigator.userAgent,
        isElectron: navigator.userAgent.includes('Electron'),
      });
      
      // Show user-friendly error message
      alert(
        `Unable to open file dialog.\n\n` +
        `Error: ${errorMessage}\n\n` +
        `Debug info:\n` +
        `- API exists: ${apiExists}\n` +
        `- Function available: ${hasFunction}\n` +
        `- Web shim initialized: ${shimInitialized}\n\n` +
        `Please ensure:\n` +
        `1. You are using a modern browser (Chrome, Firefox, Safari, Edge)\n` +
        `2. File access is not blocked by browser settings\n` +
        `3. Check the browser console for more details\n` +
        `4. Try refreshing the page if the issue persists`
      );
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-xl min-w-[500px]">
        <DialogHeader>
          <DialogTitle className="text-h3 font-semibold gradient-text">
            Upload Media Files
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-lg py-2">
          {/* Web mode info banner */}
          {isWebMode && (
            <div className="bg-blue-500/20 border border-blue-500/50 rounded-lg p-md text-sm text-blue-200">
              <p className="font-semibold mb-1">🌐 Web Mode</p>
              <p className="text-xs">
                Running in browser. Some features like video export and screen recording require the Electron app.
              </p>
            </div>
          )}

          {/* API availability warning */}
          {!apiAvailable && (
            <div className="bg-yellow-500/20 border border-yellow-500/50 rounded-lg p-md text-sm text-yellow-200">
              <p className="font-semibold mb-1">⚠️ File API not available</p>
              <p className="text-xs">
                Please refresh the page or check your browser settings.
              </p>
            </div>
          )}

          {/* Upload area */}
          <div
            className="border-2 border-dashed rounded-xl p-2xl text-center transition-all duration-200 border-white/30 hover:border-light-blue/50 bg-white/5 hover:bg-white/10 cursor-pointer"
            onClick={handleUploadClick}
          >
            <Upload className="h-16 w-16 text-white/50 mx-auto mb-lg" />
            <p className="text-h4 text-white mb-md font-medium">
              Click to select files
            </p>
            <Button
              variant="gradient"
              size="lg"
              onClick={(e) => {
                e.stopPropagation();
                handleUploadClick();
              }}
              disabled={isUploading}
              className="mb-md"
            >
              Choose Files
            </Button>
            <p className="text-body-small text-white/50 mt-md">
              Supports MP4, MOV, MP3, WAV, JPG, PNG
            </p>
          </div>

          {/* Upload status */}
          {isUploading && (
            <div className="text-center py-4">
              <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-light-blue mb-md"></div>
              <p className="text-body text-white/70">Processing files...</p>
            </div>
          )}

          {/* Actions */}
          <div className="flex justify-end space-x-sm pt-2">
            <Button
              variant="outline"
              onClick={() => onOpenChange(false)}
              disabled={isUploading}
            >
              Cancel
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
