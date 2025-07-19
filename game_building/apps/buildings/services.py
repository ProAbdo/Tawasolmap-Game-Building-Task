from asgiref.sync import sync_to_async
from game_building.apps.buildings.models import Building
from game_building.apps.buildings.serializers import (
    BuildingCreateSerializer,
    BuildingSerializer,
)
from datetime import timedelta
from django.utils import timezone
from game_building.apps.players.tasks import complete_building_task
from game_building.config.celery import app as celery_app

revoke = celery_app.control.revoke


@sync_to_async
def create_building(data):
    last = Building.objects.order_by("-building_id").first()
    next_id = (last.building_id + 1) if last else 1
    data["building_id"] = next_id
    serializer = BuildingCreateSerializer(data=data)
    if not serializer.is_valid():
        return None, serializer.errors
    building = serializer.save(building_id=next_id)
    return building, None


@sync_to_async
def get_building(building_id):
    try:
        building = Building.objects.get(building_id=building_id)
        return building
    except Building.DoesNotExist:
        return None


@sync_to_async
def accelerate_building(player, building_id, percent):
    pb = next(
        (b for b in player.buildings if str(b.building_id) == str(building_id)), None
    )
    if not pb or pb.status != "in_progress":
        return {"type": "error", "error": "Building not in progress"}
    now = timezone.now()
    finish_eta = pb.finish_eta
    time_left = (finish_eta - now).total_seconds()
    if time_left <= 0:
        return {"type": "error", "error": "Building already finished"}
    reduction = time_left * (percent / 100)
    new_time_left = max(0, time_left - reduction)
    new_finish_eta = now + timedelta(seconds=new_time_left)
    # Cancel old celery task
    if pb.celery_task_id:
        revoke(pb.celery_task_id, terminate=True)
    # If new_time_left == 0, complete immediately
    if new_time_left == 0:
        complete_building_task.delay(str(player.id), str(building_id))
        pb.finish_eta = now
        pb.status = "completed"
        pb.celery_task_id = None
        player.save()
        return {
            "type": "building_accelerated",
            "building_id": building_id,
            "status": "completed",
        }
    # Schedule new celery task
    result = complete_building_task.apply_async(
        args=[str(player.id), str(building_id)],
        countdown=new_time_left,
    )
    pb.finish_eta = new_finish_eta
    pb.celery_task_id = result.id
    player.save()
    return {
        "type": "building_accelerated",
        "building_id": building_id,
        "new_finish_eta": new_finish_eta.isoformat(),
    }


@sync_to_async
def get_allowed_buildings(player):
    try:
        all_buildings = Building.objects.all()
        allowed_buildings = []
        # Get player's completed buildings
        completed_building_ids = [
            str(b.building_id) for b in player.buildings if b.status == "completed"
        ]

        for building in all_buildings:
            # Check if player already has this building (in progress or completed)
            player_has_building = any(
                str(b.building_id) == str(building.building_id)
                for b in player.buildings
            )

            if player_has_building:
                continue
            # Check if player has all dependencies
            dependencies_met = True
            for dep_id in building.dependencies:
                if str(dep_id) not in completed_building_ids:
                    dependencies_met = False
                    break
            if dependencies_met:
                # Check if player has enough resources
                has_resources = player.has_sufficient_resources(
                    building.required_wood, building.required_stone
                )
                building_data = BuildingSerializer(building).data
                building_data["can_afford"] = has_resources
                building_data["missing_resources"] = (
                    {
                        "wood": max(0, building.required_wood - player.resources.wood),
                        "stone": max(
                            0, building.required_stone - player.resources.stone
                        ),
                    }
                    if not has_resources
                    else None
                )
                allowed_buildings.append(building_data)

        return {
            "type": "allowed_buildings",
            "buildings": allowed_buildings,
            "total_count": len(allowed_buildings),
        }

    except Exception as e:
        return {"type": "error", "error": f"Failed to get allowed buildings: {str(e)}"}
