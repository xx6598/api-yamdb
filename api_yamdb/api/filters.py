from django.db.models import Q
from django_filters import rest_framework as filters

from reviews.models import Title


class TitleFilter(filters.FilterSet):
    name = filters.CharFilter(
        field_name='name',
        lookup_expr='icontains',
    )
    year = filters.NumberFilter(field_name='year', lookup_expr='exact')
    year__gt = filters.NumberFilter(field_name='year', lookup_expr='gt')
    year__lt = filters.NumberFilter(field_name='year', lookup_expr='lt')
    year_range = filters.RangeFilter(field_name='year')
    category = filters.CharFilter(
        field_name='category__slug',
        lookup_expr='exact',
    )

    genre = filters.CharFilter(
        field_name='genre__slug',
        lookup_expr='exact',
    )
    search = filters.CharFilter(method='filter_search')

    ordering = filters.OrderingFilter(
        fields=('name', 'year', 'rating', 'id'),
    )

    class Meta:
        model = Title
        fields = (
            'name',
            'year',
            'year__gt',
            'year__lt',
            'year_range',
            'category',
            'genre',
        )

    def filter_search(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(
            Q(name__icontains=value) | Q(description__icontains=value)
        )

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)
        return queryset.select_related('category').prefetch_related('genre')
