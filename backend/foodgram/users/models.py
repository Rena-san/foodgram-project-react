from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """ Mодель пользователя."""

    email = models.EmailField(
        'Почта',
        max_length=254,
        unique=True
    )
    first_name = models.CharField(
        'Имя',
        max_length=150,
        blank=False
    )
    last_name = models.CharField(
        'Фамилия',
        max_length=150,
        blank=False
    )
    username = models.CharField(
        'Логин',
        max_length=150,
        unique=True
    )

    class Meta:
        ordering = ['-pk',]
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return f'{self.username}, {self.email}'
