from django.core.exceptions import ValidationError
from django.core.paginator import Paginator

PAGE_SIZE = 12

GITHUB_DOMAIN = "github.com"


def paginate(queryset, page_number, per_page=PAGE_SIZE):
    paginator = Paginator(queryset, per_page)
    return paginator.get_page(page_number)


def validate_github_url(url):
    if url and GITHUB_DOMAIN not in url:
        raise ValidationError("URL должен быть на github.com")
