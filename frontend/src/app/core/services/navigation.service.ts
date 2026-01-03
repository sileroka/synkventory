import { Injectable, signal, computed, inject } from '@angular/core';
import { AuthService } from './auth.service';
import { UserRole } from '../../models/user.model';

export type NavViewMode = 'expanded' | 'collapsed' | 'mega-menu';

export interface NavItem {
  id: string;
  label: string;
  icon: string;
  route?: string;
  children?: NavItem[];
  badge?: number;
  badgeSeverity?: 'success' | 'info' | 'warning' | 'danger';
  roles?: UserRole[]; // Roles that can see this item
}

export interface NavSection {
  id: string;
  title?: string;
  items: NavItem[];
  roles?: UserRole[]; // Roles that can see this section
}

@Injectable({
  providedIn: 'root'
})
export class NavigationService {
  private readonly authService = inject(AuthService);

  // Persist nav mode in localStorage
  private readonly STORAGE_KEY = 'synkventory_nav_mode';

  // Reactive state using signals
  private _viewMode = signal<NavViewMode>(this.loadViewMode());
  private _mobileMenuOpen = signal<boolean>(false);
  private _expandedMenuIds = signal<Set<string>>(new Set());

  // Public readonly signals
  readonly viewMode = this._viewMode.asReadonly();
  readonly mobileMenuOpen = this._mobileMenuOpen.asReadonly();
  readonly expandedMenuIds = this._expandedMenuIds.asReadonly();

  // Computed properties
  readonly isExpanded = computed(() => this._viewMode() === 'expanded');
  readonly isCollapsed = computed(() => this._viewMode() === 'collapsed');
  readonly isMegaMenu = computed(() => this._viewMode() === 'mega-menu');
  readonly showSidebar = computed(() => this._viewMode() !== 'mega-menu');

  // Base navigation structure
  private readonly baseNavSections: NavSection[] = [
    {
      id: 'main',
      items: [
        {
          id: 'dashboard',
          label: 'Dashboard',
          icon: 'pi-home',
          route: '/dashboard'
        },
        {
          id: 'inventory',
          label: 'Inventory',
          icon: 'pi-box',
          route: '/inventory',
          children: [
            { id: 'inventory-list', label: 'All Items', icon: 'pi-list', route: '/inventory' },
            { id: 'inventory-add', label: 'Add Item', icon: 'pi-plus', route: '/inventory/new' },
            { id: 'inventory-import', label: 'Import', icon: 'pi-upload', route: '/inventory/import' }
          ]
        },
        {
          id: 'locations',
          label: 'Locations',
          icon: 'pi-map-marker',
          route: '/locations',
          children: [
            { id: 'locations-list', label: 'All Locations', icon: 'pi-list', route: '/locations' },
            { id: 'locations-add', label: 'Add Location', icon: 'pi-plus', route: '/locations/new' }
          ]
        },
        {
          id: 'categories',
          label: 'Categories',
          icon: 'pi-tags',
          route: '/categories'
        },
        {
          id: 'stock-movements',
          label: 'Stock Movements',
          icon: 'pi-arrows-h',
          route: '/stock-movements',
          children: [
            { id: 'movements-list', label: 'All Movements', icon: 'pi-list', route: '/stock-movements' },
            { id: 'movements-receive', label: 'Receive Stock', icon: 'pi-download', route: '/stock-movements/receive' },
            { id: 'movements-transfer', label: 'Transfer', icon: 'pi-arrows-h', route: '/stock-movements/transfer' }
          ]
        }
      ]
    },
    {
      id: 'reports',
      title: 'Reports',
      items: [
        {
          id: 'report-valuation',
          label: 'Inventory Valuation',
          icon: 'pi-chart-bar',
          route: '/reports/valuation'
        },
        {
          id: 'report-movements',
          label: 'Stock Movements',
          icon: 'pi-history',
          route: '/reports/movements'
        }
      ]
    },
    {
      id: 'admin',
      title: 'Administration',
      roles: [UserRole.ADMIN, UserRole.MANAGER],
      items: [
        {
          id: 'users',
          label: 'User Management',
          icon: 'pi-users',
          route: '/users',
          roles: [UserRole.ADMIN, UserRole.MANAGER]
        }
      ]
    }
  ];

  // Filtered navigation based on user role
  readonly navSections = computed(() => {
    const currentUser = this.authService.currentUser();
    const userRole = currentUser?.role as UserRole | undefined;

    return this.baseNavSections
      .filter(section => this.canAccessSection(section, userRole))
      .map(section => ({
        ...section,
        items: section.items.filter(item => this.canAccessItem(item, userRole))
      }))
      .filter(section => section.items.length > 0);
  });

  // Flat list of all nav items for search/reference
  readonly allNavItems = computed(() => {
    const items: NavItem[] = [];
    const flatten = (navItems: NavItem[]) => {
      navItems.forEach(item => {
        items.push(item);
        if (item.children) {
          flatten(item.children);
        }
      });
    };
    this.navSections().forEach(section => flatten(section.items));
    return items;
  });

  private canAccessSection(section: NavSection, userRole: UserRole | undefined): boolean {
    if (!section.roles || section.roles.length === 0) {
      return true;
    }
    if (!userRole) {
      return false;
    }
    return section.roles.includes(userRole);
  }

  private canAccessItem(item: NavItem, userRole: UserRole | undefined): boolean {
    if (!item.roles || item.roles.length === 0) {
      return true;
    }
    if (!userRole) {
      return false;
    }
    return item.roles.includes(userRole);
  }

  private loadViewMode(): NavViewMode {
    if (typeof localStorage !== 'undefined') {
      const saved = localStorage.getItem(this.STORAGE_KEY);
      if (saved && ['expanded', 'collapsed', 'mega-menu'].includes(saved)) {
        return saved as NavViewMode;
      }
    }
    return 'expanded';
  }

  setViewMode(mode: NavViewMode): void {
    this._viewMode.set(mode);
    if (typeof localStorage !== 'undefined') {
      localStorage.setItem(this.STORAGE_KEY, mode);
    }
  }

  cycleViewMode(): void {
    const modes: NavViewMode[] = ['expanded', 'collapsed', 'mega-menu'];
    const currentIndex = modes.indexOf(this._viewMode());
    const nextIndex = (currentIndex + 1) % modes.length;
    this.setViewMode(modes[nextIndex]);
  }

  toggleMobileMenu(): void {
    this._mobileMenuOpen.update(open => !open);
  }

  closeMobileMenu(): void {
    this._mobileMenuOpen.set(false);
  }

  toggleSubmenu(itemId: string): void {
    this._expandedMenuIds.update(ids => {
      const newIds = new Set(ids);
      if (newIds.has(itemId)) {
        newIds.delete(itemId);
      } else {
        newIds.add(itemId);
      }
      return newIds;
    });
  }

  isSubmenuExpanded(itemId: string): boolean {
    return this._expandedMenuIds().has(itemId);
  }

  expandSubmenu(itemId: string): void {
    this._expandedMenuIds.update(ids => {
      const newIds = new Set(ids);
      newIds.add(itemId);
      return newIds;
    });
  }

  collapseSubmenu(itemId: string): void {
    this._expandedMenuIds.update(ids => {
      const newIds = new Set(ids);
      newIds.delete(itemId);
      return newIds;
    });
  }

  collapseAllSubmenus(): void {
    this._expandedMenuIds.set(new Set());
  }
}
