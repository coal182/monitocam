import { TestBed } from '@angular/core/testing';
import { HttpClient, provideHttpClient, withInterceptors } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { authInterceptor } from './auth.interceptor';
import { AuthService } from './auth.service';

describe('authInterceptor', () => {
  let http: HttpClient;
  let httpMock: HttpTestingController;
  let authService: AuthService;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        AuthService,
        provideHttpClient(withInterceptors([authInterceptor])),
        provideHttpClientTesting()
      ]
    });
    http = TestBed.inject(HttpClient);
    httpMock = TestBed.inject(HttpTestingController);
    authService = TestBed.inject(AuthService);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('ends the session on a 401 from a protected endpoint', () => {
    const spy = spyOn(authService, 'handleSessionExpired');
    http.get('/api/recordings/').subscribe({ error: () => {} });
    httpMock.expectOne('/api/recordings/').flush({}, { status: 401, statusText: 'Unauthorized' });
    expect(spy).toHaveBeenCalled();
  });

  it('does not end the session on a 401 from the session probe', () => {
    const spy = spyOn(authService, 'handleSessionExpired');
    http.get('/api/auth/me/').subscribe({ error: () => {} });
    httpMock.expectOne('/api/auth/me/').flush({}, { status: 401, statusText: 'Unauthorized' });
    expect(spy).not.toHaveBeenCalled();
  });

  it('does not end the session on a 401 from login', () => {
    const spy = spyOn(authService, 'handleSessionExpired');
    http.post('/api/auth/login/', {}).subscribe({ error: () => {} });
    httpMock.expectOne('/api/auth/login/').flush({}, { status: 401, statusText: 'Unauthorized' });
    expect(spy).not.toHaveBeenCalled();
  });

  it('does not end the session on non-401 errors', () => {
    const spy = spyOn(authService, 'handleSessionExpired');
    http.get('/api/recordings/').subscribe({ error: () => {} });
    httpMock.expectOne('/api/recordings/').flush({}, { status: 500, statusText: 'Server Error' });
    expect(spy).not.toHaveBeenCalled();
  });
});
