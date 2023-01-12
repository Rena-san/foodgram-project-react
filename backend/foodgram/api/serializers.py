from django.contrib.auth.hashers import check_password
from djoser.serializers import (PasswordSerializer, UserCreateSerializer,
                                UserSerializer)
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers

from recipes.models import (FavoriteRecipe, Follow, Ingredient,
                            IngredientsAmount, Recipe, ShoppingCart, Tag)
from users.models import User


class UserListSerializer(UserSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'is_subscribed')

    def get_is_subscribed(self, obj):
        return (self.context.get('request').user.is_authenticated
                and Follow.objects.filter(
                    user=self.context.get('request').user,
                    author=obj
                ).exists())


class UserCreateSerializer(UserCreateSerializer):
    class Meta:
        model = User
        fields = ('email', 'username', 'first_name', 'last_name', 'password')
        required_fields = (
            'email',
            'username',
            'first_name',
            'last_name',
            'password'
        )

    def validate(self, data):
        if data['username'] == 'me':
            raise serializers.ValidationError('Username "me" уже занято.')
        return data


class IngredientsAmountSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(
        source='ingredient.id',
    )
    name = serializers.ReadOnlyField(
        source='ingredient.name',
    )
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit',
    )

    class Meta:
        model = IngredientsAmount
        fields = ('id', 'name', 'measurement_unit', 'amount')


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'


class RecipeReadSerializer(serializers.ModelSerializer):
    ingredients = IngredientsAmountSerializer(
        many=True,
        source='recipe',
        required=True,
    )
    tags = TagSerializer(
        many=True,
        read_only=True
    )
    author = UserListSerializer(
        read_only=True,
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients', 'is_favorited',
            'is_in_shopping_cart', 'name', 'image', 'text', 'cooking_time'
        )

    def get_is_favorited(self, obj):
        return (self.context.get('request').user.is_authenticated
                and FavoriteRecipe.objects.filter(
                    user=self.context.get('request').user,
                    favorite_recipe=obj
                ).exists())

    def get_is_in_shopping_cart(self, obj):
        return (self.context.get('request').user.is_authenticated
                and ShoppingCart.objects.filter(
                    user=self.context.get('request').user,
                    recipe=obj
                ).exists())


class IngredientsEditSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()
    amount = serializers.IntegerField()

    class Meta:
        model = Ingredient
        fields = ('id', 'amount')


class RecipeEditSerializer(serializers.ModelSerializer):
    image = Base64ImageField(
        max_length=None,
        use_url=True)
    ingredients = IngredientsEditSerializer(
        many=True)
    author = serializers.PrimaryKeyRelatedField(
        read_only=True)

    class Meta:
        model = Recipe
        fields = '__all__'

    def create_ingredients(self, ingredients, recipe):
        for ingredient in ingredients:
            IngredientsAmount.objects.bulk_create([
                IngredientsAmount(
                    recipe=recipe,
                    ingredient_id=ingredient.get('id'),
                    amount=ingredient.get('amount'), )
            ])

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        self.create_ingredients(ingredients, recipe)
        return recipe

    def update(self, instance, validated_data):
        if 'ingredients' in validated_data:
            ingredients = validated_data.pop('ingredients')
            instance.ingredients.clear()
            self.create_ingredients(ingredients, instance)
        if 'tags' in validated_data:
            instance.tags.set(
                validated_data.pop('tags'))
        return super().update(
            instance, validated_data)

    def to_representation(self, instance):
        return RecipeReadSerializer(
            instance,
            context={
                'request': self.context.get('request')
            }).data


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = '__all__'


class SetPasswordSerializer(PasswordSerializer):
    current_password = serializers.CharField(
        required=True,
        label='Текущий пароль')

    def validate(self, data):
        user = self.context.get('request').user
        if data['new_password'] == data['current_password']:
            raise serializers.ValidationError({
                "new_password": "Пароли не должны совпадать"})
        check_current = check_password(data['current_password'], user.password)
        if check_current is False:
            raise serializers.ValidationError({
                "current_password": "Введен неверный пароль"})
        return data


class FollowRecipeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class FollowSerializer(serializers.ModelSerializer):
    email = serializers.CharField(
        source='author.email',
        read_only=True)
    id = serializers.IntegerField(
        source='author.id',
        read_only=True)
    username = serializers.CharField(
        source='author.username',
        read_only=True)
    first_name = serializers.CharField(
        source='author.first_name',
        read_only=True)
    last_name = serializers.CharField(
        source='author.last_name',
        read_only=True)
    recipes = serializers.SerializerMethodField()
    is_subscribed = serializers.SerializerMethodField()
    recipes_count = serializers.ReadOnlyField(
        source='author.recipe.count')

    class Meta:
        model = Follow
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'is_subscribed', 'recipes', 'recipes_count',)

    def validate(self, data):
        user = self.context.get('request').user
        author = self.context.get('author_id')
        if user.id == int(author):
            raise serializers.ValidationError({
                'errors': 'Нельзя подписаться на самого себя'})
        if Follow.objects.filter(user=user, author=author).exists():
            raise serializers.ValidationError({
                'errors': 'Вы уже подписаны на данного пользователя'})
        return data

    def get_recipes(self, obj):
        recipes = obj.author.recipe.all()
        return FollowRecipeSerializer(
            recipes,
            many=True).data

    def get_is_subscribed(self, obj):
        subscribe = Follow.objects.filter(
            user=self.context.get('request').user,
            author=obj.author
        )
        if subscribe:
            return True
        return False


class FavoriteRecipeSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(
        source='favorite_recipe.id',
    )
    name = serializers.ReadOnlyField(
        source='favorite_recipe.name',
    )
    image = serializers.CharField(
        source='favorite_recipe.image',
        read_only=True,
    )
    cooking_time = serializers.ReadOnlyField(
        source='favorite_recipe.cooking_time',
    )

    class Meta:
        model = FavoriteRecipe
        fields = ('id', 'name', 'image', 'cooking_time')

    def validate(self, data):
        user = self.context.get('request').user
        recipe = self.context.get('recipe_id')
        if FavoriteRecipe.objects.filter(user=user,
                                         favorite_recipe=recipe).exists():
            raise serializers.ValidationError({
                'errors': 'Рецепт уже в избранном'})
        return data


class ShoppingCartSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(
        source='recipe.id',
    )
    name = serializers.ReadOnlyField(
        source='recipe.name',
    )
    image = serializers.CharField(
        source='recipe.image',
        read_only=True,
    )
    cooking_time = serializers.ReadOnlyField(
        source='recipe.cooking_time',
    )

    class Meta:
        model = ShoppingCart
        fields = ('id', 'name', 'image', 'cooking_time')

    def validate(self, data):
        user = self.context.get('request').user
        recipe = self.context.get('recipe_id')
        if ShoppingCart.objects.filter(user=user,
                                       recipe=recipe).exists():
            raise serializers.ValidationError({
                'errors': 'Рецепт уже добавлен в список покупок'})
        return data
