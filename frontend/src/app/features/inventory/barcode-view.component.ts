import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ButtonModule } from 'primeng/button';

@Component({
    selector: 'app-barcode-view',
    standalone: true,
    imports: [CommonModule, ButtonModule],
    template: `
  <div class="barcode-card">
    <h3 class="title">Barcode</h3>
    <div *ngIf="barcodeImageUrl; else noBarcode">
      <img [src]="barcodeImageUrl" alt="Barcode" class="barcode-img" />
      <div class="actions">
        <button pButton type="button" label="Print" (click)="printBarcode()"></button>
      </div>
    </div>
    <ng-template #noBarcode>
      <p>No barcode generated yet.</p>
    </ng-template>
  </div>
  `,
    styles: [`
    .barcode-card { background: #F1F5F9; padding: 1rem; border-radius: 0.5rem; }
    .title { color: #0F172A; }
    .barcode-img { max-width: 320px; border: 1px solid #CBD5E1; background: #FFFFFF; }
    .actions { margin-top: 0.5rem; }
  `]
})
export class BarcodeViewComponent {
    @Input() barcodeImageUrl?: string | null;

    printBarcode() {
        if (!this.barcodeImageUrl) return;
        const w = window.open('', '_blank');
        if (!w) return;
        w.document.write(`<img src="${this.barcodeImageUrl}" style="max-width:100%" />`);
        w.document.close();
        w.focus();
        w.print();
        w.close();
    }
}
