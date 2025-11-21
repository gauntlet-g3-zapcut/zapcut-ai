/**
 * Brand type definitions
 */

import { ImageMetadata } from './image';

export interface Brand {
  id: string;
  title: string;
  description: string;
  product_image_1_url?: string;  // Legacy - for backward compatibility
  product_image_2_url?: string;  // Legacy - for backward compatibility
  images: ImageMetadata[];  // New: array of image metadata
  created_at: string;
  campaign_count: number;
}

export interface CreateBrandRequest {
  title: string;
  description: string;
  images: File[];  // Multiple images
}

export interface UpdateBrandRequest {
  title: string;
  description: string;
}
