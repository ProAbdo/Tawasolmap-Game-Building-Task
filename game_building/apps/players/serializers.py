from rest_framework import serializers
from .models import Player, PlayerBuilding, Resources


class ResourcesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Resources
        fields = ["wood", "stone"]


class PlayerBuildingSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlayerBuilding
        fields = [
            "building_id",
            "status",
            "started_at",
            "finish_eta",
            "celery_task_id",
        ]
        read_only_fields = ["building_id"]


class PlayerSerializer(serializers.ModelSerializer):
    id = serializers.SerializerMethodField()
    resources = ResourcesSerializer()
    buildings = PlayerBuildingSerializer(many=True, read_only=True)

    class Meta:
        model = Player
        fields = [
            "id",
            "username",
            "email",
            "resources",
            "buildings",
        ]
        read_only_fields = ["id"]

    def get_id(self, obj):
        return str(obj.id)


class PlayerCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = Player
        fields = ["username", "email", "password"]


class PlayerLoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()


class PlayerBuildingCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlayerBuilding
        fields = [
            "building_id",
            "status",
            "started_at",
            "finish_eta",
            "celery_task_id",
        ]


class PlayerResourcesUpdateSerializer(serializers.Serializer):
    wood = serializers.IntegerField(min_value=0, required=False)
    stone = serializers.IntegerField(min_value=0, required=False)

    def validate(self, data):
        if not data:
            raise serializers.ValidationError("At least one resource must be provided.")
        return data
