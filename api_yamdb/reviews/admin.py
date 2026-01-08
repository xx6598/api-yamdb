from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from reviews.models import User, Category, Genre, Title, Review, Comment


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = (
        'username',
        'email',
        'role',
        'bio',
        'first_name',
        'last_name',
    )
    search_fields = (
        'username',
        'email',
        'role',
    )
    list_filter = ('role',)
    empty_value_display = '-пусто-'
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (
            'Персональная информация',
            {'fields': ('first_name', 'last_name', 'email', 'bio')},
        ),
        (
            'Права доступа',
            {
                'fields': (
                    'role',
                    'is_active',
                    'is_staff',
                    'is_superuser',
                    'user_permissions',
                )
            },
        ),
        (
            'Дата регистрации и последнего входа',
            {'fields': ('last_login', 'date_joined')},
        ),
    )

    add_fieldsets = (
        (
            None,
            {
                'classes': ('wide',),
                'fields': (
                    'username',
                    'email',
                    'password1',
                    'password2',
                    'role',
                ),
            },
        ),
    )


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    search_fields = (
        'name',
        'slug',
    )
    list_filter = ('slug',)


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    search_fields = (
        'name',
        'slug',
    )
    list_filter = ('slug',)


@admin.register(Title)
class TitleAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'year',
        'category',
        'description',
        'get_genres',
    )
    search_fields = (
        'name',
        'category__name',
        'genre__name',
    )
    list_filter = ('category', 'genre')

    @admin.display(description='Жанры')
    def get_genres(self, obj):
        return ', '.join([genre.name for genre in obj.genre.all()])


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'text',
        'author',
        'score',
        'pub_date',
    )
    search_fields = (
        'title__name',
        'author__username',
        'text',
    )
    list_filter = ('author',)


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = (
        'review',
        'text',
        'author',
    )
    search_fields = (
        'review__title__name',
        'author__username',
        'text',
    )
    list_filter = ('author',)
