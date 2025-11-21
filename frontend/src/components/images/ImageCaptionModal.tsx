import React, { useState, useEffect } from 'react';
import { X, Star } from 'lucide-react';
import type { ImageMetadata } from '../../types/image';

interface ImageCaptionModalProps {
  image: ImageMetadata | null;
  isOpen: boolean;
  onClose: () => void;
  onSave: (imageId: string, caption: string, isPrimary: boolean) => Promise<void>;
}

export const ImageCaptionModal: React.FC<ImageCaptionModalProps> = ({
  image,
  isOpen,
  onClose,
  onSave,
}) => {
  const [caption, setCaption] = useState('');
  const [isPrimary, setIsPrimary] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (image) {
      setCaption(image.caption || '');
      setIsPrimary(image.is_primary);
    }
  }, [image]);

  if (!isOpen || !image) return null;

  const handleSave = async () => {
    try {
      setSaving(true);
      setError('');
      await onSave(image.id, caption, isPrimary);
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save');
    } finally {
      setSaving(false);
    }
  };

  const handleClose = () => {
    if (!saving) {
      setError('');
      onClose();
    }
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black bg-opacity-50 transition-opacity"
        onClick={handleClose}
      />

      {/* Modal */}
      <div className="flex min-h-full items-center justify-center p-4">
        <div className="relative bg-white rounded-lg shadow-xl max-w-2xl w-full p-6">
          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-semibold text-gray-900">Edit Image</h2>
            <button
              onClick={handleClose}
              disabled={saving}
              className="text-gray-400 hover:text-gray-600 transition-colors disabled:opacity-50"
              aria-label="Close"
            >
              <X className="h-6 w-6" />
            </button>
          </div>

          {/* Image Preview */}
          <div className="mb-6">
            <img
              src={image.url}
              alt={image.filename}
              className="w-full h-64 object-contain rounded-lg border border-gray-200 bg-gray-50"
            />
          </div>

          {/* Form */}
          <div className="space-y-4">
            {/* Caption */}
            <div>
              <label htmlFor="caption" className="block text-sm font-medium text-gray-700 mb-2">
                Caption (optional)
              </label>
              <textarea
                id="caption"
                value={caption}
                onChange={(e) => setCaption(e.target.value)}
                placeholder="Add a description for this image..."
                rows={3}
                maxLength={500}
                disabled={saving}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
              />
              <div className="mt-1 text-xs text-gray-500 text-right">
                {caption.length}/500 characters
              </div>
            </div>

            {/* Primary Checkbox */}
            <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
              <input
                type="checkbox"
                id="is_primary"
                checked={isPrimary}
                onChange={(e) => setIsPrimary(e.target.checked)}
                disabled={saving}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded disabled:opacity-50"
              />
              <label htmlFor="is_primary" className="flex items-center gap-2 text-sm font-medium text-gray-700 cursor-pointer">
                <Star className="h-4 w-4 text-yellow-500" />
                Set as primary image
              </label>
            </div>

            {/* Filename */}
            <div className="text-xs text-gray-500">
              <span className="font-medium">Filename:</span> {image.filename}
            </div>
          </div>

          {/* Error */}
          {error && (
            <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
              {error}
            </div>
          )}

          {/* Actions */}
          <div className="mt-6 flex items-center justify-end gap-3">
            <button
              onClick={handleClose}
              disabled={saving}
              className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Cancel
            </button>
            <button
              onClick={handleSave}
              disabled={saving}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              {saving ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                  Saving...
                </>
              ) : (
                'Save Changes'
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
