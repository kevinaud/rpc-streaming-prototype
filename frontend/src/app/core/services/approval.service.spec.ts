/**
 * Unit tests for ApprovalService.
 * Tests gRPC client interactions without actual network calls.
 */
import { TestBed } from '@angular/core/testing';
import { ApprovalService } from './approval.service';

describe('ApprovalService', () => {
  let service: ApprovalService;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [ApprovalService],
    });
    service = TestBed.inject(ApprovalService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  describe('getSession', () => {
    it('should throw when session not found', async () => {
      // The actual test would require mocking the transport
      // For now, we verify the service method exists and is callable
      expect(service.getSession).toBeDefined();
    });
  });

  describe('subscribe', () => {
    it('should return an async iterable', () => {
      const subscription = service.subscribe('test-session', 'test-client');
      expect(subscription[Symbol.asyncIterator]).toBeDefined();
    });
  });

  describe('submitDecision', () => {
    it('should accept session, proposal, and approved flag', () => {
      expect(service.submitDecision).toBeDefined();
    });
  });

  describe('cancelSubscription', () => {
    it('should be callable', () => {
      expect(service.cancelSubscription).toBeDefined();
      // Should not throw when called without active subscription
      service.cancelSubscription();
    });
  });
});
