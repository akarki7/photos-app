from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password

from .models import Photo, Album, Collaboration


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email"]


class PhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Photo
        fields = [
            "id",
            "image",
            "created_at",
            "updated_at",
            "format",
            "is_bookmarked",
            "metadata",
        ]
        read_only_fields = ["created_at", "updated_at", "format"]

    def create(self, validated_data):
        # Set the user from the request
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)


class PhotoDetailSerializer(PhotoSerializer):
    user = UserSerializer(read_only=True)

    class Meta(PhotoSerializer.Meta):
        fields = PhotoSerializer.Meta.fields + ["user"]


class AlbumSerializer(serializers.ModelSerializer):
    cover_photo = PhotoSerializer(read_only=True)
    cover_photo_id = serializers.PrimaryKeyRelatedField(
        queryset=Photo.objects.all(),
        source="cover_photo",
        required=False,
        allow_null=True,
        write_only=True,
    )
    photo_count = serializers.SerializerMethodField()

    class Meta:
        model = Album
        fields = [
            "id",
            "name",
            "description",
            "cover_photo",
            "cover_photo_id",
            "created_at",
            "updated_at",
            "photo_count",
        ]
        read_only_fields = ["created_at", "updated_at"]

    def get_photo_count(self, obj):
        photos_count = obj.photos.count()

        if obj.cover_photo and not obj.photos.filter(id=obj.cover_photo.id).exists():
            return photos_count + 1

        return photos_count

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)


class AlbumDetailSerializer(AlbumSerializer):
    photos = PhotoSerializer(many=True, read_only=True)
    user = UserSerializer(read_only=True)

    class Meta(AlbumSerializer.Meta):
        fields = AlbumSerializer.Meta.fields + ["photos", "user"]


class CollaborationSerializer(serializers.ModelSerializer):
    shared_by = UserSerializer(read_only=True)
    shared_with_email = serializers.EmailField(write_only=True)
    shared_with = UserSerializer(read_only=True)

    # Content type field
    content_type = serializers.ChoiceField(choices=Collaboration.CONTENT_TYPE_CHOICES)

    # Photo fields (used when content_type is PHOTO)
    photo = PhotoSerializer(read_only=True)
    photo_id = serializers.PrimaryKeyRelatedField(
        queryset=Photo.objects.all(), source="photo", write_only=True, required=False
    )

    # Album fields (used when content_type is ALBUM)
    album = AlbumSerializer(read_only=True)
    album_id = serializers.PrimaryKeyRelatedField(
        queryset=Album.objects.all(), source="album", write_only=True, required=False
    )

    class Meta:
        model = Collaboration
        fields = [
            "id",
            "shared_by",
            "shared_with_email",
            "shared_with",
            "message",
            "content_type",
            "photo",
            "photo_id",
            "album",
            "album_id",
            "permission",
            "created_at",
        ]
        read_only_fields = ["created_at"]

    def validate_shared_with_email(self, value):
        try:
            User.objects.get(email=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("User with this email does not exist.")
        return value

    def validate(self, data):
        # Ensure user doesn't share with themselves
        user_email = self.context["request"].user.email
        if data.get("shared_with_email") == user_email:
            raise serializers.ValidationError("You cannot share with yourself.")

        # Check content type and corresponding ID field
        content_type = data.get("content_type")
        if content_type == "PHOTO" and "photo" not in data:
            raise serializers.ValidationError(
                "Photo ID is required when content_type is PHOTO."
            )
        if content_type == "ALBUM" and "album" not in data:
            raise serializers.ValidationError(
                "Album ID is required when content_type is ALBUM."
            )

        # Validate the user has access to the item
        if content_type == "PHOTO":
            photo = data.get("photo")
            if photo and photo.user != self.context["request"].user:
                # Check if the user has edit permission through collaboration
                has_permission = Collaboration.objects.filter(
                    content_type="PHOTO",
                    photo=photo,
                    shared_with=self.context["request"].user,
                    permission="EDIT",
                ).exists()

                if not has_permission:
                    raise serializers.ValidationError(
                        "You do not have permission to share this photo."
                    )
        elif content_type == "ALBUM":
            album = data.get("album")
            if album and album.user != self.context["request"].user:
                # Check if the user has edit permission through collaboration
                has_permission = Collaboration.objects.filter(
                    content_type="ALBUM",
                    album=album,
                    shared_with=self.context["request"].user,
                    permission="EDIT",
                ).exists()

                if not has_permission:
                    raise serializers.ValidationError(
                        "You do not have permission to share this album."
                    )

        return data

    def create(self, validated_data):
        # Get the shared_with user from email
        shared_with_email = validated_data.pop("shared_with_email")
        shared_with = User.objects.get(email=shared_with_email)

        # Set the shared_by user from the request
        validated_data["shared_by"] = self.context["request"].user
        validated_data["shared_with"] = shared_with

        # Enforce null constraints based on content_type
        content_type = validated_data.get("content_type")
        if content_type == "PHOTO":
            validated_data["album"] = None
        elif content_type == "ALBUM":
            validated_data["photo"] = None

        return super().create(validated_data)


class UserCreateSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(
        write_only=True, required=True, validators=[validate_password]
    )
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ("email", "password", "password2")

    def validate(self, attrs):
        if attrs["password"] != attrs["password2"]:
            raise serializers.ValidationError(
                {"password": "Password fields didn't match."}
            )
        return attrs

    def create(self, validated_data):
        validated_data.pop("password2")
        username = validated_data.get("email")
        user = User.objects.create(
            username=username,
            email=validated_data["email"],
        )
        user.set_password(validated_data["password"])
        user.save()

        return user


class HomePagePhotoSerializer(serializers.ModelSerializer):
    username = serializers.SerializerMethodField()
    is_shared = serializers.SerializerMethodField()

    class Meta:
        model = Photo
        fields = [
            "id",
            "image",
            "created_at",
            "is_bookmarked",
            "format",
            "username",
            "is_shared",
        ]

    def get_username(self, obj):
        return obj.user.username

    def get_is_shared(self, obj):
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            return obj.user != request.user
        return False


class HomePageAlbumSerializer(serializers.ModelSerializer):
    photo_count = serializers.SerializerMethodField()
    cover_image = serializers.SerializerMethodField()
    username = serializers.SerializerMethodField()
    is_shared = serializers.SerializerMethodField()
    photos = serializers.SerializerMethodField()

    class Meta:
        model = Album
        fields = [
            "id",
            "name",
            "created_at",
            "photo_count",
            "cover_image",
            "username",
            "is_shared",
            "photos",
        ]

    def get_photo_count(self, obj):
        photos_count = obj.photos.count()

        if obj.cover_photo and not obj.photos.filter(id=obj.cover_photo.id).exists():
            return photos_count + 1

        return photos_count

    def get_cover_image(self, obj):
        request = self.context.get("request")
        if obj.cover_photo and obj.cover_photo.image:
            return (
                request.build_absolute_uri(obj.cover_photo.image.url)
                if request
                else obj.cover_photo.image.url
            )
        return None

    def get_username(self, obj):
        return obj.user.username

    def get_is_shared(self, obj):
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            return obj.user != request.user
        return False

    def get_photos(self, obj):
        # Get all photos in the album
        album_photos = list(obj.photos.all())

        # Include cover photo if it exists and isn't already in the album photos
        if obj.cover_photo and not obj.photos.filter(id=obj.cover_photo.id).exists():
            album_photos.append(obj.cover_photo)

        # Use the existing photo serializer
        from .serializers import HomePagePhotoSerializer

        return HomePagePhotoSerializer(
            album_photos, many=True, context=self.context
        ).data
