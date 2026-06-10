import { Injectable, NgZone } from '@angular/core';
import { signal } from '@angular/core';

export interface StatusEvent {
  camera_id: number;
  is_recording: boolean;
}

@Injectable({ providedIn: 'root' })
export class SseService {
  private eventSource: EventSource | null = null;
  private reconnectTimeout: ReturnType<typeof setTimeout> | null = null;
  private listeners: ((event: StatusEvent) => void)[] = [];

  statuses = signal<Record<number, boolean>>({});

  constructor(private zone: NgZone) {}

  connect(): void {
    if (this.eventSource) return;

    this.eventSource = new EventSource('/api/cameras/events/');

    this.eventSource.onmessage = (event) => {
      this.zone.run(() => {
        try {
          const data = JSON.parse(event.data);

          if (Array.isArray(data)) {
            const statuses: Record<number, boolean> = {};
            data.forEach((s: { id: number; is_recording: boolean }) => {
              statuses[s.id] = s.is_recording;
            });
            this.statuses.set(statuses);
          } else if (data.camera_id !== undefined) {
            this.statuses.update((prev) => ({
              ...prev,
              [data.camera_id]: data.is_recording,
            }));
            this.listeners.forEach((cb) => cb(data));
          }
        } catch (e) {
          console.error('SSE parse error:', e);
        }
      });
    };

    this.eventSource.onerror = () => {
      this.disconnect();
      this.reconnectTimeout = setTimeout(() => this.connect(), 3000);
    };
  }

  disconnect(): void {
    if (this.eventSource) {
      this.eventSource.close();
      this.eventSource = null;
    }
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }
  }

  onStatusChange(callback: (event: StatusEvent) => void): () => void {
    this.listeners.push(callback);
    return () => {
      this.listeners = this.listeners.filter((l) => l !== callback);
    };
  }
}
