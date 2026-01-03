import { Component, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ButtonModule } from 'primeng/button';

@Component({
  selector: 'app-landing',
  standalone: true,
  imports: [CommonModule, ButtonModule],
  templateUrl: './landing.component.html',
  styleUrl: './landing.component.scss'
})
export class LandingComponent {
  currentYear = new Date().getFullYear();

  // Billing toggle: false = monthly, true = yearly
  isYearly = signal(false);

  // Pricing tiers with monthly prices (yearly gets 10% discount)
  pricingTiers = [
    {
      name: 'Starter',
      monthlyPrice: 29,
      description: 'Perfect for small businesses',
      features: [
        'Up to 1,000 items',
        '2 locations',
        '3 team members',
        'Basic reporting',
        'Email support'
      ],
      featured: false,
      cta: 'Get Started'
    },
    {
      name: 'Professional',
      monthlyPrice: 79,
      description: 'For growing businesses',
      features: [
        'Up to 10,000 items',
        '10 locations',
        '15 team members',
        'Advanced reporting',
        'Priority support',
        'API access'
      ],
      featured: true,
      cta: 'Get Started'
    },
    {
      name: 'Enterprise',
      monthlyPrice: null, // Custom pricing
      description: 'For large organizations',
      features: [
        'Unlimited items',
        'Unlimited locations',
        'Unlimited team members',
        'Custom integrations',
        'Dedicated support',
        'SLA guarantee'
      ],
      featured: false,
      cta: 'Contact Sales'
    }
  ];

  toggleBilling(): void {
    this.isYearly.update(v => !v);
  }

  getPrice(monthlyPrice: number | null): string {
    if (monthlyPrice === null) return 'Custom';
    if (this.isYearly()) {
      // 10% discount for yearly, displayed as monthly equivalent
      const yearlyTotal = monthlyPrice * 12 * 0.9;
      const monthlyEquivalent = Math.round(yearlyTotal / 12);
      return monthlyEquivalent.toString();
    }
    return monthlyPrice.toString();
  }

  getYearlySavings(monthlyPrice: number): number {
    return Math.round(monthlyPrice * 12 * 0.1);
  }

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
}
