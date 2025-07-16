from django.contrib import admin
from .models import Player


@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = ("username", "email", "display_wood", "display_stone")
    search_fields = ("username", "email")
    readonly_fields = ()

    def display_wood(self, obj):
        return obj.resources.wood

    display_wood.short_description = "Wood"

    def display_stone(self, obj):
        return obj.resources.stone

    display_stone.short_description = "Stone"
