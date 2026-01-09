"""
Database seed utilities for initial data setup.
"""

import os
from sqlalchemy.orm import Session
from app.models.user import User, UserRole, SYSTEM_USER_ID
from app.models.tenant import Tenant, DEFAULT_TENANT_ID
from app.models.admin_user import AdminUser
from app.core.security import get_password_hash


def seed_default_tenant(db: Session) -> Tenant:
    """
    Create or get the default tenant.

    The default tenant is used for:
    - Single-tenant deployments
    - Development and testing
    - Initial setup before tenant creation

    Returns:
        Tenant: The default tenant instance
    """
    # Check if default tenant already exists
    default_tenant = db.query(Tenant).filter(Tenant.id == DEFAULT_TENANT_ID).first()

    if default_tenant is None:
        default_tenant = Tenant(
            id=DEFAULT_TENANT_ID,
            name="Default Tenant",
            slug="default",
            is_active=True,
        )
        db.add(default_tenant)
        db.commit()
        db.refresh(default_tenant)
        print(f"Created default tenant: {default_tenant.name}")
    else:
        print(f"Default tenant already exists: {default_tenant.name}")

    return default_tenant


def seed_system_user(db: Session, default_tenant: Tenant) -> User:
    """
    Create or get the system user.

    The system user is used for:
    - Migrations and schema changes
    - Automated processes and cron jobs
    - Seed data creation
    - Any operation that isn't triggered by a real user

    Args:
        db: Database session
        default_tenant: The default tenant to associate the system user with

    Returns:
        User: The system user instance
    """
    # Check if system user already exists
    system_user = db.query(User).filter(User.id == SYSTEM_USER_ID).first()

    if system_user is None:
        system_user = User(
            id=SYSTEM_USER_ID,
            tenant_id=default_tenant.id,
            email="system@synkventory.local",
            name="System",
            password_hash="!disabled",  # Cannot login - not a valid bcrypt hash
            role=UserRole.ADMIN.value,
            is_active=True,
        )
        db.add(system_user)
        db.commit()
        db.refresh(system_user)
        print(f"Created system user: {system_user.email}")
    else:
        print(f"System user already exists: {system_user.email}")

    return system_user


def seed_demo_admin(db: Session, default_tenant: Tenant) -> User:
    """
    Create or get the demo admin user for testing.

    This user can be used to login during development.
    Default credentials: admin@demo.com / Changeme123!

    Args:
        db: Database session
        default_tenant: The default tenant to associate the user with

    Returns:
        User: The demo admin user instance
    """
    demo_email = "admin@demo.com"
    demo_user = db.query(User).filter(User.email == demo_email).first()

    if demo_user is None:
        demo_user = User(
            tenant_id=default_tenant.id,
            email=demo_email,
            name="Demo Admin",
            password_hash=get_password_hash("Changeme123!"),
            role=UserRole.ADMIN.value,
            is_active=True,
        )
        db.add(demo_user)
        db.commit()
        db.refresh(demo_user)
        print(f"Created demo admin user: {demo_user.email} (password: Changeme123!)")
    else:
        print(f"Demo admin user already exists: {demo_user.email}")

    return demo_user


def seed_super_admin(db: Session) -> AdminUser | None:
    """
    Create or get the super admin user for the admin portal.

    Credentials are read from environment variables:
    - ADMIN_EMAIL: Admin email (default: admin@synkadia.com)
    - ADMIN_PASSWORD: Admin password (required, no default)

    Returns:
        AdminUser: The super admin user instance, or None if password not set
    """
    admin_email = os.getenv("ADMIN_EMAIL", "admin@synkadia.com")
    admin_password = os.getenv("ADMIN_PASSWORD")

    if not admin_password:
        print("Skipping super admin seed: ADMIN_PASSWORD not set")
        return None

    admin_user = db.query(AdminUser).filter(AdminUser.email == admin_email).first()

    if admin_user is None:
        admin_user = AdminUser(
            email=admin_email,
            name="Super Admin",
            password_hash=get_password_hash(admin_password),
            is_active=True,
            is_super_admin=True,
        )
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        print(f"Created super admin user: {admin_user.email}")
    else:
        print(f"Super admin user already exists: {admin_user.email}")

    return admin_user


def run_seeds(db: Session) -> None:
    """
    Run all database seeds.

    This function should be called after database migrations to ensure
    all required seed data exists.
    """
    print("Running database seeds...")
    # Tenant must be seeded first since users and other entities reference it
    default_tenant = seed_default_tenant(db)
    seed_system_user(db, default_tenant)
    seed_demo_admin(db, default_tenant)
    seed_super_admin(db)
    seed_demo_suppliers(db, default_tenant)
    print("Database seeding complete.")


def seed_demo_suppliers(db: Session, default_tenant: Tenant) -> None:
    """
    Create demo supplier data for testing and development.

    Creates a variety of suppliers with different characteristics to
    demonstrate the supplier management features.

    Args:
        db: Database session
        default_tenant: The default tenant to associate suppliers with
    """
    from app.models.supplier import Supplier

    # Check if suppliers already exist
    existing_count = db.query(Supplier).filter(Supplier.tenant_id == default_tenant.id).count()
    
    if existing_count > 0:
        print(f"Demo suppliers already exist ({existing_count} found), skipping...")
        return

    demo_suppliers = [
        {
            "name": "ACME Industrial Supplies",
            "contact_name": "Sarah Johnson",
            "email": "sarah.j@acme-industrial.com",
            "phone": "+1-555-0101",
            "address_line1": "1234 Industrial Blvd",
            "city": "Chicago",
            "state": "IL",
            "postal_code": "60601",
            "country": "USA",
            "is_active": True,
        },
        {
            "name": "Global Tech Distributors",
            "contact_name": "Michael Chen",
            "email": "m.chen@globaltech.com",
            "phone": "+1-555-0102",
            "address_line1": "567 Tech Park Drive",
            "address_line2": "Suite 200",
            "city": "San Jose",
            "state": "CA",
            "postal_code": "95110",
            "country": "USA",
            "is_active": True,
        },
        {
            "name": "Quality Parts Co.",
            "contact_name": "Emily Rodriguez",
            "email": "erodriguez@qualityparts.com",
            "phone": "+1-555-0103",
            "address_line1": "890 Manufacturing Way",
            "city": "Detroit",
            "state": "MI",
            "postal_code": "48201",
            "country": "USA",
            "is_active": True,
        },
        {
            "name": "Office Essentials Plus",
            "contact_name": "David Kim",
            "email": "dkim@officeessentials.com",
            "phone": "+1-555-0104",
            "address_line1": "321 Commerce Street",
            "city": "New York",
            "state": "NY",
            "postal_code": "10001",
            "country": "USA",
            "is_active": True,
        },
        {
            "name": "Green Packaging Solutions",
            "contact_name": "Jennifer Martinez",
            "email": "jmartinez@greenpack.com",
            "phone": "+1-555-0105",
            "address_line1": "456 Eco Lane",
            "city": "Portland",
            "state": "OR",
            "postal_code": "97201",
            "country": "USA",
            "is_active": True,
        },
        {
            "name": "Budget Supplies Warehouse",
            "contact_name": "Robert Taylor",
            "email": "rtaylor@budgetsupplies.com",
            "phone": "+1-555-0106",
            "address_line1": "789 Discount Drive",
            "city": "Dallas",
            "state": "TX",
            "postal_code": "75201",
            "country": "USA",
            "is_active": True,
        },
        {
            "name": "Premium Components Ltd",
            "contact_name": "Amanda White",
            "email": "awhite@premiumcomponents.com",
            "phone": "+1-555-0107",
            "address_line1": "159 Quality Court",
            "city": "Boston",
            "state": "MA",
            "postal_code": "02101",
            "country": "USA",
            "is_active": True,
        },
        {
            "name": "Legacy Suppliers Inc",
            "contact_name": "Thomas Anderson",
            "email": "tanderson@legacysuppliers.com",
            "phone": "+1-555-0108",
            "address_line1": "753 Heritage Blvd",
            "city": "Philadelphia",
            "state": "PA",
            "postal_code": "19101",
            "country": "USA",
            "is_active": False,  # Inactive supplier for testing
        },
    ]

    for supplier_data in demo_suppliers:
        supplier = Supplier(
            tenant_id=default_tenant.id,
            **supplier_data
        )
        db.add(supplier)

    db.commit()
    print(f"Created {len(demo_suppliers)} demo suppliers")


if __name__ == "__main__":
    # Allow running seeds directly: python -m app.db.seed
    from app.db.session import SessionLocal

    db = SessionLocal()
    try:
        run_seeds(db)
    finally:
        db.close()
