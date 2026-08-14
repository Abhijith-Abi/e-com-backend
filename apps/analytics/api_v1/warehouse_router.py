from django.urls import path

from apps.analytics.api_v1.cancellation_report import WarehouseCancellationReportView, WarehouseCancellationReportExportView
from apps.analytics.api_v1.dashboard import WarehouseDashboardView
from apps.analytics.api_v1.orders_report import WarehouseOrdersReportView, WarehouseOrdersReportExportView
from apps.analytics.api_v1.sales_report import WarehouseSalesReportView, WarehouseSalesReportExportView
from apps.analytics.api_v1.shipment_report import WarehouseShipmentReportView, WarehouseShipmentReportExportView

app_name = "warehouse_analytics_api_v1"

urlpatterns = [
    path("dashboard/", WarehouseDashboardView.as_view(), name="warehouse-dashboard"),
    path("reports/sales/", WarehouseSalesReportView.as_view(), name="warehouse-sales-report"),
    path("reports/sales/export/", WarehouseSalesReportExportView.as_view(), name="warehouse-sales-report-export"),
    path("reports/orders/", WarehouseOrdersReportView.as_view(), name="warehouse-orders-report"),
    path("reports/orders/export/", WarehouseOrdersReportExportView.as_view(), name="warehouse-orders-report-export"),
    path("reports/shipment/", WarehouseShipmentReportView.as_view(), name="warehouse-shipment-report"),
    path("reports/shipment/export/", WarehouseShipmentReportExportView.as_view(), name="warehouse-shipment-report-export"),
    path("reports/cancellation/", WarehouseCancellationReportView.as_view(), name="warehouse-cancellation-report"),
    path("reports/cancellation/export/", WarehouseCancellationReportExportView.as_view(), name="warehouse-cancellation-report-export"),
]
