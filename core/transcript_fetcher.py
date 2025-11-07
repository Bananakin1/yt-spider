"""
Transcript fetching with rate limiting, retry logic, and error handling.

Prevents IP blocking through:
- Configurable delays between requests (default: 2 seconds)
- Exponential backoff retry logic
- Proper error handling for 429 rate limits

Supports:
- English and Spanish transcripts
- Manual and auto-generated transcripts
- Language fallback (try English, then Spanish)

Uses youtube-transcript-api v1.2.3+ instance methods.
"""

from typing import Tuple, Dict, Optional
import time
import random
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound


class TranscriptFetcher:
    """Fetch YouTube transcripts with safety features to prevent blocking."""

    def __init__(self, delay_seconds: float = 2.0):
        """
        Initialize transcript fetcher.

        Args:
            delay_seconds: Delay between requests to prevent rate limiting
        """
        self.delay = delay_seconds
        self.requests_made = 0
        # Initialize API instance (v1.2.3+ requires instance methods)
        self.api = YouTubeTranscriptApi()

    def check_availability(self, video_id: str) -> Tuple[bool, str, Optional[str]]:
        """
        Check if transcripts are available for a video.

        Checks in order:
        1. Manual English transcript
        2. Auto-generated English transcript
        3. Manual Spanish transcript
        4. Auto-generated Spanish transcript
        5. Other languages (not used, just reported)

        Args:
            video_id: YouTube video ID

        Returns:
            Tuple of (is_available, status_message, language_code)
            - is_available: True if English or Spanish transcript found
            - status_message: Human-readable status
            - language_code: 'en', 'es', or None
        """
        try:
            # Use instance method (v1.2.3+ API)
            transcript_list = self.api.list(video_id)

            # Try English (manual first, then auto)
            try:
                manual_en = transcript_list.find_manually_created_transcript(['en', 'en-US', 'en-GB'])
                return True, f"Manual English transcript ({manual_en.language})", 'en'
            except NoTranscriptFound:
                pass

            try:
                auto_en = transcript_list.find_generated_transcript(['en', 'en-US', 'en-GB'])
                return True, f"Auto-generated English transcript ({auto_en.language})", 'en'
            except NoTranscriptFound:
                pass

            # Try Spanish (manual first, then auto)
            try:
                manual_es = transcript_list.find_manually_created_transcript(['es', 'es-ES', 'es-MX'])
                return True, f"Manual Spanish transcript ({manual_es.language})", 'es'
            except NoTranscriptFound:
                pass

            try:
                auto_es = transcript_list.find_generated_transcript(['es', 'es-ES', 'es-MX'])
                return True, f"Auto-generated Spanish transcript ({auto_es.language})", 'es'
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
            if "429" in str(e) or "Too Many Requests" in str(e):
                return False, "Rate limited (wait a few minutes)", None
            return False, f"Error: {str(e)[:100]}", None

    def fetch_transcript(
        self,
        video_id: str,
        prefer_english: bool = True
    ) -> Optional[Dict]:
        """
        Fetch transcript for a video with language fallback.

        Priority:
        1. English (if prefer_english=True)
        2. Spanish (if English unavailable or prefer_english=False)

        Args:
            video_id: YouTube video ID
            prefer_english: Try English first before Spanish

        Returns:
            Dict with keys:
            - text: Full transcript text
            - language: 'en' or 'es'
            - type: 'manual' or 'auto'
            Or None if fetch failed
        """
        try:
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
                    # Use instance method (v1.2.3+ API)
                    # fetch() returns FetchedTranscript object
                    fetched_transcript = self.api.fetch(
                        video_id,
                        languages=lang_group
                    )

                    # Extract text from snippets
                    text = ' '.join([snippet.text for snippet in fetched_transcript])

                    # Get language code (e.g., 'en' from 'en-US')
                    actual_lang = 'en' if fetched_transcript.language_code.startswith('en') else 'es'

                    # Get type from is_generated property
                    transcript_type = 'manual' if not fetched_transcript.is_generated else 'auto'

                    return {
                        'text': text,
                        'language': actual_lang,
                        'type': transcript_type
                    }

                except NoTranscriptFound:
                    continue

            # No transcript in preferred languages
            return None

        except TranscriptsDisabled:
            print(f"    Transcripts disabled for video {video_id}")
            return None
        except Exception as e:
            if "429" in str(e) or "Too Many Requests" in str(e):
                print(f"    Rate limited for video {video_id}")
            else:
                print(f"    Error fetching transcript: {str(e)[:100]}")
            return None

    def fetch_with_retry(
        self,
        video_id: str,
        prefer_english: bool = True,
        max_retries: int = 3
    ) -> Optional[Dict]:
        """
        Fetch transcript with exponential backoff retry logic.

        Retry strategy:
        - Attempt 1: Immediate
        - Attempt 2: Wait ~1 second
        - Attempt 3: Wait ~2 seconds
        - Attempt 4: Wait ~4 seconds

        Only retries on rate limit errors (429).
        Other errors fail immediately.

        Args:
            video_id: YouTube video ID
            prefer_english: Try English first before Spanish
            max_retries: Maximum retry attempts

        Returns:
            Transcript dict or None if all attempts failed
        """
        for attempt in range(max_retries):
            # Add delay before request (except first attempt)
            if attempt > 0 or self.requests_made > 0:
                time.sleep(self.delay)

            try:
                result = self.fetch_transcript(video_id, prefer_english)
                self.requests_made += 1
                return result

            except Exception as e:
                # Only retry on rate limit errors
                if "429" in str(e) or "Too Many Requests" in str(e):
                    if attempt < max_retries - 1:
                        # Exponential backoff with jitter
                        delay = (2 ** attempt) + random.uniform(0, 1)
                        print(f"    Rate limited. Retrying in {delay:.1f}s... (attempt {attempt + 2}/{max_retries})")
                        time.sleep(delay)
                        continue
                    else:
                        print(f"    Rate limited after {max_retries} attempts. Giving up.")
                        return None
                else:
                    # Other errors don't retry
                    self.requests_made += 1
                    return None

        return None

    def get_requests_made(self) -> int:
        """
        Get total number of transcript requests made.

        Returns:
            Request count
        """
        return self.requests_made
