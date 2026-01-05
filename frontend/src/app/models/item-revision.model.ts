/**
 * Item Revision models for tracking inventory item version history.
 */

export enum RevisionType {
  CREATE = 'CREATE',
  UPDATE = 'UPDATE',
  RESTORE = 'RESTORE'
}

export interface IChangeDetail {
  old: any;
  new: any;
}

export interface IRelatedUser {
  id: string;
  name: string;
  email: string;
}

/**
 * Full item revision with complete snapshot data.
 */
export interface IItemRevision {
  id: string;
  inventoryItemId: string;
  revisionNumber: number;
  revisionType: RevisionType;
  name: string;
  sku: string;
  description?: string | null;
  quantity: number;
  reorderPoint: number;
  unitPrice: number;
  status: string;
  categoryId?: string | null;
  locationId?: string | null;
  imageKey?: string | null;
  customAttributes?: Record<string, any> | null;
  changes?: Record<string, IChangeDetail> | null;
  changeSummary?: string | null;
  createdBy?: string | null;
  creator?: IRelatedUser | null;
  createdAt: string;
}

/**
 * Summarized revision for list views.
 */
export interface IItemRevisionSummary {
  id: string;
  revisionNumber: number;
  revisionType: RevisionType;
  changeSummary?: string | null;
  createdBy?: string | null;
  creator?: IRelatedUser | null;
  createdAt: string;
}

/**
 * Comparison between two revisions.
 */
export interface IRevisionCompare {
  fromRevision: IItemRevision;
  toRevision: IItemRevision;
  differences: Record<string, IChangeDetail>;
}

/**
 * Request to restore an item to a previous revision.
 */
export interface IRestoreRevisionRequest {
  revisionNumber: number;
  reason?: string;
}
