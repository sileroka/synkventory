# Barcodes & Scanning

## Overview

Synkventory can generate Code128 barcodes for inventory items to speed up receiving, picking, and counting.

Each item includes:
- `barcode`: the encoded value (defaults to SKU if not set)
- `barcodeImageKey`: storage key for the generated PNG image

## Endpoint

`POST /api/v1/inventory/{id}/barcode`

Behavior:
- Generates a Code128 PNG barcode using the item’s `barcode` or fallback `sku`
- Stores the image via storage service (e.g., DigitalOcean Spaces/S3)
- Persists `barcode` and `barcodeImageKey` on the item

## Example

```bash
curl -X POST "http://localhost:8000/api/v1/inventory/{id}/barcode" \
  -H "Content-Type: application/json" \
  -H "X-Tenant-Slug: demo"
```

## Roadmap

- Support EAN-13 barcodes and QR codes
- Mobile scanner integrations (USB HID, Bluetooth, Android/iOS app)
- Frontend barcode rendering and print labels
- Scanning workflows for receiving, picking, and cycle counting
