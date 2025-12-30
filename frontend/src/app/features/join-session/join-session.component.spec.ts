/**
 * Unit tests for JoinSessionComponent.
 * Tests form validation and navigation.
 */
import { type ComponentFixture, TestBed } from '@angular/core/testing';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { Router } from '@angular/router';
import { vi } from 'vitest';

import { ApprovalService } from '../../core/services/approval.service';
import { SessionStateService } from '../../core/services/session-state.service';
import { JoinSessionComponent } from './join-session.component';

describe('JoinSessionComponent', () => {
  let component: JoinSessionComponent;
  let fixture: ComponentFixture<JoinSessionComponent>;
  let routerNavigate: ReturnType<typeof vi.fn>;
  let getSession: ReturnType<typeof vi.fn>;

  beforeEach(async () => {
    routerNavigate = vi.fn().mockResolvedValue(true);
    getSession = vi.fn().mockResolvedValue({ session: { sessionId: 'test-session' } });

    await TestBed.configureTestingModule({
      imports: [JoinSessionComponent, NoopAnimationsModule],
      providers: [
        { provide: Router, useValue: { navigate: routerNavigate } },
        { provide: ApprovalService, useValue: { getSession } },
        SessionStateService,
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(JoinSessionComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  describe('form initialization', () => {
    it('should have empty sessionId initially', () => {
      expect(component.form.get('sessionId')?.value).toBe('');
    });

    it('should have sessionId field required', () => {
      const control = component.form.get('sessionId');
      control?.setValue('');
      expect(control?.valid).toBeFalsy();
    });
  });

  describe('form validation', () => {
    it('should be invalid when sessionId is empty', () => {
      expect(component.form.valid).toBeFalsy();
    });

    it('should be valid when sessionId is provided', () => {
      component.form.get('sessionId')?.setValue('test-session-123');
      expect(component.form.valid).toBeTruthy();
    });
  });

  describe('form submission', () => {
    it('should not navigate when form is invalid', async () => {
      component.form.get('sessionId')?.setValue('');
      await component.onSubmit();
      expect(routerNavigate).not.toHaveBeenCalled();
    });

    it('should navigate to session when form is valid', async () => {
      component.form.get('sessionId')?.setValue('test-session-123');
      await component.onSubmit();
      expect(routerNavigate).toHaveBeenCalledWith(['/session', 'test-session-123']);
    });

    it('should trim whitespace from sessionId', async () => {
      component.form.get('sessionId')?.setValue('  session-with-spaces  ');
      await component.onSubmit();
      expect(routerNavigate).toHaveBeenCalledWith(['/session', 'session-with-spaces']);
    });

    it('should verify session exists before navigating', async () => {
      component.form.get('sessionId')?.setValue('test-session-123');
      await component.onSubmit();
      expect(getSession).toHaveBeenCalledWith('test-session-123');
    });

    it('should show error when session not found', async () => {
      getSession.mockRejectedValue(new Error('Session not found'));
      component.form.get('sessionId')?.setValue('invalid-session');
      await component.onSubmit();
      expect(component.errorMessage).toBeTruthy();
      expect(routerNavigate).not.toHaveBeenCalled();
    });

    it('should set loading state during submission', async () => {
      let resolvePromise: () => void;
      const controlledPromise = new Promise<void>((resolve) => {
        resolvePromise = resolve;
      });
      getSession.mockReturnValue(controlledPromise);

      component.form.get('sessionId')?.setValue('test-session-123');
      const submitPromise = component.onSubmit();

      expect(component.isLoading).toBeTruthy();

      resolvePromise!();
      await submitPromise;

      expect(component.isLoading).toBeFalsy();
    });
  });

  describe('UI rendering', () => {
    it('should show form title', () => {
      const compiled = fixture.nativeElement as HTMLElement;
      expect(compiled.textContent).toContain('Join Session');
    });

    it('should have submit button', () => {
      const compiled = fixture.nativeElement as HTMLElement;
      const button = compiled.querySelector('button[type="submit"]');
      expect(button).toBeTruthy();
    });
  });
});
