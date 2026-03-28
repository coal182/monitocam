import { Component, signal, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { AuthService } from '../../core/auth.service';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [FormsModule],
  templateUrl: './login.component.html',
  styleUrl: './login.component.css'
})
export class LoginComponent {
  private authService = inject(AuthService);
  private router = inject(Router);

  username = '';
  password = '';
  loading = signal(false);
  error = signal('');

  async login(): Promise<void> {
    this.error.set('');
    this.loading.set(true);

    try {
      await this.authService.login(this.username, this.password);
      this.router.navigate(['/']);
    } catch (e: unknown) {
      const error = e as { error?: { detail?: string } };
      this.error.set(error.error?.detail || 'Login failed');
    } finally {
      this.loading.set(false);
    }
  }
}
