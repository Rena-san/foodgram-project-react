from django.core.validators import MinValueValidator
from django.db import models

from users.models import User


class Tag(models.Model):
    name = models.CharField(
        "Название",
        max_length=50,
        unique=True
    )
    color = models.CharField(
        "Цвет",
        max_length=10,
        unique=True
    )
    slug = models.CharField(
        "Слаг",
        max_length=50,
        unique=True
    )

    class Meta:
        ordering = ['name', ]
        verbose_name = 'Тэг'
        verbose_name_plural = 'Тэги'

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    name = models.CharField(
        "Название",
        max_length=200,
    )
    measurement_unit = models.CharField(
        "Ед. измерения",
        max_length=200
    )

    class Meta:
        ordering = ['name', ]
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return f'{self.name} ({self.measurement_unit})'


class Recipe(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор рецепта',
        related_name='recipes',
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        verbose_name='Ингредиенты',
        through='IngredientsAmount'
    )
    tags = models.ManyToManyField(
        Tag,
        verbose_name='Тэг',
        related_name='recipes',
    )
    image = models.ImageField(
        "Пикча=)",
        upload_to='recipes/images/',
        blank=True,
        null=True,
        default=None
    )
    name = models.CharField(
        'Название рецепта',
        max_length=200
    )
    text = models.TextField(
        'Описание рецепта',
    )
    cooking_time = models.PositiveIntegerField(
        'Время приготовления',
        default=1,
        validators=(MinValueValidator(1, 'Минимум 1 минута'),),
    )
    pub_date = models.DateTimeField(
        'Дата публикации рецепта',
        auto_now_add=True)

    class Meta:
        ordering = ['-pub_date', ]
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.name


class IngredientsAmount(models.Model):
    """Модель количества ингредиентов в рецепте."""

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipe'
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='ingredient'
    )
    amount = models.PositiveSmallIntegerField(
        default=1,
        validators=[
            MinValueValidator(
                1, message='Минимальное количество ингредиентов'), ],
        verbose_name='Количество', )

    class Meta:
        ordering = ['-id', ]
        verbose_name = 'Количество'
        constraints = [
            models.UniqueConstraint(
                fields=('recipe', 'ingredient'),
                name='unique ingredient')]

    def __str__(self):
        return (f'{self.ingredient.name}, {self.amount},'
                f'{self.ingredient.measurement_unit}')


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='Подписчик'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Подписка на автора'
    )
    created = models.DateTimeField(
        'Дата и время подписки',
        auto_now_add=True
    )

    class Meta:
        ordering = ['-created', ]
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'],
                name='unique_author_following')]

    def __str__(self):
        return '{} подписан {}'.format(self.user, self.author)


class FavoriteRecipe(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorite',
        verbose_name='Пользователь'
    )
    favorite_recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorite_recipe',
        verbose_name='Избранный рецепт'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'favorite_recipe'],
                name='unique_favorite_recipe')]
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'
        ordering = ['id', ]

    def __str__(self):
        return '{} добавил в избранное рецепт: {}'.format(
            self.user.username,
            self.favorite_recipe.name
        )


class ShoppingCart(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shopping_cart',
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipe_shopping_cart',
        verbose_name='Рецепт'
    )

    class Meta:
        ordering = ['id', ]
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='unique_recipe_shopping_cart')]
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Список покупок'

    def __str__(self):
        return '{} добавил в корзину {}'.format(self.user.username,
                                                self.recipe.name)
