from rest_framework import serializers
from .models import Building


class BuildingSerializer(serializers.ModelSerializer):
    id = serializers.SerializerMethodField()

    class Meta:
        model = Building
        fields = [
            "id",
            "building_id",
            "name",
            "build_time",
            "required_wood",
            "required_stone",
            "dependencies",
        ]
        read_only_fields = ["id"]

    def get_id(self, obj):
        return str(obj.id)


class BuildingCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Building
        fields = [
            "name",
            "building_id",
            "build_time",
            "required_wood",
            "required_stone",
            "dependencies",
        ]
