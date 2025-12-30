/**
 * Unit tests for HistoryPanelComponent.
 * Tests proposal history display and formatting.
 */
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { HistoryPanelComponent } from './history-panel.component';
import { SessionStateService } from '../../../../core/services/session-state.service';
import { ProposalStatus, ProposalSchema } from '../../../../generated/proposal/v1/proposal_pb';
import { create } from '@bufbuild/protobuf';

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

  describe('getStatusLabel', () => {
    it('should return "Approved" for APPROVED status', () => {
      expect(component.getStatusLabel(ProposalStatus.APPROVED)).toBe('Approved');
    });

    it('should return "Rejected" for REJECTED status', () => {
      expect(component.getStatusLabel(ProposalStatus.REJECTED)).toBe('Rejected');
    });

    it('should return "Pending" for PENDING status', () => {
      expect(component.getStatusLabel(ProposalStatus.PENDING)).toBe('Pending');
    });

    it('should return "Unknown" for UNSPECIFIED status', () => {
      expect(component.getStatusLabel(ProposalStatus.UNSPECIFIED)).toBe('Unknown');
    });
  });

  describe('getStatusIcon', () => {
    it('should return check_circle for APPROVED', () => {
      expect(component.getStatusIcon(ProposalStatus.APPROVED)).toBe('check_circle');
    });

    it('should return cancel for REJECTED', () => {
      expect(component.getStatusIcon(ProposalStatus.REJECTED)).toBe('cancel');
    });

    it('should return hourglass_empty for PENDING', () => {
      expect(component.getStatusIcon(ProposalStatus.PENDING)).toBe('hourglass_empty');
    });

    it('should return help for UNSPECIFIED', () => {
      expect(component.getStatusIcon(ProposalStatus.UNSPECIFIED)).toBe('help');
    });
  });

  describe('getStatusClass', () => {
    it('should return approved class for APPROVED', () => {
      expect(component.getStatusClass(ProposalStatus.APPROVED)).toBe('approved');
    });

    it('should return rejected class for REJECTED', () => {
      expect(component.getStatusClass(ProposalStatus.REJECTED)).toBe('rejected');
    });

    it('should return pending class for PENDING', () => {
      expect(component.getStatusClass(ProposalStatus.PENDING)).toBe('pending');
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
