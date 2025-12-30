/**
 * Decision panel component.
 * Displays the current pending proposal and approve/reject buttons.
 */
import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { ApprovalService } from '../../../../core/services/approval.service';
import { SessionStateService } from '../../../../core/services/session-state.service';

@Component({
  selector: 'app-decision-panel',
  standalone: true,
  imports: [CommonModule, MatCardModule, MatButtonModule, MatIconModule, MatProgressSpinnerModule],
  templateUrl: './decision-panel.component.html',
  styleUrl: './decision-panel.component.scss',
})
export class DecisionPanelComponent {
  private readonly approvalService = inject(ApprovalService);
  readonly sessionState = inject(SessionStateService);

  isSubmitting = false;

  async submitDecision(approved: boolean): Promise<void> {
    const pending = this.sessionState.pendingProposal();
    const sessionId = this.sessionState.sessionId();

    if (!pending || !sessionId || this.isSubmitting) {
      return;
    }

    this.isSubmitting = true;

    try {
      const response = await this.approvalService.submitDecision(
        sessionId,
        pending.proposalId,
        approved,
      );

      // The subscription will receive the update event,
      // but we can also update locally for immediate feedback
      if (response.proposal) {
        this.sessionState.updateProposal(response.proposal);
      }
    } catch (error) {
      console.error('Failed to submit decision:', error);
      this.sessionState.setError('Failed to submit decision. Please try again.');
    } finally {
      this.isSubmitting = false;
    }
  }
}
