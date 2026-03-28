export interface Recording {
  id: string;
  camera_id: number;
  camera_name: string;
  filename: string;
  path: string;
  start_time: string;
  duration?: number;
  size?: number;
  has_gif: boolean;
}

export interface GifItem {
  id: string;
  camera_id: number;
  camera_name: string;
  filename: string;
  path: string;
  timestamp: string;
  size: number;
}
