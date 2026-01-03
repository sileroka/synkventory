import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { InputTextModule } from 'primeng/inputtext';
import { PasswordModule } from 'primeng/password';
import { ButtonModule } from 'primeng/button';
import { CardModule } from 'primeng/card';
import { MessageModule } from 'primeng/message';
import { AdminAuthService } from '../../../core/services/admin-auth.service';

@Component({
  selector: 'app-admin-login',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    InputTextModule,
    PasswordModule,
    ButtonModule,
    CardModule,
    MessageModule,
  ],
  templateUrl: './admin-login.component.html',
  styleUrl: './admin-login.component.scss'
})
export class AdminLoginComponent {
  private adminAuthService = inject(AdminAuthService);
  private router = inject(Router);

  email = '';
  password = '';
  error = signal<string | null>(null);
  isLoading = signal(false);

  onSubmit(): void {
    if (!this.email || !this.password) {
      this.error.set('Please enter email and password');
      return;
    }

    this.isLoading.set(true);
    this.error.set(null);

    this.adminAuthService.login({ email: this.email, password: this.password }).subscribe({
      next: () => {
        this.router.navigate(['/admin/dashboard']);
      },
      error: (err) => {
        this.isLoading.set(false);
        this.error.set(err.error?.detail || 'Invalid email or password');
      }
    });
  }
}
