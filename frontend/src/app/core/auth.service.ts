import { Injectable, signal, inject } from '@angular/core';
import { ApiService } from '../services/api.service';

@Injectable({ providedIn: 'root' })
export class AuthService {
  private api = inject(ApiService);

  private usernameSignal = signal<string | null>(null);
  private hasSessionSignal = signal(false);

  readonly username = this.usernameSignal.asReadonly();
  readonly isAuthenticated = this.hasSessionSignal.asReadonly();

  private sessionProbe: Promise<boolean> | null = null;

  async ensureSession(): Promise<boolean> {
    if (!this.sessionProbe) {
      this.sessionProbe = this.probeSession();
    }
    return this.sessionProbe;
  }

  private async probeSession(): Promise<boolean> {
    try {
      const response = await this.api.checkAuth();
      this.usernameSignal.set(response.username);
      this.hasSessionSignal.set(true);
      return true;
    } catch (e: unknown) {
      const status = (e as { status?: number }).status;
      if (status === 401) {
        this.endSession();
      } else {
        this.hasSessionSignal.set(false);
      }
      return false;
    }
  }

  async login(username: string, password: string): Promise<void> {
    const response = await this.api.login(username, password);
    this.usernameSignal.set(response.username);
    this.hasSessionSignal.set(true);
    this.sessionProbe = Promise.resolve(true);
  }

  async logout(): Promise<void> {
    try {
      await this.api.logout();
    } finally {
      this.endSession();
      window.location.href = '/login';
    }
  }

  handleSessionExpired(): void {
    this.endSession();
    window.location.href = '/login';
  }

  private endSession(): void {
    this.usernameSignal.set(null);
    this.hasSessionSignal.set(false);
    this.sessionProbe = null;
  }
}
