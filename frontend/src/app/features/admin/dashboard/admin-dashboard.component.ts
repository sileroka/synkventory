import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { CardModule } from 'primeng/card';
import { ButtonModule } from 'primeng/button';
import { AdminApiService, Tenant } from '../../../core/services/admin-api.service';

@Component({
  selector: 'app-admin-dashboard',
  standalone: true,
  imports: [CommonModule, RouterLink, CardModule, ButtonModule],
  templateUrl: './admin-dashboard.component.html',
  styleUrl: './admin-dashboard.component.scss'
})
export class AdminDashboardComponent implements OnInit {
  private adminApiService = inject(AdminApiService);

  tenants = signal<Tenant[]>([]);
  isLoading = signal(true);

  stats = signal({
    totalTenants: 0,
    activeTenants: 0,
    totalUsers: 0,
  });

  ngOnInit(): void {
    this.loadTenants();
  }

  loadTenants(): void {
    this.isLoading.set(true);
    this.adminApiService.getTenants().subscribe({
      next: (tenants) => {
        this.tenants.set(tenants);
        this.stats.set({
          totalTenants: tenants.length,
          activeTenants: tenants.filter(t => t.is_active).length,
          totalUsers: tenants.reduce((sum, t) => sum + t.user_count, 0),
        });
        this.isLoading.set(false);
      },
      error: () => {
        this.isLoading.set(false);
      }
    });
  }
}
