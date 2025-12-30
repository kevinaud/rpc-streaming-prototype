/**
 * Unit tests for ConnectionStatusComponent.
 * Tests connection status display.
 */
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ConnectionStatusComponent } from './connection-status.component';
import { SessionStateService } from '../../../../core/services/session-state.service';

describe('ConnectionStatusComponent', () => {
  let component: ConnectionStatusComponent;
  let fixture: ComponentFixture<ConnectionStatusComponent>;
  let sessionState: SessionStateService;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ConnectionStatusComponent],
      providers: [SessionStateService],
    }).compileComponents();

    fixture = TestBed.createComponent(ConnectionStatusComponent);
    component = fixture.componentInstance;
    sessionState = TestBed.inject(SessionStateService);
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  describe('status display', () => {
    it('should show Not connected when disconnected', () => {
      sessionState.setConnectionStatus('disconnected');
      fixture.detectChanges();

      const compiled = fixture.nativeElement as HTMLElement;
      expect(compiled.textContent).toContain('Not connected');
    });

    it('should show Connecting when connecting', () => {
      sessionState.setConnectionStatus('connecting');
      fixture.detectChanges();

      const compiled = fixture.nativeElement as HTMLElement;
      expect(compiled.textContent).toContain('Connecting');
    });

    it('should show Connected when connected', () => {
      sessionState.setConnectionStatus('connected');
      fixture.detectChanges();

      const compiled = fixture.nativeElement as HTMLElement;
      expect(compiled.textContent).toContain('Connected');
    });

    it('should show Reconnecting when reconnecting', () => {
      sessionState.setConnectionStatus('reconnecting');
      fixture.detectChanges();

      const compiled = fixture.nativeElement as HTMLElement;
      expect(compiled.textContent).toContain('Reconnecting');
    });
  });

  describe('status icons', () => {
    it('should have cloud_off icon when disconnected', () => {
      sessionState.setConnectionStatus('disconnected');
      fixture.detectChanges();

      const compiled = fixture.nativeElement as HTMLElement;
      expect(compiled.textContent).toContain('cloud_off');
    });

    it('should have cloud_done icon when connected', () => {
      sessionState.setConnectionStatus('connected');
      fixture.detectChanges();

      const compiled = fixture.nativeElement as HTMLElement;
      expect(compiled.textContent).toContain('cloud_done');
    });
  });

  describe('CSS classes', () => {
    it('should have disconnected class when disconnected', () => {
      sessionState.setConnectionStatus('disconnected');
      fixture.detectChanges();

      const indicator = fixture.nativeElement.querySelector('.connection-status');
      expect(indicator?.classList.contains('disconnected')).toBeTruthy();
    });

    it('should have connected class when connected', () => {
      sessionState.setConnectionStatus('connected');
      fixture.detectChanges();

      const indicator = fixture.nativeElement.querySelector('.connection-status');
      expect(indicator?.classList.contains('connected')).toBeTruthy();
    });

    it('should have connecting class when connecting', () => {
      sessionState.setConnectionStatus('connecting');
      fixture.detectChanges();

      const indicator = fixture.nativeElement.querySelector('.connection-status');
      expect(indicator?.classList.contains('connecting')).toBeTruthy();
    });

    it('should have reconnecting class when reconnecting', () => {
      sessionState.setConnectionStatus('reconnecting');
      fixture.detectChanges();

      const indicator = fixture.nativeElement.querySelector('.connection-status');
      expect(indicator?.classList.contains('reconnecting')).toBeTruthy();
    });
  });
});
