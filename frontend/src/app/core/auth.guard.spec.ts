import { TestBed } from '@angular/core/testing';
import { Router } from '@angular/router';
import { RouterTestingModule } from '@angular/router/testing';
import { AuthService } from './auth.service';

describe('AuthGuard', () => {
  let router: Router;
  let authService: AuthService;

  beforeEach(() => {
    localStorage.clear();
    TestBed.configureTestingModule({
      imports: [RouterTestingModule],
      providers: [AuthService]
    });
    router = TestBed.inject(Router);
    authService = TestBed.inject(AuthService);
  });

  afterEach(() => {
    localStorage.clear();
  });

  describe('AuthService basic', () => {
    it('should be created', () => {
      expect(authService).toBeTruthy();
    });

    it('should return false for isAuthenticated when not logged in', () => {
      expect(authService.isAuthenticated()).toBeFalse();
    });

    it('should return null username initially', () => {
      expect(authService.username()).toBeNull();
    });
  });
});
