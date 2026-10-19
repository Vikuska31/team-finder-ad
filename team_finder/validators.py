from urllib.parse import urlparse

from django.core.exceptions import ValidationError

GITHUB_DOMAIN = "github.com"


def validate_github_url(value):
    host = urlparse(value).netloc
    if host != GITHUB_DOMAIN and not host.endswith(f".{GITHUB_DOMAIN}"):
        raise ValidationError("Ссылка должна вести на GitHub.")
