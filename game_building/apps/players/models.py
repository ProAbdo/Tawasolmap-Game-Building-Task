from django.db import models
from django_mongodb_backend.fields import (
    ObjectIdAutoField,
    EmbeddedModelField,
    EmbeddedModelArrayField,
)
from django_mongodb_backend.models import EmbeddedModel


class Resources(EmbeddedModel):
    wood = models.PositiveIntegerField(default=1000)
    stone = models.PositiveIntegerField(default=1000)


class PlayerBuilding(EmbeddedModel):
    building_id = models.CharField(max_length=24, help_text="Reference to Building.id")
    status = models.CharField(
        max_length=20,
        choices=[
            ("in_progress", "In Progress"),
            ("completed", "Completed"),
            ("failed", "Failed"),
        ],
        default="in_progress",
        help_text="Current build status",
    )
    started_at = models.DateTimeField(auto_now_add=True)
    finish_eta = models.DateTimeField(help_text="Expected completion datetime")
    celery_task_id = models.CharField(
        max_length=128,
        blank=True,
        null=True,
        help_text="Celery task id for scheduled completion",
    )

    def __str__(self):
        return f"{self.building_id} ({self.status})"


class Player(models.Model):
    id = ObjectIdAutoField(primary_key=True)
    username = models.CharField(max_length=100, unique=True, blank=False)
    email = models.EmailField(unique=True, blank=False)
    password = models.CharField(max_length=128, blank=False)

    resources = EmbeddedModelField(
        Resources, default=Resources, help_text="Player's available resources"
    )

    buildings = EmbeddedModelArrayField(
        PlayerBuilding,
        blank=True,
        default=list,
        help_text="List of buildings the player has started or completed",
    )

    def __str__(self):
        return self.username

    class Meta:
        ordering = ["username"]
        verbose_name = "Player"
        verbose_name_plural = "Players"

    def has_sufficient_resources(self, required_wood, required_stone):
        """Check if player has enough resources for building."""
        return (
            self.resources.wood >= required_wood
            and self.resources.stone >= required_stone
        )

    def consume_resources(self, wood, stone):
        """Consume resources for building if possible. Returns True if successful."""
        if self.has_sufficient_resources(wood, stone):
            self.resources.wood -= wood
            self.resources.stone -= stone
            self.save()
            return True
        return False

    def add_resources(self, wood=0, stone=0):
        """Add resources to the player."""
        self.resources.wood += wood
        self.resources.stone += stone
        self.save()

    def get_building(self, building_id):
        """Return PlayerBuilding by building_id, or None if not found."""
        for b in self.buildings:
            if str(b.building_id) == str(building_id):
                return b
        return None

    def has_completed_building(self, building_id):
        """Check if player has completed a specific building."""
        b = self.get_building(building_id)
        return b is not None and b.status == "completed"

    def add_building_progress(self, building_id, finish_eta):
        """Add a new PlayerBuilding entry for a started building."""
        pb = PlayerBuilding(
            building_id=building_id, status="in_progress", finish_eta=finish_eta
        )
        self.buildings.append(pb)
        self.save()
        return pb
