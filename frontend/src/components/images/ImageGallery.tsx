import React from 'react';
import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  DragEndEvent,
  DragStartEvent,
  DragOverlay,
} from '@dnd-kit/core';
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  rectSortingStrategy,
} from '@dnd-kit/sortable';
import { ImageCard } from './ImageCard';
import { SortableImageCard } from './SortableImageCard';
import { AlertCircle, Plus, Trash2 } from 'lucide-react';
import type { ImageMetadata } from '../../types/image';

interface ImageGalleryProps {
  images: ImageMetadata[];
  onDelete?: (imageId: string) => void;
  onImageClick?: (imageId: string) => void;
  onSetPrimary?: (imageId: string) => void;
  onReorder?: (imageIds: string[]) => void;
  onAddMore?: () => void;
  onDeleteAll?: () => void;
  maxImages?: number;
  entityType?: 'brand' | 'campaign';
  loading?: boolean;
  error?: string;
}

export const ImageGallery: React.FC<ImageGalleryProps> = ({
  images,
  onDelete,
  onImageClick,
  onSetPrimary,
  onReorder,
  onAddMore,
  onDeleteAll,
  maxImages,
  entityType = 'brand',
  loading = false,
  error,
}) => {
  const [activeId, setActiveId] = React.useState<string | null>(null);
  const [showDeleteAllConfirm, setShowDeleteAllConfirm] = React.useState(false);

  const handleDeleteAllClick = () => {
    setShowDeleteAllConfirm(true);
  };

  const handleConfirmDeleteAll = () => {
    if (onDeleteAll) {
      onDeleteAll();
    }
    setShowDeleteAllConfirm(false);
  };

  const handleCancelDeleteAll = () => {
    setShowDeleteAllConfirm(false);
  };

  // Sort images: primary first, then by order
  const sortedImages = [...images].sort((a, b) => {
    // Primary image always comes first
    if (a.is_primary) return -1;
    if (b.is_primary) return 1;
    return a.order - b.order;
  });

  // Separate primary and non-primary images
  const primaryImage = sortedImages.find((img) => img.is_primary);
  const nonPrimaryImages = sortedImages.filter((img) => !img.is_primary);

  const canAddMore = maxImages ? images.length < maxImages : true;

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        distance: 8, // 8px movement required before drag starts
      },
    }),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  );

  const handleDragStart = (event: DragStartEvent) => {
    setActiveId(event.active.id as string);
    console.log('[ImageGallery] Drag start:', event.active.id);
  };

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;

    console.log('[ImageGallery] Drag end:', { active: active.id, over: over?.id });

    if (over && active.id !== over.id) {
      // Find indices in the non-primary array
      const oldIndex = nonPrimaryImages.findIndex((img) => img.id === active.id);
      const newIndex = nonPrimaryImages.findIndex((img) => img.id === over.id);

      // Reorder only the non-primary images
      const reorderedNonPrimary = arrayMove(nonPrimaryImages, oldIndex, newIndex);

      // Reconstruct full array: primary first, then reordered non-primary
      const fullReorderedArray = primaryImage
        ? [primaryImage, ...reorderedNonPrimary]
        : reorderedNonPrimary;

      const newImageIds = fullReorderedArray.map((img) => img.id);

      console.log('[ImageGallery] Reordered:', newImageIds);

      if (onReorder) {
        onReorder(newImageIds);
      }
    }

    setActiveId(null);
  };

  const handleDragCancel = () => {
    setActiveId(null);
  };

  const activeImage = activeId ? sortedImages.find((img) => img.id === activeId) : null;

  if (loading) {
    return (
      <div className="flex items-center justify-center h-48">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center gap-2 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
        <AlertCircle className="h-5 w-5 flex-shrink-0" />
        <p>{error}</p>
      </div>
    );
  }

  if (images.length === 0) {
    return (
      <div className="text-center py-12 border-2 border-dashed border-gray-300 rounded-lg">
        <p className="text-gray-500 mb-4">No images yet</p>
        {onAddMore && canAddMore && (
          <button
            onClick={onAddMore}
            className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            <Plus className="h-4 w-4" />
            Add Images
          </button>
        )}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">
            Images ({images.length}{maxImages ? `/${maxImages}` : ''})
          </h3>
          {onReorder && (
            <p className="text-sm text-gray-500 mt-1">
              Drag and drop to reorder
            </p>
          )}
        </div>

        <div className="flex items-center gap-2">
          {onDeleteAll && images.length > 0 && (
            <button
              onClick={handleDeleteAllClick}
              className="inline-flex items-center gap-2 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors text-sm"
            >
              <Trash2 className="h-4 w-4" />
              Delete All
            </button>
          )}
          {onAddMore && canAddMore && (
            <button
              onClick={onAddMore}
              className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm"
            >
              <Plus className="h-4 w-4" />
              Add More
            </button>
          )}
        </div>
      </div>

      {/* Gallery Grid with DndKit */}
      <DndContext
        sensors={sensors}
        collisionDetection={closestCenter}
        onDragStart={handleDragStart}
        onDragEnd={handleDragEnd}
        onDragCancel={handleDragCancel}
      >
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
          {/* Primary Image - Non-draggable, always first */}
          {primaryImage && (
            <ImageCard
              image={primaryImage}
              onDelete={onDelete}
              onClick={onImageClick}
              onSetPrimary={onSetPrimary}
              showActions={true}
            />
          )}

          {/* Non-Primary Images - Draggable */}
          <SortableContext
            items={nonPrimaryImages.map((img) => img.id)}
            strategy={rectSortingStrategy}
          >
            {nonPrimaryImages.map((image) => (
              <SortableImageCard
                key={image.id}
                image={image}
                onDelete={onDelete}
                onClick={onImageClick}
                onSetPrimary={onSetPrimary}
                disabled={!onReorder}
              />
            ))}
          </SortableContext>
        </div>

        {/* Drag Overlay - shows the dragged item following cursor */}
        <DragOverlay>
          {activeImage ? (
            <div className="opacity-90 rotate-3 scale-105">
              <ImageCard
                image={activeImage}
                showActions={false}
              />
            </div>
          ) : null}
        </DragOverlay>
      </DndContext>

      {/* Info */}
      {maxImages && (
        <div className="text-sm text-gray-500 text-center pt-2">
          {images.length === maxImages ? (
            <span className="text-yellow-600 font-medium">Maximum images reached</span>
          ) : (
            <span>{maxImages - images.length} slots remaining</span>
          )}
        </div>
      )}

      {/* Delete All Confirmation Modal */}
      {showDeleteAllConfirm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-2xl max-w-md w-full p-6 space-y-4">
            <div className="flex items-start gap-3">
              <div className="flex-shrink-0 w-10 h-10 bg-red-100 rounded-full flex items-center justify-center">
                <AlertCircle className="h-6 w-6 text-red-600" />
              </div>
              <div className="flex-1">
                <h3 className="text-lg font-semibold text-gray-900">
                  Delete All Images?
                </h3>
                <p className="text-sm text-gray-600 mt-1">
                  Are you sure you want to delete all {images.length} image{images.length !== 1 ? 's' : ''}?
                  This action cannot be undone.
                </p>
              </div>
            </div>

            <div className="flex gap-3 justify-end pt-2">
              <button
                onClick={handleCancelDeleteAll}
                className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors text-sm font-medium"
              >
                Cancel
              </button>
              <button
                onClick={handleConfirmDeleteAll}
                className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors text-sm font-medium"
              >
                Delete All
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
