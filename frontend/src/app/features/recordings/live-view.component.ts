import { Component, Input, OnDestroy, OnInit, inject, signal } from '@angular/core';
import { ApiService } from '../../services/api.service';

export type LiveViewState = 'loading' | 'live' | 'not-recording' | 'error';

@Component({
  selector: 'app-live-view',
  standalone: true,
  template: `
    @if (state() === 'not-recording') {
      <div class="live-view-placeholder">
        <span class="placeholder-text">Camera is not recording</span>
      </div>
    }
    @if (state() === 'loading') {
      <div class="live-view-loading">
        <span class="loading-text">Loading live view...</span>
      </div>
    }
    @if (state() === 'live') {
      <div class="live-view-container">
        <div class="live-badge">LIVE</div>
        <img [src]="snapshotUrl()" (error)="onError()" (load)="onLoad()" alt="Live snapshot" />
      </div>
    }
    @if (state() === 'error') {
      <div class="live-view-error">
        <span class="error-text">Live view unavailable</span>
      </div>
    }
  `,
  styles: [`
    :host { display: block; }
    .live-view-container {
      position: relative;
      border-radius: 8px;
      overflow: hidden;
      background: #000;
      aspect-ratio: 16/9;
      width: 100%;
      max-width: 640px;
      margin: 0 auto;
    }
    .live-view-container img {
      width: 100%;
      height: 100%;
      object-fit: contain;
      display: block;
    }
    .live-badge {
      position: absolute;
      top: 8px;
      left: 8px;
      background: #e94560;
      color: white;
      font-size: 0.7rem;
      font-weight: 700;
      padding: 2px 8px;
      border-radius: 4px;
      letter-spacing: 0.5px;
      z-index: 2;
    }
    .live-view-placeholder,
    .live-view-loading,
    .live-view-error {
      border-radius: 8px;
      background: #f0f0f0;
      display: flex;
      align-items: center;
      justify-content: center;
      aspect-ratio: 16/9;
      width: 100%;
      max-width: 640px;
      margin: 0 auto;
    }
    .placeholder-text,
    .loading-text,
    .error-text {
      color: #888;
      font-size: 0.9rem;
    }
    @media (max-width: 640px) {
      .live-view-container,
      .live-view-placeholder,
      .live-view-loading,
      .live-view-error {
        max-width: 100%;
      }
    }
  `],
})
export class LiveViewComponent implements OnInit, OnDestroy {
  private api = inject(ApiService);

  @Input({ required: true }) cameraId!: number;
  @Input() isRecording = false;

  state = signal<LiveViewState>('loading');
  snapshotUrl = signal<string>('');
  private refreshTimer: ReturnType<typeof setInterval> | null = null;

  ngOnInit(): void {
    this.updateState();
    this.startRefresh();
  }

  ngOnDestroy(): void {
    this.stopRefresh();
  }

  private updateState(): void {
    if (!this.isRecording) {
      this.state.set('not-recording');
      this.stopRefresh();
      return;
    }
    this.state.set('loading');
    this.refreshSnapshot();
    this.startRefresh();
  }

  private refreshSnapshot(): void {
    this.snapshotUrl.set(
      this.api.getSnapshotUrl(this.cameraId, Date.now())
    );
  }

  private startRefresh(): void {
    this.stopRefresh();
    if (!this.isRecording) return;
    this.refreshTimer = setInterval(() => this.refreshSnapshot(), 2000);
  }

  private stopRefresh(): void {
    if (this.refreshTimer) {
      clearInterval(this.refreshTimer);
      this.refreshTimer = null;
    }
  }

  onLoad(): void {
    if (this.state() === 'loading') {
      this.state.set('live');
    }
  }

  onError(): void {
    this.state.set('error');
  }
}
