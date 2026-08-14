from django.urls import path
from rest_framework.routers import SimpleRouter

from apps.analytics.api_v1.cancellation_report import CancellationReportExportView, CancellationReportView
from apps.analytics.api_v1.dashboard import DashboardView
from apps.analytics.api_v1.orders_report import OrdersReportExportView, OrdersReportView
from apps.analytics.api_v1.sales_report import SalesReportExportView, SalesReportView
from apps.analytics.api_v1.shipment_report import ShipmentReportExportView, ShipmentReportView
from apps.analytics.api_v1.views import StoreAnalyticsViewSet

app_name = "analytics_api_v1"

router = SimpleRouter()
router.register("", StoreAnalyticsViewSet, basename="analytics")

urlpatterns = [
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
    path("reports/sales/", SalesReportView.as_view(), name="sales-report"),
    path("reports/sales/export/", SalesReportExportView.as_view(), name="sales-report-export"),
    path("reports/orders/", OrdersReportView.as_view(), name="orders-report"),
    path("reports/orders/export/", OrdersReportExportView.as_view(), name="orders-report-export"),
    path("reports/shipment/", ShipmentReportView.as_view(), name="shipment-report"),
    path("reports/shipment/export/", ShipmentReportExportView.as_view(), name="shipment-report-export"),
    path("reports/cancellation/", CancellationReportView.as_view(), name="cancellation-report"),
    path("reports/cancellation/export/", CancellationReportExportView.as_view(), name="cancellation-report-export"),
] + router.urls
