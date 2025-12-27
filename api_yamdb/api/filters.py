from django_filters import rest_framework as filters
from django.db.models import Q
from reviews.models import Title, Category, Genre


class TitleFilter(filters.FilterSet):
    """Расширенный фильтр для произведений (Title)."""

    # Фильтрация по названию произведения
    name = filters.CharFilter(
        field_name='name',
        lookup_expr='icontains',
        help_text='Поиск по названию произведения (частичное совпадение)'
    )

    # Фильтрация по году
    year = filters.NumberFilter(
        field_name='year',
        lookup_expr='exact',
        help_text='Точный год выпуска'
    )

    # Диапазон годов
    year_range = filters.RangeFilter(
        field_name='year',
        help_text='Диапазон годов (например: 2000,2020)'
    )

    # Фильтрация по году (больше чем)
    year__gt = filters.NumberFilter(
        field_name='year',
        lookup_expr='gt',
        help_text='Произведения после указанного года'
    )

    # Фильтрация по году (меньше чем)
    year__lt = filters.NumberFilter(
        field_name='year',
        lookup_expr='lt',
        help_text='Произведения до указанного года'
    )

    # Фильтрация по категории (slug)
    category = filters.ModelChoiceFilter(
        field_name='category',
        queryset=Category.objects.all(),
        to_field_name='slug',
        help_text='Фильтрация по slug категории'
    )

    # Фильтрация по имени категории
    category_name = filters.CharFilter(
        field_name='category__name',
        lookup_expr='icontains',
        help_text='Поиск по названию категории'
    )

    # Фильтрация по жанрам (множественный выбор)
    genre = filters.ModelMultipleChoiceFilter(
        field_name='genre',
        queryset=Genre.objects.all(),
        to_field_name='slug',
        help_text='Фильтрация по slug жанров (можно несколько через запятую)'
    )

    # Фильтрация по имени жанра
    genre_name = filters.CharFilter(
        field_name='genre__name',
        lookup_expr='icontains',
        help_text='Поиск по названию жанра'
    )

    # Общий поиск по названию и описанию
    search = filters.CharFilter(
        method='filter_search',
        help_text='Общий поиск по названию и описанию'
    )

    # Фильтрация по рейтингу (если есть поле rating)
    rating__gte = filters.NumberFilter(
        field_name='rating',
        lookup_expr='gte',
        help_text='Рейтинг не менее указанного'
    )

    rating__lte = filters.NumberFilter(
        field_name='rating',
        lookup_expr='lte',
        help_text='Рейтинг не более указанного'
    )

    # Сортировка
    ordering = filters.OrderingFilter(
        fields=(
            ('name', 'name'),
            ('year', 'year'),
            ('rating', 'rating'),
            ('id', 'id'),
        ),
        field_labels={
            'name': 'По названию',
            'year': 'По году',
            'rating': 'По рейтингу',
            'id': 'По ID',
        },
        help_text='Сортировка результатов'
    )

    def filter_search(self, queryset, name, value):
        """Метод для общего поиска."""
        if value:
            return queryset.filter(
                Q(name__icontains=value) |
                Q(description__icontains=value)
            )
        return queryset

    def filter_queryset(self, queryset):
        """Переопределение для оптимизации запросов."""
        queryset = super().filter_queryset(queryset)
        return queryset.select_related('category').prefetch_related('genre')

    class Meta:
        model = Title
        fields = {
            'name': ['icontains'],
            'year': ['exact', 'gt', 'lt', 'gte', 'lte'],
            'category': ['exact'],
            'genre': ['exact'],
        }


class CompactTitleFilter(filters.FilterSet):
    """Упрощенная версия фильтра для базового использования."""

    name = filters.CharFilter(lookup_expr='icontains')
    year = filters.NumberFilter()
    category = filters.CharFilter(field_name='category__slug')
    genre = filters.CharFilter(field_name='genre__slug')

    ordering = filters.OrderingFilter(
        fields=['name', 'year'],
    )

    class Meta:
        model = Title
        fields = ['name', 'year', 'category', 'genre']