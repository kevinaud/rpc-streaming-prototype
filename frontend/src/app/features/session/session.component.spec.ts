/**
 * Unit tests for SessionComponent.
 * Tests subscription management and session lifecycle.
 */
import { type ComponentFixture, TestBed } from '@angular/core/testing';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { ActivatedRoute, convertToParamMap, Router } from '@angular/router';
import { vi } from 'vitest';

import { ApprovalService } from '../../core/services/approval.service';
import { SessionStateService } from '../../core/services/session-state.service';
import { SessionComponent } from './session.component';

describe('SessionComponent', () => {
  let component: SessionComponent;
  let fixture: ComponentFixture<SessionComponent>;
  let routerNavigate: ReturnType<typeof vi.fn>;
  let subscribe: ReturnType<typeof vi.fn>;
  let cancelSubscription: ReturnType<typeof vi.fn>;
  let sessionState: SessionStateService;

  // Mock async iterator that yields nothing and completes
  function createMockSubscription() {
    return {
      [Symbol.asyncIterator]: () => ({
        next: () => Promise.resolve({ done: true, value: undefined }),
        return: () => Promise.resolve({ done: true, value: undefined }),
      }),
    };
  }

  beforeEach(async () => {
    routerNavigate = vi.fn();
    subscribe = vi.fn().mockReturnValue(createMockSubscription());
    cancelSubscription = vi.fn();

    await TestBed.configureTestingModule({
      imports: [SessionComponent, NoopAnimationsModule],
      providers: [
        { provide: Router, useValue: { navigate: routerNavigate } },
        {
          provide: ApprovalService,
          useValue: { subscribe, cancelSubscription },
        },
        SessionStateService,
        {
          provide: ActivatedRoute,
          useValue: {
            snapshot: {
              paramMap: convertToParamMap({ id: 'test-session-123' }),
            },
          },
        },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(SessionComponent);
    component = fixture.componentInstance;
    sessionState = TestBed.inject(SessionStateService);
  });

  it('should create', () => {
    fixture.detectChanges();
    expect(component).toBeTruthy();
  });

  describe('initialization', () => {
    it('should set session ID from route parameter', () => {
      fixture.detectChanges();
      expect(sessionState.sessionId()).toBe('test-session-123');
    });

    it('should redirect to home if no session ID', async () => {
      // Reconfigure with no session ID
      TestBed.resetTestingModule();

      await TestBed.configureTestingModule({
        imports: [SessionComponent, NoopAnimationsModule],
        providers: [
          { provide: Router, useValue: { navigate: routerNavigate } },
          {
            provide: ApprovalService,
            useValue: { subscribe, cancelSubscription },
          },
          SessionStateService,
          {
            provide: ActivatedRoute,
            useValue: {
              snapshot: {
                paramMap: convertToParamMap({}),
              },
            },
          },
        ],
      }).compileComponents();

      const newFixture = TestBed.createComponent(SessionComponent);
      newFixture.detectChanges();

      expect(routerNavigate).toHaveBeenCalledWith(['/']);
    });

    it('should start subscription on init', () => {
      fixture.detectChanges();
      expect(subscribe).toHaveBeenCalledWith('test-session-123', expect.any(String));
    });

    it('should set connection status to connecting', () => {
      fixture.detectChanges();
      expect(sessionState.connectionStatus()).toBe('connecting');
    });
  });

  describe('cleanup', () => {
    it('should cancel subscription on destroy', () => {
      fixture.detectChanges();
      component.ngOnDestroy();
      expect(cancelSubscription).toHaveBeenCalled();
    });

    it('should reset state on destroy', () => {
      fixture.detectChanges();
      sessionState.setConnectionStatus('connected');
      component.ngOnDestroy();
      expect(sessionState.connectionStatus()).toBe('disconnected');
    });
  });

  describe('leaveSession', () => {
    it('should navigate to home', () => {
      fixture.detectChanges();
      component.leaveSession();
      expect(routerNavigate).toHaveBeenCalledWith(['/']);
    });
  });

  describe('UI rendering', () => {
    it('should show session ID in toolbar', () => {
      fixture.detectChanges();
      const compiled = fixture.nativeElement as HTMLElement;
      expect(compiled.textContent).toContain('Session');
    });

    it('should have connection status component', () => {
      fixture.detectChanges();
      const compiled = fixture.nativeElement as HTMLElement;
      expect(compiled.querySelector('app-connection-status')).toBeTruthy();
    });

    it('should have history panel component', () => {
      fixture.detectChanges();
      const compiled = fixture.nativeElement as HTMLElement;
      expect(compiled.querySelector('app-history-panel')).toBeTruthy();
    });

    it('should have decision panel component', () => {
      fixture.detectChanges();
      const compiled = fixture.nativeElement as HTMLElement;
      expect(compiled.querySelector('app-decision-panel')).toBeTruthy();
    });
  });
});
