import { Component, inject, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterOutlet } from '@angular/router';
import { HeaderComponent } from './header/header.component';
import { SidebarComponent } from './sidebar/sidebar.component';
import { NavigationService } from '../core/services/navigation.service';

@Component({
  selector: 'app-layout',
  standalone: true,
  imports: [CommonModule, RouterOutlet, HeaderComponent, SidebarComponent],
  templateUrl: './layout.component.html',
  styleUrl: './layout.component.scss'
})
export class LayoutComponent {
  private navService = inject(NavigationService);

  // Computed classes for the layout based on navigation state
  layoutClasses = computed(() => {
    const viewMode = this.navService.viewMode();
    return {
      'sidebar-expanded': viewMode === 'expanded',
      'sidebar-collapsed': viewMode === 'collapsed',
      'sidebar-hidden': viewMode === 'mega-menu'
    };
  });
}
