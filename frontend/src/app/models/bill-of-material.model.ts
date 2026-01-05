/**
 * Bill of Materials (BOM) TypeScript models.
 * 
 * These models represent the data structures for managing
 * item compositions and build operations.
 */

import { IRelatedLocation, IRelatedCategory } from './inventory-item.model';

/**
 * Minimal item info for embedding in BOM responses.
 */
export interface IBOMComponentItem {
  id: string;
  name: string;
  sku: string;
  quantity: number;
  unitPrice: number;
  status: string;
  imageUrl?: string | null;
}

/**
 * Full BOM component entry with all details.
 */
export interface IBillOfMaterial {
  id: string;
  parentItemId: string;
  componentItemId: string;
  quantityRequired: number;
  unitOfMeasure?: string | null;
  notes?: string | null;
  displayOrder?: number | null;
  componentItem?: IBOMComponentItem | null;
  createdAt?: string;
  updatedAt?: string;
  createdBy?: string | null;
  updatedBy?: string | null;
}

/**
 * Summary of a BOM entry for list views.
 */
export interface IBillOfMaterialSummary {
  id: string;
  componentItemId: string;
  quantityRequired: number;
  unitOfMeasure?: string | null;
  displayOrder?: number | null;
  componentItem?: IBOMComponentItem | null;
}

/**
 * Request to create a new BOM component entry.
 */
export interface IBillOfMaterialCreate {
  componentItemId: string;
  quantityRequired: number;
  unitOfMeasure?: string;
  notes?: string;
  displayOrder?: number;
}

/**
 * Request to update a BOM component entry.
 */
export interface IBillOfMaterialUpdate {
  quantityRequired?: number;
  unitOfMeasure?: string;
  notes?: string;
  displayOrder?: number;
}

/**
 * Availability details for a single component.
 */
export interface IBOMComponentAvailability {
  componentItemId: string;
  componentName: string;
  componentSku: string;
  quantityRequired: number;
  quantityAvailable: number;
  maxAssemblies: number;
  isLimiting: boolean;
}

/**
 * Availability info for building assemblies.
 */
export interface IBOMAvailability {
  parentItemId: string;
  parentItemName: string;
  maxBuildable: number;
  components: IBOMComponentAvailability[];
  message?: string;
}

/**
 * Request to build assemblies from components.
 */
export interface IBOMBuildRequest {
  quantityToBuild: number;
  notes?: string;
}

/**
 * Details of component consumption in a build.
 */
export interface IComponentConsumption {
  componentItemId: string;
  componentName: string;
  quantityConsumed: number;
  newQuantity: number;
}

/**
 * Result of a build operation.
 */
export interface IBOMBuildResult {
  success: boolean;
  quantityBuilt: number;
  parentItemId: string;
  parentItemName: string;
  newParentQuantity: number;
  componentsConsumed: IComponentConsumption[];
  message: string;
}

/**
 * Request to disassemble items back into components.
 */
export interface IBOMUnbuildRequest {
  quantityToUnbuild: number;
  notes?: string;
}

/**
 * Details of component return in an unbuild.
 */
export interface IComponentReturn {
  componentItemId: string;
  componentName: string;
  quantityReturned: number;
  newQuantity: number;
}

/**
 * Result of an unbuild operation.
 */
export interface IBOMUnbuildResult {
  success: boolean;
  quantityUnbuilt: number;
  parentItemId: string;
  parentItemName: string;
  newParentQuantity: number;
  componentsReturned: IComponentReturn[];
  message: string;
}

/**
 * Entry showing where a component is used in assemblies.
 */
export interface IWhereUsedEntry {
  id: string;
  parentItemId: string;
  parentItem?: IBOMComponentItem | null;
  quantityRequired: number;
  unitOfMeasure?: string | null;
}
