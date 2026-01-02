export interface ICategory {
  id?: string;
  name: string;
  code: string;
  description?: string;
  parentId?: string | null;
  isActive: boolean;
  createdAt?: string;
  updatedAt?: string;
}

export interface ICategoryTreeNode extends ICategory {
  children?: ICategoryTreeNode[];
}
