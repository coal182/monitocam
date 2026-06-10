import { ComponentFixture, TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { RecordingsComponent } from './recordings.component';
import { ApiService } from '../../services/api.service';

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
    httpMock.expectOne('/api/recordings/gifs/list/').flush([]);

    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.querySelector('h1')?.textContent).toContain('Recordings');
  });

  it('should show refresh button', () => {
    fixture.detectChanges();
    httpMock.expectOne('/api/cameras/').flush([]);
    httpMock.expectOne('/api/recordings/gifs/list/').flush([]);

    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.querySelector('.btn-refresh')).toBeTruthy();
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

  it('should get gif url with trailing slash', () => {
    expect(component.getGifUrl('123')).toBe('/api/recordings/gifs/123/file/');
  });

  it('should get download url with trailing slash', () => {
    expect(component.getDownloadUrl('123')).toBe('/api/recordings/123/download/');
  });
});
