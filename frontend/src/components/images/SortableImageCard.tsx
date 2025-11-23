import React from 'react';
import { useSortable } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { ImageCard } from './ImageCard';
import type { ImageMetadata } from '../../types/image';

interface SortableImageCardProps {
  image: ImageMetadata;
  onDelete?: (imageId: string) => void;
  onClick?: (imageId: string) => void;
  onSetPrimary?: (imageId: string) => void;
  disabled?: boolean;
}

export const SortableImageCard: React.FC<SortableImageCardProps> = ({
  image,
  onDelete,
  onClick,
  onSetPrimary,
  disabled = false,
}) => {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({
    id: image.id,
    disabled,
  });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.4 : 1,
    cursor: disabled ? 'default' : 'grab',
  };

  return (
    <div
      ref={setNodeRef}
      style={style}
      className={`
        rounded-lg
        ${isDragging ? 'z-50 shadow-2xl' : ''}
        ${!disabled ? 'touch-none' : ''}
      `}
      {...attributes}
      {...listeners}
    >
      <ImageCard
        image={image}
        onDelete={onDelete}
        onClick={onClick}
        onSetPrimary={onSetPrimary}
        showActions={!isDragging}
      />
    </div>
  );
};
