"""
YouTube Data API wrapper with quota management and Shorts detection.

Handles:
- Channel lookups
- Playlist fetching
- Video details (duration, metadata)
- YouTube Shorts detection (≤180 seconds)
"""

from typing import List, Dict, Optional
import isodate
from googleapiclient.discovery import build


class YouTubeAPI:
    """YouTube Data API v3 wrapper with Shorts detection."""

    def __init__(self, api_key: str):
        """
        Initialize YouTube API client.

        Args:
            api_key: YouTube Data API v3 key
        """
        self.youtube = build('youtube', 'v3', developerKey=api_key)
        self.quota_used = 0

    def get_uploads_playlist_id(self, channel_id: str) -> str:
        """
        Get uploads playlist ID for a channel.

        Cost: 1 unit

        Args:
            channel_id: YouTube channel ID

        Returns:
            Uploads playlist ID (starts with 'UU')

        Raises:
            Exception: If channel not found
        """
        request = self.youtube.channels().list(
            part='contentDetails',
            id=channel_id
        )
        response = request.execute()
        self.quota_used += 1

        if not response['items']:
            raise Exception(f"Channel not found: {channel_id}")

        return response['items'][0]['contentDetails']['relatedPlaylists']['uploads']

    def get_recent_videos(
        self,
        playlist_id: str,
        max_results: int = 50
    ) -> List[Dict]:
        """
        Get recent videos from uploads playlist.

        Cost: 1 unit

        Args:
            playlist_id: Playlist ID (from get_uploads_playlist_id)
            max_results: Maximum videos to fetch (1-50)

        Returns:
            List of video info dicts with keys:
            - video_id: YouTube video ID
            - title: Video title
            - published_at: Publication timestamp
        """
        request = self.youtube.playlistItems().list(
            part='snippet',
            playlistId=playlist_id,
            maxResults=min(max_results, 50)
        )
        response = request.execute()
        self.quota_used += 1

        videos = []
        for item in response['items']:
            video_info = {
                'video_id': item['snippet']['resourceId']['videoId'],
                'title': item['snippet']['title'],
                'published_at': item['snippet']['publishedAt']
            }
            videos.append(video_info)

        return videos

    def get_video_details(self, video_ids: List[str]) -> List[Dict]:
        """
        Get detailed video information including duration.

        Cost: 1 unit per 50 videos (batched)

        Args:
            video_ids: List of YouTube video IDs (max 50)

        Returns:
            List of video detail dicts with contentDetails and snippet
        """
        if not video_ids:
            return []

        # Batch up to 50 video IDs
        request = self.youtube.videos().list(
            part='contentDetails,snippet',
            id=','.join(video_ids[:50])
        )
        response = request.execute()
        self.quota_used += 1

        return response.get('items', [])

    def is_short(self, video_details: Dict) -> bool:
        """
        Check if video is a YouTube Short based on duration.

        YouTube Shorts criteria (as of 2025):
        - Duration ≤ 180 seconds (3 minutes)
        - Previously ≤ 60 seconds until October 2024

        Args:
            video_details: Video details dict from get_video_details()

        Returns:
            True if video is a Short, False otherwise
        """
        try:
            duration_str = video_details['contentDetails']['duration']
            # Parse ISO 8601 duration (e.g., PT1M30S = 1 min 30 sec)
            duration = isodate.parse_duration(duration_str)

            # Shorts: ≤180 seconds
            return duration.total_seconds() <= 180
        except (KeyError, ValueError):
            # If we can't determine duration, assume it's not a Short
            return False

    def filter_shorts(
        self,
        videos: List[Dict],
        video_details: List[Dict]
    ) -> List[Dict]:
        """
        Filter out YouTube Shorts from video list.

        Args:
            videos: List of video info dicts (from get_recent_videos)
            video_details: List of video details (from get_video_details)

        Returns:
            Filtered list excluding Shorts
        """
        # Create lookup map: video_id -> details
        details_map = {v['id']: v for v in video_details}

        filtered = []
        for video in videos:
            video_id = video['video_id']
            details = details_map.get(video_id)

            if details and self.is_short(details):
                # Skip Shorts
                continue

            filtered.append(video)

        return filtered

    def get_quota_used(self) -> int:
        """
        Get total quota units used by this instance.

        Returns:
            Total units consumed
        """
        return self.quota_used
