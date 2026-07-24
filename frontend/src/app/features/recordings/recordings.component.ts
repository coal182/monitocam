import { Component, OnInit, signal, inject, computed } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../services/api.service';
import { SseService } from '../../services/sse.service';
import { Camera } from '../../models/camera.model';
import { GifItem } from '../../models/recording.model';
import { LiveViewComponent } from './live-view.component';

@Component({
  selector: 'app-recordings',
  standalone: true,
  imports: [FormsModule, LiveViewComponent],
  templateUrl: './recordings.component.html',
  styleUrl: './recordings.component.css'
})
export class RecordingsComponent implements OnInit {
  private api = inject(ApiService);
  private sse = inject(SseService);

  gifs = signal<GifItem[]>([]);
  cameras = signal<Camera[]>([]);
  loading = signal(false);
  selectedCamera = signal<number | null>(null);
  selectedGif = signal<GifItem | null>(null);
  currentPage = signal(1);
  totalCount = signal(0);
  pageSize = 10;
  totalPages = computed(() => Math.max(1, Math.ceil(this.totalCount() / this.pageSize)));
  private pendingPage = 0;

  liveCameraId = computed(() => this.selectedCamera());
  liveIsRecording = computed(() => {
    const camId = this.selectedCamera();
    return camId !== null
      ? !!this.sse.statuses()[camId]
      : false;
  });

  ngOnInit(): void {
    this.loadCameras();
    this.loadGifs();
    this.sse.connect();
  }

  loadGifs(resetPage = false): void {
    if (resetPage) {
      this.currentPage.set(1);
    }
    this.gifs.set([]);
    this.loading.set(true);
    const page = this.currentPage();
    this.pendingPage = page;
    const params: { camera_id?: number; page?: number; page_size?: number } = {
      page: page,
      page_size: this.pageSize,
    };
    const camId = this.selectedCamera();
    if (camId) {
      params.camera_id = camId;
    }
    this.api.getGifs(params)
      .then(data => {
        if (this.pendingPage !== page) return;
        if (Array.isArray(data)) {
          this.gifs.set(data);
          this.totalCount.set(data.length);
        } else {
          this.gifs.set(data.results ?? []);
          this.totalCount.set(data.count ?? 0);
        }
        this.loading.set(false);
      })
      .catch(() => this.loading.set(false));
  }

  onCameraChange(cameraId: number | null): void {
    this.selectedCamera.set(cameraId);
    this.loadGifs(true);
  }

  loadCameras(): void {
    this.api.getCameras()
      .then(data => {
        this.cameras.set(data);
        if (data.length >= 1) {
          this.selectedCamera.set(data[0].id);
          this.loadGifs(true);
        }
      });
  }

  deleteGif(gif: GifItem, event: Event): void {
    event.stopPropagation();
    if (!confirm(`Eliminar grabación ${gif.filename}?`)) return;
    this.api.deleteRecording(gif.id)
      .then(() => this.loadGifs());
  }

  nextPage(): void {
    if (this.currentPage() < this.totalPages()) {
      this.currentPage.update(p => p + 1);
      this.loadGifs();
    }
  }

  prevPage(): void {
    if (this.currentPage() > 1) {
      this.currentPage.update(p => p - 1);
      this.loadGifs();
    }
  }

  cleanupOldRecordings(): void {
    const days = prompt('Eliminar grabaciones de hace cuántos días?', '7');
    if (!days) return;
    const daysNum = parseInt(days, 10);
    if (isNaN(daysNum) || daysNum < 0) {
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
    const date = new Date(ts);
    return date.toLocaleString('es-ES', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
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


}
