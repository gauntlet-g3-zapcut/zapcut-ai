/**
 * Image metadata type definitions
 */

export interface ImageMetadata {
  id: string;
  url: string;
  filename: string;
  uploaded_at: string;
  size_bytes: number;
  order: number;
  caption: string;
  is_primary: boolean;
}

export interface ImageUploadResponse {
  uploaded_count: number;
  failed_count: number;
  images: ImageMetadata[];
  failures?: {
    filename: string;
    error: string;
  }[];
}

export interface UpdateImageMetadataRequest {
  caption?: string;
  is_primary?: boolean;
}

export interface ReorderImagesRequest {
  image_ids: string[];
}

export const MAX_BRAND_IMAGES = 10;
export const MAX_CAMPAIGN_IMAGES = 20;
export const MAX_IMAGE_SIZE_MB = 10;
export const ALLOWED_IMAGE_TYPES = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp'];
