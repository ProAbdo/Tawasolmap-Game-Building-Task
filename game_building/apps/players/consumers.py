import json
from channels.generic.websocket import AsyncWebsocketConsumer
from django.utils import timezone
from datetime import timedelta
from asgiref.sync import sync_to_async
from game_building.config.celery import app as celery_app
from apps.players.tasks import complete_building_task
from apps.players.serializers import (
    PlayerSerializer,
    PlayerCreateSerializer,
    PlayerLoginSerializer,
    PlayerBuildingCreateSerializer,
)
from apps.buildings.serializers import BuildingSerializer, BuildingCreateSerializer

revoke = celery_app.control.revoke


class GameConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        self.player = None

    async def disconnect(self, close_code):
        if self.player:
            await self.channel_layer.group_discard(
                f"player_{self.player.id}", self.channel_name
            )
        self.player = None

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            msg_type = data.get("type")

            if msg_type == "register":
                await self.handle_register(data)
            elif msg_type == "login":
                await self.handle_login(data)
            elif msg_type == "start_building":
                await self.handle_start_building(data)
            elif msg_type == "create_building":
                await self.handle_create_building(data)
            elif msg_type == "accelerate_building":
                await self.handle_accelerate_building(data)
            else:
                raise ValueError(f"Unknown message type: {msg_type}")
        except json.JSONDecodeError:
            await self.send(json.dumps({"type": "error", "error": "Invalid JSON"}))
        except ValueError as e:
            await self.send(json.dumps({"type": "error", "error": str(e)}))
        except Exception as e:
            await self.send(json.dumps({"type": "error", "error": "An error occurred"}))
            raise e

    @sync_to_async
    def create_player(self, username, password, email):
        from apps.players.models import Player

        # Validate data using serializer
        serializer = PlayerCreateSerializer(
            data={"username": username, "email": email, "password": password}
        )

        if not serializer.is_valid():
            raise ValueError("Invalid player data", serializer.errors)

        if Player.objects.filter(username=username).exists():
            return None, "Username already exists"
        if Player.objects.filter(email=email).exists():
            return None, "Email already exists"

        player = serializer.save()
        return player, None

    async def handle_register(self, data):
        username = data.get("username")
        password = data.get("password")
        email = data.get("email")
        player, error = await self.create_player(username, password, email)
        if player:
            self.player = player
            await self.channel_layer.group_add(
                f"player_{self.player.id}", self.channel_name
            )
            # Use serializer to format response
            serializer = PlayerSerializer(player)
            await self.send(
                json.dumps({"type": "register_success", "player": serializer.data})
            )
        else:
            await self.send(
                json.dumps(
                    {
                        "type": "register_failed",
                        "error": (
                            error if isinstance(error, str) else "Validation failed"
                        ),
                    }
                )
            )

    @sync_to_async
    def get_player(self, username, password):
        from apps.players.models import Player

        # Validate login data
        serializer = PlayerLoginSerializer(
            data={"username": username, "password": password}
        )
        if not serializer.is_valid():
            raise ValueError("Invalid login data", serializer.errors)

        try:
            player = Player.objects.get(username=username, password=password)
            return player
        except Player.DoesNotExist:
            return None

    async def handle_login(self, data):
        username = data.get("username")
        password = data.get("password")
        player = await self.get_player(username, password)
        if player:
            self.player = player
            await self.channel_layer.group_add(
                f"player_{self.player.id}", self.channel_name
            )
            # Use serializer to format response
            serializer = PlayerSerializer(player)
            await self.send(
                json.dumps({"type": "login_success", "player": serializer.data})
            )
        else:
            await self.send(
                json.dumps({"type": "login_failed", "error": "Invalid credentials"})
            )

    @sync_to_async
    def can_start_building(self, player, building_id):
        from apps.buildings.models import Building
        from apps.players.models import Player

        playerr = Player.objects.get(id=player.id)
        for b in playerr.buildings:
            print(f"Checking building {b} for ID {building_id}")
            if str(b.building_id) == str(building_id):
                if b.status == "in_progress":
                    raise ValueError("Building already in progress")
                elif b.status == "completed":
                    raise ValueError("Building already completed")
        try:
            building = Building.objects.get(building_id=building_id)
        except Building.DoesNotExist:
            return False, "Building not found", None

        if not player.has_sufficient_resources(
            building.required_wood, building.required_stone
        ):
            return False, "Not enough resources", None
        try:
            for dep_id in building.dependencies:
                found = any(
                    str(b.building_id) == str(dep_id) and b.status == "completed"
                    for b in player.buildings
                )
                if not found:
                    return False, f"Dependency {dep_id} not completed", None

        except Exception as e:
            raise ValueError(f"Error checking dependencies: {str(e)}")
        return True, "", building

    @sync_to_async
    def building_for_player_validation(self, building):
        from apps.players.models import PlayerBuilding

        now = timezone.now()
        completion_time = now + timedelta(seconds=building.build_time)
        building_progress = {
            "building_id": str(building.building_id),
            "status": "in_progress",
            "started_at": now,
            "finish_eta": completion_time,
            "celery_task_id": None,
        }
        serializer = PlayerBuildingCreateSerializer(data=building_progress)
        if not serializer.is_valid():
            raise ValueError("Invalid building progress data", serializer.errors)

        player_building = PlayerBuilding(**serializer.validated_data)
        return player_building

    async def handle_start_building(self, data):
        if not self.player:
            await self.send(json.dumps({"type": "error", "error": "Not authenticated"}))
            return
        building_id = data.get("building_id")

        can_start, error, building = await self.can_start_building(
            self.player, building_id
        )
        if not can_start:
            raise ValueError(error)
        player_building = await self.building_for_player_validation(building)

        # Schedule Celery task
        task = complete_building_task.apply_async(
            args=[str(self.player.id), str(building_id)],
            countdown=building.build_time,
        )
        print("player_building\n\n\n\n", player_building)
        player_building.celery_task_id = task.id
        self.player.buildings.append(player_building)
        await sync_to_async(self.player.save)()
        await self.send(
            json.dumps(
                {
                    "type": "building_started",
                    "building_id": building_id,
                    "completion_time": player_building.finish_eta.isoformat(),
                }
            )
        )

    @sync_to_async
    def create_building(
        self, name, build_time, required_wood, required_stone, dependencies
    ):
        from apps.buildings.models import Building

        # Validate building data using serializer
        next_building_id = (
            Building.objects.order_by("-building_id").first().building_id + 1
            if Building.objects.exists()
            else 1
        )
        serializer = BuildingCreateSerializer(
            data={
                "name": name,
                "building_id": next_building_id,
                "build_time": build_time,
                "required_wood": required_wood,
                "required_stone": required_stone,
                "dependencies": dependencies or [],
            }
        )

        if not serializer.is_valid():
            raise ValueError("Invalid building data", serializer.errors)

        building = serializer.save()
        return building, None

    async def handle_create_building(self, data):
        name = data.get("name")
        build_time = data.get("build_time")
        required_wood = data.get("required_wood")
        required_stone = data.get("required_stone")
        dependencies = data.get("dependencies", [])
        building, error = await self.create_building(
            name, build_time, required_wood, required_stone, dependencies
        )

        if building:
            # Use serializer to format response
            serializer = BuildingSerializer(building)
            await self.send(
                json.dumps(
                    {"type": "create_building_success", "building": serializer.data}
                )
            )
        else:
            await self.send(
                json.dumps(
                    {
                        "type": "create_building_failed",
                        "error": (
                            error if isinstance(error, str) else "Validation failed"
                        ),
                    }
                )
            )

    async def handle_accelerate_building(self, data):
        if not self.player:
            await self.send(json.dumps({"type": "error", "error": "Not authenticated"}))
            return
        building_id = data.get("building_id")
        percent = data.get("percent", 100)  # 100% = finish now
        # Find the building in player's buildings
        player_building = await sync_to_async(self.player.get_building)(building_id)
        if not player_building:
            raise ValueError("Building not found for player")

        if not player_building or player_building.status != "in_progress":
            await self.send(
                json.dumps({"type": "error", "error": "Building not in progress"})
            )
            return

        now = timezone.now()
        finish_eta = player_building.finish_eta
        time_left = (finish_eta - now).total_seconds()
        if time_left <= 0:
            await self.send(
                json.dumps({"type": "error", "error": "Building already finished"})
            )
            return

        reduction = time_left * (percent / 100)
        new_time_left = max(0, time_left - reduction)
        new_finish_eta = now + timedelta(seconds=new_time_left)

        # Cancel old celery task
        celery_task_id = player_building.celery_task_id
        if celery_task_id:
            revoke(celery_task_id, terminate=True)

        # If new_time_left == 0, complete immediately
        if new_time_left == 0:
            complete_building_task.delay(str(self.player.id), str(building_id))
            player_building.finish_eta = now
            player_building.status = "completed"
            player_building.celery_task_id = None
            await sync_to_async(self.player.save)()
            await self.send(
                json.dumps(
                    {
                        "type": "building_accelerated",
                        "building_id": building_id,
                        "status": "completed",
                    }
                )
            )
            return

        # Schedule new celery task
        result = complete_building_task.apply_async(
            args=[str(self.player.id), str(building_id)],
            countdown=new_time_left,
        )
        player_building.finish_eta = new_finish_eta
        player_building.celery_task_id = result.id
        await sync_to_async(self.player.save)()
        await self.send(
            json.dumps(
                {
                    "type": "building_accelerated",
                    "building_id": building_id,
                    "new_finish_eta": new_finish_eta.isoformat(),
                }
            )
        )

    async def building_completed(self, event):
        await self.send(
            json.dumps(
                {
                    "type": "building_completed",
                    "building_id": event["building_id"],
                }
            )
        )

    async def player_updated(self, event):
        player_data = event["player"]
        await self.send(
            json.dumps(
                {
                    "type": "player_updated",
                    "player": player_data,
                }
            )
        )
