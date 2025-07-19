import json
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from functools import wraps

from game_building.apps.players.models import Player
from game_building.apps.players.serializers import PlayerSerializer
from game_building.apps.buildings.serializers import BuildingSerializer
from game_building.apps.players.services import (
    register_player,
    login_player,
    can_start_building,
    start_building_for_player,
    update_player_resources,
    get_player_info,
)
from game_building.apps.buildings.services import (
    accelerate_building,
    create_building,
    get_allowed_buildings,
)


def require_auth(func):
    @wraps(func)
    async def wrapper(self, *args, **kwargs):
        if not self.player:
            return await self.send_error("Not authenticated")

        await sync_to_async(self.player.refresh_from_db)()
        return await func(self, *args, **kwargs)

    return wrapper


class GameConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        self.player = None

    async def disconnect(self, close_code):
        if self.player:
            await self.channel_layer.group_discard(
                f"player_{self.player.id}", self.channel_name
            )

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            msg_type = data.get("type")
            handler = {
                "register": self.handle_register,
                "login": self.handle_login,
                "start_building": self.handle_start_building,
                "create_building": self.handle_create_building,
                "accelerate_building": self.handle_accelerate_building,
                "update_resources": self.handle_update_resources,
                "get_player_info": self.handle_get_player_info,
                "get_allowed_buildings": self.handle_get_allowed_buildings,
            }.get(msg_type)

            if handler:
                await handler(data)
            else:
                await self.send_error(f"Unknown message type: {msg_type}")
        except Exception as e:
            await self.send_error(str(e))

    async def handle_register(self, data):
        result = await register_player(data)
        if result["type"] == "register_success":
            self.player = await sync_to_async(Player.objects.get)(
                username=data["username"]
            )
            await self.channel_layer.group_add(
                f"player_{self.player.id}", self.channel_name
            )
        await self.send_json(result)

    async def handle_login(self, data):
        player, error = await login_player(data)
        if player:
            self.player = player
            await self.channel_layer.group_add(
                f"player_{self.player.id}", self.channel_name
            )
            serialized = PlayerSerializer(player)
            await self.send_json({"type": "login_success", "player": serialized.data})
        else:
            await self.send_json({"type": "login_failed", "error": error})

    @require_auth
    async def handle_start_building(self, data):
        building_id = data.get("building_id")
        can_start, error, building = await can_start_building(self.player, building_id)
        if not can_start:
            return await self.send_error(error)

        try:
            completion_time = await start_building_for_player(self.player, building)
            await self.send_json(
                {
                    "type": "building_started",
                    "building_id": str(building_id),
                    "completion_time": completion_time.isoformat(),
                }
            )
        except ValueError as e:
            await self.send_error(str(e), "building_start_failed")
        except Exception as e:
            await self.send_error(
                f"Unexpected error starting building: {str(e)}", "building_start_failed"
            )

    async def handle_create_building(self, data):
        building, error = await create_building(data)
        if building:
            serializer = BuildingSerializer(building)
            await self.send_json(
                {"type": "create_building_success", "building": serializer.data}
            )
        else:
            await self.send_error(error, "create_building_failed")

    @require_auth
    async def handle_accelerate_building(self, data):
        building_id = data.get("building_id")
        percent = data.get("percent", 100)
        result = await accelerate_building(self.player, building_id, percent)
        await self.send_json(result)

    @require_auth
    async def handle_update_resources(self, data):
        result = await update_player_resources(self.player, data)
        await self.send_json(result)

    @require_auth
    async def handle_get_player_info(self, data):
        result = await get_player_info(self.player)
        await self.send_json(result)

    @require_auth
    async def handle_get_allowed_buildings(self, data):
        result = await get_allowed_buildings(self.player)
        await self.send_json(result)

    async def building_completed(self, event):
        await self.send_json(
            {"type": "building_completed", "building_id": event["building_id"]}
        )

    async def player_updated(self, event):
        await self.send_json({"type": "player_updated", "player": event["player"]})

    async def send_error(self, error, msg_type="error"):
        await self.send_json({"type": msg_type, "error": error})

    async def send_json(self, data):
        await self.send(text_data=json.dumps(data))
