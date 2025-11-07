"""
Translation Test Script

Tests the Spanish-to-English translation pipeline on existing transcripts
from backlog_JLC/transcripts/.

Features:
- Translates existing Spanish transcripts using core/translator.py
- Saves translations to test_translations/ directory
- Provides translation statistics and quality checks
- Supports testing on subset or all transcripts

Usage:
    # Test on first 3 transcripts (default)
    python test_translation.py

    # Test on specific number of transcripts
    python test_translation.py --count 5

    # Test all transcripts
    python test_translation.py --all

    # Test specific video ID
    python test_translation.py --video-id nqYul4Np-1s
"""

import os
import sys
import argparse
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Add core modules to path (tests/ is subdirectory, core/ is in parent)
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core import TranscriptTranslator

# Load environment variables
load_dotenv()

# Configuration
AZURE_OPENAI_ENDPOINT = os.getenv('AZURE_OPENAI_ENDPOINT')
AZURE_OPENAI_API_KEY = os.getenv('AZURE_OPENAI_API_KEY')
AZURE_OPENAI_TRANSLATION_NAME = os.getenv('AZURE_OPENAI_TRANSLATION_NAME')
AZURE_OPENAI_API_VERSION = os.getenv('AZURE_OPENAI_API_VERSION', '2024-02-15-preview')

# Paths (script is in tests/, data is in parent directory)
SCRIPT_DIR = Path(__file__).parent
TRANSCRIPT_DIR = PROJECT_ROOT / 'backlog_JLC' / 'transcripts'
OUTPUT_DIR = PROJECT_ROOT / 'test_translations'


def parse_transcript_file(filepath: Path) -> dict:
    """
    Parse transcript file and extract metadata and content.

    Args:
        filepath: Path to transcript file

    Returns:
        Dict with metadata and transcript text
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # Extract metadata
        metadata = {}
        transcript_lines = []
        separator_found = False

        for line in lines:
            if '=' * 10 in line:
                separator_found = True
                continue

            if not separator_found:
                # Parse metadata lines
                if ':' in line:
                    key, value = line.split(':', 1)
                    metadata[key.strip()] = value.strip()
            else:
                # Transcript content
                transcript_lines.append(line)

        transcript_text = ''.join(transcript_lines).strip()

        return {
            'video_id': metadata.get('Video ID', 'unknown'),
            'title': metadata.get('Title', 'Unknown Title'),
            'language': metadata.get('Language', 'unknown'),
            'type': metadata.get('Type', 'unknown'),
            'published': metadata.get('Published', 'unknown'),
            'downloaded': metadata.get('Downloaded', 'unknown'),
            'transcript': transcript_text,
            'char_count': len(transcript_text)
        }

    except Exception as e:
        print(f"Error parsing {filepath.name}: {e}")
        return None


def save_translation(output_path: Path, metadata: dict, translation: str):
    """
    Save translated transcript to file with metadata.

    Args:
        output_path: Path to save translation
        metadata: Transcript metadata
        translation: Translated text
    """
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(f"Video ID: {metadata['video_id']}\n")
        f.write(f"Title: {metadata['title']}\n")
        f.write(f"Original Language: {metadata['language']}\n")
        f.write(f"Translation: Spanish → English\n")
        f.write(f"Transcript Type: {metadata['type']}\n")
        f.write(f"Published: {metadata['published']}\n")
        f.write(f"Translated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Original Length: {metadata['char_count']} characters\n")
        f.write(f"Translation Length: {len(translation)} characters\n")
        f.write("=" * 80 + "\n\n")
        f.write(translation)


def analyze_translation(original: str, translation: str, metadata: dict) -> dict:
    """
    Analyze translation quality metrics.

    Args:
        original: Original Spanish text
        translation: Translated English text
        metadata: Transcript metadata

    Returns:
        Dict with analysis metrics
    """
    # Count specific corrections/flags
    verify_count = translation.count('[VERIFY]')
    unclear_count = translation.count('[UNCLEAR]')
    usd_count = translation.count('USD')

    # Calculate length ratio
    length_ratio = len(translation) / len(original) if len(original) > 0 else 0

    return {
        'original_chars': len(original),
        'translated_chars': len(translation),
        'length_ratio': length_ratio,
        'verify_flags': verify_count,
        'unclear_flags': unclear_count,
        'usd_mentions': usd_count,
        'has_flags': verify_count > 0 or unclear_count > 0
    }


def test_translation(
    translator: TranscriptTranslator,
    transcript_files: list,
    output_dir: Path
) -> dict:
    """
    Test translation on multiple transcripts.

    Args:
        translator: TranscriptTranslator instance
        transcript_files: List of transcript file paths
        output_dir: Directory to save translations

    Returns:
        Dict with test results
    """
    results = {
        'total': len(transcript_files),
        'successful': 0,
        'failed': 0,
        'translations': []
    }

    print(f"\n{'='*80}")
    print(f"Testing Translation Pipeline")
    print(f"{'='*80}")
    print(f"Transcripts to process: {len(transcript_files)}")
    print(f"Output directory: {output_dir}\n")

    for i, filepath in enumerate(transcript_files, 1):
        print(f"[{i}/{len(transcript_files)}] Processing: {filepath.name}")

        # Parse transcript
        parsed = parse_transcript_file(filepath)
        if not parsed:
            results['failed'] += 1
            continue

        # Check if Spanish
        if parsed['language'] != 'es':
            print(f"  [SKIP] Not Spanish (language: {parsed['language']})")
            results['failed'] += 1
            continue

        print(f"  Title: {parsed['title']}")
        print(f"  Language: {parsed['language']}")
        print(f"  Length: {parsed['char_count']:,} characters")

        # Translate
        print(f"  [TRANSLATING] Spanish → English (GPT-4o)...")
        translation = translator.translate(
            spanish_transcript=parsed['transcript'],
            video_title=parsed['title'],
            video_topic="Economics and financial markets analysis"
        )

        if not translation:
            print(f"  [ERROR] Translation failed")
            results['failed'] += 1
            continue

        # Analyze translation
        analysis = analyze_translation(parsed['transcript'], translation, parsed)
        print(f"  [SUCCESS] Translation complete")
        print(f"    - Original: {analysis['original_chars']:,} chars")
        print(f"    - Translated: {analysis['translated_chars']:,} chars")
        print(f"    - Ratio: {analysis['length_ratio']:.2f}x")

        if analysis['has_flags']:
            print(f"    - Flags: [VERIFY]={analysis['verify_flags']}, [UNCLEAR]={analysis['unclear_flags']}")

        # Save translation
        output_filename = filepath.stem + '_translated.txt'
        output_path = output_dir / output_filename
        save_translation(output_path, parsed, translation)
        print(f"  [SAVED] {output_filename}\n")

        results['successful'] += 1
        results['translations'].append({
            'filename': filepath.name,
            'video_id': parsed['video_id'],
            'title': parsed['title'],
            'analysis': analysis
        })

    return results


def print_summary(results: dict):
    """
    Print test summary statistics.

    Args:
        results: Test results dict
    """
    print(f"\n{'='*80}")
    print(f"Translation Test Summary")
    print(f"{'='*80}")
    print(f"Total transcripts: {results['total']}")
    print(f"Successful: {results['successful']}")
    print(f"Failed: {results['failed']}")
    print(f"Success rate: {(results['successful']/results['total']*100):.1f}%")

    if results['translations']:
        print(f"\n{'='*80}")
        print(f"Translation Details")
        print(f"{'='*80}\n")

        total_original = 0
        total_translated = 0
        total_flags = 0

        for trans in results['translations']:
            analysis = trans['analysis']
            total_original += analysis['original_chars']
            total_translated += analysis['translated_chars']
            if analysis['has_flags']:
                total_flags += 1

            print(f"Video: {trans['title'][:60]}")
            print(f"  - Video ID: {trans['video_id']}")
            print(f"  - Original: {analysis['original_chars']:,} chars")
            print(f"  - Translated: {analysis['translated_chars']:,} chars")
            print(f"  - Ratio: {analysis['length_ratio']:.2f}x")
            if analysis['has_flags']:
                print(f"  - Flags: [VERIFY]={analysis['verify_flags']}, [UNCLEAR]={analysis['unclear_flags']}")
            print()

        avg_ratio = total_translated / total_original if total_original > 0 else 0
        print(f"Average length ratio: {avg_ratio:.2f}x")
        print(f"Translations with flags: {total_flags}/{len(results['translations'])}")
        print(f"Total characters translated: {total_original:,} → {total_translated:,}")


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(description='Test Spanish-to-English translation pipeline')
    parser.add_argument('--count', type=int, default=3, help='Number of transcripts to test (default: 3)')
    parser.add_argument('--all', action='store_true', help='Test all transcripts')
    parser.add_argument('--video-id', type=str, help='Test specific video ID')
    args = parser.parse_args()

    print(f"\n{'='*80}")
    print(f"Translation Test Script")
    print(f"{'='*80}\n")

    # Validate environment variables
    if not AZURE_OPENAI_ENDPOINT or not AZURE_OPENAI_API_KEY or not AZURE_OPENAI_TRANSLATION_NAME:
        print("ERROR: Azure OpenAI credentials not found in .env")
        print("Required variables:")
        print("  - AZURE_OPENAI_ENDPOINT")
        print("  - AZURE_OPENAI_API_KEY")
        print("  - AZURE_OPENAI_TRANSLATION_NAME")
        return

    # Validate transcript directory
    if not TRANSCRIPT_DIR.exists():
        print(f"ERROR: Transcript directory not found: {TRANSCRIPT_DIR}")
        return

    # Create output directory
    OUTPUT_DIR.mkdir(exist_ok=True)
    print(f"Output directory: {OUTPUT_DIR}")

    # Get transcript files
    all_transcripts = sorted(TRANSCRIPT_DIR.glob('*.txt'))
    if not all_transcripts:
        print(f"ERROR: No transcript files found in {TRANSCRIPT_DIR}")
        return

    print(f"Found {len(all_transcripts)} transcript files")

    # Select transcripts based on arguments
    if args.video_id:
        # Filter by video ID
        selected = [f for f in all_transcripts if args.video_id in f.name]
        if not selected:
            print(f"ERROR: No transcript found for video ID: {args.video_id}")
            return
        print(f"Testing specific video: {args.video_id}")
    elif args.all:
        # Test all
        selected = all_transcripts
        print(f"Testing ALL {len(selected)} transcripts")
    else:
        # Test subset
        selected = all_transcripts[:args.count]
        print(f"Testing first {len(selected)} transcripts")

    # Initialize translator
    print("\nInitializing translator...")
    try:
        translator = TranscriptTranslator(
            azure_openai_endpoint=AZURE_OPENAI_ENDPOINT,
            azure_openai_key=AZURE_OPENAI_API_KEY,
            azure_openai_deployment=AZURE_OPENAI_TRANSLATION_NAME,
            azure_openai_api_version=AZURE_OPENAI_API_VERSION
        )
        print("Translator initialized successfully")
    except Exception as e:
        print(f"ERROR: Failed to initialize translator: {e}")
        return

    # Run translation test
    results = test_translation(translator, selected, OUTPUT_DIR)

    # Print summary
    print_summary(results)

    print(f"\n{'='*80}")
    print(f"Test complete!")
    print(f"Translations saved to: {OUTPUT_DIR}")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    main()
