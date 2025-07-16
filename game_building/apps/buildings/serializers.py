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
    dependencies = serializers.JSONField(default=list, required=False)

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

    def validate_dependencies(self, value):
        print(f"Validating dependencies: {value}")
        for dep_id in value:
            if not Building.objects.filter(building_id=dep_id).exists():
                raise serializers.ValidationError(
                    f"Dependency with id {dep_id} does not exist."
                )
        return value
