/**
 * Category attribute models for custom fields.
 */

export interface ICategoryAttribute {
  id: string;
  categoryId?: string; // Null for global attributes
  isGlobal: boolean;
  name: string;
  key: string;
  attributeType: AttributeType;
  description?: string;
  options?: string; // Comma-separated for select type
  isRequired: boolean;
  defaultValue?: string;
  displayOrder: number;
  isActive: boolean;
  createdAt?: string;
  updatedAt?: string;
}

export type AttributeType = 'text' | 'number' | 'boolean' | 'date' | 'select';

export interface ICategoryAttributeCreate {
  categoryId?: string; // Null for global attributes
  isGlobal?: boolean;
  name: string;
  key: string;
  attributeType: AttributeType;
  description?: string;
  options?: string;
  isRequired?: boolean;
  defaultValue?: string;
  displayOrder?: number;
}

export interface ICategoryAttributeUpdate {
  name?: string;
  description?: string;
  options?: string;
  isRequired?: boolean;
  defaultValue?: string;
  displayOrder?: number;
  isActive?: boolean;
}

/**
 * Parsed attribute for form display with options array.
 */
export interface IParsedAttribute extends ICategoryAttribute {
  parsedOptions: string[];
}

/**
 * Parse options string to array.
 */
export function parseOptions(options?: string): string[] {
  if (!options) return [];
  return options.split(',').map(o => o.trim()).filter(o => o.length > 0);
}

/**
 * Attribute type labels for display.
 */
export const AttributeTypeLabels: Record<AttributeType, string> = {
  text: 'Text',
  number: 'Number',
  boolean: 'Yes/No',
  date: 'Date',
  select: 'Dropdown',
};

/**
 * Attribute type icons.
 */
export const AttributeTypeIcons: Record<AttributeType, string> = {
  text: 'pi pi-pencil',
  number: 'pi pi-hashtag',
  boolean: 'pi pi-check-square',
  date: 'pi pi-calendar',
  select: 'pi pi-list',
};
