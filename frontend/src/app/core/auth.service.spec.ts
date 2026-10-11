import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { AuthService } from './auth.service';

describe('AuthService', () => {
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [AuthService]
    });
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('should be created', () => {
    expect(TestBed.inject(AuthService)).toBeTruthy();
  });

  it('should return null username and no session initially', () => {
    const service = TestBed.inject(AuthService);
    expect(service.username()).toBeNull();
    expect(service.isAuthenticated()).toBeFalse();
  });

  it('should authenticate when the session probe succeeds', async () => {
    const service = TestBed.inject(AuthService);
    const promise = service.ensureSession();
    httpMock.expectOne('/api/auth/me/').flush({ username: 'admin' });

    await expectAsync(promise).toBeResolvedTo(true);
    expect(service.isAuthenticated()).toBeTrue();
    expect(service.username()).toBe('admin');
  });

  it('should end the session on a 401 probe', async () => {
    const service = TestBed.inject(AuthService);
    const promise = service.ensureSession();
    httpMock.expectOne('/api/auth/me/').flush({ detail: 'no' }, { status: 401, statusText: 'Unauthorized' });

    await expectAsync(promise).toBeResolvedTo(false);
    expect(service.isAuthenticated()).toBeFalse();
    expect(service.username()).toBeNull();
  });

  it('should stay unauthenticated when the probe is unreachable', async () => {
    const service = TestBed.inject(AuthService);
    const promise = service.ensureSession();
    httpMock.expectOne('/api/auth/me/').error(new ErrorEvent('error'));

    await expectAsync(promise).toBeResolvedTo(false);
    expect(service.isAuthenticated()).toBeFalse();
    expect(service.username()).toBeNull();
  });

  it('should memoize the session probe for the app load', async () => {
    const service = TestBed.inject(AuthService);
    const first = service.ensureSession();
    const second = service.ensureSession();
    httpMock.expectOne('/api/auth/me/').flush({ username: 'admin' });

    await Promise.all([first, second]);
    expect(await first).toBeTrue();
    expect(await second).toBeTrue();
    httpMock.expectNone('/api/auth/me/');
  });

  it('should authenticate on login', async () => {
    const service = TestBed.inject(AuthService);
    const promise = service.login('admin', 'secret');
    httpMock.expectOne('/api/auth/login/').flush({ username: 'admin' });

    await promise;
    expect(service.isAuthenticated()).toBeTrue();
    expect(service.username()).toBe('admin');
  });
});
