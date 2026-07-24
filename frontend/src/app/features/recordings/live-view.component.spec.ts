import { ComponentFixture, TestBed } from '@angular/core/testing';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { LiveViewComponent } from './live-view.component';
import { ApiService } from '../../services/api.service';

describe('LiveViewComponent', () => {
  let component: LiveViewComponent;
  let fixture: ComponentFixture<LiveViewComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [HttpClientTestingModule, LiveViewComponent],
      providers: [ApiService]
    }).compileComponents();

    fixture = TestBed.createComponent(LiveViewComponent);
    component = fixture.componentInstance;
    component.cameraId = 1;
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should start in live state', () => {
    fixture.detectChanges();

    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.querySelector('.live-view-container')).toBeTruthy();
    expect(compiled.querySelector('.live-badge')?.textContent).toContain('LIVE');
    expect(compiled.querySelector('img')).toBeTruthy();
  });

  it('should keep live state after image loads', () => {
    fixture.detectChanges();

    component.onLoad();
    fixture.detectChanges();

    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.querySelector('.live-view-container')).toBeTruthy();
    expect(compiled.querySelector('.live-badge')?.textContent).toContain('LIVE');
    expect(compiled.querySelector('img')).toBeTruthy();
  });

  it('should show error state when image fails to load', () => {
    fixture.detectChanges();

    component.onError();
    fixture.detectChanges();

    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.querySelector('.live-view-error')).toBeTruthy();
    expect(compiled.querySelector('.error-text')?.textContent).toContain('unavailable');
  });

  it('should generate snapshot url with timestamp', () => {
    const url = component['api'].getSnapshotUrl(1, 1234567890);
    expect(url).toBe('/api/cameras/1/snapshot/?t=1234567890');
  });

  it('should generate snapshot url without timestamp', () => {
    const url = component['api'].getSnapshotUrl(1);
    expect(url).toBe('/api/cameras/1/snapshot/');
  });
});
