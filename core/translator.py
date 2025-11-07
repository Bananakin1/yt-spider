"""
Spanish to English translation using Azure OpenAI GPT-4o.

Provides high-quality translation for YouTube transcripts with:
- Economics/geopolitics domain specialization
- Auto-generated transcript error handling
- Zero-shot prompting (research-backed optimal approach)
- Cost-efficient token usage
"""

from typing import Optional
from openai import AzureOpenAI


class TranscriptTranslator:
    """Translates Spanish YouTube transcripts to English using GPT-4o."""

    # System message defining translator role and expertise
    # Research shows clear role definition > few-shot examples for translation
    SYSTEM_MESSAGE = """You are a professional translator specializing in economics, geopolitics, and financial markets content from Spanish-language YouTube channels.

Your expertise includes:
- Accurately translating technical economic and financial terminology
- Preserving the speaker's tone, style, and intended meaning
- Handling auto-generated transcript imperfections gracefully
- Using natural, fluent English appropriate for a professional audience interested in markets and policy analysis"""

    def __init__(
        self,
        azure_openai_endpoint: str,
        azure_openai_key: str,
        azure_openai_deployment: str,
        azure_openai_api_version: str = "2024-02-15-preview"
    ):
        """
        Initialize translator with Azure OpenAI credentials.

        Args:
            azure_openai_endpoint: Azure OpenAI service endpoint
            azure_openai_key: API key
            azure_openai_deployment: Deployment name for translation model (GPT-4o)
            azure_openai_api_version: API version
        """
        self.client = AzureOpenAI(
            api_key=azure_openai_key,
            api_version=azure_openai_api_version,
            azure_endpoint=azure_openai_endpoint
        )
        self.deployment = azure_openai_deployment
        self.translations_made = 0

    def translate(
        self,
        spanish_transcript: str,
        video_title: str,
        video_topic: Optional[str] = None
    ) -> Optional[str]:
        """
        Translate Spanish transcript to English.

        Uses zero-shot prompting with clear instructions and domain context.
        Research shows this approach optimal for GPT-4o Spanish-English translation,
        outperforming few-shot at lower token cost (arXiv:2301.08745).

        Args:
            spanish_transcript: Spanish text to translate
            video_title: Video title for context
            video_topic: Optional topic description (e.g., "Bitcoin analysis", "central bank policy")

        Returns:
            English translation or None if translation fails
        """
        try:
            # Build user prompt with context and clear instructions
            user_prompt = self._build_prompt(
                spanish_transcript=spanish_transcript,
                video_title=video_title,
                video_topic=video_topic
            )

            # Call Azure OpenAI with optimal parameters for translation
            response = self.client.chat.completions.create(
                model=self.deployment,
                messages=[
                    {"role": "system", "content": self.SYSTEM_MESSAGE},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.2,  # Low for factual accuracy (PROMPT_ENGINEERING_REFERENCE.md)
                max_tokens=8000,  # Sufficient for long transcripts
                frequency_penalty=0.0,  # Not needed for translation
                presence_penalty=0.0
            )

            self.translations_made += 1
            return response.choices[0].message.content

        except Exception as e:
            print(f"    [ERROR] Translation failed: {str(e)[:100]}")
            return None

    def _build_prompt(
        self,
        spanish_transcript: str,
        video_title: str,
        video_topic: Optional[str]
    ) -> str:
        """
        Build translation prompt with context and instructions.

        Follows GPT-4o prompting best practices:
        - Clear, specific instructions
        - Domain context
        - Structured format with delimiters
        - Output format specification

        Args:
            spanish_transcript: Text to translate
            video_title: Video title
            video_topic: Optional topic description

        Returns:
            Formatted prompt string
        """
        # Build topic context if provided
        topic_context = ""
        if video_topic:
            topic_context = f"- Topic: {video_topic}\n"

        # Prompt structure optimized for translation quality
        prompt = f"""Translate the following Spanish YouTube transcript to English.

VIDEO CONTEXT:
- Title: {video_title}
{topic_context}- Source: Auto-generated YouTube transcript (may contain minor transcription errors)

INSTRUCTIONS:
- Translate accurately while preserving the speaker's meaning, tone, and style
- Use correct technical terminology for economics, finance, and geopolitics
- Correct obvious transcription errors (missing punctuation, run-on sentences) while translating
- Maintain the conversational tone appropriate for video content
- Output ONLY the English translation without explanations or notes

TRANSCRIPTION ERROR CORRECTIONS:
1. Currency: Add "USD" to all amounts (assumed default)
2. Magnitudes:
   - "900.000 millones" with context of Fed/Treasury = 900 billions
   - Verify magnitude makes sense for context
3. Incomplete years ("202"): Mark as "202X"
4. Incomplete dollar amounts: Output as "$[UNCLEAR],XXX" and flag
5. Glossary for specific content-creator terms and transcribe errors:
   - "Main Street" → "Wall Street"
   - "una maldad" / "maldades" → "a malice" / "malices" (NEVER "badness", "evil")
   - "¿Queda la idea clara?" → "Is that clear?"
   - "¿Me explico?" → "Do you follow?"
   - Correct based on context

IF UNSURE about any correction, preserve original and add [VERIFY] marker.

SPANISH TRANSCRIPT:
{spanish_transcript}

ENGLISH TRANSLATION:"""

        return prompt

    def get_translations_made(self) -> int:
        """
        Get total number of translations performed.

        Returns:
            Translation count
        """
        return self.translations_made
