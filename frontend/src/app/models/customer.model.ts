export interface ICustomer {
  id: string;
  tenantId: string;
  name: string;
  email?: string;
  phone?: string;
  shippingAddress?: Record<string, any> | null;
  billingAddress?: Record<string, any> | null;
  notes?: string;
  isActive: boolean;
  createdAt: string;
  updatedAt: string;
  createdBy?: string;
  updatedBy?: string;
}

export interface ICustomerCreate {
  name: string;
  email?: string;
  phone?: string;
  shippingAddress?: Record<string, any> | null;
  billingAddress?: Record<string, any> | null;
  notes?: string;
}

export interface ICustomerUpdate {
  name?: string;
  email?: string;
  phone?: string;
  shippingAddress?: Record<string, any> | null;
  billingAddress?: Record<string, any> | null;
  notes?: string;
  isActive?: boolean;
}
