import { ComponentFixture, TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { CamerasComponent } from './cameras.component';
import { ApiService } from '../../services/api.service';
import { SseService } from '../../services/sse.service';
import { Camera } from '../../models/camera.model';

describe('CamerasComponent', () => {
  let component: CamerasComponent;
  let fixture: ComponentFixture<CamerasComponent>;
  let httpMock: HttpTestingController;
  let sseService: jasmine.SpyObj<SseService>;

  const mockCameras: Camera[] = [
    { id: 1, name: 'Camera 1', rtsp_url: 'rtsp://test1', enabled: true, status: 'stopped' },
    { id: 2, name: 'Camera 2', rtsp_url: 'rtsp://test2', enabled: false, status: 'stopped' }
  ];

  beforeEach(async () => {
    const sseSpy = jasmine.createSpyObj('SseService', ['connect', 'disconnect', 'onStatusChange', 'statuses']);
    sseSpy.statuses.and.returnValue({});
    sseSpy.onStatusChange.and.returnValue(() => {});

    await TestBed.configureTestingModule({
      imports: [HttpClientTestingModule, CamerasComponent],
      providers: [
        ApiService,
        { provide: SseService, useValue: sseSpy }
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(CamerasComponent);
    component = fixture.componentInstance;
    httpMock = TestBed.inject(HttpTestingController);
    sseService = TestBed.inject(SseService) as jasmine.SpyObj<SseService>;
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should show add camera button', () => {
    fixture.detectChanges();
    const req = httpMock.expectOne('/api/cameras/');
    req.flush([]);

    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.querySelector('.header button')).toBeTruthy();
    expect(compiled.querySelector('.header button')?.textContent).toContain('Anadir Camara');
  });

  it('should load cameras on init', async () => {
    fixture.detectChanges();

    const req = httpMock.expectOne('/api/cameras/');
    expect(req.request.method).toBe('GET');
    req.flush(mockCameras);

    await fixture.whenStable();

    expect(component.cameras().length).toBe(2);
  });

  it('should connect SSE on init', () => {
    fixture.detectChanges();

    const req = httpMock.expectOne('/api/cameras/');
    req.flush(mockCameras);

    expect(sseService.connect).toHaveBeenCalled();
  });

  it('should toggle recording without reload', () => {
    fixture.detectChanges();

    const req = httpMock.expectOne('/api/cameras/');
    req.flush(mockCameras);

    component.toggleRecording(mockCameras[0]);

    const startReq = httpMock.expectOne('/api/cameras/1/start/');
    expect(startReq.request.method).toBe('POST');
    startReq.flush({});

    httpMock.expectNone('/api/cameras/');
  });
});
