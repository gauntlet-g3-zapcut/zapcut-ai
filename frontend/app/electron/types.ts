// Shared type definitions for Electron main process

import { BrowserWindow } from 'electron';
import { ChildProcess } from 'child_process';

export interface MediaMetadata {
  duration_ms: number;
  width: number | null;
  height: number | null;
  has_audio: boolean | null;
  codec_video: string | null;
  codec_audio: string | null;
  rotation_deg: number | null;
}

export interface ExportSettings {
  format: 'mp4' | 'mov';
  width: number;
  height: number;
  fps?: number;
  bitrate: number;
  filename?: string;
}

export interface ExportResult {
  path: string;
  duration_ms: number;
  size_bytes: number;
}

export interface ProgressEvent {
  phase: string;
  current: number;
  total: number;
  message: string;
}

export interface DisplayDevice {
  id: string;
  name: string;
  thumbnail: string;
  index: number;
}

export interface ListDevicesResult {
  displays: DisplayDevice[];
  audio_inputs: string[];
}

export interface RecordSettings {
  display_index?: number;
  audio_index?: number;
  fps?: number;
}

export interface RecordingInfo {
  source: Electron.DesktopCapturerSource;
  outputPath: string;
  startTime: number;
  settings: RecordSettings;
}

export interface IngestRequest {
  file_paths: string[];
}

export interface IngestResult {
  asset_id: string;
  file_path: string;
  original_file_name: string;
  thumbnail_path: string | null;
  file_size: number;
  metadata: MediaMetadata;
}

export interface GenerateImageResult {
  success: boolean;
  path: string;
}

export interface ProjectJson {
  id: string;
  assets?: Record<string, any>;
  clips?: Record<string, any>;
  tracks?: Record<string, any>;
  canvasNodes?: Record<string, any>;
}

export interface SeqClip {
  srcPath: string;
  inMs: number;
  outMs: number;
  startMs: number;
  endMs: number;
  assetWidth?: number;
  assetHeight?: number;
  canvasNode?: {
    x: number;
    y: number;
    width: number;
    height: number;
    rotation: number;
    opacity: number;
  };
}

export interface EditPlan {
  id: string;
  mainTrack: SeqClip[];
  overlayTrack: SeqClip[];
}

export type TrackProcessFn = (process: ChildProcess) => void;

