import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { ApiService } from './api.service';
import { Camera } from '../models/camera.model';
import { GifItem } from '../models/recording.model';

describe('ApiService', () => {
  let service: ApiService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [ApiService]
    });
    service = TestBed.inject(ApiService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  describe('Cameras API', () => {
    it('should get cameras', async () => {
      const mockCameras: Camera[] = [
        { id: 1, name: 'Camera 1', rtsp_url: 'rtsp://test', enabled: true, status: 'stopped' }
      ];

      const promise = service.getCameras();
      
      const req = httpMock.expectOne('/api/cameras');
      expect(req.request.method).toBe('GET');
      req.flush(mockCameras);
      
      const cameras = await promise;
      expect(cameras).toEqual(mockCameras);
    });

    it('should create camera', async () => {
      const newCamera: Camera = { id: 1, name: 'Test', rtsp_url: 'rtsp://test', enabled: true, status: 'stopped' };

      const promise = service.createCamera({ name: 'Test', rtsp_url: 'rtsp://test' });
      
      const req = httpMock.expectOne('/api/cameras');
      expect(req.request.method).toBe('POST');
      req.flush(newCamera);
      
      const camera = await promise;
      expect(camera).toEqual(newCamera);
    });

    it('should delete camera', async () => {
      const promise = service.deleteCamera(1);
      
      const req = httpMock.expectOne('/api/cameras/1');
      expect(req.request.method).toBe('DELETE');
      req.flush({});
      
      await promise;
    });

    it('should start recording', async () => {
      const promise = service.startRecording(1);
      
      const req = httpMock.expectOne('/api/cameras/1/start');
      expect(req.request.method).toBe('POST');
      req.flush({});
      
      await promise;
    });

    it('should stop recording', async () => {
      const promise = service.stopRecording(1);
      
      const req = httpMock.expectOne('/api/cameras/1/stop');
      expect(req.request.method).toBe('POST');
      req.flush({});
      
      await promise;
    });
  });

  describe('Recordings API', () => {
    it('should get recordings', async () => {
      const mockRecordings = [{ id: '1', camera_id: 1, camera_name: 'Test', filename: 'test.mp4', path: '/test', start_time: '2024-01-01', has_gif: true }];

      const promise = service.getRecordings();
      
      const req = httpMock.expectOne('/api/recordings');
      expect(req.request.method).toBe('GET');
      req.flush(mockRecordings);
      
      const recordings = await promise;
      expect(recordings).toEqual(mockRecordings);
    });

    it('should get recordings with camera_id filter', async () => {
      const promise = service.getRecordings({ camera_id: 1 });
      
      const req = httpMock.expectOne('/api/recordings?camera_id=1');
      expect(req.request.method).toBe('GET');
      req.flush([]);
      
      await promise;
    });

    it('should get gifs', async () => {
      const mockGifs: GifItem[] = [
        { id: '1', camera_id: 1, camera_name: 'Test', filename: 'test.gif', path: '/test', timestamp: '2024-01-01', size: 1000 }
      ];

      const promise = service.getGifs();
      
      const req = httpMock.expectOne('/api/recordings/gifs/list');
      expect(req.request.method).toBe('GET');
      req.flush(mockGifs);
      
      const gifs = await promise;
      expect(gifs).toEqual(mockGifs);
    });

    it('should delete recording', async () => {
      const promise = service.deleteRecording('1');
      
      const req = httpMock.expectOne('/api/recordings/1');
      expect(req.request.method).toBe('DELETE');
      req.flush({});
      
      await promise;
    });
  });

  describe('Auth API', () => {
    it('should login', async () => {
      const mockResponse = { username: 'admin' };

      const promise = service.login('admin', 'password');
      
      const req = httpMock.expectOne('/api/auth/login');
      expect(req.request.method).toBe('POST');
      expect(req.request.headers.get('Content-Type')).toBe('application/x-www-form-urlencoded');
      req.flush(mockResponse);
      
      const response = await promise;
      expect(response).toEqual(mockResponse);
    });

    it('should logout', async () => {
      const promise = service.logout();
      
      const req = httpMock.expectOne('/api/auth/logout');
      expect(req.request.method).toBe('POST');
      req.flush({});
      
      await promise;
    });

    it('should check auth', async () => {
      const mockResponse = { username: 'admin' };

      const promise = service.checkAuth();
      
      const req = httpMock.expectOne('/api/auth/me');
      expect(req.request.method).toBe('GET');
      req.flush(mockResponse);
      
      const response = await promise;
      expect(response).toEqual(mockResponse);
    });
  });

  describe('URL helpers', () => {
    it('should return correct gif url', () => {
      expect(service.getGifUrl('123')).toBe('/api/recordings/gifs/123/file');
    });

    it('should return correct download url', () => {
      expect(service.getDownloadUrl('123')).toBe('/api/recordings/123/download');
    });
  });
});
