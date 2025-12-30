/**
 * Unit tests for SessionStateService.
 * Tests Angular Signals-based state management.
 */
import { TestBed } from '@angular/core/testing';
import { create } from '@bufbuild/protobuf';

import { type Proposal, ProposalStatus } from '../../generated/proposal/v1/proposal_pb';
import { ProposalSchema } from '../../generated/proposal/v1/proposal_pb';
import { SessionStateService } from './session-state.service';

describe('SessionStateService', () => {
  let service: SessionStateService;

  // Helper to create a test proposal
  function createTestProposal(
    id: string,
    status: ProposalStatus = ProposalStatus.PENDING,
    text = 'Test proposal',
  ): Proposal {
    return create(ProposalSchema, {
      proposalId: id,
      text,
      status,
    });
  }

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [SessionStateService],
    });
    service = TestBed.inject(SessionStateService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  describe('initial state', () => {
    it('should have null sessionId', () => {
      expect(service.sessionId()).toBeNull();
    });

    it('should have disconnected status', () => {
      expect(service.connectionStatus()).toBe('disconnected');
    });

    it('should have empty proposals', () => {
      expect(service.proposals()).toEqual([]);
    });

    it('should have null error', () => {
      expect(service.error()).toBeNull();
    });
  });

  describe('setSessionId', () => {
    it('should update sessionId', () => {
      service.setSessionId('test-session-123');
      expect(service.sessionId()).toBe('test-session-123');
    });
  });

  describe('setConnectionStatus', () => {
    it('should update connection status', () => {
      service.setConnectionStatus('connecting');
      expect(service.connectionStatus()).toBe('connecting');

      service.setConnectionStatus('connected');
      expect(service.connectionStatus()).toBe('connected');

      service.setConnectionStatus('reconnecting');
      expect(service.connectionStatus()).toBe('reconnecting');
    });
  });

  describe('setError', () => {
    it('should update error', () => {
      service.setError('Connection failed');
      expect(service.error()).toBe('Connection failed');
    });
  });

  describe('addProposal', () => {
    it('should add a proposal to the list', () => {
      const proposal = createTestProposal('prop-1');
      service.addProposal(proposal);

      expect(service.proposals().length).toBe(1);
      expect(service.proposals()[0]!.proposalId).toBe('prop-1');
    });

    it('should add multiple proposals', () => {
      service.addProposal(createTestProposal('prop-1'));
      service.addProposal(createTestProposal('prop-2'));

      expect(service.proposals().length).toBe(2);
    });
  });

  describe('upsertProposal', () => {
    it('should add new proposal if not exists', () => {
      const proposal = createTestProposal('prop-1');
      service.upsertProposal(proposal);

      expect(service.proposals().length).toBe(1);
    });

    it('should update existing proposal', () => {
      service.addProposal(createTestProposal('prop-1', ProposalStatus.PENDING));

      const updated = createTestProposal('prop-1', ProposalStatus.APPROVED);
      service.upsertProposal(updated);

      expect(service.proposals().length).toBe(1);
      expect(service.proposals()[0]!.status).toBe(ProposalStatus.APPROVED);
    });
  });

  describe('pendingProposal', () => {
    it('should return null when no proposals', () => {
      expect(service.pendingProposal()).toBeNull();
    });

    it('should return the pending proposal', () => {
      service.addProposal(createTestProposal('prop-1', ProposalStatus.PENDING));
      service.addProposal(createTestProposal('prop-2', ProposalStatus.APPROVED));

      const pending = service.pendingProposal();
      expect(pending).toBeTruthy();
      expect(pending!.proposalId).toBe('prop-1');
    });

    it('should return null when no pending proposals', () => {
      service.addProposal(createTestProposal('prop-1', ProposalStatus.APPROVED));
      expect(service.pendingProposal()).toBeNull();
    });
  });

  describe('proposalHistory', () => {
    it('should return empty array when no proposals', () => {
      expect(service.proposalHistory()).toEqual([]);
    });

    it('should return non-pending proposals', () => {
      service.addProposal(createTestProposal('prop-1', ProposalStatus.APPROVED));
      service.addProposal(createTestProposal('prop-2', ProposalStatus.REJECTED));
      service.addProposal(createTestProposal('prop-3', ProposalStatus.PENDING));

      const history = service.proposalHistory();
      // History excludes the pending proposal
      expect(history.length).toBe(2);
      expect(history.find((p) => p.proposalId === 'prop-3')).toBeFalsy();
    });

    it('should return all proposals when none are pending', () => {
      service.addProposal(createTestProposal('prop-1', ProposalStatus.APPROVED));
      service.addProposal(createTestProposal('prop-2', ProposalStatus.REJECTED));
      service.addProposal(createTestProposal('prop-3', ProposalStatus.APPROVED));

      const history = service.proposalHistory();
      expect(history.length).toBe(3);
    });
  });

  describe('isConnected', () => {
    it('should return false when disconnected', () => {
      service.setConnectionStatus('disconnected');
      expect(service.isConnected()).toBe(false);
    });

    it('should return false when connecting', () => {
      service.setConnectionStatus('connecting');
      expect(service.isConnected()).toBe(false);
    });

    it('should return true when connected', () => {
      service.setConnectionStatus('connected');
      expect(service.isConnected()).toBe(true);
    });

    it('should return false when reconnecting', () => {
      service.setConnectionStatus('reconnecting');
      expect(service.isConnected()).toBe(false);
    });
  });

  describe('reset', () => {
    it('should reset all state', () => {
      service.setSessionId('test-session');
      service.setConnectionStatus('connected');
      service.addProposal(createTestProposal('prop-1'));
      service.setError('Some error');

      service.reset();

      expect(service.sessionId()).toBeNull();
      expect(service.connectionStatus()).toBe('disconnected');
      expect(service.proposals()).toEqual([]);
      expect(service.error()).toBeNull();
    });
  });
});
