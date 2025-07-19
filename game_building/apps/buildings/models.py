# backend/apps/buildings/models.py
from django.db import models
from django_mongodb_backend.fields import ObjectIdAutoField


class Building(models.Model):
    id = ObjectIdAutoField(primary_key=True)
    building_id = models.PositiveIntegerField(unique=True)
    name = models.CharField(max_length=100, blank=False)
    build_time = models.PositiveIntegerField(
        blank=False, help_text="Time to complete building in seconds"
    )
    required_wood = models.PositiveIntegerField(blank=False)
    required_stone = models.PositiveIntegerField(blank=False)
    dependencies = models.JSONField(
        blank=True,
        default=list,
        help_text="List of Building IDs that this building depends on (by building_id)",
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Building"
        verbose_name_plural = "Buildings"
        ordering = ["name"]
        indexes = [
            models.Index(fields=["building_id"]),
            models.Index(fields=["name"]),
        ]
