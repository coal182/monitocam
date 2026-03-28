import { Injectable, signal, computed, inject } from '@angular/core';
import { ApiService } from '../services/api.service';

@Injectable({ providedIn: 'root' })
export class AuthService {
  private api = inject(ApiService);
  
  private usernameSignal = signal<string | null>(localStorage.getItem('username'));
  
  readonly username = this.usernameSignal.asReadonly();
  readonly isAuthenticated = computed(() => !!this.usernameSignal());

  constructor() {
    this.checkAuth();
  }

  async checkAuth(): Promise<void> {
    if (!this.usernameSignal()) return;
    
    try {
      const response = await this.api.checkAuth();
      this.usernameSignal.set(response.username);
      localStorage.setItem('username', response.username);
    } catch {
      this.clearAuth();
    }
  }

  async login(username: string, password: string): Promise<void> {
    const response = await this.api.login(username, password);
    this.usernameSignal.set(response.username);
    localStorage.setItem('username', response.username);
  }

  async logout(): Promise<void> {
    try {
      await this.api.logout();
    } finally {
      this.clearAuth();
      window.location.href = '/login';
    }
  }

  private clearAuth(): void {
    this.usernameSignal.set(null);
    localStorage.removeItem('username');
  }
}
