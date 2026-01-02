export interface IInventoryItem {
  id?: string;
  name: string;
  sku: string;
  description?: string;
  quantity: number;
  unit_price: number;
  category?: string;
  location?: string;
  created_at?: string;
  updated_at?: string;
}
