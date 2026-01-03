"""
Tenant context management for multi-tenancy.
"""
import re
from contextvars import ContextVar
from dataclasses import dataclass
from typing import Optional
from uuid import UUID


@dataclass
class TenantContext:
    """Holds tenant information for the current request."""
    id: UUID
    slug: str
    name: str
    is_active: bool


# Context variable to store tenant info for current request
_tenant_context: ContextVar[Optional[TenantContext]] = ContextVar(
    "tenant_context", default=None
)


def get_current_tenant() -> Optional[TenantContext]:
    """Get the current tenant context."""
    return _tenant_context.get()


def set_current_tenant(tenant: Optional[TenantContext]) -> None:
    """Set the current tenant context."""
    _tenant_context.set(tenant)


def clear_current_tenant() -> None:
    """Clear the current tenant context."""
    _tenant_context.set(None)


# Subdomain extraction pattern
# Valid: demo, my-company, company123
# Invalid: -demo, demo-, my--company
SUBDOMAIN_PATTERN = re.compile(r"^[a-z][a-z0-9-]{0,61}[a-z0-9]$|^[a-z]$")


def extract_subdomain(host: str, base_domain: str = "synkventory.com") -> Optional[str]:
    """
    Extract subdomain from host header.
    
    Args:
        host: The Host header value (e.g., "demo.synkventory.com")
        base_domain: The base domain to extract subdomain from
        
    Returns:
        The subdomain if valid, None otherwise
    """
    # Remove port if present
    host = host.split(":")[0].lower()
    
    # Check if host ends with base domain
    if not host.endswith(base_domain):
        return None
    
    # Extract potential subdomain
    if host == base_domain:
        return None
    
    # Remove base domain to get subdomain
    subdomain = host[: -(len(base_domain) + 1)]  # +1 for the dot
    
    # Validate subdomain format
    if not subdomain or not SUBDOMAIN_PATTERN.match(subdomain):
        return None
    
    return subdomain
