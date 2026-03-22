from django.urls import path
from . import views

urlpatterns = [
    path("telemetry/", views.telemetry_ingest, name="telemetry-ingest"),
    path("bins/status/", views.bins_status, name="bins-status"),
    path("bins/<str:bin_id>/history/", views.bin_history, name="bin-history"),
]
