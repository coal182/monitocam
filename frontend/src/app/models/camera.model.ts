export interface Camera {
  id: number;
  name: string;
  rtsp_url: string;
  enabled: boolean;
  status: string;
  created_at?: string;
}

export interface CameraCreate {
  name: string;
  rtsp_url: string;
  enabled?: boolean;
}
