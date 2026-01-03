import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { ButtonModule } from 'primeng/button';

@Component({
  selector: 'app-landing',
  standalone: true,
  imports: [CommonModule, ButtonModule],
  templateUrl: './landing.component.html',
  styleUrl: './landing.component.scss'
})
export class LandingComponent {
  private router = inject(Router);
  
  currentYear = new Date().getFullYear();

  features = [
    {
      icon: 'pi pi-box',
      title: 'Real-time Inventory Tracking',
      description: 'Track stock levels across multiple locations with instant updates and alerts.'
    },
    {
      icon: 'pi pi-map-marker',
      title: 'Multi-Location Support',
      description: 'Manage inventory across warehouses, stores, and facilities from one dashboard.'
    },
    {
      icon: 'pi pi-chart-bar',
      title: 'Powerful Reporting',
      description: 'Generate valuation reports, movement history, and low stock alerts.'
    },
    {
      icon: 'pi pi-users',
      title: 'Team Collaboration',
      description: 'Role-based access control for your entire team with audit trails.'
    },
    {
      icon: 'pi pi-sync',
      title: 'Always in Sync',
      description: 'Real-time synchronization keeps everyone on the same page.'
    },
    {
      icon: 'pi pi-shield',
      title: 'Enterprise Security',
      description: 'Bank-level security with tenant isolation and encrypted data.'
    }
  ];

  onSignIn(): void {
    // In production, this would redirect to a subdomain or show a tenant selector
    // For now, just go to login page
    this.router.navigate(['/login']);
  }
}
