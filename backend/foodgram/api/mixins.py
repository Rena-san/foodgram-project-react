from django.shortcuts import get_object_or_404
from rest_framework import mixins, serializers, status, viewsets
from rest_framework.response import Response

from recipes.models import Follow, Recipe
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


class BaseClassViewSets(CreateDestroyViewSet):

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['recipe_id'] = self.kwargs.get('recipe_id')
        return context

    def perform_create(self, serializer):
        user = self.request.user
        serializer.save(
            user=user,
            recipe=get_object_or_404(
                Recipe,
                id=self.kwargs.get('recipe_id')
            )
        )

    def destroy(self, request, recipe_id, model):
        user = request.user
        if not model.objects.filter(
                user=user,
                recipe_id=recipe_id).exists():
            return Response(status=status.HTTP_400_BAD_REQUEST)
        get_object_or_404(
            model,
            user=user,
            recipe=recipe_id
        ).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
