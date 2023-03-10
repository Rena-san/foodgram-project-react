from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response

from recipes.models import (FavoriteRecipe, Follow, Ingredient,
                            IngredientsAmount, Recipe, ShoppingCart, Tag)
from users.models import User

from .filters import IngredientsFilter, RecipesFilter
from .mixins import BaseClassViewSets, CreateDestroyViewSet
from .permissions import IsOwnerOrReadOnly
from .serializers import (AllUserSerializer, ChangePasswordSerializer,
                          FavoriteRecipeSerializer, FollowSerializer,
                          IngredientSerializer, NewUserCreateSerializer,
                          RecipeCreatUpdateSerializer, RecipeGetSerializer,
                          ShoppingCartSerializer, TagSerializer)


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = (IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly)
    filterset_class = RecipesFilter

    def get_serializer_class(self):
        if self.request.method == "GET":
            return RecipeGetSerializer
        return RecipeCreatUpdateSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(
        detail=False,
        methods=('GET',),
        permission_classes=(IsAuthenticated,))
    def download_shopping_cart(self, request):
        user = request.user
        if not user.shopping_cart.exists():
            return Response(
                'Список покупок пуст.', status=status.HTTP_400_BAD_REQUEST)

        text = 'Список покупок:\n\n'
        ingred_name = 'recipe__recipe__ingredient__name'
        ingred_unit = 'recipe__recipe__ingredient__measurement_unit'
        ingred_amount = 'recipe__recipe__amount'
        ingred_sum = 'recipe__recipe__amount__sum'
        cart = user.shopping_cart.select_related('recipe').values(
            ingred_name, ingred_unit).annotate(Sum(ingred_amount)
                                               ).order_by(ingred_name)
        for item in cart:
            text += (
                f'{item[ingred_name]} ({item[ingred_unit]})'
                f' — {item[ingred_sum]}\n'
            )
        response = HttpResponse(text, content_type='text/plain')
        filename = 'shopping_list.txt'
        response['Content-Disposition'] = f'attachment; filename={filename}'
        return response


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,)
    pagination_class = None
    filterset_class = IngredientsFilter


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,)
    pagination_class = None


class CustomUserViewSet(UserViewSet):
    queryset = User.objects.all()
    permission_classes = (IsAuthenticated,)

    def get_serializer_class(self):
        if self.action == 'set_password':
            return ChangePasswordSerializer
        if self.action == 'create':
            return NewUserCreateSerializer
        return AllUserSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_200_OK, headers=headers
        )

    @action(
        detail=False,
        permission_classes=(IsAuthenticated,))
    def subscriptions(self, request):
        queryset = Follow.objects.filter(user=request.user)
        pages = self.paginate_queryset(queryset)
        serializer = FollowSerializer(
            pages,
            many=True,
            context={'request': request},
        )
        return self.get_paginated_response(serializer.data)


class FollowViewSet(CreateDestroyViewSet):
    serializer_class = FollowSerializer

    def get_queryset(self):
        return self.request.user.follower.all()

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['author_id'] = self.kwargs.get('user_id')
        return context

    def perform_create(self, serializer):
        serializer.save(
            user=self.request.user,
            author=get_object_or_404(
                User,
                id=self.kwargs.get('user_id')
            )
        )

    @action(methods=('DELETE',), detail=True)
    def delete(self, request, user_id):
        get_object_or_404(User, id=user_id)
        if not Follow.objects.filter(
                user=request.user, author_id=user_id).exists():
            return Response(status=status.HTTP_400_BAD_REQUEST)
        get_object_or_404(
            Follow,
            user=request.user,
            author_id=user_id
        ).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class FavoriteRecipeViewSet(BaseClassViewSets):
    serializer_class = FavoriteRecipeSerializer
    permission_classes = (IsAuthenticated,)
    queryset = FavoriteRecipe.objects.all()
    pagination_class = None

    def get_queryset(self):
        user = self.request.user
        return FavoriteRecipe.objects.filter(user=user)

    @action(methods=('DELETE',), detail=True)
    def delete(self, request, recipe_id):
        return self.destroy(request, recipe_id, FavoriteRecipe)


class ShoppingCartViewSet(BaseClassViewSets):
    serializer_class = ShoppingCartSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        user = self.request.user
        return ShoppingCart.objects.filter(user=user)

    @action(methods=('DELETE',), detail=True)
    def delete(self, request, recipe_id):
        return self.destroy(request, recipe_id, ShoppingCart)
