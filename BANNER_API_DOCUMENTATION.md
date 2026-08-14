# Banner API - Complete Documentation

## Overview
The Banner API provides endpoints for managing promotional banners in the e-commerce system. There are two sets of endpoints:
1. **Warehouse-scoped endpoints** - For warehouse admins to manage their own banners
2. **Global endpoints** - For viewing active banners (public/read-only)

---

## Base URLs

### Warehouse-Scoped Endpoints (Admin Only)
```
/api/v1/warehouses/{warehouse_id}/banners/
```

### Global Endpoints (Public Read, Admin Write)
```
/api/v1/banners/
```

---

## Banner Model Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUID | Auto | Unique identifier (read-only) |
| `warehouse` | UUID | Auto | Warehouse ID (auto-assigned, read-only) |
| `warehouse_name` | String | - | Warehouse name (read-only) |
| `headline_en` | String | Yes | Banner headline in English (max 255 chars) |
| `headline_ar` | String | No | Banner headline in Arabic (max 255 chars) |
| `sub_text_en` | Text | No | Sub-text in English |
| `sub_text_ar` | Text | No | Sub-text in Arabic |
| `sub_paragraph_en` | Text | No | Additional paragraph in English |
| `sub_paragraph_ar` | Text | No | Additional paragraph in Arabic |
| `cta_label_en` | String | Yes | Call-to-action button label in English (max 100 chars) |
| `cta_label_ar` | String | No | Call-to-action button label in Arabic (max 100 chars) |
| `image` | File | No | Banner image file |
| `link` | String | No | Link/route (max 500 chars) - **No http:// required!** |
| `device` | String | No | Target device: `mobile`, `desktop`, `both` (default: `both`) |
| `status` | String | No | Status: `active`, `inactive` (default: `active`) |
| `is_active` | Boolean | No | Active flag (default: true) |
| `created_at` | DateTime | Auto | Creation timestamp (read-only) |
| `updated_at` | DateTime | Auto | Last update timestamp (read-only) |
| `delete_image` | Boolean | No | Set to `true` to delete existing image (write-only) |

---

## API Endpoints

### 1. List Banners (Warehouse-Scoped)

**Endpoint:** `GET /api/v1/warehouses/{warehouse_id}/banners/`

**Permission:** Warehouse Admin or Super Admin

**Query Parameters:**
- `device` - Filter by device (`mobile`, `desktop`, `both`)
- `status` - Filter by status (`active`, `inactive`)
- `search` - Search in headline_en, headline_ar
- `ordering` - Order by `created_at` (use `-created_at` for descending)
- `page` - Page number
- `page_size` - Items per page

**Example Request:**
```bash
GET /api/v1/warehouses/4aa18d50-f9f8-4f9d-a888-89baac26bff7/banners/?status=active&device=both
Authorization: Bearer {token}
```

**Example Response:**
```json
{
  "count": 2,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "warehouse": "4aa18d50-f9f8-4f9d-a888-89baac26bff7",
      "warehouse_name": "Main Warehouse",
      "headline_en": "Summer Sale 2026",
      "headline_ar": "تخفيضات الصيف 2026",
      "sub_text_en": "Up to 50% off",
      "sub_text_ar": "خصم يصل إلى 50%",
      "sub_paragraph_en": "Limited time offer on selected items",
      "sub_paragraph_ar": "عرض لفترة محدودة على منتجات مختارة",
      "cta_label_en": "Shop Now",
      "cta_label_ar": "تسوق الآن",
      "image": "https://api.iqraamark.com/media/banners/images/summer_sale.jpg",
      "link": "/products/summer-collection",
      "device": "both",
      "status": "active",
      "is_active": true,
      "created_at": "2026-05-19T10:00:00+05:30",
      "updated_at": "2026-05-19T10:00:00+05:30"
    }
  ]
}
```

---

### 2. Create Banner (Warehouse-Scoped)

**Endpoint:** `POST /api/v1/warehouses/{warehouse_id}/banners/`

**Permission:** Warehouse Admin or Super Admin

**Content-Type:** `multipart/form-data` (for image upload)

**Request Body:**
```json
{
  "headline_en": "Summer Sale 2026",
  "headline_ar": "تخفيضات الصيف 2026",
  "sub_text_en": "Up to 50% off",
  "sub_text_ar": "خصم يصل إلى 50%",
  "sub_paragraph_en": "Limited time offer",
  "sub_paragraph_ar": "عرض لفترة محدودة",
  "cta_label_en": "Shop Now",
  "cta_label_ar": "تسوق الآن",
  "link": "/products/summer-collection",
  "device": "both",
  "status": "active",
  "is_active": true
}
```

**With Image (Form Data):**
```bash
POST /api/v1/warehouses/4aa18d50-f9f8-4f9d-a888-89baac26bff7/banners/
Authorization: Bearer {token}
Content-Type: multipart/form-data

headline_en: Summer Sale 2026
headline_ar: تخفيضات الصيف 2026
cta_label_en: Shop Now
cta_label_ar: تسوق الآن
link: /products/summer-collection
device: both
status: active
image: [file upload]
```

**Important Notes:**
- ✅ `link` field accepts ANY text - no http:// required!
- ✅ Use internal routes like `/products/123`, `category/shoes`, `home`
- ✅ Or use full URLs if needed: `https://example.com`
- ✅ `warehouse` is auto-assigned from URL, don't include it in body

**Example Response:**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "warehouse": "4aa18d50-f9f8-4f9d-a888-89baac26bff7",
  "warehouse_name": "Main Warehouse",
  "headline_en": "Summer Sale 2026",
  "headline_ar": "تخفيضات الصيف 2026",
  "sub_text_en": "Up to 50% off",
  "sub_text_ar": "خصم يصل إلى 50%",
  "sub_paragraph_en": "Limited time offer",
  "sub_paragraph_ar": "عرض لفترة محدودة",
  "cta_label_en": "Shop Now",
  "cta_label_ar": "تسوق الآن",
  "image": "https://api.iqraamark.com/media/banners/images/summer_sale.jpg",
  "link": "/products/summer-collection",
  "device": "both",
  "status": "active",
  "is_active": true,
  "created_at": "2026-05-19T10:00:00+05:30",
  "updated_at": "2026-05-19T10:00:00+05:30"
}
```

---

### 3. Get Single Banner (Warehouse-Scoped)

**Endpoint:** `GET /api/v1/warehouses/{warehouse_id}/banners/{banner_id}/`

**Permission:** Warehouse Admin or Super Admin

**Example Request:**
```bash
GET /api/v1/warehouses/4aa18d50-f9f8-4f9d-a888-89baac26bff7/banners/123e4567-e89b-12d3-a456-426614174000/
Authorization: Bearer {token}
```

**Example Response:** (Same as create response)

---

### 4. Update Banner (Warehouse-Scoped)

**Endpoint:** `PUT /api/v1/warehouses/{warehouse_id}/banners/{banner_id}/`

**Permission:** Warehouse Admin or Super Admin

**Content-Type:** `multipart/form-data` (if updating image)

**Request Body:** (All fields required for PUT)
```json
{
  "headline_en": "Updated Summer Sale",
  "headline_ar": "تخفيضات الصيف المحدثة",
  "sub_text_en": "Up to 70% off",
  "sub_text_ar": "خصم يصل إلى 70%",
  "sub_paragraph_en": "Extended offer",
  "sub_paragraph_ar": "عرض ممتد",
  "cta_label_en": "Shop Now",
  "cta_label_ar": "تسوق الآن",
  "link": "/products/mega-sale",
  "device": "both",
  "status": "active",
  "is_active": true
}
```

**Example Response:** (Updated banner object)

---

### 5. Partial Update Banner (Warehouse-Scoped)

**Endpoint:** `PATCH /api/v1/warehouses/{warehouse_id}/banners/{banner_id}/`

**Permission:** Warehouse Admin or Super Admin

**Request Body:** (Only fields to update)
```json
{
  "status": "inactive"
}
```

**Or update just the link:**
```json
{
  "link": "/new-collection"
}
```

**Delete Image:**
```json
{
  "delete_image": true
}
```

**Example Response:** (Updated banner object)

---

### 6. Delete Banner (Warehouse-Scoped)

**Endpoint:** `DELETE /api/v1/warehouses/{warehouse_id}/banners/{banner_id}/`

**Permission:** Warehouse Admin or Super Admin

**Example Request:**
```bash
DELETE /api/v1/warehouses/4aa18d50-f9f8-4f9d-a888-89baac26bff7/banners/123e4567-e89b-12d3-a456-426614174000/
Authorization: Bearer {token}
```

**Response:** `204 No Content`

---

## Global Banner Endpoints (Public)

### 7. List Active Banners (Public)

**Endpoint:** `GET /api/v1/banners/`

**Permission:** Public (No authentication required for GET)

**Query Parameters:** (Same as warehouse-scoped)
- `device` - Filter by device
- `status` - Filter by status
- `warehouse` - Filter by warehouse ID
- `search` - Search in headlines
- `ordering` - Order by created_at

**Example Request:**
```bash
GET /api/v1/banners/?device=mobile&status=active
```

**Example Response:**
```json
{
  "count": 5,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "warehouse": "4aa18d50-f9f8-4f9d-a888-89baac26bff7",
      "warehouse_name": "Main Warehouse",
      "headline_en": "Summer Sale 2026",
      "headline_ar": "تخفيضات الصيف 2026",
      "sub_text_en": "Up to 50% off",
      "sub_text_ar": "خصم يصل إلى 50%",
      "cta_label_en": "Shop Now",
      "cta_label_ar": "تسوق الآن",
      "image": "https://api.iqraamark.com/media/banners/images/summer_sale.jpg",
      "link": "/products/summer-collection",
      "device": "mobile",
      "status": "active",
      "is_active": true,
      "created_at": "2026-05-19T10:00:00+05:30",
      "updated_at": "2026-05-19T10:00:00+05:30"
    }
  ]
}
```

**Note:** This endpoint only returns **active** banners for the current warehouse.

---

## Device Types

| Value | Description |
|-------|-------------|
| `mobile` | Banner shown only on mobile devices |
| `desktop` | Banner shown only on desktop devices |
| `both` | Banner shown on all devices (default) |

---

## Status Types

| Value | Description |
|-------|-------------|
| `active` | Banner is visible to users (default) |
| `inactive` | Banner is hidden from users |

---

## Link Field Examples

The `link` field is now flexible and accepts any text:

### Internal Routes (Recommended)
```json
{
  "link": "/products/summer-collection"
}
```

```json
{
  "link": "category/shoes"
}
```

```json
{
  "link": "home"
}
```

### Full URLs (If needed)
```json
{
  "link": "https://example.com/external-page"
}
```

### Empty (No link)
```json
{
  "link": ""
}
```

**✅ No validation - you can type anything!**

---

## Error Responses

### 400 Bad Request
```json
{
  "headline_en": ["This field is required."],
  "cta_label_en": ["This field is required."]
}
```

### 401 Unauthorized
```json
{
  "detail": "Authentication credentials were not provided."
}
```

### 403 Forbidden
```json
{
  "detail": "You do not have permission to perform this action."
}
```

### 404 Not Found
```json
{
  "detail": "Not found."
}
```

---

## Permissions Summary

| Endpoint | Method | Permission |
|----------|--------|------------|
| `/api/v1/warehouses/{id}/banners/` | GET | Warehouse Admin or Super Admin |
| `/api/v1/warehouses/{id}/banners/` | POST | Warehouse Admin or Super Admin |
| `/api/v1/warehouses/{id}/banners/{id}/` | GET | Warehouse Admin or Super Admin |
| `/api/v1/warehouses/{id}/banners/{id}/` | PUT/PATCH | Warehouse Admin or Super Admin |
| `/api/v1/warehouses/{id}/banners/{id}/` | DELETE | Warehouse Admin or Super Admin |
| `/api/v1/banners/` | GET | Public (No auth required) |
| `/api/v1/banners/` | POST/PUT/PATCH/DELETE | Super Admin only |

---

## Testing with Postman

### 1. Create Banner
```
POST https://api.iqraamark.com/api/v1/warehouses/4aa18d50-f9f8-4f9d-a888-89baac26bff7/banners/
Headers:
  Authorization: Bearer {your_token}
  Content-Type: multipart/form-data

Body (form-data):
  headline_en: Summer Sale
  headline_ar: تخفيضات الصيف
  cta_label_en: Shop Now
  cta_label_ar: تسوق الآن
  link: /products/sale
  device: both
  status: active
  image: [select file]
```

### 2. Update Link Only
```
PATCH https://api.iqraamark.com/api/v1/warehouses/4aa18d50-f9f8-4f9d-a888-89baac26bff7/banners/{banner_id}/
Headers:
  Authorization: Bearer {your_token}
  Content-Type: application/json

Body (raw JSON):
{
  "link": "/new-collection"
}
```

### 3. Get Active Banners (Public)
```
GET https://api.iqraamark.com/api/v1/banners/?status=active&device=mobile
(No authorization header needed)
```

---

## Recent Changes

✅ **Removed URL validation** - The `link` field now accepts any text without requiring http:// or https://

---

## Notes

- Banners are warehouse-scoped - each warehouse manages its own banners
- The `warehouse` field is automatically assigned based on the URL or request context
- Images are uploaded to `media/banners/images/` directory
- Use `delete_image: true` in PATCH request to remove existing image
- Global endpoints only show active banners for the current warehouse
- Warehouse-scoped endpoints show all banners (active and inactive)
