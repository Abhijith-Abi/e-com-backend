import csv
import io

from django.db.models import DecimalField, F, Sum
from django.db.models.functions import Coalesce
from django.http import HttpResponse
from drf_spectacular.utils import OpenApiParameter, extend_schema, OpenApiResponse
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.analytics.api_v1.dashboard import _parse_date_range
from apps.orders.models import OrderItem
from apps.products.models import Product


_PARAMS = [
    OpenApiParameter("date_from", description="Start date (YYYY-MM-DD)", required=False),
    OpenApiParameter("date_to", description="End date (YYYY-MM-DD)", required=False),
    OpenApiParameter("dummy", description="Return dummy data (dummy=true)", required=False),
]


def _build_product_report(date_from, date_to, warehouse=None):
    wh_filter = {"warehouse": warehouse} if warehouse else {}
    order_wh_filter = {"order__warehouse": warehouse} if warehouse else {}

    # Top selling products
    top_products = (
        OrderItem.objects.filter(
            order__created_at__gte=date_from,
            order__created_at__lte=date_to,
            order__is_deleted=False,
            order__payment_status="paid",
            order__order_status__in=["confirmed", "processing", "shipped", "delivered"],
            is_deleted=False,
            **order_wh_filter,
        )
        .values("product__id", "product__name_en", "product__sku", "product__stock")
        .annotate(
            units_sold=Sum("quantity"),
            total_revenue=Coalesce(
                Sum(F("quantity") * F("price"), output_field=DecimalField()),
                0,
                output_field=DecimalField(),
            ),
        )
        .order_by("-units_sold")[:10]
    )

    # Low stock products
    low_stock = (
        Product.objects.filter(
            is_active=True, is_deleted=False,
            stock__lte=F("low_stock_threshold"),
            **wh_filter,
        )
        .values("id", "name_en", "sku", "stock", "low_stock_threshold")
        .order_by("stock")[:20]
    )

    # Inventory summary
    inventory = Product.objects.filter(is_deleted=False, **wh_filter)
    total_products = inventory.count()
    out_of_stock = inventory.filter(stock=0).count()
    low_stock_count = inventory.filter(stock__lte=F("low_stock_threshold"), stock__gt=0).count()
    in_stock = inventory.filter(stock__gt=F("low_stock_threshold")).count()

    return {
        "date_from": date_from.date(),
        "date_to": date_to.date(),
        "warehouse_id": str(warehouse.id) if warehouse else None,
        "inventory_summary": {
            "total_products": total_products,
            "in_stock": in_stock,
            "low_stock": low_stock_count,
            "out_of_stock": out_of_stock,
        },
        "top_selling_products": [
            {
                "product_id": str(row["product__id"]),
                "name_en": row["product__name_en"],
                "sku": row["product__sku"],
                "stock": row["product__stock"],
                "units_sold": row["units_sold"],
                "total_revenue": float(row["total_revenue"]),
            }
            for row in top_products
        ],
        "low_stock_products": [
            {
                "product_id": str(row["id"]),
                "name_en": row["name_en"],
                "sku": row["sku"],
                "stock": row["stock"],
                "low_stock_threshold": row["low_stock_threshold"],
            }
            for row in low_stock
        ],
    }


def _build_dummy_product_report():
    return {
        "date_from": "2024-01-01",
        "date_to": "2024-06-30",
        "warehouse_id": None,
        "inventory_summary": {
            "total_products": 320,
            "in_stock": 280,
            "low_stock": 25,
            "out_of_stock": 15,
        },
        "top_selling_products": [
            {"product_id": "11111111-1111-1111-1111-111111111111", "name_en": "Classic White Tee", "sku": "SKU-001", "stock": 45, "units_sold": 84, "total_revenue": 12600.00},
            {"product_id": "22222222-2222-2222-2222-222222222222", "name_en": "Slim Fit Jeans", "sku": "SKU-002", "stock": 30, "units_sold": 61, "total_revenue": 18300.00},
            {"product_id": "33333333-3333-3333-3333-333333333333", "name_en": "Floral Dress", "sku": "SKU-003", "stock": 12, "units_sold": 45, "total_revenue": 13500.00},
        ],
        "low_stock_products": [
            {"product_id": "44444444-4444-4444-4444-444444444444", "name_en": "Leather Jacket", "sku": "SKU-004", "stock": 3, "low_stock_threshold": 5},
            {"product_id": "55555555-5555-5555-5555-555555555555", "name_en": "Sneakers Pro", "sku": "SKU-005", "stock": 2, "low_stock_threshold": 5},
        ],
    }


@extend_schema(
    tags=["Analytics"],
    summary="Product report — top selling, low stock, inventory summary",
    parameters=_PARAMS,
    responses={200: OpenApiResponse(description="Product report data")},
)
class ProductReportView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.query_params.get("dummy", "").lower() == "true":
            return Response(_build_dummy_product_report())
        date_from, date_to = _parse_date_range(request)
        return Response(_build_product_report(date_from, date_to))


@extend_schema(
    tags=["Warehouse Analytics"],
    summary="Warehouse product report — top selling, low stock, inventory summary",
    parameters=_PARAMS,
    responses={200: OpenApiResponse(description="Product report data")},
)
class WarehouseProductReportView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        if request.query_params.get("dummy", "").lower() == "true":
            data = _build_dummy_product_report()
            wh = getattr(request, "warehouse", None)
            data["warehouse_id"] = str(wh.id) if wh else None
            return Response(data)
        date_from, date_to = _parse_date_range(request)
        return Response(_build_product_report(date_from, date_to, warehouse=request.warehouse))


@extend_schema(
    tags=["Analytics"],
    summary="Export product report as CSV",
    parameters=_PARAMS,
    responses={200: OpenApiResponse(description="CSV File attachment")},
)
class ProductReportExportView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        date_from, date_to = _parse_date_range(request)
        data = _build_product_report(date_from, date_to)

        output = io.StringIO()
        writer = csv.writer(output)

        writer.writerow(["Product Report"])
        writer.writerow(["Date From", data["date_from"], "Date To", data["date_to"]])
        writer.writerow([])
        writer.writerow(["Inventory Summary"])
        for k, v in data["inventory_summary"].items():
            writer.writerow([k.replace("_", " ").title(), v])
        writer.writerow([])

        writer.writerow(["Top Selling Products"])
        writer.writerow(["Name", "SKU", "Stock", "Units Sold", "Total Revenue"])
        for row in data["top_selling_products"]:
            writer.writerow([row["name_en"], row["sku"], row["stock"], row["units_sold"], row["total_revenue"]])
        writer.writerow([])

        writer.writerow(["Low Stock Products"])
        writer.writerow(["Name", "SKU", "Stock", "Threshold"])
        for row in data["low_stock_products"]:
            writer.writerow([row["name_en"], row["sku"], row["stock"], row["low_stock_threshold"]])

        response = HttpResponse(output.getvalue(), content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="product_report.csv"'
        return response
