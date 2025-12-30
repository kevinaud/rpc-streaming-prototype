/**
 * Join Session component.
 * Allows the Approver to join an existing session by entering a session ID.
 */
import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { ApprovalService } from '../../core/services/approval.service';
import { SessionStateService } from '../../core/services/session-state.service';

@Component({
  selector: 'app-join-session',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    MatFormFieldModule,
    MatInputModule,
    MatButtonModule,
    MatCardModule,
    MatProgressSpinnerModule,
  ],
  templateUrl: './join-session.component.html',
  styleUrl: './join-session.component.scss',
})
export class JoinSessionComponent {
  private readonly fb = inject(FormBuilder);
  private readonly router = inject(Router);
  private readonly approvalService = inject(ApprovalService);
  private readonly sessionState = inject(SessionStateService);

  readonly form = this.fb.group({
    sessionId: ['', [Validators.required, Validators.minLength(1)]],
  });

  isLoading = false;
  errorMessage: string | null = null;

  async onSubmit(): Promise<void> {
    if (this.form.invalid || this.isLoading) {
      return;
    }

    const sessionId = this.form.value.sessionId?.trim();
    if (!sessionId) {
      return;
    }

    this.isLoading = true;
    this.errorMessage = null;

    try {
      // Verify session exists
      await this.approvalService.getSession(sessionId);

      // Session found - navigate to session view
      this.sessionState.setSessionId(sessionId);
      await this.router.navigate(['/session', sessionId]);
    } catch (error) {
      // Session not found or network error
      this.errorMessage = 'Session not found. Please check the ID and try again.';
      console.error('Failed to join session:', error);
    } finally {
      this.isLoading = false;
    }
  }
}
