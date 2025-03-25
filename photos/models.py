from django.db import models
import os
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError


class Photo(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="photos")
    image = models.ImageField(upload_to="photos/%Y/%m/%d/")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    format = models.CharField(max_length=10, blank=True)
    is_bookmarked = models.BooleanField(default=False)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Photo {self.id} by {self.user.username}"

    def save(self, *args, **kwargs):
        # Set format based on file extension if not already set
        if not self.format and self.image:
            name, extension = os.path.splitext(self.image.name)
            self.format = extension[1:].lower()  # Remove the leading dot
        super().save(*args, **kwargs)


class Album(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="albums")
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    cover_photo = models.ForeignKey(
        Photo,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="cover_for_albums",
    )
    photos = models.ManyToManyField(Photo, related_name="albums", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} by {self.user.username}"


class Collaboration(models.Model):
    PERMISSION_CHOICES = [
        ("VIEW", "View"),
        ("EDIT", "Edit"),
    ]

    CONTENT_TYPE_CHOICES = [
        ("PHOTO", "Photo"),
        ("ALBUM", "Album"),
    ]

    shared_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="shared_items"
    )
    shared_with = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="received_shared_items"
    )
    message = models.TextField(blank=True)

    # Content type field to distinguish between photos and albums
    content_type = models.CharField(max_length=5, choices=CONTENT_TYPE_CHOICES)

    # Generic foreign keys for photos and albums
    photo = models.ForeignKey(
        Photo,
        on_delete=models.CASCADE,
        related_name="collaborations",
        null=True,
        blank=True,
    )
    album = models.ForeignKey(
        Album,
        on_delete=models.CASCADE,
        related_name="collaborations",
        null=True,
        blank=True,
    )

    permission = models.CharField(
        max_length=4, choices=PERMISSION_CHOICES, default="VIEW"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Ensure a user can only be shared with once per item
        constraints = [
            models.UniqueConstraint(
                fields=["shared_with", "photo"],
                condition=models.Q(content_type="PHOTO", photo__isnull=False),
                name="unique_photo_collaboration",
            ),
            models.UniqueConstraint(
                fields=["shared_with", "album"],
                condition=models.Q(content_type="ALBUM", album__isnull=False),
                name="unique_album_collaboration",
            ),
            # Ensure exactly one of photo or album is set based on content_type
            models.CheckConstraint(
                check=(
                    models.Q(
                        content_type="PHOTO", photo__isnull=False, album__isnull=True
                    )
                    | models.Q(
                        content_type="ALBUM", album__isnull=False, photo__isnull=True
                    )
                ),
                name="content_type_consistency",
            ),
        ]
        ordering = ["-created_at"]

    def clean(self):
        # Additional validation to ensure content_type matches the provided object
        if self.content_type == "PHOTO" and self.photo is None:
            raise ValidationError("Photo must be provided when content_type is PHOTO")
        if self.content_type == "ALBUM" and self.album is None:
            raise ValidationError("Album must be provided when content_type is ALBUM")

        super().clean()

    def __str__(self):
        if self.content_type == "PHOTO":
            item_id = self.photo.id if self.photo else "None"
            item_type = "Photo"
        else:
            item_id = self.album.id if self.album else "None"
            item_type = "Album"

        return f"{item_type} {item_id} shared by {self.shared_by.username} with {self.shared_with.username}"

    @property
    def shared_item(self):
        """Return the shared item (photo or album) based on content_type"""
        if self.content_type == "PHOTO":
            return self.photo
        else:
            return self.album
