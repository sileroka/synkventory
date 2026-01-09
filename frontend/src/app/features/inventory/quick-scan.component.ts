import { Component, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ButtonModule } from 'primeng/button';
import { InputTextModule } from 'primeng/inputtext';
import { InventoryApiService } from '../../services/inventory-api.service';

@Component({
    selector: 'app-quick-scan',
    standalone: true,
    imports: [CommonModule, FormsModule, ButtonModule, InputTextModule],
    template: `
  <div class="scan-card">
    <h3 class="title">Quick Scan</h3>
    <div class="row">
      <input pInputText type="text" [(ngModel)]="code" placeholder="Scan or type barcode/SKU" />
      <button pButton type="button" label="Lookup" (click)="lookup()"></button>
    </div>
    <div class="actions">
      <button pButton type="button" label="Receive +1" (click)="receive(1)"></button>
      <button pButton type="button" label="Pick -1" (click)="pick(1)"></button>
      <button pButton type="button" label="Count Set" (click)="count()"></button>
    </div>
    <div class="result" *ngIf="item()">
      <p><strong>{{ item()!.name }}</strong> ({{ item()!.sku }})</p>
      <p>Quantity: {{ item()!.quantity }}</p>
    </div>
  </div>
  `,
    styles: [`
    .scan-card { background: #F1F5F9; padding: 1rem; border-radius: 0.5rem; }
    .title { color: #0F172A; }
    .row { display: flex; gap: 0.5rem; }
    .actions { margin-top: 0.5rem; display: flex; gap: 0.5rem; }
    .result { margin-top: 0.75rem; }
  `]
})
export class QuickScanComponent {
    code = '';
    item = signal<any | null>(null);
    constructor(private api: InventoryApiService) { }

    async lookup() {
        if (!this.code) return;
        try {
            const data = await this.api.getItemByBarcode(this.code);
            this.item.set(data);
        } catch (e) { /* no-op */ }
    }

    async receive(qty: number) {
        if (!this.code) return;
        try { await this.api.scanReceive(this.code, qty); this.lookup(); } catch (e) { }
    }

    async pick(qty: number) {
        if (!this.code) return;
        try { await this.api.scanPick(this.code, qty); this.lookup(); } catch (e) { }
    }

    async count() {
        if (!this.code) return;
        const qty = window.prompt('Set counted quantity to:');
        if (qty == null) return;
        try { await this.api.scanCount(this.code, Number(qty)); this.lookup(); } catch (e) { }
    }

    async generateBarcode(kind: 'code128' | 'ean13' | 'qr' = 'code128') {
        if (!this.item()) return;
        // EAN-13 prompt and validation
        let valueOverride: string | undefined = undefined;
        if (kind === 'ean13') {
            const v = window.prompt('Enter 12 or 13-digit EAN-13 value (digits only). Leave blank to use current barcode/SKU.');
            if (v) {
                const digitsOnly = /^[0-9]{12,13}$/;
                if (!digitsOnly.test(v)) { alert('EAN-13 must be 12 or 13 digits.'); return; }
                valueOverride = v;
            }
        }
        try {
            const data = await this.api.generateBarcode(this.item()!.id, kind);
            this.item.set(data);
        } catch (e) { }
    }
}
