"""
JLC Channel Transcript Fetcher

Fetches transcripts from economics/geopolitics YouTube channel.

Features:
- Processes up to 5 videos per run (conservative to avoid IP blocking)
- Filters out YouTube Shorts (≤180 seconds)
- Skips already-processed videos
- Supports English and Spanish transcripts
- Rate limiting (15s delays) to prevent YouTube IP blocking
- Retry logic with exponential backoff
- Automatic Spanish→English translation
- Stores transcripts in backlog_JLC/

Run frequency: Every 6-12 hours (reduced to avoid blocking)
Historical backlog: Processes all videos + ongoing new uploads

Note: YouTube blocks aggressive scraping. Conservative delays are essential.
"""

import os
import sys
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

from core import YouTubeAPI, TranscriptFetcher, VideoProcessor, StorageManager, TranscriptTranslator

# Load environment variables
load_dotenv()

# Configuration
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')
CHANNEL_ID = os.getenv('YOUTUBE_CHANNEL_ID2')  # JLC economics channel
MAX_VIDEOS_PER_RUN = 5  # Conservative limit (reduced from 10 to avoid blocking)
DELAY_BETWEEN_REQUESTS = 15.0  # Seconds (increased from 2.0 to prevent IP blocking)
PREFER_ENGLISH = True  # Try English first, fallback to Spanish

# Azure OpenAI Configuration (for translation)
AZURE_OPENAI_ENDPOINT = os.getenv('AZURE_OPENAI_ENDPOINT')
AZURE_OPENAI_API_KEY = os.getenv('AZURE_OPENAI_API_KEY')
AZURE_OPENAI_TRANSLATION_NAME = os.getenv('AZURE_OPENAI_TRANSLATION_NAME')
AZURE_OPENAI_API_VERSION = os.getenv('AZURE_OPENAI_API_VERSION', '2024-02-15-preview')

# Paths
BASE_DIR = Path(__file__).parent / 'backlog_JLC'
ORIGINAL_TRANSCRIPT_DIR = BASE_DIR / 'original_transcript'
PROCESSED_VIDEOS_FILE = 'processed_videos.json'


def main():
    """Main execution function."""
    print(f"\n{'='*70}")
    print(f"JLC Channel Transcript Fetcher - Running at {datetime.now()}")
    print(f"{'='*70}\n")

    # Validate environment variables
    if not YOUTUBE_API_KEY:
        print("ERROR: YOUTUBE_API_KEY not found in .env")
        return
    if not CHANNEL_ID:
        print("ERROR: YOUTUBE_CHANNEL_ID2 not found in .env")
        return
    if not AZURE_OPENAI_ENDPOINT or not AZURE_OPENAI_API_KEY or not AZURE_OPENAI_TRANSLATION_NAME:
        print("ERROR: Azure OpenAI credentials not found in .env")
        print("       Required: AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY, AZURE_OPENAI_TRANSLATION_NAME")
        return

    try:
        # Initialize components
        print("[1/7] Initializing components...")
        youtube_api = YouTubeAPI(YOUTUBE_API_KEY)
        transcript_fetcher = TranscriptFetcher(delay_seconds=DELAY_BETWEEN_REQUESTS)
        translator = TranscriptTranslator(
            azure_openai_endpoint=AZURE_OPENAI_ENDPOINT,
            azure_openai_key=AZURE_OPENAI_API_KEY,
            azure_openai_deployment=AZURE_OPENAI_TRANSLATION_NAME,
            azure_openai_api_version=AZURE_OPENAI_API_VERSION
        )
        storage = StorageManager(BASE_DIR)
        original_storage = StorageManager(ORIGINAL_TRANSCRIPT_DIR)
        print(f"      Storage: {BASE_DIR}")
        print(f"      Original transcripts: {ORIGINAL_TRANSCRIPT_DIR}")
        print(f"      Max videos per run: {MAX_VIDEOS_PER_RUN}")
        print(f"      Rate limit: {DELAY_BETWEEN_REQUESTS}s between requests")
        print(f"      Translation: Enabled (GPT-4o)")

        # Load processed videos
        print("\n[2/7] Loading processed videos...")
        processed_videos = storage.load_processed_videos(PROCESSED_VIDEOS_FILE)
        print(f"      Already processed: {len(processed_videos)} videos")
        print(f"      Total transcripts saved: {storage.get_transcript_count()}")

        # Get uploads playlist ID
        print(f"\n[3/7] Fetching uploads playlist for channel: {CHANNEL_ID}")
        playlist_id = youtube_api.get_uploads_playlist_id(CHANNEL_ID)
        print(f"      Playlist ID: {playlist_id}")

        # Get recent videos (fetch 50 to build backlog faster)
        print(f"\n[4/7] Fetching recent videos...")
        recent_videos = youtube_api.get_recent_videos(playlist_id, max_results=50)
        print(f"      Found: {len(recent_videos)} recent videos")

        # Get video details for Shorts detection
        print(f"\n[5/7] Checking for YouTube Shorts...")
        video_ids = VideoProcessor.get_video_ids(recent_videos)
        video_details = youtube_api.get_video_details(video_ids)

        # Filter out Shorts
        filtered_videos = youtube_api.filter_shorts(recent_videos, video_details)
        shorts_count = len(recent_videos) - len(filtered_videos)
        print(f"      Shorts detected and skipped: {shorts_count}")
        print(f"      Regular videos: {len(filtered_videos)}")

        # Filter out already-processed videos
        processed_set = set(processed_videos)
        new_videos = VideoProcessor.filter_processed(filtered_videos, processed_set)
        print(f"      New unprocessed videos: {len(new_videos)}")

        if not new_videos:
            print(f"\n[INFO] No new videos to process. Exiting.")
            print(f"\nQuota used this run: {youtube_api.get_quota_used()} units")
            print(f"{'='*70}\n")
            return

        # Limit to max per run
        videos_to_process = new_videos[:MAX_VIDEOS_PER_RUN]
        if len(new_videos) > MAX_VIDEOS_PER_RUN:
            print(f"      [INFO] Limiting to {MAX_VIDEOS_PER_RUN} videos this run")
            print(f"      Remaining {len(new_videos) - MAX_VIDEOS_PER_RUN} will be processed next run")

        # Process videos
        print(f"\n[6/7] Processing {len(videos_to_process)} videos...")
        print(f"{'='*70}")

        successfully_processed = 0
        failed_videos = []

        for i, video in enumerate(videos_to_process, 1):
            video_id = video['video_id']
            video_title = video['title']
            published_at = video.get('published_at')

            print(f"\n  [{i}/{len(videos_to_process)}] {video_title}")
            print(f"       Video ID: {video_id}")
            print(f"       Published: {published_at}")

            # Check transcript availability
            print(f"       Checking transcript availability...")
            is_available, status_msg, lang = transcript_fetcher.check_availability(video_id)
            print(f"       Status: {status_msg}")

            if not is_available:
                print(f"       [SKIP] No English/Spanish transcript available")
                failed_videos.append({
                    'video_id': video_id,
                    'title': video_title,
                    'reason': status_msg
                })
                continue

            # Fetch transcript with retry logic
            print(f"       Fetching transcript...")
            transcript_data = transcript_fetcher.fetch_with_retry(
                video_id,
                prefer_english=PREFER_ENGLISH,
                max_retries=3
            )

            if not transcript_data:
                print(f"       [ERROR] Failed to fetch transcript")
                failed_videos.append({
                    'video_id': video_id,
                    'title': video_title,
                    'reason': 'Fetch failed'
                })
                continue

            # Translation pipeline: Spanish → English
            original_language = transcript_data['language']
            print(f"       Language: {original_language.upper()}")
            print(f"       Type: {transcript_data['type']}")
            print(f"       Length: {len(transcript_data['text'])} characters")

            final_text = transcript_data['text']
            translation_performed = False

            if original_language == 'es':
                # Save original Spanish transcript first
                print(f"       [SAVING] Original Spanish transcript...")
                original_filepath = original_storage.save_transcript(
                    video_id=video_id,
                    video_title=video_title,
                    transcript_text=transcript_data['text'],
                    language='es',
                    transcript_type=transcript_data['type'],
                    published_at=published_at
                )
                print(f"       [SAVED] Original: {original_filepath.name}")

                # Translate to English
                print(f"       [TRANSLATING] Spanish → English (GPT-4o)...")
                english_translation = translator.translate(
                    spanish_transcript=transcript_data['text'],
                    video_title=video_title,
                    video_topic="Economics and financial markets analysis"
                )

                if english_translation:
                    final_text = english_translation
                    translation_performed = True
                    print(f"       [SUCCESS] Translation complete ({len(final_text)} characters)")
                else:
                    print(f"       [ERROR] Translation failed - skipping English save")
                    failed_videos.append({
                        'video_id': video_id,
                        'title': video_title,
                        'reason': 'Translation failed'
                    })
                    continue

            # Save English transcript (original or translated)
            filepath = storage.save_transcript(
                video_id=video_id,
                video_title=video_title,
                transcript_text=final_text,
                language='en',  # Always save as English
                transcript_type=transcript_data['type'],
                published_at=published_at
            )

            print(f"       [SAVED] {filepath.name}")

            # Mark as processed
            processed_videos.append(video_id)
            storage.save_processed_videos(processed_videos, PROCESSED_VIDEOS_FILE)
            successfully_processed += 1

        # Summary
        print(f"\n{'='*70}")
        print(f"[7/7] Processing Complete")
        print(f"{'='*70}")
        print(f"  Successfully processed: {successfully_processed}/{len(videos_to_process)}")
        print(f"  Failed: {len(failed_videos)}")

        if failed_videos:
            print(f"\n  Failed videos:")
            for failed in failed_videos:
                print(f"    - {failed['title'][:50]}... ({failed['reason']})")

        print(f"\n  Total English transcripts: {storage.get_transcript_count()}")
        print(f"  Total original Spanish transcripts: {original_storage.get_transcript_count()}")
        print(f"  Total videos tracked: {len(processed_videos)}")
        print(f"  API quota used this run: {youtube_api.get_quota_used()} units")
        print(f"  Transcript API requests: {transcript_fetcher.get_requests_made()}")
        print(f"  Translations performed: {translator.get_translations_made()}")

        print(f"\n{'='*70}\n")

    except Exception as e:
        print(f"\n[ERROR] Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
