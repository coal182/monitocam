import { ComponentFixture, TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { RecordingsComponent } from './recordings.component';
import { ApiService } from '../../services/api.service';
import { PaginatedResponse } from '../../models/recording.model';

function paginated<T>(results: T[]): PaginatedResponse<T> {
  return { count: results.length, next: null, previous: null, results };
}

describe('RecordingsComponent', () => {
  let component: RecordingsComponent;
  let fixture: ComponentFixture<RecordingsComponent>;
  let httpMock: HttpTestingController;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [HttpClientTestingModule, RecordingsComponent],
      providers: [ApiService]
    }).compileComponents();

    fixture = TestBed.createComponent(RecordingsComponent);
    component = fixture.componentInstance;
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should show header with title', () => {
    fixture.detectChanges();
    httpMock.expectOne('/api/cameras/').flush([]);
    httpMock.expectOne('/api/recordings/gifs/list/?page=1&page_size=10').flush(paginated([]));
 
    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.querySelector('h1')?.textContent).toContain('Recordings');
  });

  it('should show refresh button', () => {
    fixture.detectChanges();
    httpMock.expectOne('/api/cameras/').flush([]);
    httpMock.expectOne('/api/recordings/gifs/list/?page=1&page_size=10').flush(paginated([]));
 
    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.querySelector('.btn-refresh')).toBeTruthy();
  });

  function flushPending() {
    const pending = httpMock.match(() => true);
    for (const req of pending) req.flush(paginated([]));
  }

  it('should auto-select camera when only one exists', (done) => {
    fixture.detectChanges();
    const camReq = httpMock.expectOne('/api/cameras/');
    camReq.flush([{ id: 1, name: 'Test Cam', status: 'idle' }]);
    const gifReq1 = httpMock.expectOne('/api/recordings/gifs/list/?page=1&page_size=10');
    gifReq1.flush(paginated([]));

    setTimeout(() => {
      flushPending();
      expect(component.selectedCamera()).toBe(1);
      done();
    });
  });

  it('should auto-select first camera when multiple exist', (done) => {
    fixture.detectChanges();
    const camReq = httpMock.expectOne('/api/cameras/');
    camReq.flush([
      { id: 1, name: 'Cam 1', status: 'idle' },
      { id: 2, name: 'Cam 2', status: 'idle' }
    ]);
    const gifReq1 = httpMock.expectOne('/api/recordings/gifs/list/?page=1&page_size=10');
    gifReq1.flush(paginated([]));

    setTimeout(() => {
      flushPending();
      expect(component.selectedCamera()).toBe(1);
      done();
    });
  });

  it('should format size correctly', () => {
    expect(component.formatSize(500)).toBe('500.0 B');
    expect(component.formatSize(1024)).toBe('1.0 KB');
    expect(component.formatSize(1048576)).toBe('1.0 MB');
  });

  it('should format timestamp with ISO date', () => {
    const result = component.formatTimestamp('2024-01-15T14:30:00+01:00');
    expect(result).toContain('15/01/2024');
  });

  it('should format timestamp empty string', () => {
    const result = component.formatTimestamp('');
    expect(result).toBe('');
  });

  it('should show pagination controls when gifs exist', (done) => {
    fixture.detectChanges();
    httpMock.expectOne('/api/cameras/').flush([]);
    httpMock.expectOne('/api/recordings/gifs/list/?page=1&page_size=10').flush(paginated([
      { id: '1', camera_id: 1, camera_name: 'Test', filename: 'test.gif', path: '/test', timestamp: '2024-01-01', size: 1000 }
    ]));

    setTimeout(() => {
      fixture.detectChanges();
      const compiled = fixture.nativeElement as HTMLElement;
      expect(compiled.querySelector('.pagination')).toBeTruthy();
      expect(compiled.querySelector('.page-info')?.textContent).toContain('Página 1 de 1');
      done();
    });
  });

  it('should get gif url with trailing slash', () => {
    expect(component.getGifUrl('123')).toBe('/api/recordings/gifs/123/file/');
  });

  it('should get download url with trailing slash', () => {
    expect(component.getDownloadUrl('123')).toBe('/api/recordings/123/download/');
  });
});
