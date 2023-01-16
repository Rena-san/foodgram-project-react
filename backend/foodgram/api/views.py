from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (SAFE_METHODS, IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response

from recipes.models import (FavoriteRecipe, Follow, Ingredient, Recipe,
                            ShoppingCart, Tag, IngredientsAmount)
from users.models import User

from .filters import IngredientsFilter, RecipesFilter
from .mixins import CreateDestroyViewSet
from .permissions import IsOwnerOrReadOnly
from .serializers import (FavoriteRecipeSerializer, FollowSerializer,
                          IngredientSerializer, RecipeCreatUpdateSerializer,
                          RecipeGetSerializer, ChangePasswordSerializer,
                          ShoppingCartSerializer, TagSerializer,
                          NewUserCreateSerializer, AllUserSerializer)
import io
from reportlab.pdfgen import canvas
from django.http import FileResponse
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = (IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly)
    filterset_class = RecipesFilter

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return RecipeGetSerializer
        return RecipeCreatUpdateSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(
        detail=False,
        methods=('get',),
        url_path='download_shopping_cart',
        pagination_class=None)
    def download_shop_list_pdf(self, request):
        buf = io.BytesIO()
        canvas_page = canvas.Canvas(buf)
        pdfmetrics.registerFont(TTFont('TNR', 'times.ttf'))
        pdfmetrics.registerFont(TTFont('TNRB', 'timesbd.ttf'))
        x, y = 20, 800

        ingred_name = 'recipe__recipe__ingredient__name'
        ingred_unit = 'recipe__recipe__ingredient__measurement_unit'
        recipe_amount = 'recipe__recipe__amount'
        amount_sum = 'recipe__recipe__amount__sum'

        user = request.user
        shopping_cart = user.shopping_cart.select_related('recipe').values(
            ingred_name,
            ingred_unit
        ).annotate(Sum(recipe_amount)).order_by(ingred_name)

        if shopping_cart:
            indent = 10
            canvas_page.setFont('TNRB', 30)
            canvas_page.drawString(x, y, 'Список необходимых ингредиентов:')
            y -= 20
            canvas_page.setFont('TNR', 20)
            for i, recipe in enumerate(shopping_cart, start=1):
                canvas_page.drawString(
                    x, y - indent,
                    f'{i}. {recipe[ingred_name].capitalize()} - '
                    f'{recipe[amount_sum]} '
                    f'{recipe[ingred_unit]}.')
                y -= 30
                if y <= 50:
                    canvas_page.showPage()
                    y = 900
            canvas_page.save()
            buf.seek(0)
            return FileResponse(
                buf,
                as_attachment=True,
                filename="Shopping_list.pdf"
            )
        canvas_page.setFont('TNRB', 40)
        canvas_page.drawString(
            x, y,
            'Рецепты не добавлялись в список покупок!'
        )
        canvas_page.save()
        buf.seek(0)
        return FileResponse(
            buf,
            as_attachment=True,
            filename="Shopping_list.pdf"
        )


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
    permission_classes = (IsAuthenticatedOrReadOnly,)

    def get_serializer_class(self):
        if self.action == 'set_password':
            return ChangePasswordSerializer
        if self.action == 'create':
            return NewUserCreateSerializer
        return AllUserSerializer

    def get_permissions(self):
        if self.action == 'me':
            self.permission_classes = [IsAuthenticated]
        return super().get_permissions()

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

    @action(methods=('delete',), detail=True)
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


class FavoriteRecipeViewSet(CreateDestroyViewSet):
    serializer_class = FavoriteRecipeSerializer

    def get_queryset(self):
        user = self.request.user.id
        return FavoriteRecipe.objects.filter(user=user)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['recipe_id'] = self.kwargs.get('recipe_id')
        return context

    def perform_create(self, serializer):
        serializer.save(
            user=self.request.user,
            favorite_recipe=get_object_or_404(
                Recipe,
                id=self.kwargs.get('recipe_id')
            )
        )

    @action(methods=('delete',), detail=True)
    def delete(self, request, recipe_id):
        user = request.user
        if not user.favorite.select_related(
                'favorite_recipe').filter(
            favorite_recipe_id=recipe_id
        ).exists():
            return Response(status=status.HTTP_400_BAD_REQUEST)
        get_object_or_404(
            FavoriteRecipe,
            user=request.user,
            favorite_recipe_id=recipe_id
        ).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ShoppingCartViewSet(CreateDestroyViewSet):
    serializer_class = ShoppingCartSerializer

    def get_queryset(self):
        user = self.request.user.id
        return ShoppingCart.objects.filter(user=user)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['recipe_id'] = self.kwargs.get('recipe_id')
        return context

    def perform_create(self, serializer):
        serializer.save(
            user=self.request.user,
            recipe=get_object_or_404(
                Recipe,
                id=self.kwargs.get('recipe_id')
            )
        )

    @action(methods=('delete',), detail=True)
    def delete(self, request, recipe_id):
        user = request.user
        if not user.shopping_cart.select_related('recipe').filter(
                recipe_id=recipe_id
        ).exists():
            return Response(status=status.HTTP_400_BAD_REQUEST)
        get_object_or_404(
            ShoppingCart,
            user=request.user,
            recipe=recipe_id
        ).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
