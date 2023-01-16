from rest_framework import mixins, viewsets
from rest_framework import serializers
from recipes.models import Follow
from users.models import User


class CreateDestroyViewSet(mixins.CreateModelMixin,
                           mixins.DestroyModelMixin,
                           viewsets.GenericViewSet):
    pass


class FollowMixin:
    is_subscribed = serializers.SerializerMethodField()

    def get_is_subscribed(self, obj):
        user_id = obj.id if isinstance(obj, User) else obj.author.id

        request_user = self.context.get('request').user.id
        queryset = Follow.objects.filter(author=user_id,
                                         user=request_user).exists()
        return queryset
