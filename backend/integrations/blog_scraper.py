"""
BriteCo Blog Scraper

Fetches recent blog posts from brite.co/blog using the WordPress REST API.
Used for the consumer newsletter "Two Blog Articles" section.
"""

import os
import re
import requests
from typing import List, Dict, Optional
from datetime import datetime
from html import unescape


class BlogScraper:
    """Client for fetching BriteCo blog posts via WordPress REST API"""

    BASE_URL = "https://brite.co/wp-json/wp/v2"
    BLOG_URL = "https://brite.co/blog"

    def __init__(self):
        """Initialize blog scraper"""
        print("[OK] Blog scraper initialized (brite.co/blog)")

    def get_recent_posts(
        self,
        count: int = 10,
        category: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 1
    ) -> List[Dict]:
        """
        Fetch recent blog posts from brite.co.

        Args:
            count: Number of posts to return (max 100)
            category: Optional category slug to filter by
            search: Optional search term to filter posts
            page: Page number for pagination (default 1)

        Returns:
            List of post dicts with title, url, excerpt, image, date, etc.
        """
        try:
            params = {
                "per_page": min(count, 100),
                "page": page,
                "orderby": "date",
                "order": "desc",
                "status": "publish",
                "_embed": "",  # Include featured images and author info
            }

            if search:
                params["search"] = search

            if category:
                # First resolve category slug to ID
                cat_id = self._get_category_id(category)
                if cat_id:
                    params["categories"] = cat_id

            print(f"[Blog] Fetching {count} recent posts from brite.co/blog...")
            response = requests.get(
                f"{self.BASE_URL}/posts",
                params=params,
                timeout=15
            )

            if response.status_code != 200:
                print(f"[Blog] API error: {response.status_code} - {response.text[:200]}")
                return []

            posts_data = response.json()

            if not isinstance(posts_data, list):
                print("[Blog] Unexpected response format")
                return []

            posts = []
            for item in posts_data:
                post = self._parse_post(item)
                if post:
                    posts.append(post)

            print(f"[Blog] Found {len(posts)} posts")
            return posts

        except requests.exceptions.Timeout:
            print("[Blog] Request timed out")
            return []
        except requests.exceptions.RequestException as e:
            print(f"[Blog] Request error: {e}")
            return []
        except Exception as e:
            print(f"[Blog] Error: {e}")
            import traceback
            traceback.print_exc()
            return []

    def get_categories(self) -> List[Dict]:
        """
        Fetch available blog categories.

        Returns:
            List of category dicts with id, name, slug, count
        """
        try:
            response = requests.get(
                f"{self.BASE_URL}/categories",
                params={"per_page": 100, "orderby": "count", "order": "desc"},
                timeout=10
            )

            if response.status_code != 200:
                return []

            categories = []
            for cat in response.json():
                if cat.get("count", 0) > 0:
                    categories.append({
                        "id": cat["id"],
                        "name": cat.get("name", ""),
                        "slug": cat.get("slug", ""),
                        "count": cat.get("count", 0),
                    })

            return categories

        except Exception as e:
            print(f"[Blog] Error fetching categories: {e}")
            return []

    def search_posts(self, query: str, count: int = 10) -> List[Dict]:
        """
        Search blog posts by keyword.

        Args:
            query: Search term
            count: Max results

        Returns:
            List of matching post dicts
        """
        return self.get_recent_posts(count=count, search=query)

    def _parse_post(self, item: dict) -> Optional[Dict]:
        """Parse a WordPress post API item into our standard format"""
        try:
            post_id = item.get("id")
            title_raw = item.get("title", {}).get("rendered", "")
            title = self._clean_html(title_raw)

            if not title:
                return None

            url = item.get("link", "")
            slug = item.get("slug", "")

            # Extract excerpt (clean HTML tags)
            excerpt_raw = item.get("excerpt", {}).get("rendered", "")
            excerpt = self._clean_html(excerpt_raw)
            # Trim to reasonable length
            if len(excerpt) > 200:
                excerpt = excerpt[:197].rsplit(" ", 1)[0] + "..."

            # Parse date
            date_str = item.get("date", "")
            published_date = ""
            published_age = ""
            if date_str:
                try:
                    pub_dt = datetime.fromisoformat(date_str)
                    published_date = pub_dt.strftime("%Y-%m-%d")
                    published_age = self._format_age(pub_dt)
                except (ValueError, TypeError):
                    published_date = date_str[:10] if len(date_str) >= 10 else ""

            # Extract featured image from _embedded data
            featured_image_url = ""
            embedded = item.get("_embedded", {})
            featured_media = embedded.get("wp:featuredmedia", [])
            if featured_media and isinstance(featured_media, list):
                media_item = featured_media[0]
                # Try to get a good-sized image (medium_large or full)
                media_details = media_item.get("media_details", {})
                sizes = media_details.get("sizes", {})

                # Prefer medium_large (768px) for newsletter cards
                for size_key in ["medium_large", "large", "full", "medium"]:
                    if size_key in sizes:
                        featured_image_url = sizes[size_key].get("source_url", "")
                        break

                # Fallback to source_url
                if not featured_image_url:
                    featured_image_url = media_item.get("source_url", "")

            # Extract author name from _embedded data
            author_name = ""
            author_data = embedded.get("author", [])
            if author_data and isinstance(author_data, list):
                author_name = author_data[0].get("name", "")

            # Extract category names from _embedded data
            categories = []
            terms = embedded.get("wp:term", [])
            if terms and isinstance(terms, list):
                for term_group in terms:
                    if isinstance(term_group, list):
                        for term in term_group:
                            if term.get("taxonomy") == "category":
                                categories.append(term.get("name", ""))

            # Extract Yoast SEO description if available
            yoast = item.get("yoast_head_json", {})
            meta_description = yoast.get("description", "")
            og_image = ""
            og_images = yoast.get("og_image", [])
            if og_images and isinstance(og_images, list):
                og_image = og_images[0].get("url", "")

            # Use OG image as fallback for featured image
            if not featured_image_url and og_image:
                featured_image_url = og_image

            return {
                "id": post_id,
                "title": title,
                "url": url,
                "slug": slug,
                "excerpt": excerpt,
                "meta_description": meta_description or excerpt,
                "featured_image_url": featured_image_url,
                "author": author_name,
                "published_date": published_date,
                "published_age": published_age,
                "categories": categories,
            }

        except Exception as e:
            print(f"[Blog] Error parsing post: {e}")
            return None

    def _get_category_id(self, slug: str) -> Optional[int]:
        """Resolve category slug to ID"""
        try:
            response = requests.get(
                f"{self.BASE_URL}/categories",
                params={"slug": slug},
                timeout=10
            )
            if response.status_code == 200:
                cats = response.json()
                if cats:
                    return cats[0].get("id")
        except Exception:
            pass
        return None

    @staticmethod
    def _clean_html(html_str: str) -> str:
        """Remove HTML tags and decode entities"""
        if not html_str:
            return ""
        # Remove HTML tags
        text = re.sub(r"<[^>]+>", "", html_str)
        # Decode HTML entities
        text = unescape(text)
        # Normalize whitespace
        text = re.sub(r"\s+", " ", text).strip()
        return text

    @staticmethod
    def _format_age(pub_dt: datetime) -> str:
        """Format publication date as relative age"""
        now = datetime.now()
        delta = now - pub_dt

        days = delta.days
        if days == 0:
            return "today"
        elif days == 1:
            return "1 day ago"
        elif days < 7:
            return f"{days} days ago"
        elif days < 30:
            weeks = days // 7
            return f"{weeks} week{'s' if weeks > 1 else ''} ago"
        elif days < 365:
            months = days // 30
            return f"{months} month{'s' if months > 1 else ''} ago"
        else:
            years = days // 365
            return f"{years} year{'s' if years > 1 else ''} ago"


# Singleton instance
_blog_scraper = None


def get_blog_scraper() -> BlogScraper:
    """Get or create blog scraper singleton"""
    global _blog_scraper
    if _blog_scraper is None:
        _blog_scraper = BlogScraper()
    return _blog_scraper
