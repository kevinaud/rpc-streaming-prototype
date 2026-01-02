/**
 * Session state service using Angular Signals for reactive state management.
 *
 * Manages the current session state including:
 * - Connection status
 * - Current session ID
 * - Proposal list
 * - Pending proposal (awaiting decision)
 */
import { computed, Injectable, signal } from '@angular/core';

import type { Proposal } from '../../generated/proposal/v1/proposal_pb';
import { ProposalStatus } from '../../generated/proposal/v1/proposal_pb';

export type ConnectionStatus =
  | 'disconnected'
  | 'connecting'
  | 'connected'
  | 'reconnecting'
  | 'error';

export interface SessionState {
  sessionId: string | null;
  connectionStatus: ConnectionStatus;
  proposals: Proposal[];
  error: string | null;
}

const initialState: SessionState = {
  sessionId: null,
  connectionStatus: 'disconnected',
  proposals: [],
  error: null,
};

@Injectable({
  providedIn: 'root',
})
export class SessionStateService {
  // Private writable signals
  private readonly _sessionId = signal<string | null>(initialState.sessionId);
  private readonly _connectionStatus = signal<ConnectionStatus>(initialState.connectionStatus);
  private readonly _proposals = signal<Proposal[]>(initialState.proposals);
  private readonly _error = signal<string | null>(initialState.error);

  // Public readonly signals
  readonly sessionId = this._sessionId.asReadonly();
  readonly connectionStatus = this._connectionStatus.asReadonly();
  readonly proposals = this._proposals.asReadonly();
  readonly error = this._error.asReadonly();

  // Computed signals
  readonly isConnected = computed(() => this._connectionStatus() === 'connected');
  readonly isConnecting = computed(
    () => this._connectionStatus() === 'connecting' || this._connectionStatus() === 'reconnecting',
  );
  readonly hasError = computed(() => this._error() !== null);

  /**
   * Get the pending proposal (if any) - the most recent proposal awaiting a decision.
   */
  readonly pendingProposal = computed<Proposal | null>(() => {
    const proposals = this._proposals();
    // Find the most recent pending proposal
    for (let i = proposals.length - 1; i >= 0; i--) {
      const proposal = proposals[i];
      if (proposal?.status === ProposalStatus.PENDING) {
        return proposal;
      }
    }
    return null;
  });

  /**
   * Get proposal history (all proposals except the current pending one).
   */
  readonly proposalHistory = computed(() => {
    const pending = this.pendingProposal();
    if (!pending) {
      return this._proposals();
    }
    return this._proposals().filter((p) => p.proposalId !== pending.proposalId);
  });

  /**
   * Set the current session ID.
   */
  setSessionId(sessionId: string): void {
    this._sessionId.set(sessionId);
  }

  /**
   * Update connection status.
   */
  setConnectionStatus(status: ConnectionStatus): void {
    this._connectionStatus.set(status);
    // Clear error when successfully connected
    if (status === 'connected') {
      this._error.set(null);
    }
  }

  /**
   * Set an error message.
   */
  setError(error: string): void {
    this._error.set(error);
    this._connectionStatus.set('error');
  }

  /**
   * Clear the current error.
   */
  clearError(): void {
    this._error.set(null);
  }

  /**
   * Add a new proposal to the list.
   */
  addProposal(proposal: Proposal): void {
    this._proposals.update((proposals) => [...proposals, proposal]);
  }

  /**
   * Update an existing proposal (e.g., when a decision is made).
   */
  updateProposal(updatedProposal: Proposal): void {
    this._proposals.update((proposals) =>
      proposals.map((p) => (p.proposalId === updatedProposal.proposalId ? updatedProposal : p)),
    );
  }

  /**
   * Add or update a proposal based on whether it already exists.
   */
  upsertProposal(proposal: Proposal): void {
    const exists = this._proposals().some((p) => p.proposalId === proposal.proposalId);
    if (exists) {
      this.updateProposal(proposal);
    } else {
      this.addProposal(proposal);
    }
  }

  /**
   * Set the full list of proposals (used when replaying history).
   */
  setProposals(proposals: Proposal[]): void {
    this._proposals.set(proposals);
  }

  /**
   * Reset all state to initial values.
   */
  reset(): void {
    this._sessionId.set(initialState.sessionId);
    this._connectionStatus.set(initialState.connectionStatus);
    this._proposals.set(initialState.proposals);
    this._error.set(initialState.error);
  }
}
