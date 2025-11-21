import React, { useState, useRef } from 'react';
import { Upload, X, AlertCircle } from 'lucide-react';
import { MAX_BRAND_IMAGES, MAX_CAMPAIGN_IMAGES, MAX_IMAGE_SIZE_MB, ALLOWED_IMAGE_TYPES } from '../../types/image';

interface ImageUploaderProps {
  entityType: 'brand' | 'campaign';
  currentImageCount?: number;
  onFilesSelected: (files: File[]) => void;
  maxImages?: number;
  disabled?: boolean;
}

interface PreviewImage {
  file: File;
  preview: string;
  error?: string;
}

export const ImageUploader: React.FC<ImageUploaderProps> = ({
  entityType,
  currentImageCount = 0,
  onFilesSelected,
  maxImages,
  disabled = false,
}) => {
  const [previews, setPreviews] = useState<PreviewImage[]>([]);
  const [dragActive, setDragActive] = useState(false);
  const [error, setError] = useState<string>('');
  const fileInputRef = useRef<HTMLInputElement>(null);

  const maxAllowed = maxImages || (entityType === 'brand' ? MAX_BRAND_IMAGES : MAX_CAMPAIGN_IMAGES);
  const remainingSlots = maxAllowed - currentImageCount;

  const validateFile = (file: File): string | null => {
    // Check file type
    if (!ALLOWED_IMAGE_TYPES.includes(file.type)) {
      return `${file.name}: Invalid file type. Only JPG, PNG, and WebP are allowed.`;
    }

    // Check file size
    const maxSizeBytes = MAX_IMAGE_SIZE_MB * 1024 * 1024;
    if (file.size > maxSizeBytes) {
      return `${file.name}: File too large. Maximum size is ${MAX_IMAGE_SIZE_MB}MB.`;
    }

    return null;
  };

  const handleFiles = (files: FileList | null) => {
    if (!files || files.length === 0) return;

    setError('');
    const fileArray = Array.from(files);

    // Check total count
    if (fileArray.length > remainingSlots) {
      setError(`Can only add ${remainingSlots} more image(s). Maximum is ${maxAllowed} total.`);
      return;
    }

    // Validate each file
    const validatedFiles: PreviewImage[] = [];
    let hasErrors = false;

    fileArray.forEach((file) => {
      const error = validateFile(file);
      if (error) {
        hasErrors = true;
        setError(error);
        return;
      }

      const preview = URL.createObjectURL(file);
      validatedFiles.push({ file, preview });
    });

    if (!hasErrors && validatedFiles.length > 0) {
      setPreviews((prev) => {
        const newPreviews = [...prev, ...validatedFiles];
        // Pass ALL accumulated files to parent, not just the new ones
        onFilesSelected(newPreviews.map((p) => p.file));
        return newPreviews;
      });
    }
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (disabled) return;
    handleFiles(e.dataTransfer.files);
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    e.preventDefault();
    if (disabled) return;
    handleFiles(e.target.files);
  };

  const removePreview = (index: number) => {
    setPreviews((prev) => {
      const newPreviews = [...prev];
      URL.revokeObjectURL(newPreviews[index].preview);
      newPreviews.splice(index, 1);
      return newPreviews;
    });

    // Update parent with remaining files
    const remainingFiles = previews.filter((_, i) => i !== index).map((p) => p.file);
    onFilesSelected(remainingFiles);
  };

  const handleButtonClick = () => {
    fileInputRef.current?.click();
  };

  // Cleanup previews on unmount
  React.useEffect(() => {
    return () => {
      previews.forEach((preview) => URL.revokeObjectURL(preview.preview));
    };
  }, []);

  return (
    <div className="w-full">
      {/* Upload Zone */}
      <div
        className={`
          relative border-2 border-dashed rounded-lg p-8 text-center transition-colors
          ${dragActive ? 'border-blue-500 bg-blue-50' : 'border-gray-300'}
          ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer hover:border-gray-400'}
        `}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onClick={disabled ? undefined : handleButtonClick}
      >
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept={ALLOWED_IMAGE_TYPES.join(',')}
          onChange={handleChange}
          className="hidden"
          disabled={disabled}
        />

        <Upload className="mx-auto h-12 w-12 text-gray-400" />
        <p className="mt-2 text-sm text-gray-600">
          <span className="font-semibold">Click to upload</span> or drag and drop
        </p>
        <p className="text-xs text-gray-500 mt-1">
          JPG, PNG, or WebP (max {MAX_IMAGE_SIZE_MB}MB per image)
        </p>
        <p className="text-xs text-gray-500 mt-1">
          {remainingSlots} of {maxAllowed} slots available
        </p>
      </div>

      {/* Error Message */}
      {error && (
        <div className="mt-4 flex items-center gap-2 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
          <AlertCircle className="h-4 w-4 flex-shrink-0" />
          <p>{error}</p>
        </div>
      )}

      {/* Previews */}
      {previews.length > 0 && (
        <div className="mt-6">
          <h4 className="text-sm font-medium text-gray-700 mb-3">
            Selected Images ({previews.length})
          </h4>
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4">
            {previews.map((preview, index) => (
              <div key={index} className="relative group">
                <img
                  src={preview.preview}
                  alt={`Preview ${index + 1}`}
                  className="w-full h-32 object-cover rounded-lg border border-gray-200"
                />
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    removePreview(index);
                  }}
                  className="absolute top-1 right-1 p-1 bg-red-500 text-white rounded-full opacity-0 group-hover:opacity-100 transition-opacity"
                  aria-label="Remove image"
                >
                  <X className="h-4 w-4" />
                </button>
                <div className="mt-1 text-xs text-gray-500 truncate">
                  {preview.file.name}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
