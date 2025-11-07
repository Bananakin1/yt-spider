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
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound

# Add core modules to path (tests/ is subdirectory, core/ is in parent)
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core import YouTubeAPI, StorageManager

# Load environment variables
load_dotenv()

# Configuration
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')
TEST_STORAGE_DIR = PROJECT_ROOT / 'test_output'


def extract_video_id(input_str: str) -> str:
    """
    Extract video ID from URL or direct ID.

    Args:
        input_str: Video ID or YouTube URL

    Returns:
        11-character video ID
    """
    # Pattern for video ID in URL
    patterns = [
        r'(?:youtube\.com\/watch\?v=|youtu\.be\/)([a-zA-Z0-9_-]{11})',
        r'^([a-zA-Z0-9_-]{11})$'  # Direct ID
    ]

    for pattern in patterns:
        match = re.search(pattern, input_str)
        if match:
            return match.group(1)

    raise ValueError(f"Could not extract video ID from: {input_str}")


def check_transcript_availability(video_id: str):
    """
    Check transcript availability using youtube-transcript-api v1.2.3 API.

    Returns:
        Tuple of (is_available, status_message, language_code)
    """
    try:
        # Initialize API instance (correct v1.2.3 syntax)
        ytt_api = YouTubeTranscriptApi()

        print(f"      Attempting to list transcripts for {video_id}...")

        # List transcripts (instance method, not static)
        transcript_list = ytt_api.list(video_id)

        # Try English (manual first, then auto)
        try:
            manual_en = transcript_list.find_manually_created_transcript(['en', 'en-US', 'en-GB'])
            return True, f"Manual English transcript ({manual_en.language_code})", 'en'
        except NoTranscriptFound:
            pass

        try:
            auto_en = transcript_list.find_generated_transcript(['en', 'en-US', 'en-GB'])
            return True, f"Auto-generated English transcript ({auto_en.language_code})", 'en'
        except NoTranscriptFound:
            pass

        # Try Spanish (manual first, then auto)
        try:
            manual_es = transcript_list.find_manually_created_transcript(['es', 'es-ES', 'es-MX'])
            return True, f"Manual Spanish transcript ({manual_es.language_code})", 'es'
        except NoTranscriptFound:
            pass

        try:
            auto_es = transcript_list.find_generated_transcript(['es', 'es-ES', 'es-MX'])
            return True, f"Auto-generated Spanish transcript ({auto_es.language_code})", 'es'
        except NoTranscriptFound:
            pass

        # Check other languages
        available_transcripts = list(transcript_list)
        if available_transcripts:
            langs = [t.language for t in available_transcripts]
            return False, f"Only available in: {', '.join(langs)}", None

        return False, "No transcripts available", None

    except TranscriptsDisabled:
        return False, "Transcripts DISABLED by owner", None
    except Exception as e:
        error_str = str(e)
        print(f"      [DEBUG] Full error: {error_str}")

        # Check for common blocking patterns
        if "429" in error_str or "Too Many Requests" in error_str:
            return False, "Rate limited - YouTube is blocking requests (429)", None
        elif "Could not retrieve" in error_str or "HTTP Error" in error_str:
            return False, "YouTube IP BLOCKED - Cannot access transcript API", None
        elif "NoTranscriptFound" in error_str:
            return False, "No transcripts available for this video", None
        else:
            return False, f"Error: {error_str[:150]}", None


def fetch_transcript(video_id: str, prefer_english: bool = True):
    """
    Fetch transcript using youtube-transcript-api v1.2.3 API.

    Returns:
        Dict with keys: text, language, type, or None on failure
    """
    try:
        # Initialize API instance
        ytt_api = YouTubeTranscriptApi()

        # Determine language priority
        if prefer_english:
            languages = [
                ['en', 'en-US', 'en-GB'],
                ['es', 'es-ES', 'es-MX']
            ]
        else:
            languages = [
                ['es', 'es-ES', 'es-MX'],
                ['en', 'en-US', 'en-GB']
            ]

        # Try each language group
        for lang_group in languages:
            try:
                # Fetch transcript (returns FetchedTranscript object)
                fetched_transcript = ytt_api.fetch(
                    video_id,
                    languages=lang_group
                )

                # Extract text from snippets
                text = ' '.join([snippet.text for snippet in fetched_transcript])

                # Determine which language was fetched
                actual_lang = 'en' if fetched_transcript.language_code.startswith('en') else 'es'

                return {
                    'text': text,
                    'language': actual_lang,
                    'type': 'manual' if not fetched_transcript.is_generated else 'auto'
                }

            except NoTranscriptFound:
                continue

        # No transcript in preferred languages
        return None

    except TranscriptsDisabled:
        print(f"    [ERROR] Transcripts disabled by owner for video {video_id}")
        return None
    except Exception as e:
        error_str = str(e)
        print(f"    [ERROR] Failed to fetch transcript")
        print(f"    [DEBUG] Error details: {error_str[:200]}")

        if "429" in error_str or "Too Many Requests" in error_str:
            print(f"    [CAUSE] Rate limited - YouTube blocking requests (HTTP 429)")
        elif "Could not retrieve" in error_str or "HTTP Error" in error_str:
            print(f"    [CAUSE] YouTube IP BLOCKED - Transcript API unavailable")
            print(f"    [FIX] Try using a different network or wait 24-48 hours")

        return None


def test_single_video(video_id: str):
    """Test transcript fetching for a single video."""

    print(f"\n{'='*70}")
    print(f"Testing Video: {video_id}")
    print(f"{'='*70}\n")

    # Validate API key
    if not YOUTUBE_API_KEY:
        print("ERROR: YOUTUBE_API_KEY not found in .env")
        return

    try:
        # Initialize components
        print("[1/5] Initializing components...")
        youtube_api = YouTubeAPI(YOUTUBE_API_KEY)
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
        is_available, status_msg, lang = check_transcript_availability(video_id)
        print(f"      Status: {status_msg}")

        if not is_available:
            print(f"\n      [RESULT] No English/Spanish transcript available")
            print(f"      Reason: {status_msg}")

            if "BLOCKED" in status_msg.upper():
                print(f"\n      {'='*66}")
                print(f"      YOUTUBE IP BLOCKING DETECTED")
                print(f"      {'='*66}")
                print(f"      This is the same issue from before. Possible solutions:")
                print(f"      1. Wait 24-48 hours before trying again")
                print(f"      2. Use a different network (mobile hotspot, VPN)")
                print(f"      3. Use cookies.txt from logged-in YouTube session")
                print(f"      4. Use residential proxy service (Webshare, etc.)")
                print(f"      {'='*66}")

            return

        # Fetch transcript
        print(f"\n[4/5] Fetching transcript...")
        print(f"      Adding 3-second delay to avoid rate limiting...")
        time.sleep(3)  # Add delay to be more conservative

        transcript_data = fetch_transcript(video_id, prefer_english=True)

        if not transcript_data:
            print(f"\n      {'='*66}")
            print(f"      TRANSCRIPT FETCH FAILED")
            print(f"      {'='*66}")
            print(f"      The transcript exists but YouTube is blocking access.")
            print(f"      This is the IP blocking issue mentioned earlier.")
            print(f"      Check the error messages above for details.")
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
