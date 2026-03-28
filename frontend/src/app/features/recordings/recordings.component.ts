import { Component, OnInit, OnDestroy, signal, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../services/api.service';
import { Camera } from '../../models/camera.model';
import { GifItem } from '../../models/recording.model';

@Component({
  selector: 'app-recordings',
  standalone: true,
  imports: [FormsModule],
  templateUrl: './recordings.component.html',
  styleUrl: './recordings.component.css'
})
export class RecordingsComponent implements OnInit, OnDestroy {
  private api = inject(ApiService);

  gifs = signal<GifItem[]>([]);
  cameras = signal<Camera[]>([]);
  loading = signal(false);
  selectedCamera: number | null = null;
  selectedGif = signal<GifItem | null>(null);
  autoRefresh = signal(true);
  private refreshInterval: ReturnType<typeof setInterval> | null = null;

  ngOnInit(): void {
    this.loadCameras();
    this.loadGifs();
    this.startAutoRefresh();
  }

  ngOnDestroy(): void {
    this.stopAutoRefresh();
  }

  loadGifs(): void {
    this.loading.set(true);
    const params = this.selectedCamera ? { camera_id: this.selectedCamera } : undefined;
    this.api.getGifs(params)
      .then(data => {
        this.gifs.set(data);
        this.loading.set(false);
      })
      .catch(() => this.loading.set(false));
  }

  loadCameras(): void {
    this.api.getCameras()
      .then(data => this.cameras.set(data));
  }

  deleteGif(gif: GifItem, event: Event): void {
    event.stopPropagation();
    if (!confirm(`Eliminar grabación ${gif.filename}?`)) return;
    this.api.deleteRecording(gif.id)
      .then(() => this.loadGifs());
  }

  cleanupOldRecordings(): void {
    const days = prompt('Eliminar grabaciones de hace cuántos días?', '7');
    if (!days) return;
    const daysNum = parseInt(days, 10);
    if (isNaN(daysNum) || daysNum < 1) {
      alert('Por favor ingresa un número válido de días');
      return;
    }
    if (!confirm(`Eliminar todas las grabaciones de hace más de ${daysNum} días?`)) return;
    this.api.cleanupOldRecordings(daysNum)
      .then(() => this.loadGifs())
      .catch(err => alert('Error al limpiar grabaciones: ' + err.message));
  }

  formatSize(bytes: number): string {
    if (!bytes) return '0 B';
    const units = ['B', 'KB', 'MB'];
    let i = 0;
    while (bytes >= 1024 && i < units.length - 1) {
      bytes /= 1024;
      i++;
    }
    return `${bytes.toFixed(1)} ${units[i]}`;
  }

  formatTimestamp(ts: string): string {
    if (!ts) return '';
    const parts = ts.split('_');
    if (parts.length >= 2) {
      const date = parts[parts.length - 2];
      const time = parts[parts.length - 1].replace('-', ':');
      return `${date} ${time}`;
    }
    return ts.replace(/_/g, ' ');
  }

  getGifUrl(id: string): string {
    return this.api.getGifUrl(id);
  }

  getDownloadUrl(id: string): string {
    return this.api.getDownloadUrl(id);
  }

  openVideo(gif: GifItem): void {
    this.selectedGif.set(gif);
  }

  closeVideo(): void {
    this.selectedGif.set(null);
  }

  toggleAutoRefresh(): void {
    this.autoRefresh.set(!this.autoRefresh());
    if (this.autoRefresh()) {
      this.startAutoRefresh();
    } else {
      this.stopAutoRefresh();
    }
  }

  startAutoRefresh(): void {
    if (this.refreshInterval) return;
    this.refreshInterval = setInterval(() => this.loadGifs(), 10000);
  }

  stopAutoRefresh(): void {
    if (this.refreshInterval) {
      clearInterval(this.refreshInterval);
      this.refreshInterval = null;
    }
  }
}
