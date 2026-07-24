import { Component, Input, OnDestroy, OnInit, inject, signal } from '@angular/core';
import { ApiService } from '../../services/api.service';

export type LiveViewState = 'loading' | 'live' | 'error';

@Component({
  selector: 'app-live-view',
  standalone: true,
  template: `
    @if (state() === 'loading') {
      <div class="live-view-loading">
        <span class="loading-text">Loading live view...</span>
      </div>
    }
    @if (state() === 'live') {
      <div class="live-view-container">
        <div class="live-scanlines"></div>
        <div class="live-hud">
          <span class="live-badge">LIVE</span>
          <span class="live-info">Sótano · {{ now() }}</span>
        </div>
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
      border-radius: var(--radius-lg);
      overflow: hidden;
      background: #000;
      aspect-ratio: 16/9;
      width: 100%;
      max-width: 640px;
      margin: 0 auto;
      box-shadow: var(--shadow-card);
    }
    .live-view-container img {
      width: 100%;
      height: 100%;
      object-fit: contain;
      display: block;
    }
    .live-scanlines {
      position: absolute;
      inset: 0;
      z-index: 2;
      pointer-events: none;
      background: repeating-linear-gradient(
        0deg,
        transparent,
        transparent 1px,
        rgba(255, 255, 255, 0.03) 1px,
        rgba(255, 255, 255, 0.03) 2px
      );
    }
    .live-hud {
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      z-index: 3;
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0.5rem 0.75rem;
      background: linear-gradient(180deg, rgba(0,0,0,0.6) 0%, transparent 100%);
      pointer-events: none;
    }
    .live-badge {
      font-family: var(--font-mono);
      font-size: 0.65rem;
      font-weight: 700;
      color: var(--alert);
      letter-spacing: 0.12em;
      animation: live-pulse 1.5s ease-in-out infinite;
    }
    .live-badge::before {
      content: '';
      display: inline-block;
      width: 6px;
      height: 6px;
      border-radius: 50%;
      background: var(--alert);
      margin-right: 0.35rem;
      vertical-align: middle;
      animation: live-pulse 1.5s ease-in-out infinite;
    }
    .live-info {
      font-family: var(--font-mono);
      font-size: 0.65rem;
      color: rgba(255,255,255,0.7);
    }
    @keyframes live-pulse {
      0%, 100% { opacity: 1; }
      50% { opacity: 0.5; }
    }
    .live-view-placeholder,
    .live-view-loading,
    .live-view-error {
      border-radius: var(--radius-lg);
      background: var(--bg-surface);
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
      font-family: var(--font-mono);
      color: var(--text-muted);
      font-size: 0.8rem;
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

  state = signal<LiveViewState>('loading');
  snapshotUrl = signal<string>('');
  private refreshTimer: ReturnType<typeof setTimeout> | null = null;
  private timeInterval: ReturnType<typeof setInterval> | null = null;
  now = signal('');

  ngOnInit(): void {
    this.updateTime();
    this.timeInterval = setInterval(() => this.updateTime(), 1000);
    this.refreshSnapshot();
  }

  ngOnDestroy(): void {
    if (this.refreshTimer) {
      clearTimeout(this.refreshTimer);
    }
    if (this.timeInterval) {
      clearInterval(this.timeInterval);
    }
  }

  private updateTime(): void {
    this.now.set(new Date().toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit', second: '2-digit' }));
  }

  private refreshSnapshot(): void {
    this.state.set('loading');
    this.snapshotUrl.set(
      this.api.getSnapshotUrl(this.cameraId, Date.now())
    );
    this.state.set('live');
  }

  private scheduleNextRefresh(): void {
    this.refreshTimer = setTimeout(() => this.refreshSnapshot(), 2000);
  }

  onLoad(): void {
    this.state.set('live');
    this.scheduleNextRefresh();
  }

  onError(): void {
    this.state.set('error');
    this.scheduleNextRefresh();
  }
}
