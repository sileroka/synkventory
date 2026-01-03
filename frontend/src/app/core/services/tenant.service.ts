import { Injectable, signal, computed } from '@angular/core';
import { environment } from '../../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class TenantService {
  private readonly rootDomains = ['synkventory.com', 'www.synkventory.com', 'localhost'];

  private _hostname = signal<string>(this.getHostname());

  readonly hostname = this._hostname.asReadonly();

  /**
   * Check if we're on the admin portal (admin.synkventory.com)
   */
  readonly isAdminPortal = computed(() => {
    const host = this._hostname();
    const subdomain = this.extractSubdomain(host);
    return subdomain === 'admin';
  });

  /**
   * Check if we're on the root domain (marketing site) vs a tenant subdomain
   */
  readonly isRootDomain = computed(() => {
    const host = this._hostname();

    // Admin portal is not root domain
    if (this.isAdminPortal()) {
      return false;
    }

    // Check for localhost development
    if (host === 'localhost' || host.startsWith('localhost:')) {
      // In dev, check if there's no subdomain or we're explicitly at the root
      return !this.hasSubdomain(host);
    }

    // Check if it's a root domain
    return this.rootDomains.some(domain =>
      host === domain || host.endsWith(`.${domain}`) === false && host.includes(domain)
    );
  });

  /**
   * Check if we're on a tenant subdomain (not admin, not root)
   */
  readonly isSubdomain = computed(() => !this.isRootDomain() && !this.isAdminPortal());

  /**
   * Get the subdomain/tenant slug if on a tenant subdomain
   */
  readonly tenantSlug = computed(() => {
    if (this.isRootDomain() || this.isAdminPortal()) {
      return null;
    }
    return this.extractSubdomain(this._hostname());
  });

  private getHostname(): string {
    if (typeof window !== 'undefined') {
      return window.location.hostname;
    }
    return 'localhost';
  }

  private hasSubdomain(host: string): boolean {
    // Remove port if present
    const hostname = host.split(':')[0];

    // localhost never has subdomain in this context
    if (hostname === 'localhost') {
      return false;
    }

    // Check for subdomain pattern
    const parts = hostname.split('.');

    // For synkventory.com or www.synkventory.com
    if (parts.length <= 2) {
      return false;
    }

    // If it's www, it's not a tenant subdomain
    if (parts[0] === 'www') {
      return false;
    }

    return true;
  }

  private extractSubdomain(host: string): string | null {
    const hostname = host.split(':')[0];
    const parts = hostname.split('.');

    if (parts.length > 2 && parts[0] !== 'www') {
      return parts[0];
    }

    return null;
  }

  /**
   * Force refresh hostname (useful for testing)
   */
  refreshHostname(): void {
    this._hostname.set(this.getHostname());
  }
}
