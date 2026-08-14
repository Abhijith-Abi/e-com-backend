# House of Vaz Backend Documentation

## Overview

House of Vaz is a modular Django REST Framework backend for a multi-region e-commerce platform.

Supported business scope:
- Multi-country warehouses: India, UAE, UK
- Multi-language content: English, Arabic
- Multi-currency commerce: INR, AED, USD
- Full commerce flow: Product -> Cart -> Checkout -> Order -> Payment

Core stack:
- Django
- Django REST Framework
- JWT authentication
- PostgreSQL-ready configuration
- Modular monolith architecture


## Project Structure

```text
house_of_vaz/
├── apps/
│   ├── user_account/
│   │   └── api_v1/
│   ├── warehouses/
│   │   └── api_v1/
│   ├── categories/
│   │   └── api_v1/
│   ├── products/
│   │   └── api_v1/
│   ├── cart/
│   │   └── api_v1/
│   ├── orders/
│   │   └── api_v1/
│   ├── payments/
│   │   └── api_v1/
│   ├── coupons/
│   │   └── api_v1/
│   ├── customers/
│   │   └── api_v1/
│   ├── banners/
│   │   └── api_v1/
│   ├── analytics/
│   │   └── api_v1/
│   └── settings/
│       └── api_v1/
├── core/
├── services/
├── repositories/
├── tasks/
├── config/
└── manage.py
```


## Shared Foundation

### BaseModel

All core models inherit from `BaseModel` in [core/base_models.py](/home/afsal/Desktop/ALGOBIZ/vaaz/core/base_models.py).

Common fields:
- `id`: UUID primary key
- `created_at`
- `updated_at`
- `is_active`
- `is_deleted`

### Shared Choices

Enums are defined in [core/choices.py](/home/afsal/Desktop/ALGOBIZ/vaaz/core/choices.py).

Main enums:
- `RegionChoices`: `INDIA`, `UAE`, `UK`
- `LanguageChoices`: `en`, `ar`
- `CurrencyChoices`: `INR`, `AED`, `USD`
- `ProductStatusChoices`
- `OrderStatusChoices`
- `PaymentStatusChoices`
- `PaymentMethodChoices`
- `CouponTypeChoices`

### Permissions

Permissions are defined in [core/permissions.py](/home/afsal/Desktop/ALGOBIZ/vaaz/core/permissions.py).

Main permission helpers:
- `IsAdminOrReadOnly`
- `IsAdminOrOwner`


## API Layer Structure

Each app now follows the `user_account` API structure:

- `models.py`
- `admin.py`
- `repositories.py`
- `services.py`
- `api_v1/serializers.py`
- `api_v1/views.py`
- `api_v1/api_router.py`

This keeps domain logic separate from API transport logic.
Top-level `serializers.py`, `views.py`, and `urls.py` were removed from the apps and are no longer used.


## Module-by-Module Models

### 1. User Account

Files:
- [apps/user_account/models.py](/home/afsal/Desktop/ALGOBIZ/vaaz/apps/user_account/models.py)
- [apps/user_account/api_v1/views.py](/home/afsal/Desktop/ALGOBIZ/vaaz/apps/user_account/api_v1/views.py)
- [apps/user_account/api_v1/serializers.py](/home/afsal/Desktop/ALGOBIZ/vaaz/apps/user_account/api_v1/serializers.py)

#### User

Purpose:
- Main authentication table
- Stores roles and selected warehouse

Fields:
- `email`
- `password`
- `full_name`
- `role`
- `selected_warehouse`
- `is_admin`
- `is_staff`
- `is_verified`

Supported roles:
- `admin`
- `warehouse_admin`
- `customer`

Behavior:
- `admin` becomes `is_admin=True`, `is_staff=True`
- `warehouse_admin` becomes `is_staff=True`
- `customer` is the default role for public registration

#### PasswordResetToken

Purpose:
- Supports forgot-password and reset-password flow

Fields:
- `user`
- `token`
- `is_used`
- `expires_at`


### 2. Warehouses

Files:
- [apps/warehouses/models.py](/home/afsal/Desktop/ALGOBIZ/vaaz/apps/warehouses/models.py)
- [apps/warehouses/views.py](/home/afsal/Desktop/ALGOBIZ/vaaz/apps/warehouses/views.py)

#### Warehouse

Purpose:
- Stores operational warehouses by region
- Users can be assigned to one selected warehouse
- Orders are fulfilled from a warehouse

Fields:
- `warehouse_name`
- `warehouse_address`
- `warehouse_location`
- `warehouse_details`
- `delivery_to`

Notes:
- `warehouse_location` supports `INDIA`, `UAE`, `UK`
- `warehouse_details` is JSON for flexible metadata
- `delivery_to` is JSON for supported delivery regions/countries


### 3. Categories

Files:
- [apps/categories/models.py](/home/afsal/Desktop/ALGOBIZ/vaaz/apps/categories/models.py)

#### Category

Purpose:
- Supports category and subcategory tree

Fields:
- `name_en`
- `name_ar`
- `slug`
- `parent`
- `status`

Behavior:
- Self-referencing `parent` supports nested category structure


### 4. Products

Files:
- [apps/products/models.py](/home/afsal/Desktop/ALGOBIZ/vaaz/apps/products/models.py)

#### Product

Purpose:
- Main product table with multilingual data, pricing, stock, and flexible attributes

Fields:
- `name_en`
- `name_ar`
- `description_en`
- `description_ar`
- `category`
- `sub_category`
- `type`
- `sku`
- `is_featured`
- `status`
- `price_inr`
- `price_aed`
- `price_usd`
- `sale_price_inr`
- `sale_price_aed`
- `sale_price_usd`
- `stock`
- `low_stock_threshold`
- `weight`
- `sizes`
- `colors`

#### ProductImage

Purpose:
- Stores product media records

Fields:
- `product`
- `image`
- `is_primary`

#### ProductWarehouseStock

Purpose:
- Stores stock per warehouse

Fields:
- `product`
- `warehouse`
- `stock`


### 5. Customers

Files:
- [apps/customers/models.py](/home/afsal/Desktop/ALGOBIZ/vaaz/apps/customers/models.py)

#### CustomerProfile

Purpose:
- Extends user for customer-facing preferences

Fields:
- `user`
- `preferred_language`
- `preferred_currency`
- `is_suspended`

#### Wishlist

Purpose:
- Stores customer saved products

Fields:
- `customer`
- `product`


### 6. Cart

Files:
- [apps/cart/models.py](/home/afsal/Desktop/ALGOBIZ/vaaz/apps/cart/models.py)
- [apps/cart/services.py](/home/afsal/Desktop/ALGOBIZ/vaaz/apps/cart/services.py)

#### Cart

Purpose:
- One active cart per customer

Fields:
- `customer`

#### CartItem

Purpose:
- Stores selected products before checkout

Fields:
- `cart`
- `product`
- `quantity`
- `price_snapshot`

Behavior:
- `price_snapshot` freezes the effective price in the customer currency when added


### 7. Orders

Files:
- [apps/orders/models.py](/home/afsal/Desktop/ALGOBIZ/vaaz/apps/orders/models.py)
- [apps/orders/services.py](/home/afsal/Desktop/ALGOBIZ/vaaz/apps/orders/services.py)

#### Order

Purpose:
- Stores completed checkout records

Fields:
- `order_id`
- `customer`
- `warehouse`
- `currency`
- `total_amount`
- `tax_amount`
- `payment_status`
- `order_status`

#### OrderItem

Purpose:
- Stores the purchased product lines

Fields:
- `order`
- `product`
- `quantity`
- `price`

Behavior:
- Checkout creates an order from cart items
- Stock is reduced from product stock and warehouse stock
- A payment record is created automatically


### 8. Payments

Files:
- [apps/payments/models.py](/home/afsal/Desktop/ALGOBIZ/vaaz/apps/payments/models.py)

#### Payment

Purpose:
- Tracks payment state for each order

Fields:
- `order`
- `payment_method`
- `payment_status`
- `transaction_id`

Supported methods:
- `razorpay`
- `stripe`
- `cod`


### 9. Coupons

Files:
- [apps/coupons/models.py](/home/afsal/Desktop/ALGOBIZ/vaaz/apps/coupons/models.py)
- [apps/coupons/services.py](/home/afsal/Desktop/ALGOBIZ/vaaz/apps/coupons/services.py)

#### Coupon

Purpose:
- Region-aware discounting

Fields:
- `coupon_code`
- `coupon_type`
- `coupon_value`
- `valid_from`
- `valid_until`
- `usage_limit`
- `region`
- `status`

Supported types:
- `percentage`
- `fixed`


### 10. Banners

Files:
- [apps/banners/models.py](/home/afsal/Desktop/ALGOBIZ/vaaz/apps/banners/models.py)

#### Banner

Purpose:
- Stores multilingual marketing banners

Fields:
- `headline_en`
- `headline_ar`
- `sub_text_en`
- `sub_text_ar`
- `cta_label_en`
- `cta_label_ar`
- `link`
- `position`
- `device`
- `status`


### 11. Analytics

Files:
- [apps/analytics/models.py](/home/afsal/Desktop/ALGOBIZ/vaaz/apps/analytics/models.py)
- [apps/analytics/services.py](/home/afsal/Desktop/ALGOBIZ/vaaz/apps/analytics/services.py)

#### StoreAnalytics

Purpose:
- Snapshot reporting table

Fields:
- `total_revenue`
- `total_orders`
- `cancellation_rate`


### 12. Settings

Files:
- [apps/settings/models.py](/home/afsal/Desktop/ALGOBIZ/vaaz/apps/settings/models.py)

#### StoreSettings

Fields:
- `store_name_en`
- `store_name_ar`
- `store_email`
- `store_phone`
- `low_stock_threshold`

#### CurrencySettings

Fields:
- `exchange_rate_inr`
- `exchange_rate_aed`
- `exchange_rate_usd`

#### ShippingSettings

Fields:
- `domestic`
- `international`
- `uk_domestic`
- `shipping_price_inr`
- `shipping_price_aed`
- `shipping_price_usd`
- `express_shipping`


## How the System Works

### Authentication Flow

1. Public user registers with email and password.
2. Admin or warehouse admin logs in using JWT.
3. Login response returns:
   - `access`
   - `refresh`
   - `user`
   - `role`
4. Authenticated requests use:

```http
Authorization: Bearer <access_token>
```

### Admin Registration Flow

Admin registration is protected by a header secret.

Required header:

```http
X-Admin-Secret: house-of-vaz-admin-secret
```

This allows safe creation of:
- `admin`
- `warehouse_admin`

### Forgot Password Flow

1. Call forgot-password with email.
2. API generates a reset token.
3. Call reset-password using token and new password.

### Warehouse Selection Flow

1. User logs in.
2. User or warehouse admin selects a warehouse.
3. Selected warehouse is saved on the user record.
4. Frontend can use returned `role` and `selected_warehouse` to scope operations.

### Commerce Flow

1. Admin creates categories and products.
2. Admin creates warehouses and warehouse stock.
3. Customer registers and logs in.
4. Customer profile stores preferred language and currency.
5. Customer adds products to cart.
6. Cart stores item quantity and `price_snapshot`.
7. Customer checks out with a selected warehouse.
8. Order and order items are created.
9. Product stock and warehouse stock are reduced.
10. Payment row is created.


## API Base

Base prefix:

```text
/api/v1/
```


## Authentication APIs

### 1. Register User

`POST /api/v1/auth/register/`

Request:

```json
{
  "email": "user@example.com",
  "full_name": "Normal User",
  "password": "StrongPass123"
}
```

Response:
- Creates a `customer` role user

### 2. Register Admin or Warehouse Admin

`POST /api/v1/auth/admin-register/`

Header:

```http
X-Admin-Secret: house-of-vaz-admin-secret
```

Request for admin:

```json
{
  "email": "admin@example.com",
  "full_name": "Main Admin",
  "password": "StrongPass123",
  "role": "admin"
}
```

Request for warehouse admin:

```json
{
  "email": "ukadmin@example.com",
  "full_name": "UK Warehouse Admin",
  "password": "StrongPass123",
  "role": "warehouse_admin",
  "selected_warehouse": "WAREHOUSE_UUID"
}
```

Response includes:
- `id`
- `email`
- `full_name`
- `role`
- `selected_warehouse`

### 3. Login

`POST /api/v1/auth/login/`

Request:

```json
{
  "email": "admin@example.com",
  "password": "StrongPass123"
}
```

Response:

```json
{
  "refresh": "jwt_refresh_token",
  "access": "jwt_access_token",
  "user": {
    "id": "USER_UUID",
    "email": "admin@example.com",
    "full_name": "Main Admin",
    "role": "admin",
    "selected_warehouse": null,
    "selected_warehouse_name": null,
    "selected_warehouse_location": null,
    "is_verified": false,
    "is_active": true
  },
  "role": "admin"
}
```

### 4. Profile

`GET /api/v1/auth/profile/`

Returns current authenticated user with role and selected warehouse.

### 5. Forgot Password

`POST /api/v1/auth/forgot-password/`

Request:

```json
{
  "email": "admin@example.com"
}
```

Response:

```json
{
  "detail": "Password reset token generated.",
  "token": "RESET_TOKEN_UUID",
  "expires_at": "2026-04-06T12:00:00Z"
}
```

### 6. Reset Password

`POST /api/v1/auth/reset-password/`

Request:

```json
{
  "token": "RESET_TOKEN_UUID",
  "new_password": "NewStrongPass123"
}
```

### 7. Select Warehouse

`POST /api/v1/auth/select-warehouse/`

Request:

```json
{
  "warehouse_id": "WAREHOUSE_UUID"
}
```

Response:
- Updated user profile with warehouse fields

### 8. Create Admin by Existing Admin

`POST /api/v1/auth/create-admin/`

Auth required.

Request:

```json
{
  "email": "manager@example.com",
  "full_name": "Manager",
  "password": "StrongPass123",
  "role": "warehouse_admin",
  "selected_warehouse": "WAREHOUSE_UUID"
}
```


## Warehouse APIs

Files:
- [apps/warehouses/urls.py](/home/afsal/Desktop/ALGOBIZ/vaaz/apps/warehouses/urls.py)

### 1. List Warehouses

`GET /api/v1/warehouses/`

Filters:
- `warehouse_location`
- `is_active`

### 2. Create Warehouse

`POST /api/v1/warehouses/`

Request:

```json
{
  "warehouse_name": "India Main Warehouse",
  "warehouse_address": "Mumbai, India",
  "warehouse_location": "INDIA",
  "warehouse_details": {
    "manager_name": "Afsal",
    "phone": "+91XXXXXXXXXX",
    "email": "india-warehouse@example.com"
  },
  "delivery_to": ["INDIA", "UK"]
}
```

### 3. Retrieve Warehouse

`GET /api/v1/warehouses/{id}/`

### 4. Update Warehouse

`PUT /api/v1/warehouses/{id}/`

### 5. Delete Warehouse

`DELETE /api/v1/warehouses/{id}/`


## Category APIs

### Base Path

`/api/v1/categories/`

Operations:
- `GET /`
- `POST /`
- `GET /{id}/`
- `PUT /{id}/`
- `PATCH /{id}/`
- `DELETE /{id}/`

Key fields:
- `name_en`
- `name_ar`
- `slug`
- `parent`
- `status`


## Product APIs

### Base Paths

- `/api/v1/products/items/`
- `/api/v1/products/images/`
- `/api/v1/products/warehouse-stocks/`

### Product Create Example

`POST /api/v1/products/items/`

```json
{
  "name_en": "Premium Abaya",
  "name_ar": "عباية فاخرة",
  "description_en": "Luxury abaya with premium fabric",
  "description_ar": "عباية فاخرة بخامة ممتازة",
  "category": "CATEGORY_UUID",
  "sub_category": "SUBCATEGORY_UUID",
  "type": "physical",
  "sku": "ABAYA-0001",
  "is_featured": true,
  "status": "active",
  "price_inr": "7999.00",
  "price_aed": "349.00",
  "price_usd": "95.00",
  "sale_price_inr": "6999.00",
  "sale_price_aed": "299.00",
  "sale_price_usd": "85.00",
  "stock": 50,
  "low_stock_threshold": 5,
  "weight": "0.750",
  "sizes": ["S", "M", "L"],
  "colors": ["Black", "Beige"]
}
```

### Product Image Create

`POST /api/v1/products/images/`

### Warehouse Stock Create

`POST /api/v1/products/warehouse-stocks/`

```json
{
  "product": "PRODUCT_UUID",
  "warehouse": "WAREHOUSE_UUID",
  "stock": 20
}
```


## Customer APIs

### Base Paths

- `/api/v1/customers/profiles/`
- `/api/v1/customers/wishlists/`

#### CustomerProfile

Example:

```json
{
  "user": "USER_UUID",
  "preferred_language": "en",
  "preferred_currency": "USD",
  "is_suspended": false
}
```

#### Wishlist

Example:

```json
{
  "customer": "CUSTOMER_PROFILE_UUID",
  "product": "PRODUCT_UUID"
}
```


## Cart APIs

### Base Paths

- `/api/v1/cart/carts/`
- `/api/v1/cart/items/`

### 1. Get or Create My Cart

`POST /api/v1/cart/carts/mine/`

### 2. Add Item to Cart

`POST /api/v1/cart/carts/add_item/`

Request:

```json
{
  "product": "PRODUCT_UUID",
  "quantity": 2
}
```

### 3. Checkout Cart

`POST /api/v1/cart/carts/{cart_id}/checkout/`

Request:

```json
{
  "warehouse": "WAREHOUSE_UUID",
  "currency": "USD"
}
```

Result:
- Creates `Order`
- Creates `OrderItem`
- Decrements stock
- Creates `Payment`
- Clears cart items


## Order APIs

### Base Paths

- `/api/v1/orders/records/`
- `/api/v1/orders/items/`

### Order Fields Returned

- `order_id`
- `customer`
- `warehouse`
- `currency`
- `total_amount`
- `tax_amount`
- `payment_status`
- `order_status`


## Payment APIs

### Base Path

`/api/v1/payments/`

Fields:
- `order`
- `payment_method`
- `payment_status`
- `transaction_id`


## Coupon APIs

### Base Path

`/api/v1/coupons/`

Create example:

```json
{
  "coupon_code": "INDIA10",
  "coupon_type": "percentage",
  "coupon_value": "10.00",
  "valid_from": "2026-04-06T00:00:00Z",
  "valid_until": "2026-05-06T00:00:00Z",
  "usage_limit": 100,
  "region": "INDIA",
  "status": "active"
}
```


## Banner APIs

### Base Path

`/api/v1/banners/`

Create example:

```json
{
  "headline_en": "New Arrivals",
  "headline_ar": "وصل حديثا",
  "sub_text_en": "Explore our newest collection",
  "sub_text_ar": "اكتشف مجموعتنا الجديدة",
  "cta_label_en": "Shop Now",
  "cta_label_ar": "تسوق الآن",
  "link": "https://houseofvaz.com/new-arrivals",
  "position": "hero",
  "device": "both",
  "status": "active"
}
```


## Analytics APIs

### Base Path

`/api/v1/analytics/`

Stores analytics snapshots:
- `total_revenue`
- `total_orders`
- `cancellation_rate`


## Store Settings APIs

### Base Paths

- `/api/v1/settings/store/`
- `/api/v1/settings/currency/`
- `/api/v1/settings/shipping/`

Examples:

#### Store Settings

```json
{
  "store_name_en": "House of Vaz",
  "store_name_ar": "هاوس أوف فاز",
  "store_email": "support@houseofvaz.com",
  "store_phone": "+971500000000",
  "low_stock_threshold": 5
}
```

#### Currency Settings

```json
{
  "exchange_rate_inr": "1.0000",
  "exchange_rate_aed": "0.0440",
  "exchange_rate_usd": "0.0120"
}
```

#### Shipping Settings

```json
{
  "domestic": true,
  "international": true,
  "uk_domestic": true,
  "shipping_price_inr": "250.00",
  "shipping_price_aed": "25.00",
  "shipping_price_usd": "10.00",
  "express_shipping": true
}
```


## API Access Rules

### Public
- Register user
- Admin register with secret
- Login
- Forgot password
- Reset password

### Authenticated User
- Profile
- Select warehouse
- Customer cart operations
- Own orders
- Own payments
- Wishlist and customer actions

### Admin or Warehouse Admin
- Warehouse operations
- Product operations
- Category operations
- Coupon operations
- Banner operations
- Reporting and settings operations

Note:
- Some endpoints currently use `IsAdminOrReadOnly`
- Some write endpoints use `IsAdminUser`


## Query Optimization

The project uses repository-based query access for better ORM control.

Optimizations included:
- `select_related()` for foreign keys
- `prefetch_related()` for reverse and related collections
- indexed fields for common filters
- unique constraints for integrity

Examples:
- Product queries preload category, images, and warehouse stock
- Order queries preload customer, warehouse, and order items
- Cart queries preload items and product data


## Important Working Files

### Routing
- [core/urls.py](/home/afsal/Desktop/ALGOBIZ/vaaz/core/urls.py)
- [config/api.py](/home/afsal/Desktop/ALGOBIZ/vaaz/config/api.py)

### Core
- [core/base_models.py](/home/afsal/Desktop/ALGOBIZ/vaaz/core/base_models.py)
- [core/choices.py](/home/afsal/Desktop/ALGOBIZ/vaaz/core/choices.py)
- [core/permissions.py](/home/afsal/Desktop/ALGOBIZ/vaaz/core/permissions.py)

### Auth
- [apps/user_account/models.py](/home/afsal/Desktop/ALGOBIZ/vaaz/apps/user_account/models.py)
- [apps/user_account/api_v1/views.py](/home/afsal/Desktop/ALGOBIZ/vaaz/apps/user_account/api_v1/views.py)
- [apps/user_account/api_v1/api_router.py](/home/afsal/Desktop/ALGOBIZ/vaaz/apps/user_account/api_v1/api_router.py)

### Commerce
- [apps/products/models.py](/home/afsal/Desktop/ALGOBIZ/vaaz/apps/products/models.py)
- [apps/cart/services.py](/home/afsal/Desktop/ALGOBIZ/vaaz/apps/cart/services.py)
- [apps/orders/services.py](/home/afsal/Desktop/ALGOBIZ/vaaz/apps/orders/services.py)
- [apps/payments/models.py](/home/afsal/Desktop/ALGOBIZ/vaaz/apps/payments/models.py)


## Setup and Run

Run:

```bash
python manage.py makemigrations
python manage.py migrate
python manage.py runserver
```

For admin creation via API, set:

```bash
export ADMIN_REGISTRATION_SECRET=house-of-vaz-admin-secret
```


## Current Notes

- The project is PostgreSQL-ready and falls back to SQLite locally if PostgreSQL drivers are unavailable.
- Product media currently uses `FileField`.
- The forgot-password API currently returns a reset token directly in the response for integration simplicity. In production, replace this with email delivery.
- If the existing database was created with a different custom user model, use a fresh database before running migrations.
