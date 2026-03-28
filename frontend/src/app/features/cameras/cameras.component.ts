import { Component, OnInit, signal, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../services/api.service';
import { Camera, CameraCreate } from '../../models/camera.model';

@Component({
  selector: 'app-cameras',
  standalone: true,
  imports: [FormsModule],
  templateUrl: './cameras.component.html',
  styleUrl: './cameras.component.css'
})
export class CamerasComponent implements OnInit {
  private api = inject(ApiService);

  cameras = signal<Camera[]>([]);
  loading = signal(false);
  showAddForm = signal(false);
  newCamera: CameraCreate = { name: '', rtsp_url: '', enabled: true };
  error = signal('');

  ngOnInit(): void {
    this.loadCameras();
  }

  loadCameras(): void {
    this.loading.set(true);
    this.api.getCameras()
      .then(data => {
        this.cameras.set(data);
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

    action
      .then(() => this.loadCameras())
      .catch(() => this.error.set('Error toggling recording'));
  }
}
