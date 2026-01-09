import { Injectable } from '@angular/core';

@Injectable({ providedIn: 'root' })
export class InventoryApiService {
    async getItemByBarcode(value: string): Promise<any> {
        const resp = await fetch(`/api/v1/inventory/by-barcode/${encodeURIComponent(value)}`, { credentials: 'include' });
        if (!resp.ok) throw new Error(await resp.text());
        return (await resp.json()).data;
    }

    async scanReceive(barcode: string, quantity: number, locationId?: string): Promise<void> {
        const url = `/api/v1/inventory/scan/receive?barcode=${encodeURIComponent(barcode)}&quantity=${quantity}` + (locationId ? `&location_id=${encodeURIComponent(locationId)}` : '');
        const resp = await fetch(url, { method: 'POST', credentials: 'include' });
        if (!resp.ok) throw new Error(await resp.text());
    }

    async scanPick(barcode: string, quantity: number, locationId?: string): Promise<void> {
        const url = `/api/v1/inventory/scan/pick?barcode=${encodeURIComponent(barcode)}&quantity=${quantity}` + (locationId ? `&location_id=${encodeURIComponent(locationId)}` : '');
        const resp = await fetch(url, { method: 'POST', credentials: 'include' });
        if (!resp.ok) throw new Error(await resp.text());
    }

    async scanCount(barcode: string, quantity: number): Promise<void> {
        const url = `/api/v1/inventory/scan/count?barcode=${encodeURIComponent(barcode)}&quantity=${encodeURIComponent(String(quantity))}`;
        const resp = await fetch(url, { method: 'POST', credentials: 'include' });
        if (!resp.ok) throw new Error(await resp.text());
    }

    async generateBarcode(itemId: string, kind: 'code128' | 'ean13' | 'qr' = 'code128'): Promise<any> {
        const resp = await fetch(`/api/v1/inventory/${encodeURIComponent(itemId)}/barcode?kind=${kind}`, { method: 'POST', credentials: 'include' });
        if (!resp.ok) throw new Error(await resp.text());
        return (await resp.json()).data;
    }
}
