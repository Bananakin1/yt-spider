"""
Test script for fetching a single video transcript.

Usage:
    python test_single_video.py <video_id>

Examples:
    python test_single_video.py dQw4w9WgXcQ
    python test_single_video.py https://www.youtube.com/watch?v=dQw4w9WgXcQ

Tests:
- Transcript availability detection
- English/Spanish language support
- Shorts detection
- Transcript fetching with retry logic
- File storage
"""

import os
import sys
import re
import time
from pathlib import Path
from dotenv import load_dotenv

# Add core modules to path (tests/ is subdirectory, core/ is in parent)
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core import YouTubeAPI, TranscriptFetcher, StorageManager

# Load environment variables
load_dotenv()

# Configuration
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')
TEST_STORAGE_DIR = PROJECT_ROOT / 'test_output'


def extract_video_id(input_str: str) -> str:
    """Extract video ID from URL or direct ID."""
    patterns = [
        r'(?:youtube\.com\/watch\?v=|youtu\.be\/)([a-zA-Z0-9_-]{11})',
        r'^([a-zA-Z0-9_-]{11})$'
    ]

    for pattern in patterns:
        match = re.search(pattern, input_str)
        if match:
            return match.group(1)

    raise ValueError(f"Could not extract video ID from: {input_str}")


def test_single_video(video_id: str):
    """Test transcript fetching for a single video."""

    print(f"\n{'='*70}")
    print(f"Testing Video: {video_id}")
    print(f"{'='*70}\n")

    if not YOUTUBE_API_KEY:
        print("ERROR: YOUTUBE_API_KEY not found in .env")
        return

    try:
        # Initialize components
        print("[1/5] Initializing components...")
        youtube_api = YouTubeAPI(YOUTUBE_API_KEY)
        fetcher = TranscriptFetcher(delay_seconds=3.0)
        storage = StorageManager(TEST_STORAGE_DIR)
        print(f"      Test storage: {TEST_STORAGE_DIR}")

        # Get video details
        print(f"\n[2/5] Fetching video details...")
        video_details = youtube_api.get_video_details([video_id])

        if not video_details:
            print(f"      [ERROR] Video not found: {video_id}")
            print(f"      Check if video ID is correct and video is public")
            return

        video = video_details[0]
        title = video['snippet']['title']
        duration_str = video['contentDetails']['duration']
        published = video['snippet']['publishedAt']

        print(f"      Title: {title}")
        print(f"      Duration: {duration_str}")
        print(f"      Published: {published}")

        # Check if Short
        is_short = youtube_api.is_short(video)
        if is_short:
            print(f"      [WARNING] This is a YouTube Short (<=180 seconds)")
            print(f"      Shorts are normally excluded from processing")

        # Check transcript availability
        print(f"\n[3/5] Checking transcript availability...")
        is_available, status_msg, lang = fetcher.check_availability(video_id)
        print(f"      Status: {status_msg}")

        if not is_available:
            print(f"\n      [RESULT] No English/Spanish transcript available")
            print(f"      Reason: {status_msg}")

            if "BLOCKED" in status_msg.upper() or "rate limit" in status_msg.lower():
                print(f"\n      {'='*66}")
                print(f"      YOUTUBE IP BLOCKING DETECTED")
                print(f"      {'='*66}")
                print(f"      Possible solutions:")
                print(f"      1. Wait 24-48 hours before trying again")
                print(f"      2. Use a different network (mobile hotspot, VPN)")
                print(f"      3. Use cookies.txt from logged-in YouTube session")
                print(f"      4. Use residential proxy service")
                print(f"      {'='*66}")

            return

        # Fetch transcript
        print(f"\n[4/5] Fetching transcript...")
        transcript_data = fetcher.fetch_with_retry(
            video_id,
            prefer_english=True,
            max_retries=3
        )

        if not transcript_data:
            print(f"\n      {'='*66}")
            print(f"      TRANSCRIPT FETCH FAILED")
            print(f"      {'='*66}")
            print(f"      The transcript exists but could not be fetched.")
            print(f"      This may be an IP blocking issue.")
            print(f"      {'='*66}")
            return

        print(f"      Language: {transcript_data['language'].upper()}")
        print(f"      Type: {transcript_data['type']}")
        print(f"      Length: {len(transcript_data['text'])} characters")

        # Preview first 500 characters
        preview = transcript_data['text'][:500]
        print(f"\n      Preview (first 500 chars):")
        print(f"      {'-'*66}")
        print(f"      {preview}...")
        print(f"      {'-'*66}")

        # Save transcript
        print(f"\n[5/5] Saving transcript...")
        filepath = storage.save_transcript(
            video_id=video_id,
            video_title=title,
            transcript_text=transcript_data['text'],
            language=transcript_data['language'],
            transcript_type=transcript_data['type'],
            published_at=published
        )

        print(f"      [SUCCESS] Saved to: {filepath}")

        # Summary
        print(f"\n{'='*70}")
        print(f"Test Results Summary")
        print(f"{'='*70}")
        print(f"  Video ID: {video_id}")
        print(f"  Title: {title}")
        print(f"  Is Short: {'Yes' if is_short else 'No'}")
        print(f"  Transcript Available: Yes")
        print(f"  Language: {transcript_data['language'].upper()}")
        print(f"  Type: {transcript_data['type']}")
        print(f"  Length: {len(transcript_data['text'])} characters")
        print(f"  Saved to: {filepath.name}")
        print(f"  API Quota Used: {youtube_api.get_quota_used()} units")
        print(f"\n{'='*70}\n")

    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python test_single_video.py <video_id_or_url>")
        print("")
        print("Examples:")
        print("  python test_single_video.py dQw4w9WgXcQ")
        print("  python test_single_video.py https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        sys.exit(1)

    try:
        video_id = extract_video_id(sys.argv[1])
        test_single_video(video_id)
    except ValueError as e:
        print(f"ERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
