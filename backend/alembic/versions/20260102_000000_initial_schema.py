"""
Initial database schema

Revision ID: 0001
Revises:
Create Date: 2026-01-02
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create initial database schema."""

    # ==========================================================================
    # Tenants Table
    # ==========================================================================
    op.create_table(
        "tenants",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(100), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_tenants_slug", "tenants", ["slug"], unique=True)
    op.create_index("ix_tenants_is_active", "tenants", ["is_active"])

    # ==========================================================================
    # Users Table
    # ==========================================================================
    op.create_table(
        "users",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("is_locked", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_users_tenant_id", "users", ["tenant_id"])
    op.create_index(
        "ix_users_tenant_email", "users", ["tenant_id", "email"], unique=True
    )
    op.create_index("ix_users_is_active", "users", ["is_active"])

    # ==========================================================================
    # Categories Table
    # ==========================================================================
    op.create_table(
        "categories",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("code", sa.String(50), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("parent_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.ForeignKeyConstraint(["parent_id"], ["categories.id"]),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"]),
    )
    op.create_index("ix_categories_tenant_id", "categories", ["tenant_id"])
    op.create_index("ix_categories_name", "categories", ["name"])
    op.create_index(
        "ix_categories_tenant_code", "categories", ["tenant_id", "code"], unique=True
    )
    op.create_index(
        "ix_categories_tenant_active", "categories", ["tenant_id", "is_active"]
    )
    op.create_index(
        "ix_categories_tenant_parent", "categories", ["tenant_id", "parent_id"]
    )
    op.create_index("ix_categories_created_by", "categories", ["created_by"])
    op.create_index("ix_categories_updated_by", "categories", ["updated_by"])

    # ==========================================================================
    # Locations Table
    # ==========================================================================
    op.create_table(
        "locations",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("code", sa.String(50), nullable=False),
        sa.Column("address", sa.String(500), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"]),
    )
    op.create_index("ix_locations_tenant_id", "locations", ["tenant_id"])
    op.create_index("ix_locations_name", "locations", ["name"])
    op.create_index(
        "ix_locations_tenant_code", "locations", ["tenant_id", "code"], unique=True
    )
    op.create_index(
        "ix_locations_tenant_active", "locations", ["tenant_id", "is_active"]
    )
    op.create_index("ix_locations_created_by", "locations", ["created_by"])
    op.create_index("ix_locations_updated_by", "locations", ["updated_by"])

    # ==========================================================================
    # Inventory Items Table
    # ==========================================================================
    op.create_table(
        "inventory_items",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("sku", sa.String(50), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("reorder_point", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("unit_price", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("status", sa.String(50), nullable=False, server_default="'in_stock'"),
        sa.Column("category_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("location_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.ForeignKeyConstraint(["category_id"], ["categories.id"]),
        sa.ForeignKeyConstraint(["location_id"], ["locations.id"]),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"]),
    )
    op.create_index("ix_inventory_items_tenant_id", "inventory_items", ["tenant_id"])
    op.create_index("ix_inventory_items_name", "inventory_items", ["name"])
    op.create_index(
        "ix_inventory_items_tenant_sku",
        "inventory_items",
        ["tenant_id", "sku"],
        unique=True,
    )
    op.create_index(
        "ix_inventory_items_tenant_status", "inventory_items", ["tenant_id", "status"]
    )
    op.create_index(
        "ix_inventory_items_tenant_category",
        "inventory_items",
        ["tenant_id", "category_id"],
    )
    op.create_index(
        "ix_inventory_items_tenant_location",
        "inventory_items",
        ["tenant_id", "location_id"],
    )
    op.create_index("ix_inventory_items_status", "inventory_items", ["status"])
    op.create_index(
        "ix_inventory_items_category_id", "inventory_items", ["category_id"]
    )
    op.create_index(
        "ix_inventory_items_location_id", "inventory_items", ["location_id"]
    )
    op.create_index("ix_inventory_items_created_by", "inventory_items", ["created_by"])
    op.create_index("ix_inventory_items_updated_by", "inventory_items", ["updated_by"])

    # ==========================================================================
    # Stock Movements Table
    # ==========================================================================
    # Create the enum type first
    movement_type_enum = postgresql.ENUM(
        "receive",
        "ship",
        "transfer",
        "adjust",
        "count",
        name="movement_type_enum",
        create_type=False,  # We create it manually below
    )
    movement_type_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "stock_movements",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("inventory_item_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "movement_type",
            movement_type_enum,
            nullable=False,
        ),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("from_location_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("to_location_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("reference_number", sa.String(100), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.ForeignKeyConstraint(["inventory_item_id"], ["inventory_items.id"]),
        sa.ForeignKeyConstraint(["from_location_id"], ["locations.id"]),
        sa.ForeignKeyConstraint(["to_location_id"], ["locations.id"]),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
    )
    op.create_index("ix_stock_movements_tenant_id", "stock_movements", ["tenant_id"])
    op.create_index(
        "ix_stock_movements_inventory_item_id", "stock_movements", ["inventory_item_id"]
    )
    op.create_index(
        "ix_stock_movements_movement_type", "stock_movements", ["movement_type"]
    )
    op.create_index(
        "ix_stock_movements_tenant_item",
        "stock_movements",
        ["tenant_id", "inventory_item_id"],
    )
    op.create_index(
        "ix_stock_movements_tenant_type",
        "stock_movements",
        ["tenant_id", "movement_type"],
    )
    op.create_index(
        "ix_stock_movements_tenant_created",
        "stock_movements",
        ["tenant_id", "created_at"],
    )
    op.create_index(
        "ix_stock_movements_from_location_id", "stock_movements", ["from_location_id"]
    )
    op.create_index(
        "ix_stock_movements_to_location_id", "stock_movements", ["to_location_id"]
    )
    op.create_index(
        "ix_stock_movements_reference_number", "stock_movements", ["reference_number"]
    )
    op.create_index("ix_stock_movements_created_by", "stock_movements", ["created_by"])

    # ==========================================================================
    # Inventory Location Quantities Table (optional - for multi-location tracking)
    # ==========================================================================
    op.create_table(
        "inventory_location_quantities",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("inventory_item_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("location_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["inventory_item_id"], ["inventory_items.id"]),
        sa.ForeignKeyConstraint(["location_id"], ["locations.id"]),
        sa.UniqueConstraint(
            "inventory_item_id", "location_id", name="uq_inventory_location"
        ),
    )
    op.create_index(
        "ix_inventory_location_quantities_inventory_item_id",
        "inventory_location_quantities",
        ["inventory_item_id"],
    )
    op.create_index(
        "ix_inventory_location_quantities_location_id",
        "inventory_location_quantities",
        ["location_id"],
    )

    # ==========================================================================
    # Row Level Security (RLS) Setup
    # ==========================================================================
    # Create app role for RLS enforcement (if not exists)
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'synkventory_app') THEN
                CREATE ROLE synkventory_app;
            END IF;
        END
        $$;
        """
    )

    # Grant usage on schema
    op.execute("GRANT USAGE ON SCHEMA public TO synkventory_app")

    # Grant table permissions to app role
    tables_with_rls = [
        "users",
        "categories",
        "locations",
        "inventory_items",
        "stock_movements",
    ]

    for table in tables_with_rls:
        op.execute(f"GRANT SELECT, INSERT, UPDATE, DELETE ON {table} TO synkventory_app")

    # Enable RLS and create policies for tenant-scoped tables
    tenant_tables = [
        "users",
        "categories",
        "locations",
        "inventory_items",
        "stock_movements",
    ]

    for table in tenant_tables:
        # Enable RLS
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")

        # Create policy: users can only see/modify rows in their tenant
        op.execute(
            f"""
            CREATE POLICY {table}_tenant_isolation ON {table}
                FOR ALL
                TO synkventory_app
                USING (tenant_id::text = current_setting('app.current_tenant_id', true))
                WITH CHECK (tenant_id::text = current_setting('app.current_tenant_id', true))
            """
        )

    # Tenants table - users can only see their own tenant
    op.execute("ALTER TABLE tenants ENABLE ROW LEVEL SECURITY")
    op.execute(
        """
        CREATE POLICY tenants_tenant_isolation ON tenants
            FOR ALL
            TO synkventory_app
            USING (id::text = current_setting('app.current_tenant_id', true))
            WITH CHECK (id::text = current_setting('app.current_tenant_id', true))
        """
    )
    op.execute("GRANT SELECT ON tenants TO synkventory_app")

    # Grant sequence permissions
    op.execute("GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO synkventory_app")


def downgrade() -> None:
    """Drop all tables in reverse order."""
    # ==========================================================================
    # Remove RLS Setup
    # ==========================================================================
    tenant_tables = [
        "users",
        "categories",
        "locations",
        "inventory_items",
        "stock_movements",
    ]

    for table in tenant_tables:
        op.execute(f"DROP POLICY IF EXISTS {table}_tenant_isolation ON {table}")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY")

    op.execute("DROP POLICY IF EXISTS tenants_tenant_isolation ON tenants")
    op.execute("ALTER TABLE tenants DISABLE ROW LEVEL SECURITY")

    # Revoke permissions and drop role
    op.execute("REVOKE ALL ON ALL TABLES IN SCHEMA public FROM synkventory_app")
    op.execute("REVOKE ALL ON ALL SEQUENCES IN SCHEMA public FROM synkventory_app")
    op.execute("REVOKE USAGE ON SCHEMA public FROM synkventory_app")

    # Drop tables
    op.drop_table("inventory_location_quantities")
    op.drop_table("stock_movements")

    # Drop the enum type
    movement_type_enum = postgresql.ENUM(
        "receive",
        "ship",
        "transfer",
        "adjust",
        "count",
        name="movement_type_enum",
    )
    movement_type_enum.drop(op.get_bind(), checkfirst=True)

    op.drop_table("inventory_items")
    op.drop_table("locations")
    op.drop_table("categories")
    op.drop_table("users")
    op.drop_table("tenants")
