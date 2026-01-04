import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterOutlet, RouterLink, RouterLinkActive, Router } from '@angular/router';
import { ButtonModule } from 'primeng/button';
import { AdminAuthService } from '../../../core/services/admin-auth.service';

@Component({
  selector: 'app-admin-layout',
  standalone: true,
  imports: [CommonModule, RouterOutlet, RouterLink, RouterLinkActive, ButtonModule],
  templateUrl: './admin-layout.component.html',
  styleUrl: './admin-layout.component.scss'
})
export class AdminLayoutComponent {
  private adminAuthService = inject(AdminAuthService);
  private router = inject(Router);

  currentAdmin = this.adminAuthService.currentAdmin;
  isSuperAdmin = this.adminAuthService.isSuperAdmin;

  navItems = [
    { label: 'Dashboard', icon: 'pi pi-home', route: '/admin/dashboard' },
    { label: 'Tenants', icon: 'pi pi-building', route: '/admin/tenants' },
    { label: 'Audit Logs', icon: 'pi pi-list', route: '/admin/audit-logs' },
  ];

  logout(): void {
    this.adminAuthService.logout().subscribe();
  }
}
