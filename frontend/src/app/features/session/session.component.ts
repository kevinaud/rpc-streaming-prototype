/**
 * Session component - main view for the Approver.
 * Displays connection status, proposal history, and decision panel.
 */
import { ChangeDetectionStrategy, Component, DestroyRef, inject, type OnInit } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatToolbarModule } from '@angular/material/toolbar';
import { ActivatedRoute, Router } from '@angular/router';
import { v4 as uuidv4 } from 'uuid';

import { ApprovalService } from '../../core/services/approval.service';
import { SessionStateService } from '../../core/services/session-state.service';
import type { SessionEvent } from '../../generated/proposal/v1/session_pb';
import { ConnectionStatusComponent } from './components/connection-status/connection-status.component';
import { DecisionPanelComponent } from './components/decision-panel/decision-panel.component';
import { HistoryPanelComponent } from './components/history-panel/history-panel.component';

@Component({
  selector: 'app-session',
  standalone: true,
  imports: [
    MatToolbarModule,
    MatButtonModule,
    MatIconModule,
    ConnectionStatusComponent,
    HistoryPanelComponent,
    DecisionPanelComponent,
  ],
  templateUrl: './session.component.html',
  styleUrl: './session.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class SessionComponent implements OnInit {
  private readonly destroyRef = inject(DestroyRef);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly approvalService = inject(ApprovalService);
  readonly sessionState = inject(SessionStateService);

  private clientId = uuidv4();
  private reconnectAttempts = 0;
  private readonly maxReconnectAttempts = 5;
  private readonly reconnectDelayMs = 2000;
  private abortController: AbortController | null = null;

  constructor() {
    // Register cleanup on destroy
    this.destroyRef.onDestroy(() => {
      this.abortController?.abort();
      this.approvalService.cancelSubscription();
      this.sessionState.reset();
    });
  }

  ngOnInit(): void {
    const sessionId = this.route.snapshot.paramMap.get('id');
    if (!sessionId) {
      void this.router.navigate(['/']);
      return;
    }

    this.sessionState.setSessionId(sessionId);
    void this.startSubscription(sessionId);
  }

  private async startSubscription(sessionId: string): Promise<void> {
    // Cancel any existing subscription
    this.abortController?.abort();
    this.abortController = new AbortController();

    this.sessionState.setConnectionStatus('connecting');

    try {
      for await (const response of this.approvalService.subscribe(sessionId, this.clientId)) {
        if (this.abortController.signal.aborted) break;

        // Successfully connected
        if (this.sessionState.connectionStatus() !== 'connected') {
          this.sessionState.setConnectionStatus('connected');
          this.reconnectAttempts = 0;
        }

        // Process the event using discriminated union pattern
        const sessionEvent = response.event;
        if (sessionEvent) {
          this.processSessionEvent(sessionEvent);
        }
      }

      // Stream ended normally
      if (!this.abortController.signal.aborted) {
        this.handleDisconnect(sessionId);
      }
    } catch (error) {
      console.error('Subscription error:', error);
      if (!this.abortController.signal.aborted) {
        this.handleDisconnect(sessionId);
      }
    }
  }

  private processSessionEvent(sessionEvent: SessionEvent): void {
    const event = sessionEvent.event;
    switch (event.case) {
      case 'proposalCreated': {
        // Use upsert to handle reconnection scenarios where history is replayed
        this.sessionState.upsertProposal(event.value);
        break;
      }
      case 'proposalUpdated': {
        this.sessionState.upsertProposal(event.value);
        break;
      }
    }
  }

  private handleDisconnect(sessionId: string): void {
    if (this.abortController?.signal.aborted) return;

    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      this.sessionState.setConnectionStatus('reconnecting');
      setTimeout(() => {
        if (!this.abortController?.signal.aborted) {
          void this.startSubscription(sessionId);
        }
      }, this.reconnectDelayMs);
    } else {
      this.sessionState.setError('Connection lost. Please refresh the page to reconnect.');
    }
  }

  leaveSession(): void {
    void this.router.navigate(['/']);
  }
}
