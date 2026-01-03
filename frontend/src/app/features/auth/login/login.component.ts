import { Component, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { AuthService } from '../../../core/services/auth.service';

// PrimeNG imports
import { CardModule } from 'primeng/card';
import { InputTextModule } from 'primeng/inputtext';
import { PasswordModule } from 'primeng/password';
import { ButtonModule } from 'primeng/button';
import { MessageModule } from 'primeng/message';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    CardModule,
    InputTextModule,
    PasswordModule,
    ButtonModule,
    MessageModule
  ],
  template: `
    <div class="login-container">
      <div class="login-card">
        <div class="logo-section">
          <img src="assets/logo.png" alt="Synkventory Logo" style="width: 400px;" />
          <p class="brand-tagline">Stock in sync.</p>
        </div>

        <p-card>
          <form [formGroup]="loginForm" (ngSubmit)="onSubmit()">
            <div class="form-field">
              <label for="email">Email</label>
              <input
                pInputText
                id="email"
                formControlName="email"
                type="email"
                placeholder="Enter your email"
                class="w-full"
                [class.ng-invalid]="loginForm.get('email')?.invalid && loginForm.get('email')?.touched"
              />
              @if (loginForm.get('email')?.invalid && loginForm.get('email')?.touched) {
                <small class="error-text">Valid email is required</small>
              }
            </div>

            <div class="form-field">
              <label for="password">Password</label>
              <p-password
                id="password"
                formControlName="password"
                placeholder="Enter your password"
                [feedback]="false"
                [toggleMask]="true"
                styleClass="w-full"
                inputStyleClass="w-full"
              />
              @if (loginForm.get('password')?.invalid && loginForm.get('password')?.touched) {
                <small class="error-text">Password is required</small>
              }
            </div>

            @if (errorMessage()) {
              <p-message severity="error" [text]="errorMessage()" styleClass="w-full mb-3" />
            }

            <p-button
              type="submit"
              label="Sign In"
              styleClass="w-full"
              [loading]="isLoading()"
              [disabled]="loginForm.invalid || isLoading()"
            />
          </form>
        </p-card>

        <p class="footer-text">
          &copy; {{ currentYear }} Synkadia. All rights reserved.
        </p>
      </div>
    </div>
  `,
  styles: [`
    .login-container {
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
      background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%);
      padding: 1rem;
    }

    .login-card {
      width: 100%;
      max-width: 400px;
    }

    .logo-section {
      text-align: center;
      margin-bottom: 2rem;
    }

    .brand-name {
      color: #0D9488;
      font-size: 2.5rem;
      font-weight: 700;
      margin: 0;
      letter-spacing: -0.025em;
    }

    .brand-tagline {
      color: #94A3B8;
      font-size: 1rem;
      margin: 0.5rem 0 0;
    }

    :host ::ng-deep .p-card {
      background: #FFFFFF;
      border-radius: 0.75rem;
      box-shadow: 0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1);
    }

    :host ::ng-deep .p-card-body {
      padding: 2rem;
    }

    .form-field {
      margin-bottom: 1.5rem;
    }

    .form-field label {
      display: block;
      font-weight: 500;
      color: #334155;
      margin-bottom: 0.5rem;
      font-size: 0.875rem;
    }

    .form-field input,
    :host ::ng-deep .p-password input {
      width: 100%;
    }

    .error-text {
      color: #EF4444;
      font-size: 0.75rem;
      margin-top: 0.25rem;
      display: block;
    }

    :host ::ng-deep .p-button {
      background: #0D9488;
      border-color: #0D9488;
      margin-top: 0.5rem;
    }

    :host ::ng-deep .p-button:hover {
      background: #0F766E;
      border-color: #0F766E;
    }

    :host ::ng-deep .p-message {
      margin-bottom: 1rem;
    }

    .footer-text {
      text-align: center;
      color: #64748B;
      font-size: 0.75rem;
      margin-top: 1.5rem;
    }

    .w-full {
      width: 100%;
    }

    .mb-3 {
      margin-bottom: 1rem;
    }
  `]
})
export class LoginComponent {
  loginForm: FormGroup;
  isLoading = signal(false);
  errorMessage = signal<string>('');
  currentYear = new Date().getFullYear();

  constructor(
    private fb: FormBuilder,
    private authService: AuthService,
    private router: Router
  ) {
    this.loginForm = this.fb.group({
      email: ['', [Validators.required, Validators.email]],
      password: ['', [Validators.required]]
    });
  }

  onSubmit(): void {
    if (this.loginForm.invalid) {
      this.loginForm.markAllAsTouched();
      return;
    }

    this.isLoading.set(true);
    this.errorMessage.set('');

    this.authService.login(this.loginForm.value).subscribe({
      next: () => {
        this.router.navigate(['/dashboard']);
      },
      error: () => {
        // Always show generic error for security
        this.errorMessage.set('Invalid email or password');
        this.isLoading.set(false);
      }
    });
  }
}
