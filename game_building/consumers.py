import json
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from game_building.apps.players.services import (
    register_player,
    login_player,
    can_start_building,
    start_building_for_player,
    update_player_resources,
    get_player_info,
)
from game_building.apps.buildings.services import accelerate_building, create_building
from game_building.apps.buildings.serializers import BuildingSerializer


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
            elif msg_type == "update_resources":
                await self.handle_update_resources(data)
            elif msg_type == "get_player_info":
                await self.handle_get_player_info(data)
            else:
                await self.send(
                    json.dumps(
                        {"type": "error", "error": f"Unknown message type: {msg_type}"}
                    )
                )
        except Exception as e:
            await self.send(json.dumps({"type": "error", "error": str(e)}))

    async def handle_register(self, data):
        result = await register_player(data)
        if result["type"] == "register_success":
            from game_building.apps.players.models import Player

            self.player = await sync_to_async(Player.objects.get)(
                username=data["username"]
            )
            await self.channel_layer.group_add(
                f"player_{self.player.id}", self.channel_name
            )
        await self.send(json.dumps(result))

    async def handle_login(self, data):
        player, error = await login_player(data)
        if player:
            self.player = player
            await self.channel_layer.group_add(
                f"player_{self.player.id}", self.channel_name
            )
            from game_building.apps.players.serializers import PlayerSerializer

            serializer = PlayerSerializer(player)
            await self.send(
                json.dumps({"type": "login_success", "player": serializer.data})
            )
        else:
            await self.send(json.dumps({"type": "login_failed", "error": error}))

    async def handle_start_building(self, data):
        if not self.player:
            await self.send(json.dumps({"type": "error", "error": "Not authenticated"}))
            return
        building_id = data.get("building_id")
        can_start, error, building = await can_start_building(self.player, building_id)
        if not can_start:
            await self.send(json.dumps({"type": "error", "error": error}))
            return
        completion_time = await start_building_for_player(self.player, building)
        await self.send(
            json.dumps(
                {
                    "type": "building_started",
                    "building_id": str(building_id),
                    "completion_time": completion_time.isoformat(),
                }
            )
        )

    async def handle_create_building(self, data):
        building, error = await create_building(data)
        if building:
            serializer = BuildingSerializer(building)
            await self.send(
                json.dumps(
                    {"type": "create_building_success", "building": serializer.data}
                )
            )
        else:
            await self.send(
                json.dumps({"type": "create_building_failed", "error": error})
            )

    async def handle_accelerate_building(self, data):
        if not self.player:
            await self.send(json.dumps({"type": "error", "error": "Not authenticated"}))
            return
        from game_building.apps.players.models import Player

        self.player = await sync_to_async(Player.objects.get)(id=self.player.id)
        building_id = data.get("building_id")
        percent = data.get("percent", 100)
        result = await accelerate_building(self.player, building_id, percent)
        await self.send(json.dumps(result))

    async def handle_update_resources(self, data):
        if not self.player:
            await self.send(json.dumps({"type": "error", "error": "Not authenticated"}))
            return
        result = await update_player_resources(self.player, data)
        await self.send(json.dumps(result))

    async def handle_get_player_info(self, data):
        from game_building.apps.players.models import Player

        if not self.player:
            await self.send(json.dumps({"type": "error", "error": "Not authenticated"}))
            return
        self.player = await sync_to_async(Player.objects.get)(id=self.player.id)
        result = await get_player_info(self.player)
        await self.send(json.dumps(result))

    async def building_completed(self, event):
        await self.send(
            json.dumps(
                {"type": "building_completed", "building_id": event["building_id"]}
            )
        )

    async def player_updated(self, event):
        await self.send(
            json.dumps({"type": "player_updated", "player": event["player"]})
        )
