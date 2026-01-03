"""
Database seed utilities for initial data setup.
"""

from sqlalchemy.orm import Session
from app.models.user import User, UserRole, SYSTEM_USER_ID
from app.models.tenant import Tenant, DEFAULT_TENANT_ID
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
    print("Database seeding complete.")


if __name__ == "__main__":
    # Allow running seeds directly: python -m app.db.seed
    from app.db.session import SessionLocal

    db = SessionLocal()
    try:
        run_seeds(db)
    finally:
        db.close()
