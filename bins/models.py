from django.db import models
from django.utils import timezone
from datetime import timedelta

class Bin(models.Model):
    bin_id = models.CharField(max_length=50, unique=True)
    location_name = models.CharField(max_length=200)
    total_depth_cm = models.FloatField(help_text="Physical depth of the bin in cm")
    threshold_cm = models.FloatField(
        default=20.0,
        help_text="Distance threshold (cm) below which bin is considered near-full",
    )
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["bin_id"]

    def __str__(self):
        return f"{self.bin_id} — {self.location_name}"

    def get_fill_rate(self):
        """
        Returns the average fill rate in cm/hour over the last 24 hours.
        Positive value = bin filling up; None if insufficient data.
        """
        since = timezone.now() - timedelta(hours=24)
        readings = list(
            self.readings.filter(timestamp__gte=since)
            .order_by("timestamp")
            .values("distance_cm", "timestamp")
        )

        if len(readings) < 2:
            return None

        first = readings[0]
        last = readings[-1]
        
        hours = (last["timestamp"] - first["timestamp"]).total_seconds() / 3600.0
        if hours == 0:
            return None

        first_fill = self.total_depth_cm - first["distance_cm"]
        last_fill = self.total_depth_cm - last["distance_cm"]
        
        slope = (last_fill - first_fill) / hours
        return round(slope, 4)

    def estimated_time_until_full(self):
        """
        Returns the estimated hours until the bin is full based on fill rate.
        Returns None if the bin is static or data is insufficient.
        """
        latest = self.readings.order_by("-timestamp").first()
        if not latest:
            return None

        fill_rate = self.get_fill_rate()
        if not fill_rate or fill_rate <= 0:
            return None

        remaining_cm = self.total_depth_cm - (
            self.total_depth_cm - latest.distance_cm
        )  # = latest.distance_cm
        if remaining_cm <= 0:
            return 0.0

        hours = remaining_cm / fill_rate
        return round(hours, 2)


class Reading(models.Model):
    bin = models.ForeignKey(Bin, on_delete=models.CASCADE, related_name="readings")
    distance_cm = models.FloatField(help_text="Raw ultrasonic sensor distance in cm")
    fill_percentage = models.FloatField(help_text="Computed fill level (0-100%)")
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.bin.bin_id} @ {self.timestamp:%Y-%m-%d %H:%M} → {self.fill_percentage:.1f}%"
