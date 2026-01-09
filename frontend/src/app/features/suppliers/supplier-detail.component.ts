import { Component, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, RouterModule } from '@angular/router';
import { TableModule } from 'primeng/table';
import { CardModule } from 'primeng/card';
import { TagModule } from 'primeng/tag';
import { TooltipModule } from 'primeng/tooltip';

import { SupplierService } from '../../services/supplier.service';
import { PurchaseOrderService } from '../../services/purchase-order.service';
import { ISupplier } from '../../models/supplier.model';
import { IPurchaseOrderListItem } from '../../models/purchase-order.model';

@Component({
  selector: 'app-supplier-detail',
  standalone: true,
  imports: [CommonModule, RouterModule, TableModule, CardModule, TagModule, TooltipModule],
  templateUrl: './supplier-detail.component.html'
})
export class SupplierDetailComponent implements OnInit {
  supplier = signal<ISupplier | null>(null);
  purchaseOrders = signal<IPurchaseOrderListItem[]>([]);
  isLoading = signal<boolean>(true);

  constructor(
    private route: ActivatedRoute,
    private supplierService: SupplierService,
    private purchaseOrderService: PurchaseOrderService,
  ) {}

  ngOnInit(): void {
    const supplierId = this.route.snapshot.paramMap.get('id');
    if (supplierId) {
      this.supplierService.getById(supplierId).subscribe({
        next: (s) => this.supplier.set(s),
      });
      this.purchaseOrderService.getPurchaseOrders({ page: 1, pageSize: 100, supplierId }).subscribe({
        next: (resp) => {
          this.purchaseOrders.set(resp.items);
          this.isLoading.set(false);
        },
        error: () => this.isLoading.set(false),
      });
    } else {
      this.isLoading.set(false);
    }
  }

  getSupplierTooltip(): string {
    const s = this.supplier();
    if (!s) return '';
    const parts: string[] = [];
    if (s.contactName) parts.push(`Contact: ${s.contactName}`);
    if (s.email) parts.push(`Email: ${s.email}`);
    if (s.phone) parts.push(`Phone: ${s.phone}`);
    return parts.join('\n');
  }
}
