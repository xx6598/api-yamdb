# api/filters.py
from django.db.models import Q
from django_filters import rest_framework as filters
from reviews.models import Title


class TitleFilter(filters.FilterSet):
    """
    Кастомный фильтр для модели Title.

    • genre и category ищут по slug (а не по id) ─ это то, чего ждут тесты:
      /api/v1/titles/?genre=comedy&category=films
    • Поддерживается частичный поиск по name, диапазоны и сравнения по year,
      а также общий текстовый поиск (name + description) через ?search=.
    """

    # Название произведения (частичное совпадение, регистронезависимо)
    name = filters.CharFilter(
        field_name='name',
        lookup_expr='icontains',
    )

    # Точный год
    year = filters.NumberFilter(field_name='year', lookup_expr='exact')
    # Больше / меньше указанного года
    year__gt = filters.NumberFilter(field_name='year', lookup_expr='gt')
    year__lt = filters.NumberFilter(field_name='year', lookup_expr='lt')
    # Диапазон годов: ?year_range_after=2000&year_range_before=2020
    year_range = filters.RangeFilter(field_name='year')

    # Категория по slug
    category = filters.CharFilter(
        field_name='category__slug',
        lookup_expr='exact',
    )

    # Жанр по slug (можно несколько: ?genre=comedy&genre=action)
    genre = filters.CharFilter(
        field_name='genre__slug',
        lookup_expr='exact',
    )

    # Общий текстовый поиск по названию и описанию
    search = filters.CharFilter(method='filter_search')

    # Сортировка: ?ordering=year,-rating
    ordering = filters.OrderingFilter(
        fields=('name', 'year', 'rating', 'id'),
    )

    class Meta:
        model = Title
        fields = (
            'name',
            'year', 'year__gt', 'year__lt', 'year_range',
            'category', 'genre',
        )

    def filter_search(self, queryset, name, value):
        """Поиск и в name, и в description одной строкой запроса."""
        if not value:
            return queryset
        return queryset.filter(
            Q(name__icontains=value) |
            Q(description__icontains=value)
        )

    def filter_queryset(self, queryset):
        """
        Добавляем select_related / prefetch_related после применения фильтров
        для минимизации количества SQL-запросов.
        """
        queryset = super().filter_queryset(queryset)
        return queryset.select_related('category').prefetch_related('genre')
