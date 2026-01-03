import { Component, inject, HostListener } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink, RouterLinkActive, Router, NavigationEnd } from '@angular/router';
import { NavigationService, NavItem, NavSection } from '../../core/services/navigation.service';
import { TooltipModule } from 'primeng/tooltip';
import { filter } from 'rxjs/operators';

@Component({
  selector: 'app-sidebar',
  standalone: true,
  imports: [CommonModule, RouterLink, RouterLinkActive, TooltipModule],
  templateUrl: './sidebar.component.html',
  styleUrl: './sidebar.component.scss'
})
export class SidebarComponent {
  private router = inject(Router);
  navService = inject(NavigationService);

  constructor() {
    // Expand parent menu when navigating to a child route
    this.router.events.pipe(
      filter(event => event instanceof NavigationEnd)
    ).subscribe(() => {
      this.expandParentOfActiveRoute();
    });
  }

  get navSections(): NavSection[] {
    return this.navService.navSections();
  }

  hasChildren(item: NavItem): boolean {
    return !!item.children && item.children.length > 0;
  }

  isExpanded(item: NavItem): boolean {
    return this.navService.isSubmenuExpanded(item.id);
  }

  toggleSubmenu(event: Event, item: NavItem): void {
    event.preventDefault();
    event.stopPropagation();
    this.navService.toggleSubmenu(item.id);
  }

  onNavItemClick(item: NavItem): void {
    // Close mobile menu on navigation
    this.navService.closeMobileMenu();
  }

  private expandParentOfActiveRoute(): void {
    const currentUrl = this.router.url;

    for (const section of this.navSections) {
      for (const item of section.items) {
        if (item.children) {
          const hasActiveChild = item.children.some(child =>
            child.route && currentUrl.startsWith(child.route)
          );
          if (hasActiveChild) {
            this.navService.expandSubmenu(item.id);
          }
        }
      }
    }
  }

  // Handle click outside to close expanded submenus in collapsed mode
  @HostListener('document:click', ['$event'])
  onDocumentClick(event: Event): void {
    if (this.navService.isCollapsed()) {
      // Could add logic to close hover menus if needed
    }
  }
}
