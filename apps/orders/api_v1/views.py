from django.db.models import Case, IntegerField, Value, When
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view, inline_serializer
from rest_framework.pagination import PageNumberPagination
from rest_framework import permissions, viewsets, status, fields
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from rest_framework.response import Response
from django.conf import settings
from apps.orders.api_v1.serializers import OrderItemSerializer, OrderSerializer, OrderTrackingSerializer
from apps.orders.models import Order, ORDER_STATUS_SEQUENCE, OrderItem
from apps.orders.repositories import OrderItemRepository, OrderRepository
from apps.orders.services import OrderService                  
from core.permissions import IsActiveCustomer

# Status sort priority: pending first, then confirmed, processing, shipped, delivered, cancelled
STATUS_ORDER = Case(
    When(order_status="pending", then=Value(0)),
    When(order_status="confirmed", then=Value(1)),
    When(order_status="processing", then=Value(2)),
    When(order_status="shipped", then=Value(3)),
    When(order_status="delivered", then=Value(4)),
    When(order_status="cancelled", then=Value(5)),
    default=Value(6),
    output_field=IntegerField(),
)

class OrderItemsPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class CustomerOrderItemsView(APIView):
    """
    Get all order items for a customer with pagination (10 per page).
    GET /api/v1/orders/customer/{customer_id}/items/?page=1&page_size=10
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        tags=["Orders"],
        summary="Get customer order items with timeline and pagination",
        parameters=[
            OpenApiParameter("page", description="Page number (default: 1)", required=False, type=int),
            OpenApiParameter("page_size", description="Items per page (default: 10, max: 100)", required=False, type=int),
            OpenApiParameter("search", description="Search by order number or tracking ID", required=False, type=str),
        ],
        responses={200: dict}
    )
    def get(self, request, customer_id=None):
        from django.core.paginator import Paginator
        from django.db.models import Q
        
        # Get all order items for customer
        # Filter by customer_id from URL and ensure user owns this customer
        order_items = OrderItem.objects.filter(
            order__customer__id=customer_id,  # ← USE customer_id from URL
            order__customer__user=request.user,  # ← VERIFY ownership
            order__is_deleted=False
        ).select_related(
            "order",
            "product"
        )
        
        # Apply search filter for order_id, tracking_number, or product name
        search_query = request.query_params.get('search', '').strip()
        if search_query:
            order_items = order_items.filter(
                Q(order__order_id__icontains=search_query) |
                Q(order__tracking_number__icontains=search_query) |
                Q(product__name_en__icontains=search_query)
            )

        
        order_items = order_items.order_by("-order__created_at")

        # Apply pagination
        paginator = Paginator(order_items, 10)  # 10 items per page
        page_number = request.query_params.get('page', 1)
        
        try:
            page_obj = paginator.page(page_number)
        except:
            return Response(
                {"error": "Invalid page number"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Build response with timeline for each item
        data = []
        for item in page_obj:
            order = item.order
            
            # Get status history for timeline
            history = {h.status: h.changed_at for h in order.status_history.all()}
            timeline = []
            for i, s in enumerate(["pending", "confirmed", "processing", "shipped", "delivered"], 1):
                timeline.append({
                    "step": i,
                    "status": s.upper(),
                    "timestamp": history.get(s).isoformat() if history.get(s) else None,
                    "message": self.get_status_message(s, order),
                    "current": (s == order.order_status.lower())
                })
            
            data.append({
                "order_id": order.order_id,
                "tracking_number": order.tracking_number or None,
                "product_name": item.product.name_en,
                "product_uid": str(item.product.id),
                "order_status": order.order_status.upper(),
                "selected_size": item.selected_size or "One Size",
                "selected_color": item.selected_color or "Default",
                "quantity": item.quantity,
                "price": str(item.price),
                "order_date": order.created_at.strftime("%Y-%m-%d"),
                "timeline": timeline
            })

        return Response({
            "status": 200,
            "message": "Customer order items retrieved successfully",
            "pagination": {
                "current_page": page_obj.number,
                "total_pages": paginator.num_pages,
                "page_size": 10,
                "total_items": paginator.count,
                "has_next": page_obj.has_next(),
                "has_previous": page_obj.has_previous(),
                "next_page": page_obj.next_page_number() if page_obj.has_next() else None,
                "previous_page": page_obj.previous_page_number() if page_obj.has_previous() else None
            },
            "data": data,
            "summary": {
                "total_items": paginator.count,
                "items_this_page": len(data)
            }
        }, status=status.HTTP_200_OK)

    def get_status_message(self, status, order):
        messages = {
            "pending": "Order placed successfully",
            "confirmed": "Order confirmed by warehouse",
            "processing": "Order is being packed",
            "shipped": f"Package shipped with {order.courier.name if order.courier else 'Courier'}",
            "delivered": "Package delivered successfully"
        }
        return messages.get(status, "")



@extend_schema_view(
    list=extend_schema(
        tags=["Orders"],
        summary="List orders",
        parameters=[
            OpenApiParameter("customer", description="Filter by customer UUID", required=False),
            OpenApiParameter("warehouse", description="Filter by warehouse UUID", required=False),
            OpenApiParameter("currency", description="Filter by currency (INR, GBP, USD)", required=False),
            OpenApiParameter("payment_status", description="Filter by payment status (pending, authorized, paid, failed, refunded)", required=False),
            OpenApiParameter("order_status", description="Filter by order status (pending, confirmed, processing, shipped, delivered, cancelled)", required=False),
            OpenApiParameter("search", description="Search by order_id, customer__user__email", required=False),
            OpenApiParameter("ordering", description="Order by: created_at, total_amount", required=False),
        ],
    ),
    create=extend_schema(tags=["Orders"], summary="Create an order"),
    retrieve=extend_schema(tags=["Orders"], summary="Get an order"),
    update=extend_schema(tags=["Orders"], summary="Update an order"),
    partial_update=extend_schema(tags=["Orders"], summary="Partially update an order"),
    destroy=extend_schema(tags=["Orders"], summary="Delete an order"),
)
class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    queryset = OrderRepository.list_orders()
    permission_classes = [IsActiveCustomer]
    filterset_fields = ("customer", "warehouse", "currency", "payment_status", "order_status")
    search_fields = ("order_id", "customer__user__email", "customer__user__full_name")
    ordering_fields = ("created_at", "total_amount")

    def get_permissions(self):
        if self.action in ("update", "partial_update", "destroy"):
            return [permissions.IsAdminUser()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.is_admin:
            return queryset.order_by("-created_at")
        return queryset.filter(customer__user=self.request.user).order_by("-created_at")

    def perform_create(self, serializer):
        serializer.save(order_id=OrderService.generate_order_id())

    @extend_schema(
        tags=["Orders"],
        summary="Cancel an order",
        description="Cancel an order by order UUID. Only allowed if order status is pending or confirmed.",
        request=inline_serializer(
            name="CancelOrderRequest",
            fields={
                "order_id": fields.UUIDField(help_text="Order UUID to cancel"),
                "reason": fields.CharField(required=False, help_text="Reason for cancellation (optional)"),
            }
        ),
        responses={200: inline_serializer(
            name="CancelOrderResponse",
            fields={
                "order_id": fields.CharField(),
                "status": fields.CharField(),
                "message": fields.CharField(),
            }
        ), 400: dict, 404: dict},
    )
    @action(detail=False, methods=["post"], url_path="cancel")
    def cancel(self, request):
        order_id = request.data.get("order_id")
        reason = request.data.get("reason", "")
        
        if not order_id:
            return Response({"detail": "order_id (UUID) is required."}, status=status.HTTP_400_BAD_REQUEST)

        # Try to find order by UUID (id field)
        try:
            order = Order.objects.get(
                id=order_id,
                customer__user=request.user,
                is_deleted=False,
            )
        except (Order.DoesNotExist, ValueError):
            return Response({"detail": "Order not found."}, status=status.HTTP_404_NOT_FOUND)

        if order.order_status not in ("pending", "confirmed"):
            return Response(
                {"detail": f"Order cannot be cancelled. Current status: {order.order_status}."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        from apps.products.services import ProductService
        for item in order.items.select_related("product").all():
            ProductService.increment_stock(
                item.product,
                item.quantity,
                selected_color=item.selected_color,
                selected_size=item.selected_size
            )

        # Refund gift card and wrap stock if any were used
        if order.applied_gift_card:
            order.applied_gift_card.units += 1
            order.applied_gift_card.save(update_fields=["units", "updated_at"])

        if order.applied_gift_wrap:
            order.applied_gift_wrap.units += 1
            order.applied_gift_wrap.save(update_fields=["units", "updated_at"])

        order.order_status = "cancelled"
        order.cancelled_by = "user"
        order.cancellation_reason = reason
        if reason:
            order.notes = f"Cancellation reason: {reason}"
        order.save(update_fields=["order_status", "cancelled_by", "cancellation_reason", "notes", "updated_at"])

        # Refund loyalty points if any were used
        if order.points_redeemed and order.points_redeemed > 0:
            from apps.redeem.services import PointWalletService
            PointWalletService.credit_points(
                customer=order.customer,
                points=order.points_redeemed,
                description=f"Points refunded for cancelled order {order.order_id}",
                order=order
            )

        return Response({
            "id": str(order.id),
            "order_id": order.order_id,
            "status": "cancelled",
            "message": "Order cancelled successfully"
        }, status=status.HTTP_200_OK)


@extend_schema_view(
    list=extend_schema(
        tags=["Orders"],
        summary="List order items",
        parameters=[
            OpenApiParameter("order", description="Filter by order UUID", required=False),
            OpenApiParameter("product", description="Filter by product UUID", required=False),
        ],
    ),
    retrieve=extend_schema(tags=["Orders"], summary="Get an order item"),
)
class OrderItemViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = OrderItemSerializer
    queryset = OrderItemRepository.list_items()
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ("order", "product")

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.is_admin:
            return queryset
        return queryset.filter(order__customer__user=self.request.user)


@extend_schema_view(
    list=extend_schema(
        tags=["Warehouse Orders"],
        summary="List orders for a warehouse",
        parameters=[
            OpenApiParameter("currency", description="Filter by currency (INR, GBP, USD)", required=False),
            OpenApiParameter("payment_status", description="Filter by payment status", required=False),
            OpenApiParameter("order_status", description="Filter by order status", required=False),
            OpenApiParameter("search", description="Search by order_id, customer__user__email", required=False),
            OpenApiParameter("ordering", description="Order by: created_at, total_amount", required=False),
            OpenApiParameter("from_date", description="Filter orders created from this date (YYYY-MM-DD)", required=False),
            OpenApiParameter("to_date", description="Filter orders created up to this date (YYYY-MM-DD)", required=False),
        ],
    ),
    retrieve=extend_schema(tags=["Warehouse Orders"], summary="Get an order"),
    update=extend_schema(tags=["Warehouse Orders"], summary="Update an order"),
    partial_update=extend_schema(tags=["Warehouse Orders"], summary="Partially update an order"),
    destroy=extend_schema(tags=["Warehouse Orders"], summary="Delete an order"),
)
class WarehouseScopedOrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ("currency", "payment_status", "order_status")
    search_fields = ("order_id", "customer__user__email", "customer__user__full_name")
    ordering_fields = ("created_at", "total_amount")

    def get_permissions(self):
        from core.permissions import IsWarehouseAdminOrAdmin
        return [IsWarehouseAdminOrAdmin()]

    def get_queryset(self):
        warehouse = getattr(self.request, "warehouse", None)
        if not warehouse:
            return OrderRepository.list_orders().none()

        queryset = (
            OrderRepository.list_orders()
            .filter(warehouse=warehouse)
            .annotate(status_priority=STATUS_ORDER)
            .order_by("-created_at")
        )

        from_date = self.request.query_params.get("from_date")
        to_date = self.request.query_params.get("to_date")

        if from_date:
            queryset = queryset.filter(created_at__date__gte=from_date)
        if to_date:
            queryset = queryset.filter(created_at__date__lte=to_date)

        return queryset

    def perform_create(self, serializer):
        serializer.save(order_id=OrderService.generate_order_id())


class OrderTrackingView(APIView):
    """
    Public Order & Shipment Tracking endpoint.
    GET /api/v1/orders/track/?order_id=ORD-XXXX
    """
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Orders"],
        summary="Track order shipment status publicly",
        parameters=[
            OpenApiParameter("order_id", description="Human-readable Order ID (e.g. ORD-XXXX)", required=True, type=str)
        ],
        responses={200: OrderTrackingSerializer, 404: dict}
    )
    def get(self, request):
        order_id = request.query_params.get("order_id")
        if not order_id:
            return Response({"detail": "order_id query parameter is required."}, status=status.HTTP_400_BAD_REQUEST)

        order = Order.objects.filter(order_id__iexact=order_id.strip()).select_related("courier").first()
        if not order:
            return Response({"detail": "Order not found."}, status=status.HTTP_404_NOT_FOUND)

        history = {h.status: h.changed_at for h in order.status_history.all()}
        status_timeline = [
            {"status": s, "reached_at": history.get(s)}
            for s in ORDER_STATUS_SEQUENCE
        ]

        # Create a dict but include the order instance for get_items to access
        tracking_data = {
            "order_id": order.order_id,
            "order_status": order.order_status,
            "courier_name": order.courier.name if order.courier else None,
            "tracking_number": order.tracking_number,
            "tracking_url": order.courier.tracking_url if order.courier else None,
            "status_timeline": status_timeline,
            "total_amount": str(order.total_amount),
            "items": order,  # Pass the order object for get_items method
        }

        serializer = OrderTrackingSerializer(tracking_data)
        return Response(serializer.data)


from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status

from drf_spectacular.utils import extend_schema

import html
import io
import os
from decimal import Decimal

from django.conf import settings

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm

from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
    Image
)

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# models import
from apps.orders.models import Order


@extend_schema(
    tags=["Orders"],
    summary="Download order invoice as PDF",
    responses={200: bytes}
)
class OrderInvoiceView(APIView):

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, order_id):

        try:

            order = Order.objects.select_related(
                "customer__user",
                "shipping_address",
                "applied_coupon",
                "applied_gift_card",
                "applied_gift_wrap"
            ).prefetch_related(
                "items__product"
            ).get(
                id=order_id,
                is_deleted=False
            )

        except Order.DoesNotExist:

            return Response(
                {"detail": "Order not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        if (
            not request.user.is_admin
            and
            order.customer.user != request.user
        ):

            return Response(
                {"detail": "Not authorized."},
                status=status.HTTP_403_FORBIDDEN
            )

        try:

            # =====================================================
            # REGISTER FONT
            # =====================================================

            font_path = os.path.join(
                settings.BASE_DIR,
                "templates",
                "static",
                "fonts",
                "DejaVuSans.ttf"
            )

            pdfmetrics.registerFont(
                TTFont(
                    "DejaVuSans",
                    font_path
                )
            )

            pdfmetrics.registerFont(
                TTFont(
                    "DejaVuSans-Bold",
                    font_path
                )
            )

            # =====================================================
            # PDF SETUP
            # =====================================================

            buffer = io.BytesIO()

            doc = SimpleDocTemplate(
                buffer,
                pagesize=A4,
                rightMargin=1 * cm,
                leftMargin=1 * cm,
                topMargin=1 * cm,
                bottomMargin=1 * cm
            )

            page_width = doc.width

            styles = getSampleStyleSheet()

            elements = []

            # =====================================================
            # STYLES
            # =====================================================

            heading_style = ParagraphStyle(
                'HeadingStyle',
                parent=styles['Normal'],
                fontSize=12,
                textColor=colors.HexColor("#0f2d46"),
                fontName='DejaVuSans-Bold',
                leading=16
            )

            normal_style = ParagraphStyle(
                'NormalStyle',
                parent=styles['Normal'],
                fontSize=10,
                textColor=colors.black,
                fontName='DejaVuSans',
                leading=15
            )

            bold_style = ParagraphStyle(
                'BoldStyle',
                parent=styles['Normal'],
                fontSize=10,
                textColor=colors.HexColor("#0f2d46"),
                fontName='DejaVuSans-Bold',
                leading=16
            )

            footer_style = ParagraphStyle(
                'FooterStyle',
                parent=styles['Normal'],
                fontSize=9,
                alignment=TA_CENTER,
                textColor=colors.HexColor("#555555"),
                fontName='DejaVuSans'
            )

            invoice_style = ParagraphStyle(
                'InvoiceStyle',
                parent=styles['Normal'],
                alignment=TA_CENTER,
                leading=18,
                textColor=colors.HexColor("#1a1a1a"),
                fontName='DejaVuSans'
            )

            # =====================================================
            # LOGO
            # =====================================================

            logo_path = os.path.join(
                settings.BASE_DIR,
                "templates",
                "static",
                "images",
                "logo.png"
            )

            logo = Image(
                logo_path,
                width=8 * cm,
                height=2 * cm
            )

            logo_table = Table(
                [[logo]],
                colWidths=[page_width]
            )

            logo_table.setStyle(TableStyle([
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ]))

            elements.append(logo_table)

            elements.append(Spacer(1, 0.2 * cm))

            # =====================================================
            # HEADER
            # =====================================================

            invoice_text = f"""
            <font size="11">
            <b>Invoice:</b> {order.order_id}
            &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
            |
            &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
            <b>Date:</b> {order.created_at.strftime('%d %b %Y')}
            </font>
            """

            elements.append(
                Paragraph(
                    invoice_text,
                    invoice_style
                )
            )

            elements.append(Spacer(1, 0.2 * cm))

            divider = Table(
                [[""]],
                colWidths=[page_width]
            )

            divider.setStyle(TableStyle([
                (
                    "LINEBELOW",
                    (0, 0),
                    (-1, -1),
                    1,
                    colors.HexColor("#0f2d46")
                )
            ]))

            elements.append(divider)

            elements.append(Spacer(1, 0.5 * cm))

            # =====================================================
            # BILL TO
            # =====================================================

            bill_to = []

            bill_to.append(
                Paragraph(
                    "<b>BILL TO</b>",
                    heading_style
                )
            )

            bill_to.append(
                Spacer(1, 0.12 * cm)
            )

            if order.shipping_address:
                addr = order.shipping_address
                bill_to.append(
                    Paragraph(
                        f"<b>{html.escape(addr.full_name)}</b>",
                        normal_style
                    )
                )
                bill_to.append(
                    Paragraph(
                        f"Phone: {html.escape(addr.phone)}",
                        normal_style
                    )
                )
                bill_to.append(
                    Paragraph(
                        f"Email: {html.escape(order.customer.user.email)}",
                        normal_style
                    )
                )

                addr_line2_str = f"{html.escape(addr.address_line2)}<br/>" if addr.address_line2 else ""
                address = f"""
                {html.escape(addr.address_line1)}<br/>
                {addr_line2_str}
                {html.escape(addr.city)}, {html.escape(addr.state)} {html.escape(addr.postal_code)}<br/>
                {html.escape(addr.country)}
                """
                bill_to.append(
                    Paragraph(
                        address,
                        normal_style
                    )
                )
            else:
                bill_to.append(
                    Paragraph(
                        f"<b>{html.escape(order.customer.user.full_name)}</b>",
                        normal_style
                    )
                )
                bill_to.append(
                    Paragraph(
                        f"Email: {html.escape(order.customer.user.email)}",
                        normal_style
                    )
                )

            # Add BILL TO section directly to document flow
            elements.extend(bill_to)

            elements.append(Spacer(1, 0.5 * cm))

            # =====================================================
            # ORDER DETAILS TITLE
            # =====================================================

            elements.append(
                Paragraph(
                    "<b>ORDER DETAILS</b>",
                    heading_style
                )
            )

            elements.append(Spacer(1, 0.15 * cm))

            # =====================================================
            # PRODUCT TABLE
            # =====================================================

            table_data = [[
                "Sl. No.",
                "PRODUCT",
                "COLOR",
                "SIZE",
                "QTY",
                "POINTS",
                "PRICE",
                "TOTAL"
            ]]

            for i, item in enumerate(
                order.items.select_related("product").all(),
                1
            ):

                product_name = item.product.name_en or "N/A"

                points = getattr(
                    item.product,
                    "required_points",
                    0
                )

                table_data.append([
                    str(i),
                    Paragraph(html.escape(product_name), normal_style),
                    item.selected_color or "-",
                    item.selected_size or "-",
                    str(item.quantity),
                    str(points * item.quantity),
                    f"₹{item.price:,.2f}",
                    f"₹{(item.price * item.quantity):,.2f}",
                ])

            product_table = Table(
                table_data,
                colWidths=[
                    1.6 * cm,
                    5 * cm,
                    2 * cm,
                    1.8 * cm,
                    1.5 * cm,
                    2 * cm,
                    2.4 * cm,
                    2.5 * cm
                ]
            )

            product_table.setStyle(TableStyle([

                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor("#062b55")
                ),

                (
                    "TEXTCOLOR",
                    (0, 0),
                    (-1, 0),
                    colors.white
                ),

                (
                    "FONTNAME",
                    (0, 0),
                    (-1, 0),
                    "DejaVuSans-Bold"
                ),

                (
                    "FONTSIZE",
                    (0, 0),
                    (-1, 0),
                    10
                ),

                (
                    "ALIGN",
                    (0, 0),
                    (-1, 0),
                    "CENTER"
                ),

                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE"
                ),

                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.HexColor("#d9d9d9")
                ),

                (
                    "ROWBACKGROUNDS",
                    (0, 1),
                    (-1, -1),
                    [
                        colors.white,
                        colors.HexColor("#f8f8f8")
                    ]
                ),

                (
                    "FONTNAME",
                    (0, 1),
                    (-1, -1),
                    "DejaVuSans"
                ),

                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    10
                ),

                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    10
                ),

                (
                    "ALIGN",
                    (6, 1),
                    (7, -1),
                    "RIGHT"
                ),

            ]))

            elements.append(product_table)

            elements.append(Spacer(1, 0.5 * cm))

            # =====================================================
            # TOTALS
            # =====================================================

            subtotal = sum(
                item.price * item.quantity
                for item in order.items.all()
            )

            totals_data = [
                ["Subtotal", f"₹{subtotal:,.2f}"]
            ]

            if order.discount_amount:

                totals_data.append([
                    "Coupon Discount",
                    f"-₹{order.discount_amount:,.2f}"
                ])

            # Display Gift Card discount if applied
            if getattr(order, "gift_card_discount", 0) > 0:
                totals_data.append([
                    "Gift Card Discount",
                    f"-₹{order.gift_card_discount:,.2f}"
                ])

            # Display Gift Wrap and/or Gift Card charges
            if getattr(order, "gift_wrap_charges", 0) > 0:
                label = "Gift Wrap & Card"
                if order.applied_gift_wrap and order.applied_gift_card:
                    label = "Gift Wrap & Card Combo (10% Off)"
                elif order.applied_gift_wrap:
                    label = f"Gift Wrap ({order.applied_gift_wrap.wrap_name})"
                elif order.applied_gift_card:
                    label = f"Gift Card ({order.applied_gift_card.card_name})"

                totals_data.append([
                    label,
                    f"₹{order.gift_wrap_charges:,.2f}"
                ])

            if order.gst:

                totals_data.append([
                    "GST (18%)",
                    f"₹{order.gst:,.2f}"
                ])

            totals_data.append([
                "TOTAL AMOUNT",
                f"₹{order.total_amount:,.2f}"
            ])

            totals_table = Table(
                totals_data,
                colWidths=[5 * cm, 3 * cm]
            )

            totals_table.setStyle(TableStyle([

                (
                    "FONTNAME",
                    (0, 0),
                    (-1, -2),
                    "DejaVuSans"
                ),

                (
                    "FONTNAME",
                    (0, -1),
                    (-1, -1),
                    "DejaVuSans-Bold"
                ),

                (
                    "BACKGROUND",
                    (0, -1),
                    (-1, -1),
                    colors.HexColor("#e8f0fb")
                ),

                (
                    "TEXTCOLOR",
                    (0, -1),
                    (-1, -1),
                    colors.HexColor("#062b55")
                ),

                (
                    "ALIGN",
                    (1, 0),
                    (1, -1),
                    "RIGHT"
                ),

                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    8
                ),

                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    8
                ),

                (
                    "LINEBELOW",
                    (0, 0),
                    (-1, -2),
                    0.3,
                    colors.HexColor("#d9d9d9")
                ),

            ]))

            totals_wrapper = Table(
                [["", totals_table]],
                colWidths=[
                    page_width - 8 * cm,
                    8 * cm
                ]
            )

            totals_wrapper.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ALIGN", (1, 0), (1, 0), "RIGHT"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ]))

            elements.append(totals_wrapper)

            elements.append(Spacer(1, 0.5 * cm))

            # =====================================================
            # FOOTER
            # =====================================================

            footer_line = Table(
                [[""]],
                colWidths=[page_width]
            )

            footer_line.setStyle(TableStyle([
                (
                    "LINEBELOW",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.HexColor("#cfcfcf")
                )
            ]))

            elements.append(footer_line)

            elements.append(Spacer(1, 0.25 * cm))

            footer_text = """
            Thank you for shopping with IQRAAMARK!
            Your satisfaction is our priority.
            """

            elements.append(
                Paragraph(
                    footer_text,
                    footer_style
                )
            )

            # =====================================================
            # BUILD PDF
            # =====================================================

            doc.build(elements)

            pdf = buffer.getvalue()

            buffer.close()

            response = HttpResponse(
                pdf,
                content_type='application/pdf'
            )

            response[
                "Content-Disposition"
            ] = f'attachment; filename="invoice-{order.order_id}.pdf"'

            return response

        except Exception as e:

            return Response(
                {
                    "detail": f"Error generating PDF: {str(e)}"
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )