from django.core.paginator import Paginator


def get_page(request, queryset, per_page):
    """Возвращает страницу списка по номеру из GET-параметра page."""
    return Paginator(queryset, per_page).get_page(request.GET.get("page"))
