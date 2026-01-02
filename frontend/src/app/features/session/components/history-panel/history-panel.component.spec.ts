/**
 * Unit tests for HistoryPanelComponent.
 * Tests proposal history display and formatting.
 */
import { type ComponentFixture, TestBed } from '@angular/core/testing';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { create } from '@bufbuild/protobuf';

import { SessionStateService } from '../../../../core/services/session-state.service';
import { ProposalSchema, ProposalStatus } from '../../../../generated/proposal/v1/proposal_pb';
import { HistoryPanelComponent } from './history-panel.component';

describe('HistoryPanelComponent', () => {
  let component: HistoryPanelComponent;
  let fixture: ComponentFixture<HistoryPanelComponent>;
  let sessionState: SessionStateService;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [HistoryPanelComponent, NoopAnimationsModule],
      providers: [SessionStateService],
    }).compileComponents();

    fixture = TestBed.createComponent(HistoryPanelComponent);
    component = fixture.componentInstance;
    sessionState = TestBed.inject(SessionStateService);
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  describe('getStatusConfig', () => {
    it('should return correct config for APPROVED status', () => {
      const config = component.getStatusConfig(ProposalStatus.APPROVED);
      expect(config.label).toBe('Approved');
      expect(config.icon).toBe('check_circle');
      expect(config.cssClass).toBe('approved');
    });

    it('should return correct config for REJECTED status', () => {
      const config = component.getStatusConfig(ProposalStatus.REJECTED);
      expect(config.label).toBe('Rejected');
      expect(config.icon).toBe('cancel');
      expect(config.cssClass).toBe('rejected');
    });

    it('should return correct config for PENDING status', () => {
      const config = component.getStatusConfig(ProposalStatus.PENDING);
      expect(config.label).toBe('Pending');
      expect(config.icon).toBe('hourglass_empty');
      expect(config.cssClass).toBe('pending');
    });

    it('should return correct config for UNSPECIFIED status', () => {
      const config = component.getStatusConfig(ProposalStatus.UNSPECIFIED);
      expect(config.label).toBe('Unknown');
      expect(config.icon).toBe('help');
      expect(config.cssClass).toBe('');
    });
  });

  describe('trackByProposalId', () => {
    it('should return proposal ID', () => {
      const proposal = create(ProposalSchema, {
        proposalId: 'test-id-123',
        text: 'Test',
        status: ProposalStatus.PENDING,
      });
      expect(component.trackByProposalId(0, proposal)).toBe('test-id-123');
    });
  });

  describe('UI rendering', () => {
    it('should show empty state when no proposals', () => {
      const compiled = fixture.nativeElement as HTMLElement;
      expect(compiled.textContent).toContain('No proposals yet');
    });

    it('should show proposals when history exists', () => {
      sessionState.addProposal(
        create(ProposalSchema, {
          proposalId: 'prop-1',
          text: 'Test proposal',
          status: ProposalStatus.APPROVED,
        }),
      );
      fixture.detectChanges();

      const compiled = fixture.nativeElement as HTMLElement;
      expect(compiled.textContent).toContain('Test proposal');
    });

    it('should display status chip', () => {
      sessionState.addProposal(
        create(ProposalSchema, {
          proposalId: 'prop-1',
          text: 'Test proposal',
          status: ProposalStatus.APPROVED,
        }),
      );
      fixture.detectChanges();

      const compiled = fixture.nativeElement as HTMLElement;
      expect(compiled.textContent).toContain('Approved');
    });
  });
});
