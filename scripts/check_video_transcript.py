"""
Simple script to check if a YouTube video has transcripts available
Usage: python check_video_transcript.py VIDEO_ID
Example: python check_video_transcript.py dQw4w9WgXcQ
"""
import sys
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound

def check_video_transcript(video_id):
    """Check what transcripts are available for a video"""
    print(f"\nChecking video: https://www.youtube.com/watch?v={video_id}\n")

    try:
        ytt_api = YouTubeTranscriptApi()
        transcript_list = ytt_api.list(video_id)

        print("=" * 60)
        print("TRANSCRIPT AVAILABILITY")
        print("=" * 60)

        # Check for manually created transcripts
        manual_transcripts = []
        auto_transcripts = []

        for transcript in transcript_list:
            if transcript.is_generated:
                auto_transcripts.append(transcript)
            else:
                manual_transcripts.append(transcript)

        if manual_transcripts:
            print("\nManual Transcripts (created by uploader):")
            for t in manual_transcripts:
                print(f"  - {t.language} ({t.language_code})")

        if auto_transcripts:
            print("\nAuto-Generated Transcripts (by YouTube):")
            for t in auto_transcripts:
                print(f"  - {t.language} ({t.language_code})")

        if not manual_transcripts and not auto_transcripts:
            print("\nNo transcripts available")

        # Try to fetch English transcript
        print("\n" + "=" * 60)
        print("TESTING ENGLISH TRANSCRIPT FETCH")
        print("=" * 60)

        try:
            ytt_api = YouTubeTranscriptApi()
            transcript = ytt_api.fetch(video_id, languages=['en', 'en-US', 'en-GB'])
            print(f"\nSUCCESS! Fetched {len(transcript)} transcript segments")
            print(f"\nFirst 3 segments:")
            for i, segment in enumerate(transcript[:3]):
                print(f"  {i+1}. [{segment.start:.1f}s] {segment.text}")
            return True
        except NoTranscriptFound:
            print("\nNo English transcript found")
            print("Try fetching in another language from the list above")
            return False

    except TranscriptsDisabled:
        print("=" * 60)
        print("TRANSCRIPTS ARE DISABLED")
        print("=" * 60)
        print("\nThe video owner has disabled transcripts for this video.")
        print("This means:")
        print("  - Auto-generated captions are turned off")
        print("  - No manual captions were uploaded")
        print("  - The bot cannot fetch transcripts for this video")
        return False

    except Exception as e:
        print("=" * 60)
        print("ERROR")
        print("=" * 60)

        if "429" in str(e) or "Too Many Requests" in str(e):
            print("\nRate limited by YouTube!")
            print("You've made too many requests. Wait 10-15 minutes and try again.")
        elif "Video unavailable" in str(e):
            print("\nVideo is unavailable (private, deleted, or age-restricted)")
        else:
            print(f"\nError: {e}")
        return False


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python check_video_transcript.py VIDEO_ID")
        print("Example: python check_video_transcript.py dQw4w9WgXcQ")
        sys.exit(1)

    video_id = sys.argv[1]
    check_video_transcript(video_id)
