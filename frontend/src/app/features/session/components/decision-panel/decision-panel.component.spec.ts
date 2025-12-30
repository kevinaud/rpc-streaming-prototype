/**
 * Unit tests for DecisionPanelComponent.
 * Tests decision submission and UI states.
 */
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { vi } from 'vitest';
import { DecisionPanelComponent } from './decision-panel.component';
import { ApprovalService } from '../../../../core/services/approval.service';
import { SessionStateService } from '../../../../core/services/session-state.service';
import { ProposalStatus, ProposalSchema } from '../../../../generated/proposal/v1/proposal_pb';
import { create } from '@bufbuild/protobuf';

describe('DecisionPanelComponent', () => {
  let component: DecisionPanelComponent;
  let fixture: ComponentFixture<DecisionPanelComponent>;
  let submitDecision: ReturnType<typeof vi.fn>;
  let sessionState: SessionStateService;

  beforeEach(async () => {
    submitDecision = vi.fn().mockResolvedValue({});

    await TestBed.configureTestingModule({
      imports: [DecisionPanelComponent, NoopAnimationsModule],
      providers: [{ provide: ApprovalService, useValue: { submitDecision } }, SessionStateService],
    }).compileComponents();

    fixture = TestBed.createComponent(DecisionPanelComponent);
    component = fixture.componentInstance;
    sessionState = TestBed.inject(SessionStateService);
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  describe('UI states', () => {
    it('should show waiting state when no pending proposal', () => {
      const compiled = fixture.nativeElement as HTMLElement;
      expect(compiled.textContent).toContain('Waiting for proposal');
    });

    it('should show proposal when pending proposal exists', () => {
      sessionState.setSessionId('test-session');
      sessionState.addProposal(
        create(ProposalSchema, {
          proposalId: 'prop-1',
          text: 'Review this proposal',
          status: ProposalStatus.PENDING,
        }),
      );
      fixture.detectChanges();

      const compiled = fixture.nativeElement as HTMLElement;
      expect(compiled.textContent).toContain('Review this proposal');
    });

    it('should show approve and reject buttons for pending proposal', () => {
      sessionState.setSessionId('test-session');
      sessionState.addProposal(
        create(ProposalSchema, {
          proposalId: 'prop-1',
          text: 'Test',
          status: ProposalStatus.PENDING,
        }),
      );
      fixture.detectChanges();

      const compiled = fixture.nativeElement as HTMLElement;
      const buttons = compiled.querySelectorAll('button');
      expect(buttons.length).toBeGreaterThanOrEqual(2);
      expect(compiled.textContent).toContain('Approve');
      expect(compiled.textContent).toContain('Reject');
    });
  });

  describe('submitDecision', () => {
    beforeEach(() => {
      sessionState.setSessionId('test-session');
      sessionState.setConnectionStatus('connected');
      sessionState.addProposal(
        create(ProposalSchema, {
          proposalId: 'prop-1',
          text: 'Test',
          status: ProposalStatus.PENDING,
        }),
      );
      fixture.detectChanges();
    });

    it('should call approval service with correct parameters for approve', async () => {
      await component.submitDecision(true);
      expect(submitDecision).toHaveBeenCalledWith('test-session', 'prop-1', true);
    });

    it('should call approval service with correct parameters for reject', async () => {
      await component.submitDecision(false);
      expect(submitDecision).toHaveBeenCalledWith('test-session', 'prop-1', false);
    });

    it('should set isSubmitting during submission', async () => {
      let resolvePromise: () => void;
      const controlledPromise = new Promise<unknown>((resolve) => {
        resolvePromise = () => resolve({});
      });
      submitDecision.mockReturnValue(controlledPromise);

      const submissionPromise = component.submitDecision(true);
      expect(component.isSubmitting).toBeTruthy();

      resolvePromise!();
      await submissionPromise;
      expect(component.isSubmitting).toBeFalsy();
    });

    it('should not submit when no pending proposal', async () => {
      sessionState.upsertProposal(
        create(ProposalSchema, {
          proposalId: 'prop-1',
          text: 'Test',
          status: ProposalStatus.APPROVED,
        }),
      );
      fixture.detectChanges();

      await component.submitDecision(true);
      expect(submitDecision).not.toHaveBeenCalled();
    });
  });

  describe('button states', () => {
    beforeEach(() => {
      sessionState.setSessionId('test-session');
      sessionState.addProposal(
        create(ProposalSchema, {
          proposalId: 'prop-1',
          text: 'Test',
          status: ProposalStatus.PENDING,
        }),
      );
    });

    it('should disable buttons when disconnected', () => {
      sessionState.setConnectionStatus('disconnected');
      fixture.detectChanges();

      const compiled = fixture.nativeElement as HTMLElement;
      const buttons = compiled.querySelectorAll('button:disabled');
      expect(buttons.length).toBeGreaterThan(0);
    });

    it('should enable buttons when connected', () => {
      sessionState.setConnectionStatus('connected');
      fixture.detectChanges();

      const compiled = fixture.nativeElement as HTMLElement;
      const approveBtn = compiled.querySelector('.approve-button:not(:disabled)');
      const rejectBtn = compiled.querySelector('.reject-button:not(:disabled)');
      expect(approveBtn).toBeTruthy();
      expect(rejectBtn).toBeTruthy();
    });
  });
});
