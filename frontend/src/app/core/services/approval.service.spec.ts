/**
 * Unit tests for ApprovalService.
 *
 * Note: ApprovalService is a thin wrapper around Connect-ES gRPC client.
 * Testing the actual RPC behavior would require either:
 * - A running backend (integration test)
 * - A fake transport implementation
 *
 * For this learning prototype, we test only the service's own logic
 * (subscription lifecycle management) rather than the underlying gRPC client.
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

  describe('subscribe', () => {
    it('should return an async iterable', () => {
      const subscription = service.subscribe('test-session', 'test-client');
      expect(subscription[Symbol.asyncIterator]).toBeDefined();
    });
  });

  describe('cancelSubscription', () => {
    it('should not throw when called without active subscription', () => {
      expect(() => service.cancelSubscription()).not.toThrow();
    });

    it('should be idempotent', () => {
      service.cancelSubscription();
      expect(() => service.cancelSubscription()).not.toThrow();
    });
  });
});
