import { ComponentFixture, TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { CamerasComponent } from './cameras.component';
import { ApiService } from '../../services/api.service';
import { Camera } from '../../models/camera.model';

describe('CamerasComponent', () => {
  let component: CamerasComponent;
  let fixture: ComponentFixture<CamerasComponent>;
  let httpMock: HttpTestingController;

  const mockCameras: Camera[] = [
    { id: 1, name: 'Camera 1', rtsp_url: 'rtsp://test1', enabled: true, status: 'stopped' },
    { id: 2, name: 'Camera 2', rtsp_url: 'rtsp://test2', enabled: false, status: 'disabled' }
  ];

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [HttpClientTestingModule, CamerasComponent],
      providers: [ApiService]
    }).compileComponents();

    fixture = TestBed.createComponent(CamerasComponent);
    component = fixture.componentInstance;
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should show add camera button', () => {
    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.querySelector('.header button')).toBeTruthy();
    expect(compiled.querySelector('.header button')?.textContent).toContain('Anadir Camara');
  });
});
