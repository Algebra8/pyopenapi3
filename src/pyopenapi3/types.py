from typing import Pattern
import re
from enum import Enum

from pydantic import AnyUrl  # type: ignore
from pydantic.errors import UrlExtraError  # type: ignore


# Taken from Pydantic:
# We use the same regex compilation that is used in Pydantic,
# except we include a capturing group for non-numeric ports.
_url_regex_cache = None


def url_regex() -> Pattern[str]:
    global _url_regex_cache
    if _url_regex_cache is None:
        _url_regex_cache = re.compile(
            # scheme https://tools.ietf.org/html/rfc3986#appendix-A
            r'(?:(?P<scheme>[a-z][a-z0-9+\-.]+)://)?'
            # user info
            r'(?:(?P<user>[^\s:/]*)(?::(?P<password>[^\s/]*))?@)?'
            r'(?:'
            # ipv4
            r'(?P<ipv4>(?:\d{1,3}\.){3}\d{1,3})|'
            # ipv6
            r'(?P<ipv6>\[[A-F0-9]*:[A-F0-9:]+\])|'
            # domain, validation occurs later
            r'(?P<domain>[^\s/:?#]+)'
            r')?'
            # port
            r'(?::(?P<port>(\d+|({[a-zA-Z0-9_]*}))))?'
            # path
            r'(?P<path>/[^\s?#]*)?'
            # query
            r'(?:\?(?P<query>[^\s#]+))?'
            # fragment
            r'(?:#(?P<fragment>\S+))?',
            re.IGNORECASE,
        )
    return _url_regex_cache


class VariableAnyUrl(str):
    """A Pydantic `AnyUrl` that allows parameters.

    An examples is
    "https://{username}.gigantic-server.com:{someport}/{basePath}"

    `AnyUrl` will properly validate all of the url except for the port:
    it will expect the port to be a digit. Therefore, `VariableAnyUrl`
    **should** be a wrapper for `AnyUrl` in all ways except for allowing
    `port` to be something other than a digit.
    """

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, url):
        m = url_regex().match(url)
        parts = m.groupdict()
        port = parts['port']
        if port is not None:
            try:
                int(port)
            except ValueError:
                # AnyUrl's `validate_parts` will try to cast this
                # to an int; we do this here because we know
                # it is a variable.
                parts['port'] = '8000'
        parts = AnyUrl.validate_parts(parts)
        # Here we expect parts to have been validated,
        # so we can revert port back to what it was.
        parts['port'] = port
        host, tld, host_type, rebuild = AnyUrl.validate_host(parts)
        if m.end() != len(url):
            raise UrlExtraError(extra=url[m.end():])
        return AnyUrl(
            None if rebuild else url,
            scheme=parts['scheme'],
            user=parts['user'],
            password=parts['password'],
            host=host,
            tld=tld,
            host_type=host_type,
            port=parts['port'],
            path=parts['path'],
            query=parts['query'],
            fragment=parts['fragment'],
        )


# Constants for media type str definitions.
class MediaTypeEnum(str, Enum):

    JSON = "application/json"
    XML = "application/xml"
    PDF = "application/pdf"
    URL_ENCODED = "application/x-www-form-urlencoded"
    MULTIPART = "multipart/form-data"
    PLAIN = "text/plain; charset=utf-8"
    HTML = "text/html"
    PNG = "image/png"
