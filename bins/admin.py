from django.contrib import admin
from .models import Bin, Reading


@admin.register(Bin)
class BinAdmin(admin.ModelAdmin):
    list_display = ["bin_id", "location_name", "is_active", "total_depth_cm", "threshold_cm"]
    list_filter = ["is_active"]
    search_fields = ["bin_id", "location_name"]
    ordering = ["bin_id"]


@admin.register(Reading)
class ReadingAdmin(admin.ModelAdmin):
    list_display = ["bin", "distance_cm", "fill_percentage", "timestamp"]
    list_filter = ["bin"]
    ordering = ["-timestamp"]
    readonly_fields = ["timestamp"]
