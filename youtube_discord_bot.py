import os
import sys
import json
import requests
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from openai import AzureOpenAI

# Add core modules to path
sys.path.insert(0, str(Path(__file__).parent))

from core import YouTubeAPI, TranscriptFetcher, VideoProcessor

# Load environment variables
load_dotenv()

# Configuration
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')
YOUTUBE_CHANNEL_ID = os.getenv('YOUTUBE_CHANNEL_ID')
DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL')
AZURE_OPENAI_ENDPOINT = os.getenv('AZURE_OPENAI_ENDPOINT')
AZURE_OPENAI_API_KEY = os.getenv('AZURE_OPENAI_API_KEY')
AZURE_OPENAI_DEPLOYMENT = os.getenv('AZURE_OPENAI_DEPLOYMENT_NAME')
AZURE_OPENAI_API_VERSION = os.getenv('AZURE_OPENAI_API_VERSION', '2024-02-15-preview')

# Directories for storing transcripts and summaries
DATA_DIR = Path(__file__).parent / 'backlog_Nate'
METADATA_DIR = DATA_DIR / 'metadata'
TRANSCRIPTS_DIR = DATA_DIR / 'transcripts'
SUMMARIES_DIR = DATA_DIR / 'summaries'

# File to track processed videos
PROCESSED_VIDEOS_FILE = METADATA_DIR / 'processed_videos.json'


def load_processed_videos():
    """Load the list of already processed video IDs"""
    if PROCESSED_VIDEOS_FILE.exists():
        with open(PROCESSED_VIDEOS_FILE, 'r') as f:
            return json.load(f)
    return []


def save_processed_videos(video_ids):
    """Save the list of processed video IDs"""
    with open(PROCESSED_VIDEOS_FILE, 'w') as f:
        json.dump(video_ids, f, indent=2)


def ensure_data_directories():
    """Create data directories if they don't exist"""
    METADATA_DIR.mkdir(parents=True, exist_ok=True)
    TRANSCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
    SUMMARIES_DIR.mkdir(parents=True, exist_ok=True)


def save_transcript(video_id, video_title, transcript_text):
    """Save transcript to file"""
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    filename = f"{video_id}_{timestamp}.txt"
    filepath = TRANSCRIPTS_DIR / filename

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(f"Video ID: {video_id}\n")
        f.write(f"Title: {video_title}\n")
        f.write(f"Downloaded: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"{'='*80}\n\n")
        f.write(transcript_text)

    print(f"    [SAVED] Transcript saved to: {filepath.name}")
    return filepath


def save_summary(video_id, video_title, summary_text):
    """Save summary to file"""
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    filename = f"{video_id}_{timestamp}.md"
    filepath = SUMMARIES_DIR / filename

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(f"# {video_title}\n\n")
        f.write(f"**Video ID:** {video_id}\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**Video URL:** https://www.youtube.com/watch?v={video_id}\n\n")
        f.write(f"{'---'}\n\n")
        f.write(summary_text)

    print(f"    [SAVED] Summary saved to: {filepath.name}")
    return filepath




def summarize_transcript(transcript, video_title):
    """Use Azure OpenAI to summarize the transcript"""
    try:
        client = AzureOpenAI(
            api_key=AZURE_OPENAI_API_KEY,
            api_version=AZURE_OPENAI_API_VERSION,
            azure_endpoint=AZURE_OPENAI_ENDPOINT
        )

        prompt = f"""# VIDEO TITLE
{video_title}

# TRANSCRIPT
{transcript}

# CONTENT CONTEXT
This channel focuses on AI strategy for builders and executives, coding workflows and automation guides, frameworks from real AI implementations, and actionable playbooks.

# EXAMPLES

## Example 1: Technical Workflow

**Sample Transcript:**
Today I'll show you how to build an AI agent using LangChain and Claude. First, install langchain and anthropic packages. Set up your Claude API key. Create a ReAct agent that can use tools. Define your tools as Python functions with docstrings. The agent uses chain-of-thought reasoning to decide which tools to call. Add a DuckDuckGo search tool for real-time information. Test with complex queries that require multiple tool calls. Deploy using FastAPI and Docker. Pro tip: keep tools focused and well-documented for best results.

**Sample Output:**
CONTENT TYPE: Technical Workflow

OVERVIEW: Step-by-step guide to building a ReAct AI agent using LangChain and Claude API, covering tool creation, chain-of-thought reasoning, and production deployment.

CORE CONTENT:

## Setup & Architecture
- Install langchain and anthropic packages, configure Claude API authentication
- Implement ReAct pattern: agent uses chain-of-thought reasoning to select and execute tools
- Define tools as Python functions with clear docstrings for agent understanding

## Tool Integration & Testing
- Add DuckDuckGo search tool for real-time information retrieval
- Test with complex multi-step queries requiring sequential tool calls
- Keep tools focused and well-documented for optimal agent performance

## Production Deployment
- Deploy agent as FastAPI endpoint for API access
- Containerize with Docker for consistent production environment

ACTIONABLE TAKEAWAYS:
- Use ReAct pattern for transparent agent reasoning and debugging
- Tool docstrings are critical - they guide the agent's tool selection
- Start with 2-3 focused tools before scaling to complex toolsets

TOOLS/TECHNOLOGIES: LangChain, Claude API (Anthropic), DuckDuckGo API, FastAPI, Docker

FOR BUILDERS: ReAct pattern provides explicit reasoning traces for debugging agent behavior
FOR EXECUTIVES: AI agents can autonomously handle multi-step workflows with proper tool design

## Example 2: Framework

**Sample Transcript:**
Let's talk about evaluating AI implementations. Many companies rush to production without proper metrics. Start with the eval framework: define success criteria before building. For LLM apps, use semantic similarity scores, not exact matches. Implement automated evals with pytest and your test dataset. Track four metrics: accuracy, latency, cost per request, and failure rate. Use Claude's new prompt caching to reduce costs by 90% on repeated contexts. Run evals on every PR with GitHub Actions. Compare model versions side-by-side using A/B testing in production. Real example: we reduced hallucinations from 23% to 3% by iterating on prompts using this framework. Budget $500/month minimum for eval infrastructure.

**Sample Output:**
CONTENT TYPE: Framework

OVERVIEW: Comprehensive evaluation framework for AI/LLM implementations, covering metrics definition, automated testing infrastructure, and cost optimization strategies with real-world results.

CORE CONTENT:

## Evaluation Framework Foundation
- Define success criteria before building: avoid post-hoc justification of results
- Use semantic similarity for LLM outputs, not brittle exact string matching
- Track four core metrics: accuracy, latency, cost per request, failure rate

## Implementation & Automation
- Build automated eval pipeline with pytest and curated test datasets
- Integrate evals into CI/CD: run on every PR via GitHub Actions
- A/B test model versions in production for real-world performance comparison

## Cost Optimization & Results
- Claude's prompt caching: 90% cost reduction on repeated contexts
- Real case study: hallucination rate improved from 23% to 3% through iterative prompt refinement
- Budget allocation: minimum $500/month for eval infrastructure

ACTIONABLE TAKEAWAYS:
- Implement evals before scaling to production to catch issues early
- Semantic similarity metrics prevent false negatives from paraphrasing
- Prompt caching provides immediate ROI for high-volume applications

TOOLS/TECHNOLOGIES: Claude API, pytest, GitHub Actions, prompt caching

FOR BUILDERS: Automated evals in CI/CD catch regressions before production deployment
FOR EXECUTIVES: Proper eval framework reduces hallucinations by 85%+ and prevents costly production failures

---

# TASK
Analyze the transcript above and extract frameworks, actionable steps, tools/technologies mentioned, and strategic insights. Focus on what viewers can DO with this information. Avoid buzzwords - be concrete and practical.

# OUTPUT FORMAT
Provide your summary in this structure:

CONTENT TYPE: [Strategy Guide/Technical Workflow/Framework/Automation Demo/Industry Analysis/Implementation Guide]

OVERVIEW: [1-2 sentences: What problem does this solve? What will viewers learn?]

CORE CONTENT:

## [Topic Section 1]
- [Specific point with details - tools, methods, or insights]
- [Specific point with details]
- [Specific point with details]

## [Topic Section 2]
- [Specific point with details]
- [Specific point with details]

[2-4 total sections based on content]

ACTIONABLE TAKEAWAYS:
- [What can viewers immediately apply or implement?]
- [What decision or action should they take?]
- [What framework or approach can they use?]

TOOLS/TECHNOLOGIES: [List specific tools, platforms, frameworks, or "None mentioned"]

FOR BUILDERS: [Technical insight or implementation detail most relevant to developers]
FOR EXECUTIVES: [Strategic insight or business implication most relevant to decision-makers]

# CONSTRAINTS
- Use 2-4 main topic sections (not 5+)
- Each section: 2-4 concise bullets (15-25 words max per bullet)
- Maximum 400 words total
- Be specific: name tools, mention numbers, cite examples
- Separate technical depth (FOR BUILDERS) from strategic clarity (FOR EXECUTIVES)
- If no tools/frameworks are mentioned explicitly, write "None specified - conceptual discussion"
- Focus on ACTIONABLE over THEORETICAL

# DECISION RULES (Apply in Order)
1. Does it teach a technical implementation? → CONTENT TYPE: Technical Workflow
2. Does it present a structured methodology or process? → CONTENT TYPE: Framework
3. Does it analyze AI trends or industry direction? → CONTENT TYPE: Industry Analysis
4. Does it show how to automate something specific? → CONTENT TYPE: Automation Demo
5. Does it focus on business/organizational AI adoption? → CONTENT TYPE: Strategy Guide
6. If mixed or unclear → CONTENT TYPE: Implementation Guide"""

        response = client.chat.completions.create(
            model=AZURE_OPENAI_DEPLOYMENT,
            messages=[
                {
                    "role": "system",
                    "content": """You are an expert analyst specializing in AI strategy, automation, and technical implementation content. Your audience includes both technical builders and business executives who need clear, actionable insights.

You create comprehensive, well-structured summaries that extract frameworks, actionable steps, and specific tools while avoiding buzzwords. You follow instructions precisely and output content in the exact format specified."""
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,  # Balanced for analytical summaries (0.4-0.7 range per OpenAI/Azure guidance)
            max_tokens=1500,
            frequency_penalty=0.3,  # Reduce repetitive phrasing
            presence_penalty=0.1    # Encourage diverse topic coverage
        )

        return response.choices[0].message.content
    except Exception as e:
        print(f"Error summarizing transcript: {e}")
        return None


def post_to_discord(video_id, video_title, summary):
    """Post the summary to Discord via webhook"""
    try:
        video_url = f"https://www.youtube.com/watch?v={video_id}"

        # Parse content type from summary to set appropriate color and emoji
        content_type = "Implementation Guide"
        if "CONTENT TYPE:" in summary:
            type_line = summary.split('\n')[0]
            content_type = type_line.replace("CONTENT TYPE:", "").strip()

        # Color and emoji mapping based on content type
        type_config = {
            "Technical Workflow": {"color": 0x5865F2, "emoji": "⚙️"},  # Blurple
            "Framework": {"color": 0x57F287, "emoji": "🏗️"},  # Green
            "Industry Analysis": {"color": 0xFEE75C, "emoji": "📊"},  # Yellow
            "Automation Demo": {"color": 0xEB459E, "emoji": "🤖"},  # Pink
            "Strategy Guide": {"color": 0xED4245, "emoji": "🎯"},  # Red
            "Implementation Guide": {"color": 0x99AAB5, "emoji": "📘"}  # Gray
        }

        config = type_config.get(content_type, type_config["Implementation Guide"])

        # Format the description with better structure
        # Keep the full summary but ensure proper markdown formatting
        formatted_summary = summary

        embed = {
            "title": f"{config['emoji']} {video_title}",
            "description": formatted_summary,
            "url": video_url,
            "color": config["color"],
            "footer": {
                "text": f"Posted on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            },
            "thumbnail": {
                "url": f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"
            },
            "author": {
                "name": "New AI Strategy Content",
                "icon_url": "https://www.youtube.com/s/desktop/d743f786/img/favicon_96x96.png"
            }
        }

        data = {
            "username": "Capuccino",
            "embeds": [embed]
        }

        response = requests.post(DISCORD_WEBHOOK_URL, json=data)

        if response.status_code == 204:
            print(f"Successfully posted to Discord: {video_title}")
            return True
        else:
            print(f"Failed to post to Discord: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"Error posting to Discord: {e}")
        return False


def main():
    """Main function to process new videos"""
    print(f"\n{'='*60}")
    print(f"YouTube Discord Bot - Running at {datetime.now()}")
    print(f"{'='*60}\n")

    # Validate configuration
    required_vars = {
        'YOUTUBE_API_KEY': YOUTUBE_API_KEY,
        'YOUTUBE_CHANNEL_ID': YOUTUBE_CHANNEL_ID,
        'DISCORD_WEBHOOK_URL': DISCORD_WEBHOOK_URL,
        'AZURE_OPENAI_ENDPOINT': AZURE_OPENAI_ENDPOINT,
        'AZURE_OPENAI_API_KEY': AZURE_OPENAI_API_KEY,
        'AZURE_OPENAI_DEPLOYMENT_NAME': AZURE_OPENAI_DEPLOYMENT
    }

    missing_vars = [var for var, value in required_vars.items() if not value]
    if missing_vars:
        print(f"ERROR: Missing required environment variables: {', '.join(missing_vars)}")
        print("Please check your .env file")
        return

    try:
        # Initialize core components
        youtube_api = YouTubeAPI(YOUTUBE_API_KEY)
        transcript_fetcher = TranscriptFetcher(delay_seconds=15.0)  # Increased from 1.5 to prevent IP blocking

        # Ensure data directories exist
        ensure_data_directories()

        # Load processed videos
        processed_videos = load_processed_videos()
        print(f"Loaded {len(processed_videos)} previously processed videos")

        # Get uploads playlist ID
        print(f"Fetching uploads playlist for channel: {YOUTUBE_CHANNEL_ID}")
        playlist_id = youtube_api.get_uploads_playlist_id(YOUTUBE_CHANNEL_ID)
        print(f"Uploads playlist ID: {playlist_id}")

        # Get recent videos
        print(f"\nFetching recent videos...")
        recent_videos = youtube_api.get_recent_videos(playlist_id, max_results=5)
        print(f"Found {len(recent_videos)} recent videos")

        # Get video details for Shorts detection
        print(f"Checking for YouTube Shorts...")
        video_ids = VideoProcessor.get_video_ids(recent_videos)
        video_details = youtube_api.get_video_details(video_ids)

        # Filter out Shorts
        filtered_videos = youtube_api.filter_shorts(recent_videos, video_details)
        shorts_count = len(recent_videos) - len(filtered_videos)
        if shorts_count > 0:
            print(f"Filtered out {shorts_count} YouTube Short(s)")
        print(f"Regular videos: {len(filtered_videos)}")

        # Process new videos (limit to 3 per run)
        new_videos_count = 0
        max_videos_per_run = 3

        for video in filtered_videos:
            # Stop if we've already processed the maximum for this run
            if new_videos_count >= max_videos_per_run:
                print(f"\n  [INFO] Reached processing limit ({max_videos_per_run} videos per run)")
                print(f"  [INFO] Remaining new videos will be processed in the next run")
                break
            video_id = video['video_id']
            video_title = video['title']

            if video_id in processed_videos:
                print(f"  [SKIP] Already processed: {video_title}")
                continue

            print(f"\n  [NEW] Processing NEW video: {video_title}")
            print(f"    Video ID: {video_id}")

            # Check transcript availability first
            print(f"    Checking transcript availability...")
            is_available, status_message, lang = transcript_fetcher.check_availability(video_id)
            print(f"    Status: {status_message}")

            if not is_available:
                print(f"    [SKIP] {status_message}")
                continue

            # Get transcript with retry logic
            print(f"    Fetching transcript...")
            transcript_data = transcript_fetcher.fetch_with_retry(
                video_id,
                prefer_english=True,
                max_retries=3
            )

            if not transcript_data:
                print(f"    [ERROR] Could not fetch transcript, skipping")
                continue

            transcript = transcript_data['text']
            print(f"    [OK] Transcript fetched ({len(transcript)} characters, {transcript_data['language'].upper()}, {transcript_data['type']})")

            # Save transcript to file
            save_transcript(video_id, video_title, transcript)

            # Summarize with Azure OpenAI
            print(f"    Generating summary with Azure OpenAI...")
            summary = summarize_transcript(transcript, video_title)
            if not summary:
                print(f"    [ERROR] Could not generate summary, skipping")
                continue

            print(f"    [OK] Summary generated")

            # Save summary to file
            save_summary(video_id, video_title, summary)

            # Post to Discord
            print(f"    Posting to Discord...")
            if post_to_discord(video_id, video_title, summary):
                print(f"    [OK] Posted to Discord successfully")
                # Mark as processed
                processed_videos.append(video_id)
                save_processed_videos(processed_videos)
                new_videos_count += 1
            else:
                print(f"    [ERROR] Failed to post to Discord")

        print(f"\n{'='*60}")
        print(f"Processing complete: {new_videos_count} new video(s) processed")
        print(f"API quota used: {youtube_api.get_quota_used()} units")
        print(f"{'='*60}\n")

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
