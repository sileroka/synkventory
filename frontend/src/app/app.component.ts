import { Component, inject, computed } from '@angular/core';
import { Router, NavigationEnd, RouterOutlet, Event } from '@angular/router';
import { CommonModule } from '@angular/common';
import { filter, map } from 'rxjs';
import { toSignal } from '@angular/core/rxjs-interop';
import { LayoutComponent } from './layout/layout.component';
import { TenantService } from './core/services/tenant.service';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, LayoutComponent, RouterOutlet],
  templateUrl: './app.component.html',
  styleUrl: './app.component.scss'
})
export class AppComponent {
  title = 'Synkventory';

  private router = inject(Router);
  private tenantService = inject(TenantService);

  // Track if we're on the login page
  private currentUrl$ = this.router.events.pipe(
    filter((event: Event): event is NavigationEnd => event instanceof NavigationEnd),
    map((event) => event.urlAfterRedirects)
  );

  currentUrl = toSignal(this.currentUrl$, { initialValue: this.router.url });

  // Check if we're on a standalone page (no layout needed)
  isStandalonePage = computed(() => {
    const url = this.currentUrl();
    const isLogin = url === '/login' || url.startsWith('/login');
    // On root domain, any root path (including anchor links like /#features) should show landing
    const isLanding = this.tenantService.isRootDomain() && (url === '/' || url.startsWith('/#'));
    return isLogin || isLanding;
  });
}
