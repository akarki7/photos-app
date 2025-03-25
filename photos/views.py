from rest_framework import viewsets, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from drf_spectacular.utils import (
    extend_schema,
    OpenApiResponse,
    OpenApiParameter,
    OpenApiExample,
)


from .models import Photo, Album, Collaboration, User
from .serializers import (
    PhotoSerializer,
    PhotoDetailSerializer,
    AlbumSerializer,
    AlbumDetailSerializer,
    CollaborationSerializer,
    UserCreateSerializer,
    HomePagePhotoSerializer,
    HomePageAlbumSerializer,
)


class UserCreateView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = UserCreateSerializer

    @extend_schema(
        tags=["User Management"],
        summary="Register a new user",
        description="Create a new user account using email and password",
        responses={
            201: OpenApiResponse(description="User created successfully"),
            400: OpenApiResponse(description="Invalid input or validation error"),
        },
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


@extend_schema(tags=["Photos"])
class PhotoViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Get user's own photos
        user_photos = Photo.objects.filter(user=self.request.user)
        # Get photos shared with the user
        shared_photos = Photo.objects.filter(
            collaborations__shared_with=self.request.user,
            collaborations__content_type="PHOTO",
        )
        # Combine the querysets and remove duplicates
        return (user_photos | shared_photos).distinct()

    def get_serializer_class(self):
        if self.action in ["retrieve"]:
            return PhotoDetailSerializer
        return PhotoSerializer

    @extend_schema(
        tags=["Photos"],
        summary="Upload a single photo",
        description="Upload a single photo file with optional metadata",
        request={
            "multipart/form-data": {
                "type": "object",
                "properties": {
                    "image": {"type": "string", "format": "binary"},
                    "is_bookmarked": {"type": "boolean"},
                    "metadata": {"type": "object"},
                },
                "required": ["image"],
            }
        },
        responses={
            201: PhotoSerializer,
            400: OpenApiResponse(
                description="Invalid input or missing required fields"
            ),
            401: OpenApiResponse(
                description="Authentication credentials were not provided"
            ),
        },
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @extend_schema(
        tags=["Photos"],
        summary="Update a photo",
        description="Update photo properties or replace the image",
        request={
            "multipart/form-data": {
                "type": "object",
                "properties": {
                    "image": {"type": "string", "format": "binary"},
                    "is_bookmarked": {"type": "boolean"},
                    "metadata": {"type": "object"},
                },
            }
        },
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @extend_schema(
        tags=["Photos"],
        summary="Partially update a photo",
        description="Update specific photo properties without replacing the entire object",
        request={
            "multipart/form-data": {
                "type": "object",
                "properties": {
                    "image": {"type": "string", "format": "binary"},
                    "is_bookmarked": {"type": "boolean"},
                    "metadata": {"type": "object"},
                },
            }
        },
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(
        tags=["Photos"],
        summary="Get bookmarked photos",
        description="Retrieve all bookmarked photos the user has access to",
    )
    @action(detail=False, methods=["get"])
    def bookmarked(self, request):
        bookmarked_photos = self.get_queryset().filter(is_bookmarked=True)
        serializer = self.get_serializer(bookmarked_photos, many=True)
        return Response(serializer.data)

    @extend_schema(
        tags=["Photos"],
        summary="Bulk upload photos",
        description="Upload multiple photos at once (minimum 1 required)",
        request={
            "multipart/form-data": {
                "type": "object",
                "properties": {
                    "images": {
                        "type": "array",
                        "items": {"type": "string", "format": "binary"},
                        "minItems": 1,
                    },
                    "is_bookmarked": {"type": "boolean"},
                    "metadata": {"type": "object"},
                },
                "required": ["images"],
            }
        },
        responses={
            201: OpenApiResponse(description="Photos created successfully"),
            400: OpenApiResponse(description="Invalid input or no images provided"),
            401: OpenApiResponse(
                description="Authentication credentials were not provided"
            ),
        },
    )
    @action(detail=False, methods=["post"])
    def bulk(self, request):
        images = request.FILES.getlist("images")

        if not images:
            return Response(
                {"error": "At least one image is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        created_photos = []
        for image in images:
            # Create a new data dictionary for each photo
            data = {
                "image": image,
                "is_bookmarked": request.data.get("is_bookmarked", False),
                "metadata": request.data.get("metadata", {}),
            }

            serializer = self.get_serializer(data=data)
            if serializer.is_valid():
                serializer.save(user=request.user)
                created_photos.append(serializer.data)
            else:
                # You might want to handle errors differently here
                # This approach still creates valid photos even if some fail
                pass

        return Response(created_photos, status=status.HTTP_201_CREATED)


@extend_schema(tags=["Albums"])
class AlbumViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Get user's own albums
        user_albums = Album.objects.filter(user=self.request.user)
        # Get albums shared with the user
        shared_albums = Album.objects.filter(
            collaborations__shared_with=self.request.user,
            collaborations__content_type="ALBUM",
        )
        # Combine the querysets and remove duplicates
        return (user_albums | shared_albums).distinct()

    def get_serializer_class(self):
        if self.action in ["retrieve"]:
            return AlbumDetailSerializer
        return AlbumSerializer

    @extend_schema(
        tags=["Albums"],
        summary="Add photos to album",
        description="Add existing photos to an album",
        request={
            "application/json": {
                "type": "object",
                "properties": {
                    "photo_ids": {
                        "type": "array",
                        "items": {"type": "integer"},
                    }
                },
                "required": ["photo_ids"],
            }
        },
        responses={
            200: AlbumDetailSerializer,
            400: OpenApiResponse(description="Invalid input"),
            403: OpenApiResponse(description="Permission denied"),
            404: OpenApiResponse(description="Album not found"),
        },
    )
    @action(detail=True, methods=["post"])
    def add_photos(self, request, pk=None):
        album = self.get_object()
        photo_ids = request.data.get("photo_ids", [])

        if album.user != request.user:
            has_edit_permission = Collaboration.objects.filter(
                content_type="ALBUM",
                album=album,
                shared_with=request.user,
                permission="EDIT",
            ).exists()

            if not has_edit_permission:
                return Response(
                    {"detail": "You do not have permission to edit this album."},
                    status=status.HTTP_403_FORBIDDEN,
                )

        # Get user's own photos
        own_photos = Photo.objects.filter(user=request.user, id__in=photo_ids)
        # Get photos shared with user
        shared_photos = Photo.objects.filter(
            collaborations__shared_with=request.user,
            collaborations__content_type="PHOTO",
            id__in=photo_ids,
        )
        # Combine the querysets
        user_photos = (own_photos | shared_photos).distinct()

        album.photos.add(*user_photos)

        serializer = AlbumDetailSerializer(album, context={"request": request})
        return Response(serializer.data)

    @extend_schema(
        tags=["Albums"],
        summary="Remove photos from album",
        description="Remove photos from an album (does not delete the photos)",
        request={
            "application/json": {
                "type": "object",
                "properties": {
                    "photo_ids": {
                        "type": "array",
                        "items": {"type": "integer"},
                    }
                },
                "required": ["photo_ids"],
            }
        },
        responses={
            200: AlbumDetailSerializer,
            400: OpenApiResponse(description="Invalid input"),
            403: OpenApiResponse(description="Permission denied"),
            404: OpenApiResponse(description="Album not found"),
        },
    )
    @action(detail=True, methods=["post"])
    def remove_photos(self, request, pk=None):
        album = self.get_object()
        photo_ids = request.data.get("photo_ids", [])

        if album.user != request.user:
            has_edit_permission = Collaboration.objects.filter(
                content_type="ALBUM",
                album=album,
                shared_with=request.user,
                permission="EDIT",
            ).exists()

            if not has_edit_permission:
                return Response(
                    {"detail": "You do not have permission to edit this album."},
                    status=status.HTTP_403_FORBIDDEN,
                )

        photos_to_remove = Photo.objects.filter(id__in=photo_ids)
        album.photos.remove(*photos_to_remove)

        serializer = AlbumDetailSerializer(album, context={"request": request})
        return Response(serializer.data)


@extend_schema(tags=["Collaboration"])
class ShareViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = CollaborationSerializer

    def get_queryset(self):
        # Filter by content_type if specified
        content_type = self.request.query_params.get("content_type")
        queryset = Collaboration.objects.filter(shared_by=self.request.user)

        if content_type:
            queryset = queryset.filter(content_type=content_type.upper())

        return queryset

    @extend_schema(
        summary="Create sharing permission",
        description="Share a photo or album with another user",
        parameters=[
            OpenApiParameter(
                name="content_type",
                description="Filter collaborations by content type (PHOTO or ALBUM)",
                required=False,
                type=str,
                enum=["PHOTO", "ALBUM"],
                location=OpenApiParameter.QUERY,
            ),
        ],
        request=CollaborationSerializer,
        responses={
            201: OpenApiResponse(
                response=CollaborationSerializer,
                description="Sharing permission created successfully",
            ),
            400: OpenApiResponse(description="Invalid input data or validation error"),
            401: OpenApiResponse(
                description="Authentication credentials were not provided"
            ),
            403: OpenApiResponse(
                description="You don't have permission to share this item"
            ),
            404: OpenApiResponse(description="User with provided email not found"),
        },
        examples=[
            OpenApiExample(
                "Share Photo Example",
                summary="Example of sharing a photo with view permission",
                value={
                    "content_type": "PHOTO",
                    "photo_id": 1,
                    "shared_with_email": "user@example.com",
                    "permission": "VIEW",
                    "message": "Check out this photo!",
                },
                request_only=True,
            ),
            OpenApiExample(
                "Share Album Example",
                summary="Example of sharing an album with edit permission",
                value={
                    "content_type": "ALBUM",
                    "album_id": 1,
                    "shared_with_email": "user@example.com",
                    "permission": "EDIT",
                    "message": "Please add your photos to this album",
                },
                request_only=True,
            ),
        ],
    )
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @extend_schema(
        summary="List sharing permissions",
        description="Retrieve all sharing permissions created by the current user",
        parameters=[
            OpenApiParameter(
                name="content_type",
                description="Filter collaborations by content type (PHOTO or ALBUM)",
                required=False,
                type=str,
                enum=["PHOTO", "ALBUM"],
                location=OpenApiParameter.QUERY,
            ),
        ],
        responses={
            200: OpenApiResponse(
                response=CollaborationSerializer(many=True),
                description="List of sharing permissions",
            ),
            401: OpenApiResponse(
                description="Authentication credentials were not provided"
            ),
        },
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        summary="Retrieve sharing permission details",
        description="Get details of a specific sharing permission",
        responses={
            200: OpenApiResponse(
                response=CollaborationSerializer,
                description="Sharing permission details",
            ),
            401: OpenApiResponse(
                description="Authentication credentials were not provided"
            ),
            403: OpenApiResponse(
                description="You don't have permission to access this sharing permission"
            ),
            404: OpenApiResponse(description="Sharing permission not found"),
        },
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        summary="Update sharing permission",
        description="Update an existing sharing permission (e.g. change permission level)",
        request=CollaborationSerializer,
        responses={
            200: OpenApiResponse(
                response=CollaborationSerializer,
                description="Sharing permission updated successfully",
            ),
            400: OpenApiResponse(description="Invalid input data"),
            401: OpenApiResponse(
                description="Authentication credentials were not provided"
            ),
            403: OpenApiResponse(
                description="You don't have permission to update this sharing permission"
            ),
            404: OpenApiResponse(description="Sharing permission not found"),
        },
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @extend_schema(
        summary="Delete sharing permission",
        description="Remove sharing permission, revoking the user's access to the shared item",
        responses={
            204: OpenApiResponse(description="Sharing permission deleted successfully"),
            401: OpenApiResponse(
                description="Authentication credentials were not provided"
            ),
            403: OpenApiResponse(
                description="You don't have permission to delete this sharing permission"
            ),
            404: OpenApiResponse(description="Sharing permission not found"),
        },
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)


@extend_schema(tags=["Collaboration"])
class SharedWithMePhotosView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PhotoSerializer

    @extend_schema(
        summary="List photos shared with me",
        description="Retrieves all photos that have been shared with the current user",
        responses={
            200: OpenApiResponse(
                response=PhotoSerializer(many=True),
                description="List of photos shared with the current user",
            ),
            401: OpenApiResponse(
                description="Authentication credentials were not provided"
            ),
        },
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        return Photo.objects.filter(
            collaborations__shared_with=self.request.user,
            collaborations__content_type="PHOTO",
        ).distinct()


@extend_schema(tags=["Collaboration"])
class SharedWithMeAlbumsView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = AlbumSerializer

    @extend_schema(
        summary="List albums shared with me",
        description="Retrieves all albums that have been shared with the current user",
        responses={
            200: OpenApiResponse(
                response=AlbumSerializer(many=True),
                description="List of albums shared with the current user",
            ),
            401: OpenApiResponse(
                description="Authentication credentials were not provided"
            ),
        },
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        return Album.objects.filter(
            collaborations__shared_with=self.request.user,
            collaborations__content_type="ALBUM",
        ).distinct()


@extend_schema(tags=["Collaboration"])
class SharedWithMeView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CollaborationSerializer

    @extend_schema(
        summary="List all items shared with me",
        description="Retrieves all collaborations (photos and albums) that have been shared with the current user",
        parameters=[
            OpenApiParameter(
                name="content_type",
                description="Filter collaborations by content type (PHOTO or ALBUM)",
                required=False,
                type=str,
                enum=["PHOTO", "ALBUM"],
                location=OpenApiParameter.QUERY,
            ),
        ],
        responses={
            200: OpenApiResponse(
                response=CollaborationSerializer(many=True),
                description="List of all collaborations shared with the current user",
            ),
            401: OpenApiResponse(
                description="Authentication credentials were not provided"
            ),
        },
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        queryset = Collaboration.objects.filter(shared_with=self.request.user)

        # Filter by content_type if specified
        content_type = self.request.query_params.get("content_type")
        if content_type:
            queryset = queryset.filter(content_type=content_type.upper())

        return queryset


class HomePageView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Homepage"],
        summary="Get user homepage content",
        description="Retrieves all photos and albums the user has access to (both owned and shared).",
        responses={
            200: OpenApiResponse(description="Homepage content retrieved successfully"),
            401: OpenApiResponse(
                description="Authentication credentials were not provided"
            ),
        },
    )
    def get(self, request):
        # Get user's own photos
        user_photos = Photo.objects.filter(user=request.user)

        # Get photos shared with the user
        shared_photos = Photo.objects.filter(
            collaborations__shared_with=request.user,
            collaborations__content_type="PHOTO",
        )

        # Combine the photo querysets and remove duplicates
        all_photos = (
            (user_photos | shared_photos).distinct().order_by("-created_at")[:10]
        )

        # Get user's own albums
        user_albums = Album.objects.filter(user=request.user)

        # Get albums shared with the user
        shared_albums = Album.objects.filter(
            collaborations__shared_with=request.user,
            collaborations__content_type="ALBUM",
        )

        # Combine the album querysets and remove duplicates
        all_albums = (
            (user_albums | shared_albums).distinct().order_by("-created_at")[:5]
        )

        # Serialize the data
        photo_serializer = HomePagePhotoSerializer(
            all_photos, many=True, context={"request": request}
        )
        album_serializer = HomePageAlbumSerializer(
            all_albums, many=True, context={"request": request}
        )

        return Response(
            {"photos": photo_serializer.data, "albums": album_serializer.data}
        )
