import { ComponentFixture, TestBed } from '@angular/core/testing';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { RecordingsComponent } from './recordings.component';
import { ApiService } from '../../services/api.service';

describe('RecordingsComponent', () => {
  let component: RecordingsComponent;
  let fixture: ComponentFixture<RecordingsComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [HttpClientTestingModule, RecordingsComponent],
      providers: [ApiService]
    }).compileComponents();

    fixture = TestBed.createComponent(RecordingsComponent);
    component = fixture.componentInstance;
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should show header with title', () => {
    fixture.detectChanges();
    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.querySelector('h1')?.textContent).toContain('Grabaciones');
  });

  it('should show refresh button', () => {
    fixture.detectChanges();
    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.querySelector('.btn-refresh')).toBeTruthy();
  });

  it('should format size correctly', () => {
    expect(component.formatSize(500)).toBe('500.0 B');
    expect(component.formatSize(1024)).toBe('1.0 KB');
    expect(component.formatSize(1048576)).toBe('1.0 MB');
  });

  it('should format timestamp correctly', () => {
    const result = component.formatTimestamp('2024-01-15_14-30-00');
    expect(result).toContain('2024-01-15');
  });

  it('should get gif url', () => {
    expect(component.getGifUrl('123')).toBe('/api/recordings/gifs/123/file');
  });

  it('should get download url', () => {
    expect(component.getDownloadUrl('123')).toBe('/api/recordings/123/download');
  });
});
