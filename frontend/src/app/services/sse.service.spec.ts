import { TestBed } from '@angular/core/testing';
import { SseService, StatusEvent } from './sse.service';

describe('SseService', () => {
  let service: SseService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(SseService);

    (window as any).EventSource = class {
      url: string;
      onmessage: ((event: MessageEvent) => void) | null = null;
      onerror: (() => void) | null = null;
      readyState = 0;
      constructor(url: string) {
        this.url = url;
      }
      close() {}
    };
  });

  afterEach(() => {
    service.disconnect();
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('should connect to EventSource', () => {
    service.connect();
    expect(service['eventSource']).toBeTruthy();
    expect(service['eventSource']?.url).toBe('/api/cameras/events/');
  });

  it('should not connect twice', () => {
    service.connect();
    const first = service['eventSource'];
    service.connect();
    expect(service['eventSource']).toBe(first);
  });

  it('should update statuses on array message', () => {
    service.connect();

    const data = [
      { id: 1, is_recording: true },
      { id: 2, is_recording: false }
    ];

    service['eventSource']?.onmessage?.({ data: JSON.stringify(data) } as MessageEvent);

    expect(service.statuses()[1]).toBeTrue();
    expect(service.statuses()[2]).toBeFalse();
  });

  it('should update single camera status', () => {
    service.connect();

    const event: StatusEvent = { camera_id: 1, is_recording: true };
    service['eventSource']?.onmessage?.({ data: JSON.stringify(event) } as MessageEvent);

    expect(service.statuses()[1]).toBeTrue();
  });

  it('should call listeners on status change', () => {
    service.connect();

    const callback = jasmine.createSpy('callback');
    service.onStatusChange(callback);

    const event: StatusEvent = { camera_id: 1, is_recording: true };
    service['eventSource']?.onmessage?.({ data: JSON.stringify(event) } as MessageEvent);

    expect(callback).toHaveBeenCalledWith(event);
  });

  it('should disconnect cleanly', () => {
    service.connect();
    expect(service['eventSource']).toBeTruthy();

    service.disconnect();
    expect(service['eventSource']).toBeNull();
  });
});
