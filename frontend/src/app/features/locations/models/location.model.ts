/**
 * Location type enum for warehouse hierarchy
 */
export type LocationType = 'warehouse' | 'row' | 'bay' | 'level' | 'position';

/**
 * Location type display information
 */
export interface ILocationTypeInfo {
  type: LocationType;
  displayName: string;
  allowedChildType: LocationType | null;
}

/**
 * Location interface with hierarchy support
 */
export interface ILocation {
  id?: string;
  name: string;
  code: string;
  locationType: LocationType;
  parentId?: string | null;
  description?: string;
  address?: string;
  barcode?: string;
  capacity?: number;
  sortOrder: number;
  isActive: boolean;
  createdAt?: string;
  updatedAt?: string;
}

/**
 * Location tree node for hierarchical display
 */
export interface ILocationTreeNode extends ILocation {
  children: ILocationTreeNode[];
  fullPath?: string;
}

/**
 * Location type hierarchy mapping
 */
export const LOCATION_TYPE_HIERARCHY: Record<LocationType, LocationType | null> = {
  warehouse: 'row',
  row: 'bay',
  bay: 'level',
  level: 'position',
  position: null,
};

/**
 * Location type display names
 */
export const LOCATION_TYPE_DISPLAY_NAMES: Record<LocationType, string> = {
  warehouse: 'Warehouse',
  row: 'Row',
  bay: 'Bay',
  level: 'Level',
  position: 'Position',
};

/**
 * All location types in hierarchy order
 */
export const LOCATION_TYPES: LocationType[] = ['warehouse', 'row', 'bay', 'level', 'position'];

/**
 * Get the icon class for a location type
 */
export function getLocationTypeIcon(type: LocationType): string {
  const icons: Record<LocationType, string> = {
    warehouse: 'pi pi-building',
    row: 'pi pi-th-large',
    bay: 'pi pi-table',
    level: 'pi pi-bars',
    position: 'pi pi-box',
  };
  return icons[type] || 'pi pi-map-marker';
}
