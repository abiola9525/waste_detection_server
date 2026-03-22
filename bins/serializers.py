from rest_framework import serializers
from .models import Bin, Reading


class ReadingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reading
        fields = ["id", "distance_cm", "fill_percentage", "timestamp"]


class BinSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bin
        fields = [
            "bin_id",
            "location_name",
            "total_depth_cm",
            "threshold_cm",
            "latitude",
            "longitude",
            "is_active",
        ]


class BinStatusSerializer(serializers.ModelSerializer):
    latest_reading = serializers.SerializerMethodField()
    fill_percentage = serializers.SerializerMethodField()
    needs_pickup = serializers.SerializerMethodField()
    fill_rate_cm_per_hour = serializers.SerializerMethodField()
    estimated_hours_until_full = serializers.SerializerMethodField()

    class Meta:
        model = Bin
        fields = [
            "bin_id",
            "location_name",
            "total_depth_cm",
            "threshold_cm",
            "latitude",
            "longitude",
            "is_active",
            "latest_reading",
            "fill_percentage",
            "needs_pickup",
            "fill_rate_cm_per_hour",
            "estimated_hours_until_full",
        ]

    def get_latest_reading(self, obj):
        reading = obj.readings.order_by("-timestamp").first()
        if reading:
            return ReadingSerializer(reading).data
        return None

    def get_fill_percentage(self, obj):
        reading = obj.readings.order_by("-timestamp").first()
        if reading:
            return round(reading.fill_percentage, 2)
        return 0.0

    def get_needs_pickup(self, obj):
        reading = obj.readings.order_by("-timestamp").first()
        if reading:
            return reading.fill_percentage > 80
        return False

    def get_fill_rate_cm_per_hour(self, obj):
        return obj.get_fill_rate()

    def get_estimated_hours_until_full(self, obj):
        return obj.estimated_time_until_full()
