from game_building.config.celery import app as celery_app
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


def update_building_status(player, building_id):
    updated = False
    player_building = player.get_building(building_id)
    if player_building and player_building.status == "in_progress":
        player_building.status = "completed"
        player_building.celery_task_id = None
        updated = True
    if updated:
        player.save()
    return updated


@celery_app.task
def complete_building_task(player_id, building_id):
    from game_building.apps.players.models import Player
    from game_building.apps.players.serializers import PlayerSerializer

    player = Player.objects.get(id=player_id)
    updated = update_building_status(player, building_id)
    # Send WebSocket notification if updated
    if updated:
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"player_{player_id}",
            {
                "type": "building.completed",
                "building_id": building_id,
            },
        )
        print(f"Building {building_id} completed for player {player_id}")
        serializer = PlayerSerializer(player)
        async_to_sync(channel_layer.group_send)(
            f"player_{player_id}", {"type": "player.updated", "player": serializer.data}
        )
