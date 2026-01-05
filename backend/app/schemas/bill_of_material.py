"""
Pydantic schemas for Bill of Materials API operations.
"""

from pydantic import BaseModel, ConfigDict, field_validator
from typing import Optional, List, Any
from datetime import datetime


def to_camel(string: str) -> str:
    """Convert snake_case to camelCase."""
    components = string.split("_")
    return components[0] + "".join(x.title() for x in components[1:])


# ============================================================================
# Related/Embedded Schemas (for nested data in responses)
# ============================================================================


class BOMComponentItem(BaseModel):
    """Minimal item info for embedding in BOM responses."""

    model_config = ConfigDict(
        alias_generator=to_camel, populate_by_name=True, from_attributes=True
    )

    id: str
    name: str
    sku: str
    quantity: int  # Current stock quantity
    unit_price: float
    status: str
    image_url: Optional[str] = None

    @field_validator("id", mode="before")
    @classmethod
    def convert_uuid_to_str(cls, v: Any) -> Optional[str]:
        return str(v) if v else None


# ============================================================================
# Request Schemas
# ============================================================================


class BillOfMaterialCreate(BaseModel):
    """Schema for creating a new BOM component entry."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    parent_item_id: str
    component_item_id: str
    quantity_required: int = 1
    unit_of_measure: Optional[str] = "units"
    notes: Optional[str] = None
    display_order: Optional[int] = 0

    @field_validator("quantity_required")
    @classmethod
    def validate_quantity(cls, v: int) -> int:
        if v < 1:
            raise ValueError("Quantity required must be at least 1")
        return v


class BillOfMaterialUpdate(BaseModel):
    """Schema for updating a BOM component entry."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    quantity_required: Optional[int] = None
    unit_of_measure: Optional[str] = None
    notes: Optional[str] = None
    display_order: Optional[int] = None

    @field_validator("quantity_required")
    @classmethod
    def validate_quantity(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and v < 1:
            raise ValueError("Quantity required must be at least 1")
        return v


class BOMBuildRequest(BaseModel):
    """
    Request to build assemblies from components.
    
    This will:
    - Decrease component quantities based on BOM * quantity_to_build
    - Increase parent item quantity by quantity_to_build
    """

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    quantity_to_build: int = 1
    notes: Optional[str] = None

    @field_validator("quantity_to_build")
    @classmethod
    def validate_quantity(cls, v: int) -> int:
        if v < 1:
            raise ValueError("Quantity to build must be at least 1")
        return v


class BOMUnbuildRequest(BaseModel):
    """
    Request to disassemble items back into components.
    
    This will:
    - Decrease parent item quantity by quantity_to_unbuild
    - Increase component quantities based on BOM * quantity_to_unbuild
    """

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    quantity_to_unbuild: int = 1
    notes: Optional[str] = None

    @field_validator("quantity_to_unbuild")
    @classmethod
    def validate_quantity(cls, v: int) -> int:
        if v < 1:
            raise ValueError("Quantity to unbuild must be at least 1")
        return v


# ============================================================================
# Response Schemas
# ============================================================================


class BillOfMaterial(BaseModel):
    """Full BOM component entry with all details."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )

    id: str
    parent_item_id: str
    component_item_id: str
    quantity_required: int
    unit_of_measure: Optional[str] = None
    notes: Optional[str] = None
    display_order: Optional[int] = None
    
    # Embedded component item details
    component_item: Optional[BOMComponentItem] = None
    
    # Timestamps
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_by: Optional[str] = None
    updated_by: Optional[str] = None

    @field_validator(
        "id",
        "parent_item_id",
        "component_item_id",
        "created_by",
        "updated_by",
        mode="before",
    )
    @classmethod
    def convert_uuid_to_str(cls, v: Any) -> Optional[str]:
        return str(v) if v else None


class BillOfMaterialSummary(BaseModel):
    """
    Summary of a BOM entry for list views.
    Includes basic component info without full details.
    """

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )

    id: str
    component_item_id: str
    quantity_required: int
    unit_of_measure: Optional[str] = None
    display_order: Optional[int] = None
    
    # Component item details
    component_item: Optional[BOMComponentItem] = None

    @field_validator("id", "component_item_id", mode="before")
    @classmethod
    def convert_uuid_to_str(cls, v: Any) -> Optional[str]:
        return str(v) if v else None


class BOMAvailability(BaseModel):
    """
    Availability info for building assemblies.
    Shows how many assemblies can be built with current stock.
    """

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    parent_item_id: str
    parent_item_name: str
    max_buildable: int  # Maximum assemblies that can be built
    components: List["BOMComponentAvailability"]


class BOMComponentAvailability(BaseModel):
    """Availability details for a single component."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    component_item_id: str
    component_name: str
    component_sku: str
    quantity_required: int  # Per assembly
    quantity_available: int  # Current stock
    max_assemblies: int  # How many assemblies this component can support
    is_limiting: bool  # True if this is the limiting component


class BOMBuildResult(BaseModel):
    """Result of a build operation."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    success: bool
    quantity_built: int
    parent_item_id: str
    parent_item_name: str
    new_parent_quantity: int
    components_consumed: List["ComponentConsumption"]
    message: str


class ComponentConsumption(BaseModel):
    """Details of component consumption in a build."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    component_item_id: str
    component_name: str
    quantity_consumed: int
    new_quantity: int


class BOMUnbuildResult(BaseModel):
    """Result of an unbuild operation."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    success: bool
    quantity_unbuilt: int
    parent_item_id: str
    parent_item_name: str
    new_parent_quantity: int
    components_returned: List["ComponentReturn"]
    message: str


class ComponentReturn(BaseModel):
    """Details of component return in an unbuild."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    component_item_id: str
    component_name: str
    quantity_returned: int
    new_quantity: int


class WhereUsedEntry(BaseModel):
    """Entry showing where a component is used in assemblies."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )

    id: str
    parent_item_id: str
    parent_item: Optional[BOMComponentItem] = None  # Reuse same schema for parent
    quantity_required: int
    unit_of_measure: Optional[str] = None

    @field_validator("id", "parent_item_id", mode="before")
    @classmethod
    def convert_uuid_to_str(cls, v: Any) -> Optional[str]:
        return str(v) if v else None


# Update forward references
BOMAvailability.model_rebuild()
BOMBuildResult.model_rebuild()
BOMUnbuildResult.model_rebuild()
