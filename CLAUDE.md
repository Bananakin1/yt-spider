# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a dual-bot YouTube transcript fetching system with modular core architecture. It processes videos from two YouTube channels with different workflows:

1. **Nate AI Strategy Bot** (`youtube_discord_bot.py`): Fetches English transcripts, generates GPT-4o-mini summaries, posts to Discord
2. **JLC Economics Bot** (`fetch_jlc_transcripts.py`): Fetches Spanish/English transcripts, translates Spanish→English with GPT-4o, stores locally

Both bots share a common `core/` module architecture for YouTube API operations, transcript fetching, storage, and translation.

## Setup and Environment

The project uses a Python virtual environment with dependencies in `requirements.txt`:
- `youtube-transcript-api`: Fetches video transcripts
- `google-api-python-client`: Accesses YouTube Data API
- `openai`: Azure OpenAI client for summarization
- `python-dotenv`: Environment variable management
- `requests`: Discord webhook posting

Required environment variables in `.env` (see `.env.example`):
- `YOUTUBE_API_KEY`: YouTube Data API v3 key
- `YOUTUBE_CHANNEL_ID`: Nate's AI strategy channel ID
- `YOUTUBE_CHANNEL_ID2`: JLC economics channel ID
- `DISCORD_WEBHOOK_URL`: Discord webhook for Nate bot summaries
- `AZURE_OPENAI_ENDPOINT`: Azure OpenAI service endpoint
- `AZURE_OPENAI_API_KEY`: Azure OpenAI API key
- `AZURE_OPENAI_DEPLOYMENT_NAME`: GPT-4o-mini deployment for summaries
- `AZURE_OPENAI_TRANSLATION_NAME`: GPT-4o deployment for translation
- `AZURE_OPENAI_API_VERSION`: API version (default: "2024-02-15-preview")

## Running the Bots

**Nate AI Strategy Bot (production):**
```bash
run_bot.bat
```
Activates venv, runs `youtube_discord_bot.py`, logs to `logs/bot_YYYY-MM-DD_HH-MM-SS.log`

**JLC Economics Bot (manual):**
```bash
venv\Scripts\activate.bat  # Windows
python fetch_jlc_transcripts.py
```

**Manual run (Unix/Linux):**
```bash
source venv/bin/activate
python youtube_discord_bot.py        # Nate bot
python fetch_jlc_transcripts.py      # JLC bot
```

## Testing and Debugging

**Test single video transcript fetching:**
```bash
python tests/test_single_video.py VIDEO_ID_OR_URL
```
Tests transcript availability, fetching, storage. Detects YouTube IP blocking.

**Test Spanish→English translation:**
```bash
python tests/test_translation.py --count 3    # First 3 transcripts
python tests/test_translation.py --all        # All transcripts
python tests/test_translation.py --video-id nqYul4Np-1s
```
Translates existing Spanish transcripts from `backlog_JLC/transcripts/`, saves to `test_translations/`.

**Check video transcript availability:**
```bash
python scripts/check_video_transcript.py VIDEO_ID
```
Shows available transcripts (manual/auto-generated) by language.

**Analyze Spanish word frequencies:**
```bash
python scripts/analyze_transcript_words.py
```
Counts semantic word frequencies in Spanish transcripts (excludes 500+ stop words).

## Architecture

### Core Module Architecture

The `core/` directory provides shared components for both bots:

**`core/youtube_api.py`**: YouTube Data API v3 wrapper
- Quota tracking (get_quota_used)
- Channel/playlist operations (get_uploads_playlist_id, get_recent_videos)
- Video details with duration (get_video_details)
- YouTube Shorts detection (is_short, filter_shorts) - filters videos ≤180 seconds

**`core/transcript_fetcher.py`**: Transcript fetching with rate limiting
- Language support: English (en, en-US, en-GB), Spanish (es, es-ES, es-MX)
- Priority: manual transcripts > auto-generated
- Rate limiting: configurable delay (15s default to prevent IP blocking)
- Exponential backoff retry (fetch_with_retry)
- Uses youtube-transcript-api v1.2.3+ instance methods

**`core/translator.py`**: Spanish→English translation via GPT-4o
- Zero-shot prompting (optimal for GPT-4o per PROMPT_ENGINEERING_REFERENCE.md)
- Domain: economics/geopolitics/financial markets
- Temperature: 0.2 (factual accuracy)
- Transcription error corrections: currency (add USD), magnitudes (millones→billions), incomplete years (202X), glossary ("Main Street"→"Wall Street", "maldad"→"malice")

**`core/storage.py`**: File storage with metadata
- Creates transcripts/ and metadata/ subdirectories
- Saves transcripts with headers (Video ID, Title, Language, Type, Published)
- Manages processed_videos.json (load/save)
- Filename format: `{video_id}_{timestamp}.txt`

**`core/video_processor.py`**: Video filtering utilities
- filter_processed: removes already-processed videos
- get_video_ids: extracts video IDs from video list
- validate_video: checks required fields

### Nate AI Strategy Bot Flow (youtube_discord_bot.py)

**Purpose**: English transcripts → GPT-4o-mini summaries → Discord

1. Load `backlog_Nate/metadata/processed_videos.json`
2. Fetch 5 most recent videos from YOUTUBE_CHANNEL_ID
3. Filter out Shorts (≤180 seconds) and processed videos
4. Process up to 3 new videos per run:
   - Check transcript availability (English only)
   - Fetch transcript with 15s delay + retry logic
   - Save transcript to `backlog_Nate/transcripts/`
   - Generate structured summary (GPT-4o-mini, temperature 0.3)
   - Post to Discord with color-coded embed
   - Update processed_videos.json
5. Store summaries in `backlog_Nate/summaries/`

**Rate Limiting**: 15s delays, max 3 videos/run

### JLC Economics Bot Flow (fetch_jlc_transcripts.py)

**Purpose**: Spanish/English transcripts → GPT-4o translation → local storage

1. Load `backlog_JLC/processed_videos.json`
2. Fetch 50 most recent videos from YOUTUBE_CHANNEL_ID2
3. Filter out Shorts and processed videos
4. Process up to 5 new videos per run:
   - Check transcript availability (English/Spanish)
   - Fetch transcript with 15s delay + retry logic
   - **If Spanish**:
     - Save original to `backlog_JLC/original_transcript/`
     - Translate Spanish→English (GPT-4o, temperature 0.2)
     - Save translation to `backlog_JLC/transcripts/`
   - **If English**:
     - Save directly to `backlog_JLC/transcripts/`
   - Update processed_videos.json

**Rate Limiting**: 15s delays, max 5 videos/run

**Translation Features**: Domain-specific corrections for auto-generated Spanish transcripts (currency, magnitudes, glossary terms)

### Directory Structure

```
youtube_bot/
├── core/                                    # Shared modules
│   ├── __init__.py
│   ├── youtube_api.py
│   ├── transcript_fetcher.py
│   ├── translator.py
│   ├── storage.py
│   └── video_processor.py
├── backlog_Nate/                            # Nate bot data
│   ├── metadata/processed_videos.json
│   ├── transcripts/
│   └── summaries/
├── backlog_JLC/                             # JLC bot data
│   ├── processed_videos.json
│   ├── original_transcript/                 # Spanish originals
│   └── transcripts/                         # English (original or translated)
├── tests/
│   ├── test_single_video.py
│   └── test_translation.py
├── scripts/
│   ├── check_video_transcript.py
│   └── analyze_transcript_words.py
├── youtube_discord_bot.py                   # Nate bot (main)
├── fetch_jlc_transcripts.py                 # JLC bot (main)
└── run_bot.bat                              # Production runner for Nate bot
```

### Discord Summary Generation (Nate Bot Only)

**`summarize_transcript(transcript, video_title)` in youtube_discord_bot.py**:
- Sends full transcript to Azure OpenAI (GPT-4o-mini handles 128k context window)
- Domain-specific prompt tailored for AI strategy, automation, and technical implementation content
- Prompt structure follows Anthropic/OpenAI best practices:
  - XML tags (`<role>`, `<instructions>`, `<transcript>`, `<content_context>`, `<examples>`, `<output_format>`, `<constraints>`, `<decision_rules>`)
  - Few-shot learning with 2 domain-specific examples (AI Agent Tutorial, Eval Framework)
  - Clear decision rules for content type classification (Technical Workflow, Framework, Strategy Guide, etc.)
  - Output format optimized for dual audience: builders (technical depth) and executives (strategic insights)
  - Extracts frameworks, tools/technologies, actionable takeaways, and complexity level
- Temperature: 0.3 (factual extraction), max_tokens: 1200, frequency_penalty: 0.3
- Returns structured markdown summary with CONTENT TYPE, OVERVIEW, CORE CONTENT, ACTIONABLE TAKEAWAYS, TOOLS/TECHNOLOGIES, FOR BUILDERS, FOR EXECUTIVES, COMPLEXITY

**`post_to_discord(video_id, video_title, summary)`**:
- Parses CONTENT TYPE from summary to set dynamic color and emoji
- Color-coded embeds: Technical Workflow (Blurple ⚙️), Framework (Green 🏗️), Industry Analysis (Yellow 📊), Automation Demo (Pink 🤖), Strategy Guide (Red 🎯), Implementation Guide (Gray 📘)
- Creates Discord embed with:
  - Title with content type-specific emoji
  - Full structured summary in description (supports markdown)
  - Video thumbnail
  - "New AI Strategy Content" author section with YouTube branding
  - Timestamp in footer
- Username: "AI Strategy Digest" with YouTube avatar
- Returns True on success (HTTP 204)

## YouTube IP Blocking and Rate Limiting

**Critical Issue**: YouTube aggressively blocks transcript scraping (started August 2024)

**Current Protections**:
- 15-second delays between transcript requests (both bots)
- Reduced batch sizes (3 videos/run for Nate, 5 for JLC)
- Exponential backoff retry logic
- Error detection for HTTP 429 and IP blocking

**If Blocked**:
1. Wait 24-48 hours
2. Use different network (mobile hotspot, VPN)
3. Use residential proxy service

See `YOUTUBE_BLOCKING_SOLUTIONS.md` for comprehensive workarounds.

## State Management and Data Storage

**State Files** (processed_videos.json):
- `backlog_Nate/metadata/processed_videos.json`: Tracks Nate bot videos
- `backlog_JLC/processed_videos.json`: Tracks JLC bot videos
- Format: JSON array of video IDs
- Created automatically on first run

**Transcript Files** (.txt):
- Metadata header: Video ID, Title, Language, Type, Downloaded, Published
- Full transcript text below separator line
- Naming: `{video_id}_{timestamp}.txt`

**Summary Files** (.md, Nate bot only):
- Markdown format with video metadata
- Structured AI-generated summary
- Naming: `{video_id}_{timestamp}.md`

## Prompt Engineering Patterns

This codebase implements two distinct prompt engineering approaches based on use case and model. See `PROMPT_ENGINEERING_REFERENCE.md` for comprehensive guidance.

### Nate Bot: GPT-4o-mini Summary Generation (youtube_discord_bot.py)

**Model**: GPT-4o-mini (fast, cost-efficient, non-reasoning)
**Use Case**: English transcript → structured markdown summary
**Temperature**: 0.3 (factual extraction)

**1. XML Tag Structure**
- `<role>`: Defines AI as "expert analyst specializing in AI strategy, automation, and technical implementation"
- `<instructions>`: High-level task focused on extracting frameworks, actionable steps, tools, and strategic insights
- `<video_title>` and `<transcript>`: Clearly separated input content
- `<content_context>`: Provides channel focus (AI strategy, coding workflows, frameworks, future-of-work)
- `<examples>`: Contains few-shot learning examples
- `<output_format>`: Specifies exact structure with placeholders
- `<constraints>`: Explicit limitations (word count, bullet points, actionable focus)
- `<decision_rules>`: Numbered priority rules for content type classification

**2. Few-Shot Learning (Domain-Specific)**
- 2 AI-focused examples: "Building AI Agent with LangChain" (Technical Workflow) and "Evaluating AI Implementations" (Framework)
- Each example demonstrates complete input → output transformation
- Examples match actual channel content: tools mentioned (LangChain, Claude API, pytest), real metrics (23% to 3% hallucination reduction), budget figures ($500/month)
- Shows dual-audience approach: technical details FOR BUILDERS, strategic insights FOR EXECUTIVES
- Examples follow exact output format to ensure consistency

**3. Decision Rules Framework**
- Numbered priority ordering (1-6)
- Question format: "Is it X?" → Content Type Classification
- Covers: Technical Workflow, Framework, Industry Analysis, Automation Demo, Strategy Guide
- Explicit default case (rule 6: "If mixed or unclear → Implementation Guide")
- Rules ordered from specific → general

**4. Output Structure Enforcement**
- Explicit format template with placeholders
- Sections: CONTENT TYPE, OVERVIEW, CORE CONTENT, ACTIONABLE TAKEAWAYS, TOOLS/TECHNOLOGIES, FOR BUILDERS, FOR EXECUTIVES, COMPLEXITY
- Markdown formatting with headers (##) and bullets (-)
- Constraints specify 2-4 topic sections, 2-4 bullets per section (15-25 words each), max 400 words
- Extraction priorities: frameworks first, then actionable steps, tools/tech, code/prompts, strategic insights, real examples, metrics

**5. Model Parameters (Optimized for GPT-4o-mini)**
- Temperature: 0.3 (low for factual extraction, not creative generation)
- max_tokens: 1200 (accommodates structured output with multiple sections)
- frequency_penalty: 0.3 (reduces repetition in bullet points)
- Few-shot prompting is appropriate for GPT-4o-mini (non-reasoning model)

**6. System Message**
- Emphasizes following instructions precisely and outputting exact format
- Reinforces "expert analyst" role for credibility

**7. Domain Customization**
- Role explicitly mentions "AI strategy, automation, and technical implementation"
- Instructions emphasize "actionable" over theoretical, "avoid buzzwords"
- Content context explains channel focus (builders + executives audience)
- Extraction priorities target frameworks, tools, code, metrics (not generic insights)
- Dual-audience output: FOR BUILDERS (technical), FOR EXECUTIVES (strategic)

### JLC Bot: GPT-4o Spanish→English Translation (core/translator.py)

**Model**: GPT-4o (full-size, high-quality)
**Use Case**: Spanish economics transcript → English translation
**Temperature**: 0.2 (maximum factual accuracy)

**Approach**: Zero-shot prompting (research-backed optimal for GPT-4o translation, arXiv:2301.08745)

**Key Components**:
1. **System Message**: "Professional translator specializing in economics, geopolitics, and financial markets content"
2. **Clear Instructions**: "Translate accurately while preserving speaker's meaning, tone, and style"
3. **Domain Context**: Video title + optional topic (e.g., "Economics and financial markets analysis")
4. **Transcription Error Corrections**:
   - Currency: Add "USD" to all amounts (assumed default)
   - Magnitudes: "900.000 millones" with Fed/Treasury context = 900 billions USD
   - Incomplete years: "202" → "202X"
   - Incomplete dollar amounts: "$[UNCLEAR],XXX" with flag
   - Glossary: "Main Street" → "Wall Street", "maldad" → "malice", creator-specific phrases
   - Flag uncertainties with [VERIFY] marker
5. **Structured Prompt**: Uses clear delimiters (VIDEO CONTEXT, INSTRUCTIONS, TRANSCRIPTION ERROR CORRECTIONS, SPANISH TRANSCRIPT, ENGLISH TRANSLATION)

**Why Zero-Shot**:
- Research shows zero-shot outperforms few-shot for GPT-4o translation
- Lower token cost (no examples needed)
- Simpler prompt maintenance
- Sufficient quality with clear role definition and domain context

### Key Insights for Both Bots
- **Few-shot examples** (2) essential for GPT-4o-mini (Nate bot) but NOT used for GPT-4o translation (JLC bot)
- **Temperature matters**: 0.3 for summaries (slight variation acceptable), 0.2 for translation (maximum accuracy)
- **Domain-specific examples** outperform generic: AI agent tutorial > generic tutorial for Nate's audience
- **XML tags** improve structure clarity for complex prompts
- **Explicit decision rules** eliminate classification ambiguity (Nate bot content type detection)
- **Transcription error corrections** critical for auto-generated Spanish transcripts (JLC bot)
- **Constraints prevent verbose outputs**: 400 word max for Discord embed compatibility (Nate bot)

## Modifying Prompts

**Nate Bot Summary Prompt** (youtube_discord_bot.py:104-264):
- Located in `summarize_transcript()` function
- Edit XML tags directly in prompt string
- Test changes with a single video before deploying
- Keep examples domain-specific (AI/automation content)
- Maintain output format structure for Discord parsing

**JLC Bot Translation Prompt** (core/translator.py:130-162):
- Located in `_build_prompt()` method
- Edit TRANSCRIPTION ERROR CORRECTIONS section for new patterns
- Add glossary terms for content-creator specific phrases
- Test with `python tests/test_translation.py --count 3`
- Check for [VERIFY] and [UNCLEAR] flags in output

**Important**: Always refer to `PROMPT_ENGINEERING_REFERENCE.md` before modifying prompts. Follow model-specific best practices (GPT-4o-mini vs GPT-4o).

## Common Development Tasks

**Adding a new channel**:
1. Add `YOUTUBE_CHANNEL_ID3` to `.env`
2. Create new main script (e.g., `fetch_channel3.py`) using `fetch_jlc_transcripts.py` as template
3. Update imports to use `core/` modules
4. Create storage directory (e.g., `backlog_Channel3/`)
5. Test with single video first

**Modifying rate limits**:
- Update `DELAY_BETWEEN_REQUESTS` in main scripts (lines 40/370)
- Update `MAX_VIDEOS_PER_RUN` in main scripts (lines 39/403)
- Test with `tests/test_single_video.py` to verify blocking doesn't occur

**Adding translation glossary terms**:
1. Edit `core/translator.py` lines 143-157
2. Add new glossary entry with pattern: `"source phrase" → "target phrase"`
3. Test with `python tests/test_translation.py --count 3`
4. Check translations for [VERIFY] flags

**Debugging transcript fetching failures**:
1. Run `python scripts/check_video_transcript.py VIDEO_ID`
2. Check if transcripts exist (manual/auto)
3. If "Could not retrieve" error: YouTube IP blocking (see section above)
4. If "Transcripts disabled": Owner disabled, cannot bypass
5. If "Rate limited": Wait 15-30 minutes, increase delays

## YouTube API Quota Management

**Daily Quota**: 10,000 units (resets midnight PST)

**Quota Costs**:
- `channels().list()`: 1 unit (get uploads playlist ID)
- `playlistItems().list()`: 1 unit (get recent videos)
- `videos().list()`: 1 unit per 50 videos (video details for Shorts detection)

**Typical Run Costs**:
- Nate bot: 3 units (1 channel + 1 playlist + 1 videos batch)
- JLC bot: 3 units (same pattern)

**Quota Tracking**: Both bots call `youtube_api.get_quota_used()` at end of run

**Exceeded Quota**: Bots will fail with "quotaExceeded" error. Wait until midnight PST or request quota increase from Google Cloud Console.

## References

- `PROMPT_ENGINEERING_REFERENCE.md`: Comprehensive prompt engineering guide (Anthropic, OpenAI best practices)
- `YOUTUBE_BLOCKING_SOLUTIONS.md`: Solutions for YouTube IP blocking
- Core module docstrings: Inline documentation for all functions
- `.env.example`: Required environment variables with descriptions