import { Component, OnInit, OnDestroy, signal, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../services/api.service';
import { SseService } from '../../services/sse.service';
import { Camera, CameraCreate } from '../../models/camera.model';

@Component({
  selector: 'app-cameras',
  standalone: true,
  imports: [FormsModule],
  templateUrl: './cameras.component.html',
  styleUrl: './cameras.component.css'
})
export class CamerasComponent implements OnInit, OnDestroy {
  private api = inject(ApiService);
  private sse = inject(SseService);

  cameras = signal<Camera[]>([]);
  loading = signal(false);
  showAddForm = signal(false);
  newCamera: CameraCreate = { name: '', rtsp_url: '', enabled: true };
  error = signal('');
  private unsubSse: (() => void) | null = null;

  ngOnInit(): void {
    this.loadCameras();
    this.sse.connect();
    this.unsubSse = this.sse.onStatusChange((event) => {
      this.cameras.update((cams) =>
        cams.map((c) =>
          c.id === event.camera_id
            ? { ...c, status: event.is_recording ? 'recording' : 'stopped' }
            : c
        )
      );
    });
  }

  ngOnDestroy(): void {
    this.unsubSse?.();
  }

  loadCameras(): void {
    this.loading.set(true);
    this.api.getCameras()
      .then(data => {
        const statuses = this.sse.statuses();
        this.cameras.set(data.map((c) => ({
          ...c,
          status: statuses[c.id] ? 'recording' : (c.status || 'stopped'),
        })));
        this.loading.set(false);
      })
      .catch(() => {
        this.error.set('Error loading cameras');
        this.loading.set(false);
      });
  }

  addCamera(): void {
    this.api.createCamera(this.newCamera)
      .then(() => {
        this.showAddForm.set(false);
        this.newCamera = { name: '', rtsp_url: '', enabled: true };
        this.loadCameras();
      })
      .catch((e: unknown) => {
        const error = e as { error?: { detail?: string } };
        this.error.set(error.error?.detail || 'Error adding camera');
      });
  }

  deleteCamera(id: number): void {
    if (confirm('Delete this camera?')) {
      this.api.deleteCamera(id)
        .then(() => this.loadCameras())
        .catch(() => this.error.set('Error deleting camera'));
    }
  }

  toggleRecording(camera: Camera): void {
    const action = camera.status === 'recording'
      ? this.api.stopRecording(camera.id)
      : this.api.startRecording(camera.id);

    action.catch(() => this.error.set('Error toggling recording'));
  }
}
