import { Injectable, signal, computed, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';
import { Camera, CameraCreate } from '../models/camera.model';
import { GifItem, Recording } from '../models/recording.model';

@Injectable({ providedIn: 'root' })
export class ApiService {
  private baseUrl = '/api';
  private http = inject(HttpClient);

  getCameras() {
    return firstValueFrom(this.http.get<Camera[]>(`${this.baseUrl}/cameras`));
  }

  createCamera(data: CameraCreate) {
    return firstValueFrom(this.http.post<Camera>(`${this.baseUrl}/cameras`, data));
  }

  deleteCamera(id: number) {
    return firstValueFrom(this.http.delete<void>(`${this.baseUrl}/cameras/${id}`));
  }

  startRecording(id: number) {
    return firstValueFrom(this.http.post<void>(`${this.baseUrl}/cameras/${id}/start`, {}));
  }

  stopRecording(id: number) {
    return firstValueFrom(this.http.post<void>(`${this.baseUrl}/cameras/${id}/stop`, {}));
  }

  getRecordings(params?: { camera_id?: number; date?: string; page?: number; page_size?: number }) {
    const searchParams = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined) {
          searchParams.set(key, value.toString());
        }
      });
    }
    const url = `${this.baseUrl}/recordings${searchParams.toString() ? '?' + searchParams : ''}`;
    return firstValueFrom(this.http.get<Recording[]>(url));
  }

  getGifs(params?: { camera_id?: number }) {
    const searchParams = new URLSearchParams();
    if (params?.camera_id) {
      searchParams.set('camera_id', params.camera_id.toString());
    }
    const url = `${this.baseUrl}/recordings/gifs/list${searchParams.toString() ? '?' + searchParams : ''}`;
    return firstValueFrom(this.http.get<GifItem[]>(url));
  }

  deleteRecording(id: string) {
    return firstValueFrom(this.http.delete<void>(`${this.baseUrl}/recordings/${id}`));
  }

  cleanupOldRecordings(days: number) {
    return firstValueFrom(this.http.delete<void>(`${this.baseUrl}/recordings/cleanup/${days}`));
  }

  getGifUrl(id: string): string {
    return `/api/recordings/gifs/${id}/file`;
  }

  getDownloadUrl(id: string): string {
    return `/api/recordings/${id}/download`;
  }

  login(username: string, password: string) {
    const body = new URLSearchParams();
    body.set('username', username);
    body.set('password', password);
    return firstValueFrom(this.http.post<{ username: string }>(`${this.baseUrl}/auth/login`, body.toString(), {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    }));
  }

  logout() {
    return firstValueFrom(this.http.post<void>(`${this.baseUrl}/auth/logout`, {}));
  }

  checkAuth() {
    return firstValueFrom(this.http.get<{ username: string }>(`${this.baseUrl}/auth/me`));
  }
}
