/**
 * Session component - main view for the Approver.
 * Displays connection status, proposal history, and decision panel.
 */
import { Component, OnInit, OnDestroy, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router } from '@angular/router';
import { MatToolbarModule } from '@angular/material/toolbar';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { ApprovalService } from '../../core/services/approval.service';
import { SessionStateService } from '../../core/services/session-state.service';
import { ConnectionStatusComponent } from './components/connection-status/connection-status.component';
import { HistoryPanelComponent } from './components/history-panel/history-panel.component';
import { DecisionPanelComponent } from './components/decision-panel/decision-panel.component';
import { v4 as uuidv4 } from 'uuid';
import type { SessionEvent } from '../../generated/proposal/v1/session_pb';

@Component({
  selector: 'app-session',
  standalone: true,
  imports: [
    CommonModule,
    MatToolbarModule,
    MatButtonModule,
    MatIconModule,
    ConnectionStatusComponent,
    HistoryPanelComponent,
    DecisionPanelComponent,
  ],
  templateUrl: './session.component.html',
  styleUrl: './session.component.scss',
})
export class SessionComponent implements OnInit, OnDestroy {
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly approvalService = inject(ApprovalService);
  readonly sessionState = inject(SessionStateService);

  private clientId = uuidv4();
  private reconnectAttempts = 0;
  private readonly maxReconnectAttempts = 5;
  private readonly reconnectDelayMs = 2000;
  private isDestroyed = false;

  ngOnInit(): void {
    const sessionId = this.route.snapshot.paramMap.get('id');
    if (!sessionId) {
      this.router.navigate(['/']);
      return;
    }

    this.sessionState.setSessionId(sessionId);
    this.startSubscription(sessionId);
  }

  ngOnDestroy(): void {
    this.isDestroyed = true;
    this.approvalService.cancelSubscription();
    this.sessionState.reset();
  }

  private async startSubscription(sessionId: string): Promise<void> {
    this.sessionState.setConnectionStatus('connecting');

    try {
      for await (const response of this.approvalService.subscribe(sessionId, this.clientId)) {
        if (this.isDestroyed) break;

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
      if (!this.isDestroyed) {
        this.handleDisconnect(sessionId);
      }
    } catch (error) {
      console.error('Subscription error:', error);
      if (!this.isDestroyed) {
        this.handleDisconnect(sessionId);
      }
    }
  }

  private processSessionEvent(sessionEvent: SessionEvent): void {
    const event = sessionEvent.event;
    switch (event.case) {
      case 'proposalCreated':
        this.sessionState.addProposal(event.value);
        break;
      case 'proposalUpdated':
        this.sessionState.upsertProposal(event.value);
        break;
    }
  }

  private handleDisconnect(sessionId: string): void {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      this.sessionState.setConnectionStatus('reconnecting');
      setTimeout(() => {
        if (!this.isDestroyed) {
          this.startSubscription(sessionId);
        }
      }, this.reconnectDelayMs);
    } else {
      this.sessionState.setError('Connection lost. Please refresh the page to reconnect.');
    }
  }

  leaveSession(): void {
    this.router.navigate(['/']);
  }
}
