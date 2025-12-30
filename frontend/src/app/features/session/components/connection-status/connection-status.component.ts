/**
 * Connection status indicator component.
 * Shows the current connection state with appropriate visual feedback.
 */
import { ChangeDetectionStrategy, Component, inject } from '@angular/core';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';

import { SessionStateService } from '../../../../core/services/session-state.service';

@Component({
  selector: 'app-connection-status',
  standalone: true,
  imports: [MatIconModule, MatProgressSpinnerModule],
  template: `
    <div class="connection-status" [class]="sessionState.connectionStatus()">
      @switch (sessionState.connectionStatus()) {
        @case ('connected') {
          <mat-icon>cloud_done</mat-icon>
          <span>Connected</span>
        }
        @case ('connecting') {
          <mat-spinner diameter="16" />
          <span>Connecting...</span>
        }
        @case ('reconnecting') {
          <mat-spinner diameter="16" />
          <span>Reconnecting...</span>
        }
        @case ('error') {
          <mat-icon>cloud_off</mat-icon>
          <span>Disconnected</span>
        }
        @default {
          <mat-icon>cloud_off</mat-icon>
          <span>Not connected</span>
        }
      }
    </div>
  `,
  styles: [
    `
      .connection-status {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0 1rem;
        font-size: 0.875rem;

        &.connected {
          color: #4caf50;
        }

        &.connecting,
        &.reconnecting {
          color: #ff9800;
        }

        &.error,
        &.disconnected {
          color: #f44336;
        }
      }

      mat-icon {
        font-size: 18px;
        width: 18px;
        height: 18px;
      }
    `,
  ],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ConnectionStatusComponent {
  readonly sessionState = inject(SessionStateService);
}
