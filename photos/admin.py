from django.contrib import admin
from .models import Photo, Album, Collaboration


@admin.register(Photo)
class PhotoAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "format", "is_bookmarked", "created_at")
    list_filter = ("is_bookmarked", "format", "created_at")
    search_fields = ("user__username", "metadata")
    date_hierarchy = "created_at"


@admin.register(Album)
class AlbumAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "user", "created_at")
    list_filter = ("created_at",)
    search_fields = ("name", "description", "user__username")
    date_hierarchy = "created_at"
    filter_horizontal = ("photos",)


@admin.register(Collaboration)
class CollaborationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "content_type",
        "shared_by",
        "shared_with",
        "get_shared_item",
        "permission",
        "created_at",
    )
    list_filter = ("content_type", "permission", "created_at")
    search_fields = ("shared_by__username", "shared_with__username", "message")
    date_hierarchy = "created_at"
    
    def get_shared_item(self, obj):
        """Display the shared item (photo or album) based on content_type"""
        if obj.content_type == "PHOTO":
            return f"Photo: {obj.photo.id}" if obj.photo else "None"
        else:
            return f"Album: {obj.album.name}" if obj.album else "None"
    
    get_shared_item.short_description = "Shared Item"