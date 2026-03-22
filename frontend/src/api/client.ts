import axios from 'axios'

const API_BASE = '/api'

export const api = axios.create({
  baseURL: API_BASE,
  withCredentials: true
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401 && window.location.pathname !== '/login') {
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export interface Camera {
  id: number
  name: string
  rtsp_url: string
  enabled: boolean
  status: string
  created_at?: string
}

export interface Recording {
  id: string
  camera_id: number
  camera_name: string
  filename: string
  path: string
  start_time: string
  duration?: number
  size?: number
  has_gif: boolean
}

export const camerasApi = {
  list: () => api.get<Camera[]>('/cameras'),
  create: (data: { name: string; rtsp_url: string; enabled?: boolean }) =>
    api.post<Camera>('/cameras', data),
  delete: (id: number) => api.delete(`/cameras/${id}`),
  startRecording: (id: number) => api.post(`/cameras/${id}/start`),
  stopRecording: (id: number) => api.post(`/cameras/${id}/stop`)
}

export interface GifItem {
  id: string
  camera_id: number
  camera_name: string
  filename: string
  path: string
  timestamp: string
  size: number
}

export const recordingsApi = {
  list: (params?: { camera_id?: number; date?: string; page?: number; page_size?: number }) =>
    api.get<Recording[]>('/recordings', { params }),
  listGifs: (params?: { camera_id?: number }) =>
    api.get<GifItem[]>('/recordings/gifs/list', { params }),
  delete: (id: string) => api.delete(`/recordings/${id}`),
  getGifUrl: (id: string) => `/api/recordings/gifs/${id}/file`,
  getDownloadUrl: (id: string) => `/api/recordings/${id}/download`,
  getStreamUrl: (id: string) => `/api/recordings/${id}/stream`
}
