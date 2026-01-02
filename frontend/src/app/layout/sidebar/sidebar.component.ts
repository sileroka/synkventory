import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink, RouterLinkActive } from '@angular/router';

interface NavItem {
  label: string;
  icon: string;
  route: string;
  badge?: number;
}

interface NavSection {
  title?: string;
  items: NavItem[];
}

@Component({
  selector: 'app-sidebar',
  standalone: true,
  imports: [CommonModule, RouterLink, RouterLinkActive],
  templateUrl: './sidebar.component.html',
  styleUrl: './sidebar.component.scss'
})
export class SidebarComponent {
  @Input() collapsed: boolean = false;

  navSections: NavSection[] = [
    {
      items: [
        { label: 'Dashboard', icon: 'pi-home', route: '/dashboard' },
        { label: 'Inventory', icon: 'pi-box', route: '/inventory' },
        { label: 'Locations', icon: 'pi-map-marker', route: '/locations' },
        { label: 'Categories', icon: 'pi-tags', route: '/categories' },
        { label: 'Stock Movements', icon: 'pi-arrows-h', route: '/stock-movements' }
      ]
    },
    {
      title: 'Reports',
      items: [
        { label: 'Inventory Valuation', icon: 'pi-chart-bar', route: '/reports/valuation' },
        { label: 'Stock Movements', icon: 'pi-history', route: '/reports/movements' }
      ]
    }
  ];

  // Keep navItems for backwards compatibility
  navItems: NavItem[] = this.navSections.flatMap(section => section.items);
}
