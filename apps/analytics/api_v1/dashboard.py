from datetime import timedelta

from django.db.models import Count, DecimalField, F, Sum
from django.db.models.functions import Coalesce, TruncDate
from django.utils import timezone
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.customers.models import CustomerProfile
from apps.orders.models import Order, OrderItem
from apps.products.models import Product
from core.choices import OrderStatusChoices
from core.permissions import IsWarehouseAdminOrAdmin


def _parse_date_range(request):
    now = timezone.now()
    date_from_str = request.query_params.get("date_from") or request.query_params.get("from_date")
    date_to_str = request.query_params.get("date_to") or request.query_params.get("to_date")
    if date_from_str:
        from django.utils.dateparse import parse_date
        d = parse_date(date_from_str)
        date_from = timezone.make_aware(timezone.datetime(d.year, d.month, d.day)) if d else now - timedelta(days=30)
    else:
        date_from = now - timedelta(days=30)
    if date_to_str:
        from django.utils.dateparse import parse_date
        d = parse_date(date_to_str)
        date_to = timezone.make_aware(timezone.datetime(d.year, d.month, d.day, 23, 59, 59)) if d else now
    else:
        date_to = now
    return date_from, date_to


def _prev_period(date_from, date_to):
    delta = date_to - date_from
    return date_from - delta - timedelta(seconds=1), date_from - timedelta(seconds=1)


def _pct_change(current, previous):
    curr_val = float(current) if current is not None else 0.0
    prev_val = float(previous) if previous is not None else 0.0

    if prev_val == 0.0:
        return 100.0 if curr_val > 0.0 else 0.0
    
    return round((curr_val / prev_val) * 100, 1)


def _build_dashboard(date_from, date_to, warehouse=None):
    prev_date_from, prev_date_to = _prev_period(date_from, date_to)

    wh_filter = {"warehouse": warehouse} if warehouse else {}

    # 1. Total Orders (Selected Period vs Previous Period)
    total_orders = Order.objects.filter(
        created_at__gte=date_from, created_at__lte=date_to, is_deleted=False, **wh_filter
    ).count()
    prev_total_orders = Order.objects.filter(
        created_at__gte=prev_date_from, created_at__lte=prev_date_to, is_deleted=False, **wh_filter
    ).count()

    # 2. Pending Orders (Selected Period vs Previous Period)
    pending_orders = Order.objects.filter(
        created_at__gte=date_from, created_at__lte=date_to, order_status=OrderStatusChoices.PENDING, is_deleted=False, **wh_filter
    ).count()
    prev_pending_orders = Order.objects.filter(
        created_at__gte=prev_date_from, created_at__lte=prev_date_to, order_status=OrderStatusChoices.PENDING, is_deleted=False, **wh_filter
    ).count()

    # 3. Revenue (Selected Period vs Previous Period)
    revenue_today = Order.objects.filter(
        created_at__gte=date_from, created_at__lte=date_to, payment_status="paid", is_deleted=False, **wh_filter
    ).aggregate(total=Coalesce(Sum("total_amount"), 0, output_field=DecimalField()))["total"]

    prev_revenue_today = Order.objects.filter(
        created_at__gte=prev_date_from, created_at__lte=prev_date_to, payment_status="paid", is_deleted=False, **wh_filter
    ).aggregate(total=Coalesce(Sum("total_amount"), 0, output_field=DecimalField()))["total"]

    # 4. New Customers (Selected Period vs Previous Period) - global (no warehouse FK)
    new_customers = CustomerProfile.objects.filter(
        created_at__gte=date_from, created_at__lte=date_to, is_deleted=False
    ).count()
    prev_new_customers = CustomerProfile.objects.filter(
        created_at__gte=prev_date_from, created_at__lte=prev_date_to, is_deleted=False
    ).count()

    product_filter = {"warehouse": warehouse} if warehouse else {}
    from apps.gift_cards.models import GiftCard, GiftCardWrap

    low_stock_products_qs = Product.objects.filter(
        is_active=True, is_deleted=False, stock__lte=F("low_stock_threshold"), **product_filter
    )
    
    from core.choices import StatusChoices
    
    low_stock_gc_qs = GiftCard.objects.filter(
        status=StatusChoices.ACTIVE, is_deleted=False, units__lte=F("reminder_threshold"), **product_filter
    )
    
    low_stock_wrap_qs = GiftCardWrap.objects.filter(
        status=StatusChoices.ACTIVE, is_deleted=False, units__lte=F("reminder_threshold"), **product_filter
    )

    total_low_stock_count = low_stock_products_qs.count() + low_stock_gc_qs.count() + low_stock_wrap_qs.count()

    daily_sales = (
        Order.objects.filter(
            created_at__gte=date_from, created_at__lte=date_to,
            is_deleted=False, **wh_filter,
        )
        .annotate(date=TruncDate("created_at"))
        .values("date")
        .annotate(
            revenue=Coalesce(Sum("total_amount"), 0, output_field=DecimalField()),
            orders=Count("id"),
        )
        .order_by("date")
    )

    order_item_filter = {"order__warehouse": warehouse} if warehouse else {}
    top_products = (
        OrderItem.objects.filter(
            order__created_at__gte=date_from,
            order__created_at__lte=date_to,
            order__is_deleted=False,
            is_deleted=False,
            **order_item_filter,
        )
        .exclude(order__order_status=OrderStatusChoices.CANCELLED)
        .values(
            "product__id",
            "product__name_en",
            "product__name_ar",
            "product__sku",
            "product__price_inr",
            "product__sale_price_inr",
            "product__price_gbp",
            "product__sale_price_gbp",
            "product__price_usd",
            "product__sale_price_usd",
        )
        .annotate(
            units_sold=Sum("quantity"),
        )
        .order_by("-units_sold")[:5]
    )

    recent_orders = (
        Order.objects.filter(is_deleted=False, **wh_filter)
        .select_related("customer__user")
        .order_by("-created_at")[:10]
    )

    low_stock_data = {
        "count": total_low_stock_count,
        "products": [
            {
                "id": str(p.id),
                "name": p.name_en,
                "sku": p.sku,
                "stock": p.stock,
                "threshold": p.low_stock_threshold,
                "type": p.type,
                "price": float(p.sale_price_inr if p.sale_price_inr is not None else p.price_inr) if (p.sale_price_inr is not None or p.price_inr is not None) else None,
            }
            for p in low_stock_products_qs
        ],
        "gift_cards": [
            {
                "id": str(gc.id),
                "name": gc.card_name,
                "stock": gc.units,
                "threshold": gc.reminder_threshold,
                "price": float(gc.price_inr) if gc.price_inr else None,
            }
            for gc in low_stock_gc_qs
        ],
        "gift_wraps": [
            {
                "id": str(gw.id),
                "name": gw.wrap_name,
                "stock": gw.units,
                "threshold": gw.reminder_threshold,
                "price": float(gw.price_inr) if gw.price_inr else None,
            }
            for gw in low_stock_wrap_qs
        ]
    }

    return {
        "date_from": date_from.date(),
        "date_to": date_to.date(),
        "warehouse_id": str(warehouse.id) if warehouse else None,
        "warehouse_name": warehouse.warehouse_name if warehouse else None,
        "summary": {
            "total_orders": {"value": total_orders, "change_pct": _pct_change(total_orders, prev_total_orders)},
            "pending_orders": {"value": pending_orders, "change_pct": _pct_change(pending_orders, prev_pending_orders)},
            "revenue_today": {"value": revenue_today, "change_pct": _pct_change(float(revenue_today), float(prev_revenue_today))},
            "new_customers": {"value": new_customers, "change_pct": _pct_change(new_customers, prev_new_customers)},
        },
        "low_stock_alert": low_stock_data,
        "daily_sales_chart": [
            {"date": str(row["date"]), "revenue": row["revenue"], "orders": row["orders"]}
            for row in daily_sales
        ],
        "top_selling_products": [
            {
                "product_id": str(row["product__id"]),
                "name_en": row["product__name_en"],
                "name_ar": row["product__name_ar"],
                "sku": row["product__sku"],
                "units_sold": row["units_sold"],
                "price_inr": row["product__price_inr"],
                "sale_price_inr": row["product__sale_price_inr"],
                "price_gbp": row["product__price_gbp"],
                "sale_price_gbp": row["product__sale_price_gbp"],
                "price_usd": row["product__price_usd"],
                "sale_price_usd": row["product__sale_price_usd"],
                "price_inr_with_gst": round(float(row["product__sale_price_inr"] or row["product__price_inr"]) * 1.18, 2) if (row["product__sale_price_inr"] or row["product__price_inr"]) is not None else None,
                "gst_amount_inr": round(float(row["product__sale_price_inr"] or row["product__price_inr"]) * 0.18, 2) if (row["product__sale_price_inr"] or row["product__price_inr"]) is not None else None,
            }
            for row in top_products
        ],
        "recent_orders": [
            {
                "id": str(o.id),
                "order_id": o.order_id,
                "customer_name": o.customer.user.full_name or o.customer.user.email,
                "date": o.created_at.date(),
                "currency": o.currency,
                "amount": o.total_amount,
                "order_status": o.order_status,
                "payment_status": o.payment_status,
            }
            for o in recent_orders
        ],
    }


def _build_dummy_dashboard(warehouse_id=None, warehouse_name=None):
    """Returns realistic dummy data for frontend development."""
    from datetime import date, timedelta
    today = timezone.now().date()
    return {
        "date_from": str(today - timedelta(days=30)),
        "date_to": str(today),
        "warehouse_id": warehouse_id,
        "warehouse_name": warehouse_name,
        "summary": {
            "total_orders": {"value": 142, "change_pct": 12.5},
            "pending_orders": {"value": 18, "change_pct": -4.2},
            "revenue_today": {"value": 24500.00, "change_pct": 8.3},
            "new_customers": {"value": 37, "change_pct": 21.0},
        },
        "low_stock_alert": {
            "count": 5,
            "products": [
                {
                    "id": "11111111-1111-1111-1111-111111111111",
                    "name": "Classic White Tee",
                    "sku": "SKU-001",
                    "stock": 2,
                    "threshold": 5,
                    "type": "physical",
                    "price": 299.00
                }
            ],
            "gift_cards": [
                {
                    "id": "66666666-6666-6666-6666-666666666666",
                    "name": "Eid Special $50",
                    "stock": 1,
                    "threshold": 10,
                    "price": 50.00
                }
            ],
            "gift_wraps": [
                {
                    "id": "77777777-7777-7777-7777-777777777777",
                    "name": "Premium Gold Wrap",
                    "stock": 0,
                    "threshold": 5,
                    "price": 5.00
                }
            ]
        },
        "daily_sales_chart": [
            {"date": str(today - timedelta(days=i)), "revenue": round(8000 + (i * 300) % 5000, 2), "orders": 4 + i % 8}
            for i in range(29, -1, -1)
        ],
        "top_selling_products": [
            {"product_id": "11111111-1111-1111-1111-111111111111", "name_en": "Classic White Tee", "name_ar": "تيشيرت أبيض كلاسيكي", "sku": "SKU-001", "units_sold": 84, "price_inr": "299.00", "sale_price_inr": "249.00", "price_gbp": "15.00", "sale_price_gbp": "12.00", "price_usd": "20.00", "sale_price_usd": "16.00", "price_inr_with_gst": 293.82, "gst_amount_inr": 44.82},
            {"product_id": "22222222-2222-2222-2222-222222222222", "name_en": "Slim Fit Jeans", "name_ar": "جينز ضيق", "sku": "SKU-002", "units_sold": 61, "price_inr": "300.00", "sale_price_inr": None, "price_gbp": "20.00", "sale_price_gbp": None, "price_usd": "25.00", "sale_price_usd": None, "price_inr_with_gst": 354.00, "gst_amount_inr": 54.00},
            {"product_id": "33333333-3333-3333-3333-333333333333", "name_en": "Floral Dress", "name_ar": "فستان زهري", "sku": "SKU-003", "units_sold": 45, "price_inr": "499.00", "sale_price_inr": "399.00", "price_gbp": "25.00", "sale_price_gbp": "20.00", "price_usd": "35.00", "sale_price_usd": "28.00", "price_inr_with_gst": 470.82, "gst_amount_inr": 71.82},
            {"product_id": "44444444-4444-4444-4444-444444444444", "name_en": "Leather Jacket", "name_ar": "جاكيت جلد", "sku": "SKU-004", "units_sold": 29, "price_inr": "800.00", "sale_price_inr": None, "price_gbp": "50.00", "sale_price_gbp": None, "price_usd": "70.00", "sale_price_usd": None, "price_inr_with_gst": 944.00, "gst_amount_inr": 144.00},
            {"product_id": "55555555-5555-5555-5555-555555555555", "name_en": "Sneakers Pro", "name_ar": "حذاء رياضي", "sku": "SKU-005", "units_sold": 22, "price_inr": "599.00", "sale_price_inr": "499.00", "price_gbp": "35.00", "sale_price_gbp": "30.00", "price_usd": "45.00", "sale_price_usd": "40.00", "price_inr_with_gst": 588.82, "gst_amount_inr": 89.82},
        ],
        "recent_orders": [
            {"id": "11111111-1111-1111-1111-111111111111", "order_id": "ORD-1024", "customer_name": "Rahul Sharma", "date": str(today), "currency": "INR", "amount": 4599.00, "order_status": "delivered", "payment_status": "paid"},
            {"id": "22222222-2222-2222-2222-222222222222", "order_id": "ORD-1023", "customer_name": "Priya Nair", "date": str(today - timedelta(days=1)), "currency": "INR", "amount": 2999.00, "order_status": "shipped", "payment_status": "paid"},
            {"id": "33333333-3333-3333-3333-333333333333", "order_id": "ORD-1022", "customer_name": "Arjun Mehta", "date": str(today - timedelta(days=1)), "currency": "INR", "amount": 1499.00, "order_status": "processing", "payment_status": "paid"},
            {"id": "44444444-4444-4444-4444-444444444444", "order_id": "ORD-1021", "customer_name": "Sara Ali", "date": str(today - timedelta(days=2)), "currency": "INR", "amount": 7200.00, "order_status": "confirmed", "payment_status": "authorized"},
            {"id": "55555555-5555-5555-5555-555555555555", "order_id": "ORD-1020", "customer_name": "Kiran Das", "date": str(today - timedelta(days=2)), "currency": "INR", "amount": 3100.00, "order_status": "pending", "payment_status": "pending"},
        ],
    }


_DASHBOARD_PARAMS = [
    OpenApiParameter("date_from", description="Start date (YYYY-MM-DD), default: 30 days ago", required=False),
    OpenApiParameter("date_to", description="End date (YYYY-MM-DD), default: today", required=False),
    OpenApiParameter("from_date", description="Alternative start date parameter (YYYY-MM-DD)", required=False),
    OpenApiParameter("to_date", description="Alternative end date parameter (YYYY-MM-DD)", required=False),
    OpenApiParameter("dummy", description="Return dummy data for frontend dev (pass dummy=true)", required=False),
]


@extend_schema(tags=["Analytics"], summary="Global admin dashboard summary", parameters=_DASHBOARD_PARAMS)
class DashboardView(APIView):
    """Global dashboard — superadmin only, shows data across all warehouses."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.query_params.get("dummy", "").lower() == "true":
            return Response(_build_dummy_dashboard())
        date_from, date_to = _parse_date_range(request)
        return Response(_build_dashboard(date_from, date_to, warehouse=None))


@extend_schema(
    tags=["Warehouse Analytics"],
    summary="Warehouse-scoped dashboard summary",
    parameters=_DASHBOARD_PARAMS,
)
class WarehouseDashboardView(APIView):
    """Dashboard scoped to a specific warehouse — accessible by warehouse_admin of that warehouse or superadmin."""
    permission_classes = [IsWarehouseAdminOrAdmin]

    def get(self, request, *args, **kwargs):
        if request.query_params.get("dummy", "").lower() == "true":
            wh = getattr(request, "warehouse", None)
            return Response(_build_dummy_dashboard(
                warehouse_id=str(wh.id) if wh else None,
                warehouse_name=wh.warehouse_name if wh else None,
            ))
        date_from, date_to = _parse_date_range(request)
        return Response(_build_dashboard(date_from, date_to, warehouse=request.warehouse))
