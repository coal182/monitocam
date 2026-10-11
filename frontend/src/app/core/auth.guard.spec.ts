import { TestBed } from '@angular/core/testing';
import { Router, UrlTree } from '@angular/router';
import { RouterTestingModule } from '@angular/router/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { authGuard, publicGuard } from './auth.guard';
import { AuthService } from './auth.service';

describe('AuthGuard', () => {
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [RouterTestingModule, HttpClientTestingModule],
      providers: [AuthService]
    });
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  function run(guard: typeof authGuard): Promise<boolean | UrlTree> {
    return TestBed.runInInjectionContext(
      () => guard({} as never, {} as never) as Promise<boolean | UrlTree>
    );
  }

  it('allows navigation when a session exists', async () => {
    const result = run(authGuard);
    httpMock.expectOne('/api/auth/me/').flush({ username: 'admin' });
    await expectAsync(result).toBeResolvedTo(true);
  });

  it('redirects to /login when the session probe returns 401', async () => {
    const result = run(authGuard);
    httpMock.expectOne('/api/auth/me/').flush({}, { status: 401, statusText: 'Unauthorized' });

    const value = await result;
    expect(value instanceof UrlTree).toBeTrue();
    expect(TestBed.inject(Router).serializeUrl(value as UrlTree)).toBe('/login');
  });

  it('keeps you on login when there is no session', async () => {
    const result = run(publicGuard);
    httpMock.expectOne('/api/auth/me/').flush({}, { status: 401, statusText: 'Unauthorized' });
    await expectAsync(result).toBeResolvedTo(true);
  });

  it('redirects away from login when a session exists', async () => {
    const result = run(publicGuard);
    httpMock.expectOne('/api/auth/me/').flush({ username: 'admin' });

    const value = await result;
    expect(value instanceof UrlTree).toBeTrue();
    expect(TestBed.inject(Router).serializeUrl(value as UrlTree)).toBe('/');
  });
});
