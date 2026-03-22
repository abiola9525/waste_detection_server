import random
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from bins.models import Bin, Reading

class Command(BaseCommand):
    help = 'Seeds the database with 5 demo Bins and 24 hours of ultrasonic reading history'

    def handle(self, *args, **kwargs):
        # Clear existing
        Reading.objects.all().delete()
        Bin.objects.all().delete()
        
        bins_data = [
            {"bin_id": "BIN-001", "location_name": "Downtown Plaza", "total_depth_cm": 120.0, "lat": 40.7128, "lng": -74.0060},
            {"bin_id": "BIN-002", "location_name": "Central Park Entrance", "total_depth_cm": 150.0, "lat": 40.7812, "lng": -73.9665},
            {"bin_id": "BIN-003", "location_name": "Main Station", "total_depth_cm": 100.0, "lat": 40.7505, "lng": -73.9934},
            {"bin_id": "BIN-004", "location_name": "University Campus", "total_depth_cm": 120.0, "lat": 40.8075, "lng": -73.9626},
            {"bin_id": "BIN-005", "location_name": "Shopping Mall", "total_depth_cm": 200.0, "lat": 40.7484, "lng": -73.9857},
        ]
        
        now = timezone.now()
        
        for b_data in bins_data:
            bin_obj = Bin.objects.create(
                bin_id=b_data["bin_id"],
                location_name=b_data["location_name"],
                total_depth_cm=b_data["total_depth_cm"],
                latitude=b_data["lat"],
                longitude=b_data["lng"]
            )
            
            # Generate 24 hours of readings (every 30 mins -> 49 readings)
            current_distance = b_data["total_depth_cm"] # Starts empty (distance = depth)
            
            # Differentiate fill curves for realistic demo
            if b_data["bin_id"] == "BIN-002":
                fill_rate = 2.0  # cm per 30 min (Fast)
            elif b_data["bin_id"] == "BIN-003":
                fill_rate = 3.5  # Very Fast (likely to be full)
            else:
                fill_rate = 0.5  # Slow
                
            readings = []
            for i in range(48, -1, -1):
                timestamp = now - timedelta(minutes=30 * i)
                
                # Reduce distance (filling up)
                current_distance -= fill_rate * (1 + random.uniform(-0.2, 0.2))
                if current_distance < 15:
                    current_distance = 15  # almost full
                    
                    if random.random() < 0.15: # 15% chance it was emptied
                        current_distance = b_data["total_depth_cm"]
                        
                # Ensure within bounds
                current_distance = max(0, min(current_distance, b_data["total_depth_cm"]))
                
                fill_percentage = ((b_data["total_depth_cm"] - current_distance) / b_data["total_depth_cm"]) * 100
                
                reading = Reading(
                    bin=bin_obj,
                    distance_cm=round(current_distance, 1),
                    fill_percentage=round(fill_percentage, 2)
                )
                reading.timestamp = timestamp
                readings.append(reading)
                
            # We use bulk_create and then update the timestamp explicitly because auto_now_add can override it
            Reading.objects.bulk_create(readings)
            
            # After bulk create, we need to explicitly set the timestamps
            created_readings = list(Reading.objects.filter(bin=bin_obj).order_by('id'))
            for r, orig_r in zip(created_readings, readings):
                Reading.objects.filter(pk=r.pk).update(timestamp=orig_r.timestamp)

        self.stdout.write(self.style.SUCCESS('Successfully seeded 5 demo bins with 24h history.'))
