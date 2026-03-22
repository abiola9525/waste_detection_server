from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import Bin, Reading
from .serializers import ReadingSerializer, BinStatusSerializer

# ── Request body schema for Swagger ───────────────────────────────────────────
telemetry_request_body = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    required=["bin_id", "distance"],
    properties={
        "bin_id": openapi.Schema(
            type=openapi.TYPE_STRING,
            description="Unique identifier of the bin (e.g. BIN-001)",
            example="BIN-001",
        ),
        "distance": openapi.Schema(
            type=openapi.TYPE_NUMBER,
            description="Raw ultrasonic sensor distance in cm",
            example=35.5,
        ),
    },
)


# ── POST /api/telemetry/ ───────────────────────────────────────────────────────
@swagger_auto_schema(
    method="post",
    request_body=telemetry_request_body,
    operation_summary="Ingest sensor telemetry from ESP32",
    operation_description=(
        "Receives a bin_id and a raw distance reading from the ultrasonic sensor. "
        "Computes fill_percentage and stores the reading. "
        "Returns 201 on success, 400 for bad input, 404 if bin not found."
    ),
    responses={
        201: openapi.Response(
            description="Reading saved successfully",
            examples={
                "application/json": {
                    "status": "ok",
                    "bin_id": "BIN-001",
                    "fill_percentage": 65.4,
                    "needs_pickup": False,
                }
            },
        ),
        400: "Bad Request — missing or invalid fields",
        404: "Not Found — bin_id does not exist",
    },
    tags=["Telemetry"],
)
@api_view(["POST"])
def telemetry_ingest(request):
    """
    ESP32-compatible endpoint.  POST body: { "bin_id": "BIN-001", "distance": 35.5 }
    """
    bin_id = request.data.get("bin_id")
    distance = request.data.get("distance")

    if bin_id is None or distance is None:
        return Response(
            {"error": "Both 'bin_id' and 'distance' are required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        distance = float(distance)
    except (TypeError, ValueError):
        return Response(
            {"error": "'distance' must be a numeric value."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        bin_obj = Bin.objects.get(bin_id=bin_id, is_active=True)
    except Bin.DoesNotExist:
        return Response(
            {"error": f"Bin '{bin_id}' not found or is inactive."},
            status=status.HTTP_404_NOT_FOUND,
        )

    if distance < 0 or distance > bin_obj.total_depth_cm:
        return Response(
            {
                "error": f"'distance' must be between 0 and {bin_obj.total_depth_cm} cm."
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    fill_percentage = ((bin_obj.total_depth_cm - distance) / bin_obj.total_depth_cm) * 100
    fill_percentage = max(0.0, min(100.0, fill_percentage))

    reading = Reading.objects.create(
        bin=bin_obj,
        distance_cm=distance,
        fill_percentage=round(fill_percentage, 2),
    )

    return Response(
        {
            "status": "ok",
            "bin_id": bin_obj.bin_id,
            "reading_id": reading.id,
            "fill_percentage": reading.fill_percentage,
            "needs_pickup": reading.fill_percentage > 80,
        },
        status=status.HTTP_201_CREATED,
    )


# ── GET /api/bins/status/ ─────────────────────────────────────────────────────
@swagger_auto_schema(
    method="get",
    operation_summary="Get status of all active bins",
    operation_description=(
        "Returns all active bins with their latest reading, fill percentage, "
        "needs_pickup flag, fill rate, and estimated time until full."
    ),
    responses={200: BinStatusSerializer(many=True)},
    tags=["Bins"],
)
@api_view(["GET"])
def bins_status(request):
    bins = Bin.objects.filter(is_active=True).prefetch_related("readings")
    serializer = BinStatusSerializer(bins, many=True)
    return Response(serializer.data)


# ── GET /api/bins/<bin_id>/history/ ──────────────────────────────────────────
@swagger_auto_schema(
    method="get",
    operation_summary="Get reading history for a specific bin",
    operation_description="Returns all historical readings for the given bin_id, ordered by most recent first.",
    manual_parameters=[
        openapi.Parameter(
            "bin_id",
            openapi.IN_PATH,
            description="Unique bin identifier (e.g. BIN-001)",
            type=openapi.TYPE_STRING,
            required=True,
        )
    ],
    responses={200: ReadingSerializer(many=True), 404: "Bin not found"},
    tags=["Bins"],
)
@api_view(["GET"])
def bin_history(request, bin_id):
    try:
        bin_obj = Bin.objects.get(bin_id=bin_id)
    except Bin.DoesNotExist:
        return Response(
            {"error": f"Bin '{bin_id}' not found."},
            status=status.HTTP_404_NOT_FOUND,
        )

    readings = bin_obj.readings.order_by("-timestamp")
    serializer = ReadingSerializer(readings, many=True)
    return Response(serializer.data)
