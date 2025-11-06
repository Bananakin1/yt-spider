"""
Video processing utilities for filtering and validation.

Handles:
- Filtering already-processed videos
- Video validation
- Batch processing helpers
"""

from typing import List, Dict, Set


class VideoProcessor:
    """Video filtering and validation utilities."""

    @staticmethod
    def filter_processed(
        videos: List[Dict],
        processed_ids: Set[str]
    ) -> List[Dict]:
        """
        Filter out already-processed videos.

        Args:
            videos: List of video info dicts (must have 'video_id' key)
            processed_ids: Set of already-processed video IDs

        Returns:
            List of unprocessed videos
        """
        return [v for v in videos if v['video_id'] not in processed_ids]

    @staticmethod
    def validate_video(video: Dict) -> bool:
        """
        Validate that video dict has required fields.

        Args:
            video: Video info dict

        Returns:
            True if valid, False otherwise
        """
        required_fields = ['video_id', 'title']
        return all(field in video for field in required_fields)

    @staticmethod
    def get_video_ids(videos: List[Dict]) -> List[str]:
        """
        Extract video IDs from video list.

        Args:
            videos: List of video info dicts

        Returns:
            List of video IDs
        """
        return [v['video_id'] for v in videos]

    @staticmethod
    def print_video_summary(videos: List[Dict], indent: str = "  ") -> None:
        """
        Print summary of videos (for logging).

        Args:
            videos: List of video info dicts
            indent: Indentation string for output
        """
        for i, video in enumerate(videos, 1):
            print(f"{indent}[{i}] {video['title']}")
            print(f"{indent}    ID: {video['video_id']}")
            if 'published_at' in video:
                print(f"{indent}    Published: {video['published_at']}")
