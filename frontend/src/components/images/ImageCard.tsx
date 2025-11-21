import React from 'react';
import { Star, Trash2 } from 'lucide-react';
import type { ImageMetadata } from '../../types/image';

interface ImageCardProps {
  image: ImageMetadata;
  onDelete?: (imageId: string) => void;
  onClick?: (imageId: string) => void;
  onSetPrimary?: (imageId: string) => void;
  showActions?: boolean;
  className?: string;
}

export const ImageCard: React.FC<ImageCardProps> = ({
  image,
  onDelete,
  onClick,
  onSetPrimary,
  showActions = true,
  className = '',
}) => {
  const handleClick = (e: React.MouseEvent) => {
    // Don't trigger if clicking on action buttons
    if ((e.target as HTMLElement).closest('button')) {
      return;
    }
    if (onClick) {
      onClick(image.id);
    }
  };

  return (
    <div className={`relative group ${className}`}>
      {/* Image */}
      <div
        className="relative aspect-square rounded-lg overflow-hidden border-2 border-gray-200 hover:border-gray-300 transition-colors cursor-pointer"
        onClick={handleClick}
      >
        <img
          src={image.url}
          alt={image.caption || image.filename}
          className="w-full h-full object-cover"
        />

        {/* Primary Badge - Glassmorphic Star */}
        {image.is_primary && (
          <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
            <div className="backdrop-blur-md bg-gradient-to-br from-white/25 to-black/25 rounded-full p-4 shadow-2xl border border-white/50 ring-1 ring-black/20">
              <Star className="h-10 w-10 text-white fill-white/40 drop-shadow-[0_2px_12px_rgba(0,0,0,0.8)]" />
            </div>
          </div>
        )}

        {/* Actions Overlay */}
        {showActions && (
          <div className="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-40 transition-all duration-200 flex items-center justify-center gap-2 opacity-0 group-hover:opacity-100">
            {onSetPrimary && !image.is_primary && (
              <button
                onClick={() => onSetPrimary(image.id)}
                className="p-2 bg-white text-yellow-600 rounded-full hover:bg-yellow-50 transition-colors shadow-lg"
                aria-label="Set as primary"
                title="Set as primary image"
              >
                <Star className="h-4 w-4" />
              </button>
            )}

            {/* Only show delete button if NOT primary */}
            {onDelete && !image.is_primary && (
              <button
                onClick={() => onDelete(image.id)}
                className="p-2 bg-white text-red-600 rounded-full hover:bg-red-50 transition-colors shadow-lg"
                aria-label="Delete image"
                title="Delete image"
              >
                <Trash2 className="h-4 w-4" />
              </button>
            )}
          </div>
        )}
      </div>

      {/* Caption */}
      {image.caption && (
        <div className="mt-2 px-1">
          <p className="text-sm text-gray-700 line-clamp-2">{image.caption}</p>
        </div>
      )}

      {/* Filename (if no caption) */}
      {!image.caption && (
        <div className="mt-2 px-1">
          <p className="text-xs text-gray-500 truncate">{image.filename}</p>
        </div>
      )}
    </div>
  );
};
