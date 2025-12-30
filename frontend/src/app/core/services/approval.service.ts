/**
 * Approval service for communicating with the backend via gRPC-Web.
 *
 * Uses Connect-ES v2 with gRPC-Web transport through Envoy proxy.
 */
import { Injectable, type OnDestroy } from '@angular/core';
import { create } from '@bufbuild/protobuf';
import { type Client, createClient, type Transport } from '@connectrpc/connect';
import { createGrpcWebTransport } from '@connectrpc/connect-web';

import { ENVIRONMENT } from '../../../environments/environment';
import {
  type GetSessionResponse,
  ProposalService,
  type SubmitDecisionResponse,
  type SubscribeResponse,
} from '../../generated/proposal/v1/proposal_service_pb';
import {
  GetSessionRequestSchema,
  SubmitDecisionRequestSchema,
  SubscribeRequestSchema,
} from '../../generated/proposal/v1/proposal_service_pb';

type ProposalServiceClient = Client<typeof ProposalService>;

@Injectable({
  providedIn: 'root',
})
export class ApprovalService implements OnDestroy {
  private readonly transport: Transport;
  private readonly client: ProposalServiceClient;
  private abortController: AbortController | null = null;

  constructor() {
    // Create gRPC-Web transport for browser communication via Envoy proxy
    this.transport = createGrpcWebTransport({
      baseUrl: ENVIRONMENT.grpcWebUrl,
    });

    // Create typed client for ProposalService
    this.client = createClient(ProposalService, this.transport);
  }

  ngOnDestroy(): void {
    this.cancelSubscription();
  }

  /**
   * Check if a session exists.
   * @param sessionId The session ID to check.
   * @returns The session response if found.
   * @throws ConnectError if session not found or network error.
   */
  async getSession(sessionId: string): Promise<GetSessionResponse> {
    const request = create(GetSessionRequestSchema, { sessionId });
    return await this.client.getSession(request);
  }

  /**
   * Subscribe to session events (proposals, decisions).
   * Returns an async iterable that yields events as they arrive.
   *
   * @param sessionId The session ID to subscribe to.
   * @param clientId Unique identifier for this client instance.
   * @yields SubscribeResponse events from the server.
   */
  async *subscribe(sessionId: string, clientId: string): AsyncIterable<SubscribeResponse> {
    // Cancel any existing subscription
    this.cancelSubscription();

    // Create new abort controller for this subscription
    this.abortController = new AbortController();

    const request = create(SubscribeRequestSchema, { sessionId, clientId });

    try {
      for await (const response of this.client.subscribe(request, {
        signal: this.abortController.signal,
      })) {
        yield response;
      }
    } finally {
      this.abortController = null;
    }
  }

  /**
   * Submit a decision (approve/reject) for a proposal.
   *
   * @param sessionId The session containing the proposal.
   * @param proposalId The proposal to decide on.
   * @param approved True to approve, false to reject.
   * @returns The updated proposal.
   */
  async submitDecision(
    sessionId: string,
    proposalId: string,
    approved: boolean,
  ): Promise<SubmitDecisionResponse> {
    const request = create(SubmitDecisionRequestSchema, {
      sessionId,
      proposalId,
      approved,
    });
    return await this.client.submitDecision(request);
  }

  /**
   * Cancel any active subscription.
   */
  cancelSubscription(): void {
    if (this.abortController) {
      this.abortController.abort();
      this.abortController = null;
    }
  }
}
