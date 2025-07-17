from asgiref.sync import sync_to_async
from django.utils import timezone
from game_building.apps.players.models import Player, PlayerBuilding
from game_building.apps.players.serializers import (
    PlayerCreateSerializer,
    PlayerSerializer,
    PlayerLoginSerializer,
)
from game_building.apps.buildings.models import Building
from datetime import timedelta
from game_building.apps.players.tasks import complete_building_task
from game_building.apps.players.serializers import PlayerResourcesUpdateSerializer
from django.contrib.auth.hashers import check_password


@sync_to_async
def register_player(data):
    serializer = PlayerCreateSerializer(data=data)
    if serializer.is_valid():
        player = serializer.save()
        return {"type": "register_success", "player": PlayerSerializer(player).data}
    else:
        return {"type": "register_failed", "error": serializer.errors}


@sync_to_async
def login_player(data):
    serializer = PlayerLoginSerializer(data=data)
    if not serializer.is_valid():
        return None, "Invalid login data"
    try:
        player = Player.objects.get(username=data["username"])
        if not check_password(data["password"], player.password):
            return None, "Invalid credentials"
        return player, None
    except Player.DoesNotExist:
        return None, "Invalid credentials"


@sync_to_async
def can_start_building(player, building_id):
    try:
        building = Building.objects.get(building_id=building_id)
    except Building.DoesNotExist:
        return False, "Building not found", None
    # Check if already started/completed
    player = Player.objects.get(id=player.id)
    for b in player.buildings:
        if str(b.building_id) == str(building_id):
            if b.status == "in_progress":
                return False, "Building already in progress", None
            elif b.status == "completed":
                return False, "Building already completed", None
    # Check resources
    if not player.has_sufficient_resources(
        building.required_wood, building.required_stone
    ):
        return False, "Not enough resources", None
    # Check dependencies
    for dep_id in building.dependencies:
        found = any(
            str(b.building_id) == str(dep_id) and b.status == "completed"
            for b in player.buildings
        )
        if not found:
            return False, f"Dependency {dep_id} not completed", None
    return True, "", building


@sync_to_async
def start_building_for_player(player, building):
    now = timezone.now()
    completion_time = now + timedelta(seconds=building.build_time)
    pb = PlayerBuilding(
        building_id=str(building.building_id),
        status="in_progress",
        started_at=now,
        finish_eta=completion_time,
        celery_task_id=None,
    )
    player.buildings.append(pb)
    player.consume_resources(building.required_wood, building.required_stone)
    player.save()
    # Schedule Celery task
    result = complete_building_task.apply_async(
        args=[str(player.id), str(building.building_id)],
        countdown=building.build_time,
    )
    pb.celery_task_id = result.id
    player.save()
    return completion_time


@sync_to_async
def update_player_resources(player, data):
    serializer = PlayerResourcesUpdateSerializer(data=data)
    if not serializer.is_valid():
        return {"type": "update_failed", "error": serializer.errors}
    update_data = serializer.validated_data
    if "wood" in update_data:
        player.resources.wood = update_data["wood"]
    if "stone" in update_data:
        player.resources.stone = update_data["stone"]
    player.save()
    return {"type": "update_success", "player": PlayerSerializer(player).data}


@sync_to_async
def get_player_info(player):
    return {"type": "player_info", "player": PlayerSerializer(player).data}
