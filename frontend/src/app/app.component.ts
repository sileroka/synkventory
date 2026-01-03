import { Component, inject, computed } from '@angular/core';
import { Router, NavigationEnd, RouterOutlet } from '@angular/router';
import { CommonModule } from '@angular/common';
import { filter, map } from 'rxjs';
import { toSignal } from '@angular/core/rxjs-interop';
import { LayoutComponent } from './layout/layout.component';

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
  
  // Track if we're on the login page
  private currentUrl$ = this.router.events.pipe(
    filter(event => event instanceof NavigationEnd),
    map((event: NavigationEnd) => event.urlAfterRedirects)
  );
  
  currentUrl = toSignal(this.currentUrl$, { initialValue: this.router.url });
  
  isLoginPage = computed(() => {
    const url = this.currentUrl();
    return url === '/login' || url.startsWith('/login');
  });
}
