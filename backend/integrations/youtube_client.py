"""
YouTube Data API v3 Client

Fetches videos from BriteCo's YouTube channel for the consumer newsletter.
Supports listing recent uploads and sorting by view count (popularity).
"""

import os
import requests
from typing import List, Dict, Optional
from datetime import datetime


class YouTubeClient:
    """Client for YouTube Data API v3"""

    BASE_URL = "https://www.googleapis.com/youtube/v3"
    DEFAULT_CHANNEL_ID = "UCrPdDfZ6Sk6H3GqzTCpsyyQ"  # BriteCo channel

    def __init__(self, api_key: Optional[str] = None):
        """Initialize YouTube client"""
        self.api_key = api_key or os.getenv("YOUTUBE_API_KEY")

        if self.api_key:
            print("[OK] YouTube client initialized")
        else:
            print("[WARNING] YOUTUBE_API_KEY not found - YouTube integration disabled")

    def is_available(self) -> bool:
        """Check if YouTube API is configured"""
        return bool(self.api_key)

    def get_channel_videos(
        self,
        channel_id: Optional[str] = None,
        max_results: int = 20,
        page_token: Optional[str] = None
    ) -> dict:
        """
        Get recent videos from a YouTube channel.

        Uses the search endpoint to list recent uploads, then fetches
        full video details (view counts, etc.) in a second call.

        Args:
            channel_id: YouTube channel ID (defaults to BriteCo)
            max_results: Maximum number of videos to return (max 50)
            page_token: Token for next page of results

        Returns:
            Dict with 'videos' list and optional 'next_page_token'
        """
        if not self.is_available():
            print("[YouTube] API key not configured")
            return {"videos": [], "next_page_token": None}

        channel_id = channel_id or self.DEFAULT_CHANNEL_ID
        max_results = min(max_results, 50)

        try:
            # Step 1: Search for channel's recent videos
            search_params = {
                "key": self.api_key,
                "channelId": channel_id,
                "part": "snippet",
                "order": "date",
                "type": "video",
                "maxResults": max_results,
            }
            if page_token:
                search_params["pageToken"] = page_token

            print(f"[YouTube] Fetching videos for channel {channel_id}...")
            response = requests.get(
                f"{self.BASE_URL}/search",
                params=search_params,
                timeout=15
            )

            if response.status_code != 200:
                print(f"[YouTube] Search API error: {response.status_code} - {response.text[:200]}")
                return {"videos": [], "next_page_token": None}

            search_data = response.json()
            items = search_data.get("items", [])
            next_page_token = search_data.get("nextPageToken")

            if not items:
                print("[YouTube] No videos found for channel")
                return {"videos": [], "next_page_token": None}

            # Extract video IDs
            video_ids = [
                item["id"]["videoId"]
                for item in items
                if item.get("id", {}).get("videoId")
            ]

            if not video_ids:
                print("[YouTube] No video IDs extracted from search results")
                return {"videos": [], "next_page_token": None}

            # Step 2: Get full video details (view counts, duration, etc.)
            videos = self._get_video_details(video_ids)

            print(f"[YouTube] Found {len(videos)} videos (next_page: {'yes' if next_page_token else 'no'})")
            return {"videos": videos, "next_page_token": next_page_token}

        except requests.exceptions.Timeout:
            print("[YouTube] Request timed out")
            return {"videos": [], "next_page_token": None}
        except requests.exceptions.RequestException as e:
            print(f"[YouTube] Request error: {e}")
            return {"videos": [], "next_page_token": None}
        except Exception as e:
            print(f"[YouTube] Error: {e}")
            import traceback
            traceback.print_exc()
            return {"videos": [], "next_page_token": None}

    def _get_video_details(self, video_ids: List[str]) -> List[Dict]:
        """
        Fetch full details for a list of video IDs.

        Args:
            video_ids: List of YouTube video IDs

        Returns:
            List of video detail dicts
        """
        if not video_ids:
            return []

        # YouTube API allows up to 50 IDs per request
        params = {
            "key": self.api_key,
            "id": ",".join(video_ids[:50]),
            "part": "snippet,statistics,contentDetails",
        }

        response = requests.get(
            f"{self.BASE_URL}/videos",
            params=params,
            timeout=15
        )

        if response.status_code != 200:
            print(f"[YouTube] Videos API error: {response.status_code}")
            return []

        data = response.json()
        videos = []

        for item in data.get("items", []):
            snippet = item.get("snippet", {})
            stats = item.get("statistics", {})
            content = item.get("contentDetails", {})

            # Get best available thumbnail
            thumbnails = snippet.get("thumbnails", {})
            thumbnail_url = (
                thumbnails.get("maxres", {}).get("url")
                or thumbnails.get("high", {}).get("url")
                or thumbnails.get("medium", {}).get("url")
                or thumbnails.get("default", {}).get("url", "")
            )

            # Parse published date
            published_at = snippet.get("publishedAt", "")
            published_date = ""
            published_age = ""
            if published_at:
                try:
                    pub_dt = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
                    published_date = pub_dt.strftime("%Y-%m-%d")
                    published_age = self._format_age(pub_dt)
                except (ValueError, TypeError):
                    published_date = published_at[:10] if len(published_at) >= 10 else ""

            # Parse view count
            view_count = int(stats.get("viewCount", 0))

            videos.append({
                "video_id": item["id"],
                "title": snippet.get("title", ""),
                "description": snippet.get("description", ""),
                "thumbnail_url": thumbnail_url,
                "channel_title": snippet.get("channelTitle", ""),
                "published_at": published_at,
                "published_date": published_date,
                "published_age": published_age,
                "view_count": view_count,
                "view_count_formatted": self._format_count(view_count),
                "like_count": int(stats.get("likeCount", 0)),
                "comment_count": int(stats.get("commentCount", 0)),
                "duration": content.get("duration", ""),
                "duration_formatted": self._format_duration(content.get("duration", "")),
                "url": f"https://www.youtube.com/watch?v={item['id']}",
                "embed_url": f"https://www.youtube.com/embed/{item['id']}",
                "short_url": f"https://youtu.be/{item['id']}",
            })

        return videos

    def get_videos_by_popularity(
        self,
        channel_id: Optional[str] = None,
        max_results: int = 10
    ) -> dict:
        """
        Get channel videos sorted by view count (most popular first).

        Args:
            channel_id: YouTube channel ID (defaults to BriteCo)
            max_results: Number of top videos to return

        Returns:
            Dict with 'videos' sorted by view count and 'next_page_token'
        """
        # Fetch more than needed so we have a good pool to sort
        result = self.get_channel_videos(
            channel_id=channel_id,
            max_results=min(max_results * 2, 50)
        )

        videos = result.get("videos", []) if isinstance(result, dict) else result
        # Sort by view count descending
        videos.sort(key=lambda v: v.get("view_count", 0), reverse=True)

        return {"videos": videos[:max_results], "next_page_token": result.get("next_page_token") if isinstance(result, dict) else None}

    def get_videos_sorted(
        self,
        sort: str = "recent",
        channel_id: Optional[str] = None,
        max_results: int = 10,
        page_token: Optional[str] = None
    ) -> dict:
        """
        Get channel videos with flexible sorting.

        Args:
            sort: "recent" (newest first) or "popular" (most views first)
            channel_id: YouTube channel ID
            max_results: Number of videos to return
            page_token: Token for next page

        Returns:
            Dict with 'videos' list and optional 'next_page_token'
        """
        if sort == "popular":
            return self.get_videos_by_popularity(channel_id, max_results)
        else:
            result = self.get_channel_videos(channel_id, max_results, page_token)
            videos = result.get("videos", []) if isinstance(result, dict) else result
            return {"videos": videos[:max_results], "next_page_token": result.get("next_page_token") if isinstance(result, dict) else None}

    def get_video_by_url(self, url: str) -> Optional[Dict]:
        """
        Get video details from a YouTube URL.

        Supports formats:
        - https://www.youtube.com/watch?v=VIDEO_ID
        - https://youtu.be/VIDEO_ID
        - https://youtube.com/shorts/VIDEO_ID

        Args:
            url: YouTube video URL

        Returns:
            Video detail dict or None
        """
        video_id = self._extract_video_id(url)
        if not video_id:
            print(f"[YouTube] Could not extract video ID from URL: {url}")
            return None

        videos = self._get_video_details([video_id])
        return videos[0] if videos else None

    @staticmethod
    def _extract_video_id(url: str) -> Optional[str]:
        """Extract video ID from various YouTube URL formats"""
        from urllib.parse import urlparse, parse_qs

        if not url:
            return None

        try:
            parsed = urlparse(url.strip())

            # youtu.be/VIDEO_ID
            if parsed.netloc in ("youtu.be", "www.youtu.be"):
                return parsed.path.lstrip("/").split("/")[0]

            # youtube.com/watch?v=VIDEO_ID
            if parsed.netloc in ("youtube.com", "www.youtube.com", "m.youtube.com"):
                if parsed.path == "/watch":
                    qs = parse_qs(parsed.query)
                    return qs.get("v", [None])[0]

                # youtube.com/shorts/VIDEO_ID
                if parsed.path.startswith("/shorts/"):
                    return parsed.path.split("/shorts/")[1].split("/")[0].split("?")[0]

                # youtube.com/embed/VIDEO_ID
                if parsed.path.startswith("/embed/"):
                    return parsed.path.split("/embed/")[1].split("/")[0].split("?")[0]

            return None
        except Exception:
            return None

    @staticmethod
    def _format_count(count: int) -> str:
        """Format view/like count for display (e.g., 1.2K, 3.4M)"""
        if count >= 1_000_000:
            return f"{count / 1_000_000:.1f}M"
        elif count >= 1_000:
            return f"{count / 1_000:.1f}K"
        return str(count)

    @staticmethod
    def _format_duration(iso_duration: str) -> str:
        """Convert ISO 8601 duration (PT1H2M3S) to readable format (1:02:03)"""
        if not iso_duration:
            return ""

        import re
        match = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", iso_duration)
        if not match:
            return iso_duration

        hours = int(match.group(1) or 0)
        minutes = int(match.group(2) or 0)
        seconds = int(match.group(3) or 0)

        if hours > 0:
            return f"{hours}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes}:{seconds:02d}"

    @staticmethod
    def _format_age(pub_dt: datetime) -> str:
        """Format publication date as relative age"""
        from datetime import timezone
        now = datetime.now(timezone.utc)
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
_youtube_client = None


def get_youtube_client() -> YouTubeClient:
    """Get or create YouTube client singleton"""
    global _youtube_client
    if _youtube_client is None:
        _youtube_client = YouTubeClient()
    return _youtube_client
