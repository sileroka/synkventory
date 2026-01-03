import { Component, inject, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink, RouterLinkActive } from '@angular/router';
import { ButtonModule } from 'primeng/button';
import { AvatarModule } from 'primeng/avatar';
import { MenuModule } from 'primeng/menu';
import { TooltipModule } from 'primeng/tooltip';
import { MenuItem } from 'primeng/api';
import { NavigationService, NavViewMode } from '../../core/services/navigation.service';

@Component({
  selector: 'app-header',
  standalone: true,
  imports: [CommonModule, RouterLink, RouterLinkActive, ButtonModule, AvatarModule, MenuModule, TooltipModule],
  templateUrl: './header.component.html',
  styleUrl: './header.component.scss'
})
export class HeaderComponent {
  private navService = inject(NavigationService);

  viewMode = this.navService.viewMode;
  navSections = this.navService.navSections;

  userMenuItems: MenuItem[] = [
    { label: 'Profile', icon: 'pi pi-user' },
    { label: 'Settings', icon: 'pi pi-cog' },
    { separator: true },
    { label: 'Logout', icon: 'pi pi-sign-out' }
  ];

  // Icons for view mode button
  viewModeIcon = computed(() => {
    switch (this.viewMode()) {
      case 'expanded': return 'pi pi-align-left';
      case 'collapsed': return 'pi pi-bars';
      case 'mega-menu': return 'pi pi-th-large';
      default: return 'pi pi-bars';
    }
  });

  viewModeTooltip = computed(() => {
    switch (this.viewMode()) {
      case 'expanded': return 'Collapse sidebar';
      case 'collapsed': return 'Switch to mega menu';
      case 'mega-menu': return 'Expand sidebar';
      default: return 'Toggle view';
    }
  });

  cycleViewMode() {
    this.navService.cycleViewMode();
  }

  setViewMode(mode: NavViewMode) {
    this.navService.setViewMode(mode);
  }
}
