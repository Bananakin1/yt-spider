# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a YouTube Discord Bot that monitors a YouTube channel for new videos, fetches their transcripts, generates AI summaries using Azure OpenAI (GPT-4o-mini), and posts structured breakdowns to Discord via webhooks.

## Setup and Environment

The project uses a Python virtual environment with dependencies in `requirements.txt`:
- `youtube-transcript-api`: Fetches video transcripts
- `google-api-python-client`: Accesses YouTube Data API
- `openai`: Azure OpenAI client for summarization
- `python-dotenv`: Environment variable management
- `requests`: Discord webhook posting

Required environment variables in `.env` (see `.env.example`):
- `YOUTUBE_API_KEY`: YouTube Data API v3 key
- `YOUTUBE_CHANNEL_ID`: Target channel ID to monitor
- `DISCORD_WEBHOOK_URL`: Discord webhook for posting summaries
- `AZURE_OPENAI_ENDPOINT`: Azure OpenAI service endpoint
- `AZURE_OPENAI_API_KEY`: Azure OpenAI API key
- `AZURE_OPENAI_DEPLOYMENT_NAME`: Deployment name (e.g., "gpt-4o-mini")
- `AZURE_OPENAI_API_VERSION`: API version (default: "2024-02-15-preview")

## Running the Bot

**Production run:**
```bash
run_bot.bat
```
This activates the venv, runs the bot, and logs output to `logs/bot_YYYY-MM-DD_HH-MM-SS.log`

**Manual run (Windows):**
```bash
venv\Scripts\activate.bat
python youtube_discord_bot.py
```

**Manual run (Unix/Linux):**
```bash
source venv/bin/activate
python youtube_discord_bot.py
```

## Testing and Debugging

**Check if a video has transcripts:**
```bash
python check_video_transcript.py VIDEO_ID
```
Shows available transcripts (manual/auto-generated) and tests English transcript fetching.

**Test full pipeline (transcript → summary → Discord):**
```bash
python test_single_video.py
```
Edit `TEST_VIDEO_ID` in the file to test with different videos.

## Architecture

### Main Bot Flow (youtube_discord_bot.py)

1. **Load Configuration**: Validates all required environment variables
2. **Load Processed Videos**: Reads `processed_videos.json` to avoid reprocessing
3. **Fetch Channel Videos**:
   - Gets uploads playlist ID via YouTube Data API
   - Fetches 5 most recent videos from playlist
4. **Process New Videos** (limit: 3 per run):
   - Skip if already in `processed_videos.json`
   - Check transcript availability (handles disabled transcripts, rate limits)
   - Fetch transcript (tries English first, then any available language)
   - Generate structured summary with Azure OpenAI
   - Post to Discord with embed format
   - Save video ID to `processed_videos.json`

### Key Functions

**`check_transcript_availability(video_id)`**:
- Returns `(bool, str)` indicating availability and status message
- Handles transcripts disabled, rate limiting, and language availability

**`get_transcript(video_id)`**:
- Tries English transcripts first (`['en', 'en-US', 'en-GB']`)
- Falls back to any available language
- Returns transcript text or None on failure

**`summarize_transcript(transcript, video_title)`**:
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

### Transcript Context Window

GPT-4o-mini has a 128k token context window. A 20-minute video with 20,000+ characters (approximately 5,000-6,000 tokens) is well within limits. The bot sends the full transcript without truncation.

### Processing Limitations

- Processes maximum 3 new videos per run to handle variable upload schedules
- Skips videos without English transcripts or when transcripts are disabled
- Handles YouTube rate limiting (HTTP 429) gracefully
- Stores processed video IDs to prevent duplicates

## State Management

**`processed_videos.json`**: JSON array of video IDs that have been successfully processed and posted to Discord. Created automatically on first run.

## Data Storage

The bot automatically saves transcripts and summaries to local files:

**Directory Structure:**
```
data/
├── transcripts/
│   └── VIDEO_ID_YYYY-MM-DD_HH-MM-SS.txt
└── summaries/
    └── VIDEO_ID_YYYY-MM-DD_HH-MM-SS.md
```

**Transcript Files** (`data/transcripts/`):
- Plain text format (.txt)
- Includes video metadata (ID, title, download timestamp)
- Contains full transcript text
- Named with video ID and timestamp for uniqueness

**Summary Files** (`data/summaries/`):
- Markdown format (.md)
- Includes video metadata and URL
- Contains AI-generated structured summary
- Named with video ID and timestamp for uniqueness

**Functions:**
- `ensure_data_directories()`: Creates directories on first run
- `save_transcript(video_id, video_title, transcript_text)`: Saves transcript with metadata
- `save_summary(video_id, video_title, summary_text)`: Saves summary with metadata

**Note:** The `data/` directory is excluded from version control via `.gitignore`.

## Prompt Engineering Patterns

This codebase implements comprehensive prompt engineering patterns following Anthropic and OpenAI best practices, specifically tailored for AI strategy and technical implementation content.

### Implemented in `summarize_transcript()`:

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

### Key Insights
- **XML tags** significantly improve Claude's prompt parsing (Anthropic trained specifically on XML)
- **Few-shot examples** (2-3) essential for GPT-4o-mini consistency without excessive tokens
- **Domain-specific examples** outperform generic examples: AI agent tutorial > FastAPI tutorial for this channel
- **Lower temperature** (0.3) produces consistent, factual summaries vs. creative writing (0.7+)
- **Explicit decision rules** eliminate classification ambiguity
- **Dual-audience format** (FOR BUILDERS/FOR EXECUTIVES) serves mixed technical/business audience
- **Extraction priorities** guide model to focus on actionable content (frameworks, tools, metrics)
- **Constraints prevent verbose outputs** and ensure Discord embed compatibility (400 word max)