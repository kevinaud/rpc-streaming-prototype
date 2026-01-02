/**
 * History panel component.
 * Displays the list of past proposals and their outcomes.
 */
import { DatePipe } from '@angular/common';
import { ChangeDetectionStrategy, Component, inject } from '@angular/core';
import { MatCardModule } from '@angular/material/card';
import { MatChipsModule } from '@angular/material/chips';
import { MatIconModule } from '@angular/material/icon';
import { timestampDate } from '@bufbuild/protobuf/wkt';

import { SessionStateService } from '../../../../core/services/session-state.service';
import { type Proposal, ProposalStatus } from '../../../../generated/proposal/v1/proposal_pb';

/** Configuration for each proposal status display. */
interface StatusConfig {
  readonly label: string;
  readonly icon: string;
  readonly cssClass: string;
}

/** Lookup map for status display configuration. */
const STATUS_CONFIG: Readonly<Record<ProposalStatus, StatusConfig>> = {
  [ProposalStatus.APPROVED]: { label: 'Approved', icon: 'check_circle', cssClass: 'approved' },
  [ProposalStatus.REJECTED]: { label: 'Rejected', icon: 'cancel', cssClass: 'rejected' },
  [ProposalStatus.PENDING]: { label: 'Pending', icon: 'hourglass_empty', cssClass: 'pending' },
  [ProposalStatus.UNSPECIFIED]: { label: 'Unknown', icon: 'help', cssClass: '' },
};

@Component({
  selector: 'app-history-panel',
  standalone: true,
  imports: [MatCardModule, MatIconModule, MatChipsModule, DatePipe],
  templateUrl: './history-panel.component.html',
  styleUrl: './history-panel.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class HistoryPanelComponent {
  readonly sessionState = inject(SessionStateService);

  /** Get the full status configuration for a proposal status. */
  getStatusConfig(status: ProposalStatus): StatusConfig {
    return STATUS_CONFIG[status];
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
