"""
File storage utilities for transcripts and metadata.

Handles:
- Saving transcripts with metadata headers
- Loading/saving processed video lists
- Directory management
"""

from pathlib import Path
from datetime import datetime
from typing import List
import json


class StorageManager:
    """Manage file storage for transcripts and metadata."""

    def __init__(self, base_dir: Path):
        """
        Initialize storage manager.

        Args:
            base_dir: Base directory for storage (e.g., 'backlog_JLC')
        """
        self.base_dir = Path(base_dir)
        self.transcripts_dir = self.base_dir / 'transcripts'
        self.metadata_dir = self.base_dir / 'metadata'

        # Create directories if they don't exist
        self.transcripts_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_dir.mkdir(parents=True, exist_ok=True)

    def save_transcript(
        self,
        video_id: str,
        video_title: str,
        transcript_text: str,
        language: str,
        transcript_type: str = 'auto',
        published_at: str = None
    ) -> Path:
        """
        Save transcript to file with metadata header.

        Filename format: {video_id}_{timestamp}.txt

        Args:
            video_id: YouTube video ID
            video_title: Video title
            transcript_text: Full transcript text
            language: Language code ('en' or 'es')
            transcript_type: 'manual' or 'auto'
            published_at: Video publication timestamp (optional)

        Returns:
            Path to saved file
        """
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        filename = f"{video_id}_{timestamp}.txt"
        filepath = self.transcripts_dir / filename

        with open(filepath, 'w', encoding='utf-8') as f:
            # Write metadata header
            f.write(f"Video ID: {video_id}\n")
            f.write(f"Title: {video_title}\n")
            f.write(f"Language: {language}\n")
            f.write(f"Type: {transcript_type}\n")
            f.write(f"Downloaded: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            if published_at:
                f.write(f"Published: {published_at}\n")
            f.write(f"{'='*80}\n\n")

            # Write transcript
            f.write(transcript_text)

        return filepath

    def load_processed_videos(self, metadata_file: str = 'processed_videos.json') -> List[str]:
        """
        Load list of processed video IDs.

        Args:
            metadata_file: Filename in metadata directory

        Returns:
            List of video IDs (empty if file doesn't exist)
        """
        filepath = self.metadata_dir / metadata_file

        if not filepath.exists():
            return []

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            print(f"    [WARNING] Could not parse {metadata_file}, starting fresh")
            return []

    def save_processed_videos(
        self,
        video_ids: List[str],
        metadata_file: str = 'processed_videos.json'
    ) -> None:
        """
        Save list of processed video IDs.

        Args:
            video_ids: List of video IDs
            metadata_file: Filename in metadata directory
        """
        filepath = self.metadata_dir / metadata_file

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(video_ids, f, indent=2)

    def get_transcript_count(self) -> int:
        """
        Count number of saved transcripts.

        Returns:
            Number of .txt files in transcripts directory
        """
        return len(list(self.transcripts_dir.glob('*.txt')))

    def get_latest_transcripts(self, count: int = 10) -> List[Path]:
        """
        Get paths to most recently saved transcripts.

        Args:
            count: Number of transcripts to return

        Returns:
            List of transcript file paths, sorted by modification time (newest first)
        """
        transcripts = sorted(
            self.transcripts_dir.glob('*.txt'),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )
        return transcripts[:count]
