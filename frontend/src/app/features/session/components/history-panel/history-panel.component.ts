/**
 * History panel component.
 * Displays the list of past proposals and their outcomes.
 */
import { DatePipe } from '@angular/common';
import { ChangeDetectionStrategy, Component, inject } from '@angular/core';
import { MatCardModule } from '@angular/material/card';
import { MatChipsModule } from '@angular/material/chips';
import { MatIconModule } from '@angular/material/icon';
import { MatListModule } from '@angular/material/list';
import { timestampDate } from '@bufbuild/protobuf/wkt';

import { SessionStateService } from '../../../../core/services/session-state.service';
import { type Proposal, ProposalStatus } from '../../../../generated/proposal/v1/proposal_pb';

@Component({
  selector: 'app-history-panel',
  standalone: true,
  imports: [MatCardModule, MatListModule, MatIconModule, MatChipsModule, DatePipe],
  templateUrl: './history-panel.component.html',
  styleUrl: './history-panel.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class HistoryPanelComponent {
  readonly sessionState = inject(SessionStateService);

  getStatusLabel(status: ProposalStatus): string {
    switch (status) {
      case ProposalStatus.APPROVED: {
        return 'Approved';
      }
      case ProposalStatus.REJECTED: {
        return 'Rejected';
      }
      case ProposalStatus.PENDING: {
        return 'Pending';
      }
      default: {
        return 'Unknown';
      }
    }
  }

  getStatusIcon(status: ProposalStatus): string {
    switch (status) {
      case ProposalStatus.APPROVED: {
        return 'check_circle';
      }
      case ProposalStatus.REJECTED: {
        return 'cancel';
      }
      case ProposalStatus.PENDING: {
        return 'hourglass_empty';
      }
      default: {
        return 'help';
      }
    }
  }

  getStatusClass(status: ProposalStatus): string {
    switch (status) {
      case ProposalStatus.APPROVED: {
        return 'approved';
      }
      case ProposalStatus.REJECTED: {
        return 'rejected';
      }
      case ProposalStatus.PENDING: {
        return 'pending';
      }
      default: {
        return '';
      }
    }
  }

  trackByProposalId(_index: number, proposal: Proposal): string {
    return proposal.proposalId;
  }

  /**
   * Convert protobuf Timestamp to JavaScript Date.
   */
  toDate(proposal: Proposal): Date | null {
    return proposal.createdAt ? timestampDate(proposal.createdAt) : null;
  }
}
