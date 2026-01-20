"""URL metadata extraction utilities.

This module provides functionality to fetch and extract metadata from URLs,
including title, description, and favicon information.
"""

import asyncio
import re
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup, Tag

from app.config import settings


@dataclass
class URLMetadata:
    """Extracted metadata from a URL.

    Attributes:
        title: Page title from <title> or Open Graph tags.
        description: Page description from meta tags or Open Graph.
        favicon_url: URL to the site's favicon.
    """

    title: str | None = None
    description: str | None = None
    favicon_url: str | None = None


# Common user agent to avoid being blocked
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)


def _extract_title(soup: BeautifulSoup) -> str | None:
    """Extract page title from HTML.

    Checks in order:
    1. Open Graph title (og:title)
    2. Twitter card title (twitter:title)
    3. Standard <title> tag

    Args:
        soup: Parsed HTML document.

    Returns:
        Page title or None if not found.
    """
    # Try Open Graph title first (usually cleaner)
    og_title = soup.find("meta", property="og:title")
    if og_title and isinstance(og_title, Tag) and og_title.get("content"):
        return str(og_title["content"]).strip()

    # Try Twitter card title
    twitter_title = soup.find("meta", attrs={"name": "twitter:title"})
    if twitter_title and isinstance(twitter_title, Tag) and twitter_title.get("content"):
        return str(twitter_title["content"]).strip()

    # Fall back to <title> tag
    title_tag = soup.find("title")
    if title_tag and isinstance(title_tag, Tag) and title_tag.string:
        return title_tag.string.strip()

    return None


def _extract_description(soup: BeautifulSoup) -> str | None:
    """Extract page description from HTML.

    Checks in order:
    1. Open Graph description (og:description)
    2. Twitter card description (twitter:description)
    3. Standard meta description

    Args:
        soup: Parsed HTML document.

    Returns:
        Page description or None if not found.
    """
    # Try Open Graph description first
    og_desc = soup.find("meta", property="og:description")
    if og_desc and isinstance(og_desc, Tag) and og_desc.get("content"):
        return str(og_desc["content"]).strip()[:2000]  # Limit length

    # Try Twitter card description
    twitter_desc = soup.find("meta", attrs={"name": "twitter:description"})
    if twitter_desc and isinstance(twitter_desc, Tag) and twitter_desc.get("content"):
        return str(twitter_desc["content"]).strip()[:2000]

    # Fall back to standard meta description
    meta_desc = soup.find("meta", attrs={"name": "description"})
    if meta_desc and isinstance(meta_desc, Tag) and meta_desc.get("content"):
        return str(meta_desc["content"]).strip()[:2000]

    return None


def _extract_favicon(soup: BeautifulSoup, base_url: str) -> str | None:
    """Extract favicon URL from HTML.

    Checks in order:
    1. Apple touch icon (usually higher quality)
    2. Standard favicon link
    3. Default /favicon.ico path

    Args:
        soup: Parsed HTML document.
        base_url: Base URL for resolving relative paths.

    Returns:
        Absolute favicon URL or None if not found.
    """
    # Parse base URL to get origin
    parsed = urlparse(base_url)
    origin = f"{parsed.scheme}://{parsed.netloc}"

    # Try Apple touch icon first (higher quality)
    apple_icon = soup.find("link", rel=re.compile(r"apple-touch-icon", re.I))
    if apple_icon and isinstance(apple_icon, Tag) and apple_icon.get("href"):
        return urljoin(origin, str(apple_icon["href"]))

    # Try standard favicon
    favicon = soup.find("link", rel=re.compile(r"(shortcut )?icon", re.I))
    if favicon and isinstance(favicon, Tag) and favicon.get("href"):
        return urljoin(origin, str(favicon["href"]))

    # Try Open Graph image as fallback (some sites use this)
    og_image = soup.find("meta", property="og:image")
    if og_image and isinstance(og_image, Tag) and og_image.get("content"):
        # Only use if it looks like a small icon
        content = str(og_image["content"])
        if "icon" in content.lower() or "logo" in content.lower():
            return content if content.startswith("http") else urljoin(origin, content)

    # Default to /favicon.ico (most sites have this)
    return f"{origin}/favicon.ico"


async def fetch_url_metadata(
    url: str,
    timeout: float | None = None,
) -> URLMetadata:
    """Fetch and extract metadata from a URL.

    This function makes an HTTP request to the given URL, parses the HTML,
    and extracts title, description, and favicon information.

    Args:
        url: The URL to fetch metadata from.
        timeout: Request timeout in seconds. Defaults to settings value.

    Returns:
        URLMetadata with extracted information. Fields may be None if
        extraction fails or the data is not available.

    Example:
        >>> metadata = await fetch_url_metadata("https://github.com")
        >>> print(metadata.title)
        "GitHub: Let's build from here"
    """
    if timeout is None:
        timeout = settings.metadata_fetch_timeout

    metadata = URLMetadata()

    try:
        async with httpx.AsyncClient(
            timeout=timeout,
            follow_redirects=True,
            headers={"User-Agent": DEFAULT_USER_AGENT},
        ) as client:
            response = await client.get(url)
            response.raise_for_status()

            # Only parse HTML content
            content_type = response.headers.get("content-type", "")
            if "text/html" not in content_type.lower():
                return metadata

            # Parse HTML
            soup = BeautifulSoup(response.text, "html.parser")

            # Extract metadata
            metadata.title = _extract_title(soup)
            metadata.description = _extract_description(soup)
            metadata.favicon_url = _extract_favicon(soup, str(response.url))

    except httpx.TimeoutException:
        # Timeout is expected for slow sites - return empty metadata
        pass
    except httpx.HTTPStatusError:
        # HTTP errors (4xx, 5xx) - return empty metadata
        pass
    except httpx.RequestError:
        # Network errors - return empty metadata
        pass
    except Exception:
        # Any other parsing errors - return empty metadata
        pass

    return metadata


async def fetch_url_metadata_batch(
    urls: list[str],
    timeout: float | None = None,
    max_concurrent: int = 5,
) -> dict[str, URLMetadata]:
    """Fetch metadata for multiple URLs concurrently.

    Args:
        urls: List of URLs to fetch metadata from.
        timeout: Request timeout per URL in seconds.
        max_concurrent: Maximum number of concurrent requests.

    Returns:
        Dictionary mapping URLs to their extracted metadata.

    Example:
        >>> urls = ["https://github.com", "https://google.com"]
        >>> results = await fetch_url_metadata_batch(urls)
        >>> for url, metadata in results.items():
        ...     print(f"{url}: {metadata.title}")
    """
    semaphore = asyncio.Semaphore(max_concurrent)

    async def fetch_with_semaphore(url: str) -> tuple[str, URLMetadata]:
        async with semaphore:
            metadata = await fetch_url_metadata(url, timeout)
            return url, metadata

    tasks = [fetch_with_semaphore(url) for url in urls]
    results = await asyncio.gather(*tasks)

    return dict(results)
