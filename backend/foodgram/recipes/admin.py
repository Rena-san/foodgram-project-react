from django.contrib import admin

from .models import (FavoriteRecipe, Follow, Ingredient, IngredientsAmount,
                     Recipe, ShoppingCart, Tag)


class IngredientsAmountAdmin(admin.TabularInline):
    model = IngredientsAmount


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin, ):
    inlines = (IngredientsAmountAdmin,)
    list_display = (
        'id', 'name', 'author', 'text', 'pub_date', 'get_fav_amount'
    )
    list_filter = ('name', 'author', 'tags', 'pub_date')

    def get_fav_amount(self, obj):
        amount = FavoriteRecipe.objects.filter(recipe=obj).count()
        return amount

    get_fav_amount.short_description = "Кол-во добавлений в изб."


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'name', 'measurement_unit'
    )
    search_fields = ('name',)
    list_filter = ('name',)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'name', 'color', 'slug'
    )
    list_filter = ('name', 'slug')


@admin.register(FavoriteRecipe)
class FavoriteRecipeAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'user', 'recipe'
    )
    search_fields = ('recipe',)
    list_filter = ('id', 'user', 'recipe')


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'author', 'user', 'created'
    )
    list_filter = ('author', 'user', 'created')


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'user', 'recipe'
    )
    list_filter = ('user', 'recipe')
