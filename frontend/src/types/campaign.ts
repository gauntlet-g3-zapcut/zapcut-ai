/**
 * Campaign form types
 */

import { ImageMetadata } from './image';

export type QuestionId = "style" | "audience" | "emotion" | "pacing" | "colors"

export interface Question {
  id: QuestionId
  question: string
  options: readonly string[]
}

export interface CampaignAnswers {
  style?: string
  audience?: string
  emotion?: string
  pacing?: string
  colors?: string
  generation_mode?: string
  video_resolution?: string
  video_model?: string
  ideas?: string
}

export interface SubmitCampaignAnswersResponse {
  creative_bible_id: string
  message: string
}

export interface CampaignPreferences {
  style: string
  audience: string
  emotion: string
  pacing: string
  colors: string
  generation_mode: string
  video_resolution: string
  video_model: string
  ideas?: string
  [key: string]: string | undefined
}

export interface Campaign {
  id: string;
  brand_id: string;
  brand_title: string;
  status: string;
  final_video_url?: string;
  images: ImageMetadata[];  // Reference/inspiration images
  created_at: string;
  video_urls_count: number;
}
