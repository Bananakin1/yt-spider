# YouTube Transcript Fetcher - Implementation Status

## Overview

Modular YouTube transcript fetching system with two implementations:
1. **JLC Channel Fetcher** - Economics/geopolitics channel (backlog processing)
2. **Discord Bot** - AI strategy channel (real-time notifications)

Both share the same core infrastructure for maintainability and reliability.

---

## Implementation Complete

### Core Infrastructure (`core/`)

Reusable modules for all YouTube transcript operations:

#### `core/youtube_api.py`
- YouTube Data API v3 wrapper
- Quota tracking (10,000 units/day limit)
- YouTube Shorts detection (duration <= 180 seconds)
- Channel uploads playlist fetching
- Recent videos retrieval
- Video details with ISO 8601 duration parsing

#### `core/transcript_fetcher.py`
- Transcript availability checking
- Language fallback: English -> Spanish
- Manual/auto-generated transcript preference
- Rate limiting (configurable delays)
- Exponential backoff retry logic
- Handles 429 rate limit errors gracefully

#### `core/video_processor.py`
- Filter already-processed videos
- Video validation utilities
- Batch processing helpers
- Video ID extraction

#### `core/storage.py`
- Save transcripts with metadata headers
- Load/save processed video lists (JSON)
- Directory management
- Transcript counting and retrieval

### Main Scripts

#### `fetch_jlc_transcripts.py`
**Purpose:** Process JLC economics channel videos hourly

**Features:**
- Processes 10 videos per run (safe hourly rate)
- Filters YouTube Shorts (<=180 seconds)
- English preference, Spanish fallback
- 2-second delays between requests
- Tracks processed videos to avoid duplicates
- Stores in `backlog_JLC/transcripts/`
- Saves metadata to `backlog_JLC/metadata/processed_videos.json`

**Configuration:**
```python
MAX_VIDEOS_PER_RUN = 10
DELAY_BETWEEN_REQUESTS = 2.0
PREFER_ENGLISH = True
CHANNEL_ID = os.getenv('YOUTUBE_CHANNEL_ID2')
```

**Run Frequency:** Every hour via Task Scheduler
**Processing Rate:** ~240 videos/day (will process historical backlog over time)

#### `test_single_video.py`
**Purpose:** Test transcript fetching on individual videos

**Features:**
- Accepts video ID or full YouTube URL
- Tests all core functionality:
  - Transcript availability detection
  - English/Spanish language support
  - Shorts detection
  - Retry logic
  - File storage
- Detailed step-by-step output
- Saves to `test_output/`

**Usage:**
```bash
python test_single_video.py dQw4w9WgXcQ
python test_single_video.py https://www.youtube.com/watch?v=dQw4w9WgXcQ
```

#### `youtube_discord_bot.py` (Refactored)
**Purpose:** AI strategy channel -> Discord notifications

**Changes:**
- Now uses core modules (YouTubeAPI, TranscriptFetcher, VideoProcessor)
- Added YouTube Shorts filtering
- Better retry logic with exponential backoff
- Rate limiting (1.5s delays)
- Shows API quota usage in output
- Logs transcript language and type

**Preserved:**
- Azure OpenAI summarization
- Discord webhook posting
- 3 videos per run limit
- Existing prompt engineering

---

## Environment Variables Required

### `.env` file must contain:

```bash
# YouTube Data API
YOUTUBE_API_KEY=your_youtube_api_key_here

# JLC Channel (Economics/Geopolitics)
YOUTUBE_CHANNEL_ID2=UCxxxxxxxxxxxxxxxxxx

# Discord Bot Channel (AI Strategy)
YOUTUBE_CHANNEL_ID=UCxxxxxxxxxxxxxxxxxx

# Discord Webhook
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...

# Azure OpenAI (for Discord bot summaries)
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your_azure_openai_key
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o-mini
AZURE_OPENAI_API_VERSION=2024-02-15-preview
```

---

## Next Steps

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

**New dependency added:** `isodate==0.6.1` (for ISO 8601 duration parsing)

### 2. Test Single Video Fetching

Test the core functionality with a known video:

```bash
python test_single_video.py dQw4w9WgXcQ
```

**Expected output:**
- Video details fetched
- Shorts detection result
- Transcript availability check
- Transcript fetched and saved
- File saved to `test_output/transcripts/`

**What to verify:**
- API authentication works
- Transcript fetching works
- Shorts detection works (if testing a Short)
- Rate limiting doesn't cause errors
- Files are saved correctly

### 3. Test JLC Channel Fetcher

Run the JLC channel fetcher once manually:

```bash
python fetch_jlc_transcripts.py
```

**Expected output:**
- Fetches up to 50 recent videos
- Filters out Shorts
- Processes up to 10 new videos
- Saves transcripts to `backlog_JLC/transcripts/`
- Updates `backlog_JLC/metadata/processed_videos.json`

**What to verify:**
- Channel ID is correct (YOUTUBE_CHANNEL_ID2)
- Shorts are filtered correctly
- Transcripts are fetched in English or Spanish
- No rate limiting errors
- Files are saved with proper metadata headers

### 4. Test Refactored Discord Bot

Run the Discord bot once manually:

```bash
python youtube_discord_bot.py
```

**Expected output:**
- Fetches recent videos
- Filters Shorts
- Processes up to 3 new videos
- Generates summaries with Azure OpenAI
- Posts to Discord
- Shows API quota usage

**What to verify:**
- Shorts filtering works
- Transcript fetching uses new retry logic
- Discord posts still work
- Azure OpenAI summaries still work
- No regressions from refactoring

### 5. Set Up Windows Task Scheduler

#### For JLC Channel Fetcher (Hourly)

1. Open Task Scheduler
2. Create Basic Task: "JLC Transcript Fetcher"
3. Trigger: Daily, repeat every 1 hour for 24 hours
4. Action: Start a program
   - Program: `python.exe` (full path, e.g., `C:\Python311\python.exe`)
   - Arguments: `fetch_jlc_transcripts.py`
   - Start in: `C:\Users\vfizr\OneDrive\Documentos\nate_fetcher\youtube_bot`
5. Settings:
   - Allow task to be run on demand
   - Stop task if runs longer than 30 minutes
   - Run whether user is logged on or not

#### For Discord Bot (Every 2 hours)

1. Create Basic Task: "YouTube Discord Bot"
2. Trigger: Daily, repeat every 2 hours for 24 hours
3. Action: Start a program
   - Program: `python.exe`
   - Arguments: `youtube_discord_bot.py`
   - Start in: `C:\Users\vfizr\OneDrive\Documentos\nate_fetcher\youtube_bot`

### 6. Monitor Performance

#### First 24 Hours
- Check `backlog_JLC/transcripts/` for new files
- Verify `processed_videos.json` is updating
- Monitor API quota usage (should be <100 units/day)
- Check for rate limiting errors in logs

#### First Week
- Calculate processing rate (videos/day)
- Estimate time to complete historical backlog
- Verify Shorts are being filtered consistently
- Check transcript quality (English vs Spanish ratio)

---

## File Structure

```
youtube_bot/
├── core/
│   ├── __init__.py
│   ├── youtube_api.py           # YouTube Data API wrapper
│   ├── transcript_fetcher.py    # Transcript fetching with retry
│   ├── video_processor.py       # Video filtering utilities
│   └── storage.py               # File storage management
│
├── backlog_JLC/                 # JLC channel storage
│   ├── transcripts/             # Saved transcript files
│   └── metadata/
│       └── processed_videos.json
│
├── test_output/                 # Test script output
│   ├── transcripts/
│   └── metadata/
│
├── data/                        # Discord bot storage
│   ├── transcripts/
│   └── summaries/
│
├── fetch_jlc_transcripts.py    # JLC channel main script
├── test_single_video.py        # Single video test script
├── youtube_discord_bot.py      # Discord bot (refactored)
├── requirements.txt            # Python dependencies
├── .env                        # Environment variables
└── processed_videos.json       # Discord bot processed videos
```

---

## Rate Limits & Quotas

### YouTube Data API v3
- **Daily Quota:** 10,000 units
- **Cost per operation:**
  - Get uploads playlist: 1 unit
  - Get recent videos: 1 unit
  - Get video details (50 videos): 1 unit
- **Expected usage:** 50-100 units/day (both bots combined)

### youtube-transcript-api
- **NOT part of official API** (no quota usage)
- **Rate limiting:** ~100-200 requests/hour safe
- **Our implementation:** 10-30 requests/hour (very conservative)
- **Protection:** 2s delays + exponential backoff

### Processing Capacity
- **JLC Fetcher:** 10 videos/hour = 240 videos/day
- **Discord Bot:** 3 videos/2 hours = 36 videos/day
- **Combined:** ~276 videos/day maximum

---

## Troubleshooting

### "Rate limited by YouTube"
- Increase `DELAY_BETWEEN_REQUESTS` in fetch_jlc_transcripts.py
- Reduce `MAX_VIDEOS_PER_RUN`
- Wait 10-15 minutes before retrying

### "Quota exceeded" (YouTube Data API)
- Check daily quota usage: https://console.cloud.google.com/apis/api/youtube.googleapis.com/quotas
- Wait until midnight PST for quota reset
- Reduce `max_results` in get_recent_videos() calls

### "Transcripts disabled" or "No transcripts available"
- Video owner disabled transcripts (skip)
- No English/Spanish transcript exists (check other languages)
- Video is too new (transcripts not generated yet)

### Shorts not being filtered
- Check video duration in API response
- Verify isodate is installed (`pip install isodate==0.6.1`)
- Test with known Short video ID

### Discord bot not posting
- Verify DISCORD_WEBHOOK_URL is correct
- Check Azure OpenAI credentials
- Test webhook manually with curl/Postman

---

## Future Enhancements

### Phase 2: LLM Analysis (Not Yet Implemented)
- Extract causal relationships from transcripts
- Store relationships in graph database (Neo4j/TigerGraph)
- Add timestamps to relationship edges
- Build knowledge graph over time

### Phase 3: Backtesting (Not Yet Implemented)
- Integrate with Tiingo API (stocks/ETFs)
- Integrate with CCXT (cryptocurrency)
- Event study methodology
- Statistical modeling (DML, BSTS, Bayesian updating)

### Optimizations
- Parallel transcript fetching with semaphore
- Incremental backfill (process oldest videos first)
- Transcript deduplication
- Language detection improvements
- Summary caching

---

## Changelog

### 2025-11-05 - Initial Implementation
- Created core/ module structure
- Implemented YouTubeAPI with Shorts detection
- Implemented TranscriptFetcher with retry logic
- Implemented VideoProcessor and StorageManager
- Created fetch_jlc_transcripts.py
- Created test_single_video.py
- Refactored youtube_discord_bot.py to use core modules
- Added isodate dependency for duration parsing
- All code complete and ready for testing
