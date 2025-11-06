# Prompt Engineering Reference Guide

**Version:** 1.0
**Last Updated:** 2025-11-04
**Purpose:** Comprehensive reference for prompting LLMs based on official documentation from Anthropic, OpenAI, and industry research

---

## Table of Contents

1. [Universal Best Practices](#universal-best-practices)
2. [Claude Models (Sonnet 4.5)](#claude-models-sonnet-45)
3. [OpenAI Non-Reasoning Models (GPT-4o-mini)](#openai-non-reasoning-models-gpt-4o-mini)
4. [OpenAI Reasoning Models (o1/o3 series)](#openai-reasoning-models-o1o3-series)
5. [Model Selection Guide](#model-selection-guide)
6. [Quick Reference Tables](#quick-reference-tables)

---

## Universal Best Practices

These principles apply across all LLM providers and model types.

### 1. Clarity and Specificity

**Principle:** Be as clear and specific as possible. Ambiguity leads to poor results.

**Bad Example:**
```
Write about AI.
```

**Good Example:**
```
Write a 300-word explanation of transformer architecture for software engineers
with 2-3 years experience. Include how attention mechanisms work and why they're
effective. Avoid heavy mathematics.
```

**Source:** OpenAI, Anthropic, Google Cloud best practices

---

### 2. Structured Prompt Format

**Recommended Structure:**

```
<role>
You are [specific expert role with relevant experience]
</role>

<context>
[Background information relevant to the task]
</context>

<instructions>
[Clear, specific task description]
</instructions>

<constraints>
- [Limitation 1]
- [Limitation 2]
- [Limitation 3]
</constraints>

<examples>
[2-3 input-output demonstrations]
</examples>

<output_format>
[Exact structure desired]
</output_format>
```

**Why It Works:** Separates concerns, reduces ambiguity, makes prompts maintainable.

**Source:** Anthropic XML Tags Guide, PromptingGuide.ai

---

### 3. Provide Context

**Principle:** Include relevant background information to guide the model's understanding.

**Example:**

```
<context>
Your response will be read aloud by text-to-speech software for visually
impaired users.
</context>

<instructions>
Explain how to reset a password.
</instructions>

<constraints>
- Never use ellipses (...) - they create awkward pauses
- Use complete sentences only
- Avoid abbreviations
- Keep sentences under 20 words
</constraints>
```

**Source:** Anthropic Claude 4 Best Practices

---

### 4. Iterative Refinement

**Principle:** Treat prompt engineering as an iterative process.

**Process:**
1. Start simple and clear
2. Test with representative data
3. Measure performance (accuracy, format compliance, etc.)
4. Identify failure patterns
5. Refine prompt based on observations
6. Repeat until metrics meet thresholds

**Anti-Pattern:** Giving up after first attempt or over-engineering initially.

**Source:** OpenAI Best Practices, The Prompt Report (arXiv:2406.06608)

---

### 5. Few-Shot Prompting (Non-Reasoning Models Only)

**When to Use:** Non-reasoning models (GPT-4, GPT-4o-mini, Claude standard)

**When NOT to Use:** Reasoning models (o1, o3, Claude Extended Thinking)

**Best Practices:**
- Use 2-5 diverse, high-quality examples
- Cover common cases AND edge cases
- Place best example last (recency effect)
- Ensure examples match desired output format exactly

**Example:**

```
<examples>
<example>
Input: "Ship my order to 123 Main St, Austin TX 78701"
Output: {"action": "shipping", "address": "123 Main St", "city": "Austin", "state": "TX", "zip": "78701"}
</example>

<example>
Input: "Cancel order #4829"
Output: {"action": "cancel", "order_id": "4829"}
</example>

<example>
Input: "What's my order status?"
Output: {"action": "status_check", "order_id": null}
</example>
</examples>

Now process: "Update shipping address to 456 Oak Ave"
```

**Source:** OpenAI, Anthropic, PromptingGuide.ai Few-Shot Techniques

---

### 6. Chain-of-Thought (Traditional Models Only)

**When to Use:**
- Traditional models (GPT-4, GPT-4o-mini, Claude standard)
- Tasks requiring multi-step reasoning
- Models with 100B+ parameters

**When NOT to Use:**
- Reasoning models (they do this automatically)
- Simple lookup tasks
- Small models (<100B parameters)

**Implementation:**

```
<instructions>
Solve this problem step by step. Show your reasoning for each step before
providing the final answer.
</instructions>

<problem>
A store had 45 items. They sold 18 in the morning and received a shipment
of 30 items in the afternoon. How many items do they have now?
</problem>

Expected format:
Step 1: [reasoning]
Step 2: [reasoning]
Final Answer: [result]
```

**Source:** Chain-of-Thought Prompting (arXiv:2201.11903), OpenAI Cookbook

---

### 7. Output Format Specification

**Principle:** Always specify exact format desired.

**For JSON:**

```
<output_format>
Return a JSON object matching this schema:
{
  "sentiment": "positive" | "negative" | "neutral",
  "confidence": number (0.0-1.0),
  "key_phrases": string[],
  "reasoning": string
}
</output_format>
```

**For Structured Text:**

```
<output_format>
CONTENT TYPE: [Classification]
OVERVIEW: [1-2 sentences]
KEY POINTS:
- [Point 1]
- [Point 2]
CONCLUSION: [1 sentence]
</output_format>
```

**Source:** Humanloop Structured Outputs, OpenAI Structured Outputs Guide

---

### 8. Temperature Guidelines

**For Non-Reasoning Models:**

| Temperature | Use Case | Example |
|-------------|----------|---------|
| 0.0 - 0.3 | Factual, deterministic | Data extraction, classification, Q&A |
| 0.4 - 0.7 | Balanced | General content, summaries, analysis |
| 0.8 - 1.0 | Creative | Brainstorming, creative writing, diverse outputs |

**Important:** Reasoning models don't support temperature control.

**Source:** OpenAI API Documentation, GPTforWork Temperature Guide

---

### 9. Context Window Management

**Strategies:**

1. **Prioritize Critical Information**
   - Place most important content at the beginning AND end
   - Middle content is recalled less accurately

2. **Chunk Large Documents**
   ```
   Process document in segments:
   Segment 1 → Summary 1
   Segment 2 → Summary 2
   Segment 3 → Summary 3
   All summaries → Final synthesis
   ```

3. **Use Markers for Key Information**
   ```
   <critical>This information is essential</critical>
   <reference>Background information</reference>
   ```

**Source:** Anthropic Long Context Tips, PromptingGuide.ai Context Engineering

---

### 10. Validation and Error Handling

**Always Validate Outputs:**

1. **Schema Validation:** Structure matches expected format
2. **Semantic Validation:** Content makes logical sense
3. **Range Validation:** Values within acceptable bounds
4. **Format Validation:** Dates, emails, URLs are valid

**Implement Fallbacks:**

```python
# Pseudo-code
response = llm.generate(prompt)
if not validate(response):
    response = llm.generate(simplified_prompt)
    if not validate(response):
        response = fallback_model.generate(prompt)
```

**Source:** Portkey Retries and Fallbacks, LangChain Error Handling

---

## Claude Models (Sonnet 4.5)

**Model ID:** `claude-sonnet-4-5-20250929`
**Context Window:** 200,000 tokens (1M available in beta)
**Strengths:** Long-horizon reasoning, agentic tasks, coding, precise instruction following

### The Claude Prompting Hierarchy

Anthropic recommends this ranked approach:

1. **Be Clear & Direct** - Most important
2. **Use Examples** - Show, don't just tell
3. **Give Claude a Role** - Prime as expert
4. **Use XML Tags** - Structure with semantic tags
5. **Chain Prompts** - Break complex tasks into steps

**Source:** https://docs.claude.com/en/docs/build-with-claude/prompt-engineering/claude-4-best-practices

---

### XML Tags (Claude-Specific Optimization)

**Why XML for Claude:** Claude was specifically trained with XML tags in training data.

**Benefits:**
- 20-30% accuracy improvement on complex tasks
- Clearer separation of prompt components
- Easier parsing and modification

**Recommended Tags:**

```xml
<role>Expert persona</role>
<instructions>Task directives</instructions>
<context>Background information</context>
<examples>Demonstrations</examples>
<transcript>Long-form content</transcript>
<document>Source materials</document>
<thinking>Step-by-step reasoning</thinking>
<answer>Final response</answer>
<constraints>Limitations</constraints>
<output_format>Structure requirements</output_format>
```

**Example:**

```xml
<role>
You are an expert technical writer specializing in API documentation.
</role>

<instructions>
Document this API endpoint clearly for junior developers.
</instructions>

<context>
This is a payment processing API. Security is critical.
</context>

<constraints>
- Maximum 200 words
- Include security warnings
- Provide code example
</constraints>

<document>
[API specification here]
</document>

<output_format>
1. Endpoint Overview
2. Parameters
3. Response Format
4. Security Considerations
5. Code Example
</output_format>
```

**Source:** https://docs.claude.com/en/docs/build-with-claude/prompt-engineering/use-xml-tags

---

### System Messages (Role Prompting)

**Most Powerful Technique for Claude:**

```python
import anthropic

client = anthropic.Anthropic()
response = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    system="You are a Fortune 500 CFO with 20 years experience in financial analysis and risk assessment.",
    messages=[
        {"role": "user", "content": "Analyze this quarterly report..."}
    ]
)
```

**Key Insight:** Specific roles yield better results than generic descriptions.

**Better:** "CFO with 20 years experience in financial analysis"
**Worse:** "financial expert"

**Source:** https://docs.claude.com/en/docs/build-with-claude/prompt-engineering/system-prompts

---

### Prefilling (Claude Unique Feature)

**What It Is:** Start the assistant's response to guide output format.

**Use Cases:**

1. **Force JSON Output**
```python
messages=[
    {"role": "user", "content": "Analyze this data..."},
    {"role": "assistant", "content": "{"}  # Forces JSON
]
```

2. **Control Format**
```python
messages=[
    {"role": "user", "content": "Summarize..."},
    {"role": "assistant", "content": "## Executive Summary\n\n"}
]
```

3. **Skip Preambles**
```python
# Without prefill: "Certainly! Here's the analysis..."
# With prefill: Goes straight to content
{"role": "assistant", "content": "Analysis:\n"}
```

**Important:** Cannot end with trailing whitespace. Not available with Extended Thinking.

**Source:** https://docs.claude.com/en/docs/build-with-claude/prompt-engineering/prefill-claudes-response

---

### Long Context Best Practices

**For Documents 20K+ Tokens:**

1. **Put Documents at the Top**
   - 30% performance improvement
   - Place queries AFTER documents

2. **Use XML Structure**
```xml
<documents>
  <document index="1">
    <source>report_2024.pdf</source>
    <content>
    [document text]
    </content>
  </document>
  <document index="2">
    <source>analysis.txt</source>
    <content>
    [document text]
    </content>
  </document>
</documents>

<query>
Based on the documents above, identify the top 3 risks mentioned.
</query>
```

3. **Extract Quotes First**
```
Before answering, identify and quote the relevant passages from the documents
that support your response.
```

**Source:** https://docs.claude.com/en/docs/long-context-window-tips

---

### Extended Thinking (Optional Feature)

**When to Use:**
- Complex reasoning requiring 5+ steps
- Problems benefiting from self-correction
- Tasks where exploration improves results

**Configuration:**

```python
response = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    thinking={
        "type": "enabled",
        "budget_tokens": 10000  # Start at 1024, increase as needed
    },
    messages=[...]
)
```

**Budget Guidelines:**
- Minimum: 1,024 tokens
- Optimal: 1,024 - 16,000 tokens
- Diminishing returns: >32,000 tokens

**Limitations:**
- Incompatible with temperature/top_k
- Cannot prefill responses
- Tool choice limited to `auto` or `none`

**Source:** https://docs.claude.com/en/docs/build-with-claude/extended-thinking

---

### Prompt Caching

**When to Use:**
- Repetitive large context (e.g., codebase, documentation)
- Reduces cost by 90% on cached reads
- Reduces latency significantly

**Implementation:**

```python
system=[
    {
        "type": "text",
        "text": "Large system instructions...",
        "cache_control": {"type": "ephemeral"}
    }
]
```

**Minimum Cacheable:** 1,024 tokens (Opus/Sonnet), 2,048 tokens (Haiku)

**Pricing:**
- Cache writes: 1.25× base price
- Cache reads: 0.1× base price (90% savings)

**Source:** https://docs.claude.com/en/docs/build-with-claude/prompt-caching

---

### Claude-Specific Temperature

**Recommendation:** Claude documentation doesn't emphasize temperature as heavily as OpenAI.

**Default:** 1.0
**Range:** 0.0 - 1.0

**General Guidance:**
- Use 0.0-0.3 for analytical tasks
- Use 0.7-1.0 for creative tasks
- Temperature has less dramatic effect than with OpenAI models

**Source:** Anthropic API Documentation

---

### Example: Complete Claude Prompt

```python
import anthropic

client = anthropic.Anthropic()

prompt = """<role>
You are an expert analyst specializing in AI strategy, automation, and technical
implementation content. Your audience includes both technical builders and business
executives.
</role>

<instructions>
Analyze this YouTube video transcript and create a structured summary that captures
frameworks, actionable steps, tools mentioned, and strategic insights.
</instructions>

<content_context>
This channel focuses on:
- AI strategy for builders and executives
- Coding workflows and automation guides
- Frameworks from real AI implementations
- Actionable playbooks (no buzzwords)
</content_context>

<video_title>
Building Production-Ready AI Agents with Claude
</video_title>

<transcript>
[Full transcript here - can be 20K+ tokens]
</transcript>

<examples>
<example>
<sample_transcript>
Today I'll show you how to build an AI agent using LangChain and Claude.
First, install langchain and anthropic packages...
</sample_transcript>

<sample_output>
CONTENT TYPE: Technical Workflow

OVERVIEW: Step-by-step guide to building a ReAct AI agent using LangChain
and Claude API.

CORE CONTENT:
## Setup & Architecture
- Install langchain and anthropic packages
- Implement ReAct pattern for transparent reasoning
- Define tools as Python functions with docstrings

ACTIONABLE TAKEAWAYS:
- Use ReAct pattern for debugging agent behavior
- Tool docstrings guide agent's tool selection
- Start with 2-3 focused tools before scaling

TOOLS/TECHNOLOGIES: LangChain, Claude API, FastAPI, Docker
</sample_output>
</example>
</examples>

<output_format>
CONTENT TYPE: [Classification]
OVERVIEW: [1-2 sentences]
CORE CONTENT:
## [Section 1]
- [Point 1]
- [Point 2]
ACTIONABLE TAKEAWAYS:
- [Takeaway 1]
- [Takeaway 2]
TOOLS/TECHNOLOGIES: [List]
</output_format>

<constraints>
- Use 2-4 main sections
- Each section: 2-4 bullets (15-25 words max)
- Maximum 400 words total
- Focus on ACTIONABLE over THEORETICAL
</constraints>"""

response = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1200,
    temperature=0.3,
    system="You are an expert analyst who creates comprehensive, well-structured summaries. You follow instructions precisely.",
    messages=[{"role": "user", "content": prompt}]
)
```

---

## OpenAI Non-Reasoning Models (GPT-4o-mini)

**Model:** `gpt-4o-mini`
**Context Window:** 128,000 tokens
**Strengths:** Fast, cost-efficient, general-purpose tasks, STEM reasoning

### Key Characteristics

- **Parameter Count:** ~1.5B (lighter than GPT-4)
- **Pricing:** 60% cheaper than GPT-3.5 Turbo
- **Performance:** 82% on MMLU, 87% on HumanEval (coding)
- **Best For:** High-volume queries, real-time responses, parallel calls

**Source:** https://platform.openai.com/docs/models/gpt-4o-mini

---

### Six Core Strategies

OpenAI's official guide outlines six strategies:

1. **Write Clear Instructions**
2. **Provide Reference Text**
3. **Split Complex Tasks**
4. **Give Model Time to Think**
5. **Use External Tools**
6. **Test Changes Systematically**

**Source:** https://platform.openai.com/docs/guides/prompt-engineering

---

### System vs User Messages

**System Message:**
- Sets behavior, tone, constraints
- Applies to ALL user messages
- Stronger effect in GPT-4 models than GPT-3.5
- Use for high-level context

**User Message:**
- Specific task or query
- Contains the actual work
- Can include examples here

**Example:**

```python
from openai import OpenAI

client = OpenAI()

response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {
            "role": "system",
            "content": "You are a Python expert specializing in clean, maintainable code. Always explain your reasoning."
        },
        {
            "role": "user",
            "content": "Review this function and suggest improvements:\n\ndef calc(x,y):\n    return x+y*2"
        }
    ]
)
```

**Source:** https://platform.openai.com/docs/guides/prompt-engineering

---

### Few-Shot for GPT-4o-mini

**Critical:** Few-shot is HIGHLY EFFECTIVE for non-reasoning models like GPT-4o-mini.

**Format:**

```python
messages=[
    {"role": "system", "content": "Extract structured data from text."},
    {"role": "user", "content": "John Smith, age 30, lives in NYC"},
    {"role": "assistant", "content": '{"name": "John Smith", "age": 30, "city": "NYC"}'},
    {"role": "user", "content": "Sarah Lee, 25, Boston"},
    {"role": "assistant", "content": '{"name": "Sarah Lee", "age": 25, "city": "Boston"}'},
    {"role": "user", "content": "Mike Johnson, 40, lives in Seattle"}
]
```

**Best Practices:**
- 2-5 examples optimal
- Place examples in conversation history
- Ensure consistency in format
- Include edge cases

**Source:** OpenAI Cookbook, Best Practices for Prompt Engineering

---

### Chain-of-Thought for GPT-4o-mini

**Use Explicit CoT Instructions:**

```python
messages=[
    {
        "role": "system",
        "content": "You solve problems step-by-step, showing your reasoning."
    },
    {
        "role": "user",
        "content": """
        Problem: A store had 45 items. They sold 18 and received 30 more.
        How many items now?

        Let's think step by step:
        """
    }
]
```

**Alternative Format:**

```python
{
    "role": "user",
    "content": """
    Solve this problem. Show your work:

    Step 1: [Identify what we know]
    Step 2: [Calculate changes]
    Step 3: [Final answer]

    Problem: [problem here]
    """
}
```

**Source:** Chain-of-Thought Prompting (arXiv:2201.11903)

---

### Structured Outputs

**Recommended Approach:** Use `json_schema` with `strict: true`

```python
from pydantic import BaseModel

class Analysis(BaseModel):
    sentiment: str
    confidence: float
    key_phrases: list[str]

response = client.beta.chat.completions.parse(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Analyze this review..."}],
    response_format=Analysis
)
```

**Alternative (JSON Mode):**

```python
response = client.chat.completions.create(
    model="gpt-4o-mini",
    response_format={"type": "json_object"},
    messages=[
        {
            "role": "system",
            "content": "You return JSON only. Use this schema: {\"sentiment\": string, \"score\": number}"
        },
        {"role": "user", "content": "Review: Great product!"}
    ]
)
```

**Source:** https://platform.openai.com/docs/guides/structured-outputs

---

### Temperature Settings

**Recommended Values:**

| Temperature | Use Case |
|-------------|----------|
| 0.0 | Deterministic (data extraction, classification) |
| 0.3 | Mostly deterministic with slight variation |
| 0.7 | Balanced creativity and coherence (default) |
| 0.9 | High creativity (brainstorming, fiction) |

**Important:** "Alter temperature OR top_p, not both"

**Source:** https://platform.openai.com/docs/guides/text-generation

---

### Frequency and Presence Penalties

**Frequency Penalty** (0 to 2):
- Reduces repetition based on how often token appeared
- Proportional to frequency
- Use 0.3-0.5 to reduce repetitive phrasing

**Presence Penalty** (0 to 2):
- Once-off penalty for tokens that appeared at least once
- Not proportional to frequency
- Use to encourage topic diversity

**Example:**

```python
response = client.chat.completions.create(
    model="gpt-4o-mini",
    temperature=0.7,
    frequency_penalty=0.3,  # Reduce repetition
    presence_penalty=0.0,
    messages=[...]
)
```

**Source:** OpenAI API Documentation

---

### Example: Complete GPT-4o-mini Prompt

```python
from openai import OpenAI
from pydantic import BaseModel

client = OpenAI()

class VideoSummary(BaseModel):
    content_type: str
    overview: str
    key_points: list[str]
    tools_mentioned: list[str]
    complexity: str

system_message = """You are an expert analyst specializing in AI strategy and
technical implementation content. You create structured summaries with clear
sections and actionable insights."""

user_message = """Analyze this YouTube transcript and extract key information.

TRANSCRIPT:
Today I'll show you how to evaluate LLM applications. Start with the eval framework:
define success criteria before building. Use semantic similarity, not exact matches.
Implement automated evals with pytest. Track accuracy, latency, cost, and failure rate.
Use Claude's prompt caching to reduce costs by 90%. Run evals on every PR with GitHub
Actions. Real example: reduced hallucinations from 23% to 3% using this framework.

Return structured summary with:
- Content type (Technical Workflow, Framework, Strategy Guide, etc.)
- Overview (1-2 sentences)
- Key points (3-5 bullets)
- Tools/technologies mentioned
- Complexity level (Beginner/Intermediate/Advanced)"""

response = client.beta.chat.completions.parse(
    model="gpt-4o-mini",
    temperature=0.3,
    frequency_penalty=0.3,
    messages=[
        {"role": "system", "content": system_message},
        {"role": "user", "content": user_message}
    ],
    response_format=VideoSummary
)

summary = response.choices[0].message.parsed
```

---

## OpenAI Reasoning Models (o1/o3 series)

**Models:** `o1`, `o1-mini`, `o3`, `o3-mini`, `o4-mini`
**Key Innovation:** Extended thinking time before answering
**Training:** Reinforcement learning with outcome-based rewards

### Fundamental Difference

**Traditional Models:**
- Generate responses immediately
- Token-by-token prediction
- Fast but less thorough

**Reasoning Models:**
- Spend time "thinking" internally
- Generate hidden reasoning tokens
- Self-correct and explore alternatives
- Much slower but more accurate on complex tasks

**Source:** https://platform.openai.com/docs/guides/reasoning

---

### Critical Prompting Differences

**For Reasoning Models, DO:**
1. Keep prompts simple and direct
2. Use delimiters for clarity (###, XML tags)
3. Limit RAG context to essentials
4. Be explicit about output format
5. Use `reasoning_effort` parameter (low/medium/high)

**For Reasoning Models, DO NOT:**
1. Use few-shot examples (harmful)
2. Add "think step by step" instructions (redundant)
3. Include chain-of-thought examples (confusing)
4. Provide excessive context (causes overthinking)
5. Over-engineer prompts (simpler is better)

**Source:** https://platform.openai.com/docs/guides/reasoning-best-practices

---

### Official Guidance

**Quote from OpenAI:** "The o1 models perform best with straightforward prompts. Some prompt engineering techniques, like few-shot prompting or instructing the model to 'think step by step,' may not enhance performance and can sometimes hinder it."

**Why:** Reasoning models were trained with RL to develop their own reasoning strategies. External guidance can interfere with their internal processes.

**Source:** https://platform.openai.com/docs/guides/reasoning

---

### Keep Prompts Simple

**Anti-Pattern (Don't Do This):**

```python
# BAD for reasoning models
messages=[
    {"role": "user", "content": """
    Let's solve this step by step:

    Example 1:
    Problem: 2 + 2
    Step 1: Identify the numbers (2 and 2)
    Step 2: Add them together
    Answer: 4

    Example 2:
    Problem: 5 + 3
    Step 1: Identify the numbers (5 and 3)
    Step 2: Add them together
    Answer: 8

    Now think carefully and solve this step by step:
    Problem: 15 + 27
    """}
]
```

**Correct Pattern:**

```python
# GOOD for reasoning models
messages=[
    {"role": "user", "content": "Solve: 15 + 27"}
]
```

**Source:** Microsoft Azure AI Documentation, Vellum.ai

---

### Use Delimiters for Structure

**When You Have Multiple Components:**

```python
messages=[
    {"role": "user", "content": """
    ### CONTEXT
    You are analyzing customer feedback for a SaaS product.

    ### FEEDBACK
    "The app crashes frequently but customer support is responsive."

    ### TASK
    Extract sentiment for: product quality, customer support, overall experience.
    Return as JSON.
    """}
]
```

**Alternative (XML Style):**

```python
messages=[
    {"role": "user", "content": """
    <context>
    Analyzing customer feedback for SaaS product
    </context>

    <feedback>
    The app crashes frequently but customer support is responsive.
    </feedback>

    <task>
    Extract sentiment for: product quality, customer support, overall.
    Return as JSON.
    </task>
    """}
]
```

**Source:** https://platform.openai.com/docs/guides/reasoning-best-practices

---

### Reasoning Effort Parameter

**Controls how long model spends thinking:**

```python
response = client.chat.completions.create(
    model="o1",
    reasoning_effort="high",  # low, medium, high
    messages=[...]
)
```

**Guidelines:**
- **low**: Simple problems, faster responses
- **medium**: Default, balanced
- **high**: Complex reasoning, slower but more thorough

**Note:** Higher effort = more reasoning tokens = higher cost

**Source:** OpenAI API Documentation

---

### Developer Messages (Not System Messages)

**Important Change:** Reasoning models use `developer` role instead of `system`

```python
# For o1/o3 models
response = client.chat.completions.create(
    model="o1",
    messages=[
        {
            "role": "developer",
            "content": "You analyze code for security vulnerabilities."
        },
        {
            "role": "user",
            "content": "Review this function: [code]"
        }
    ]
)
```

**Markdown Note:** Add "Formatting re-enabled" to first line of developer message if you want markdown formatting in responses.

**Source:** https://learn.microsoft.com/en-us/azure/ai-foundry/openai/how-to/reasoning

---

### Limit RAG Context

**Anti-Pattern:**
```python
# DON'T: Include every possibly relevant document
context = fetch_all_related_documents(query)  # 50+ documents
```

**Best Practice:**
```python
# DO: Include only most relevant
context = fetch_top_k_documents(query, k=3)  # Top 3 most relevant
```

**Why:** Reasoning models can overthink with excessive context, reducing performance and increasing latency.

**Source:** Microsoft Azure AI, OpenAI Best Practices

---

### No Temperature Control

**Important:** Reasoning models have **fixed parameters**

```python
# This will ERROR
response = client.chat.completions.create(
    model="o1",
    temperature=0.7,  # NOT SUPPORTED
    messages=[...]
)
```

**Why:** Reasoning models need deterministic reasoning paths to maintain logical consistency.

**Alternative:** Use `reasoning_effort` parameter instead.

**Source:** OpenAI Community, Azure Documentation

---

### Example: Complete o1 Prompt

```python
from openai import OpenAI

client = OpenAI()

# Simple, direct prompt - no few-shot, no CoT
response = client.chat.completions.create(
    model="o1",
    reasoning_effort="medium",
    messages=[
        {
            "role": "developer",
            "content": "You are a code review specialist. Identify security vulnerabilities and suggest fixes."
        },
        {
            "role": "user",
            "content": """
            ### CODE TO REVIEW

            def process_user_input(user_data):
                query = "SELECT * FROM users WHERE id = " + user_data['id']
                return execute_query(query)

            ### TASK

            Identify security issues and provide secure version.
            """
        }
    ]
)

# Access reasoning (if visible)
print(response.choices[0].message.reasoning)
# Access final answer
print(response.choices[0].message.content)
```

---

## Model Selection Guide

### Decision Framework

```
START: What is your task?

┌─────────────────────────────────────┐
│ Complex reasoning (5+ steps)?      │
│ - Graduate-level STEM              │
│ - Competitive programming          │
│ - Multi-step logic problems        │
└─────────────────────────────────────┘
         │
         ├─ YES → Use Reasoning Model (o1/o3, Claude Extended)
         │
         └─ NO ↓

┌─────────────────────────────────────┐
│ Creative or multimodal?            │
│ - Content writing                  │
│ - Image analysis                   │
│ - Brainstorming                    │
└─────────────────────────────────────┘
         │
         ├─ YES → Use Traditional Model (GPT-4o, Claude)
         │
         └─ NO ↓

┌─────────────────────────────────────┐
│ Need speed/high volume?            │
│ - Real-time responses              │
│ - High query volume                │
│ - Cost-sensitive                   │
└─────────────────────────────────────┘
         │
         ├─ YES → Use Fast Model (GPT-4o-mini, Claude Haiku)
         │
         └─ NO ↓

Use Balanced Model (GPT-4o, Claude Sonnet)
```

---

### Detailed Comparison

| Criterion | Traditional (GPT-4o) | Fast (GPT-4o-mini) | Reasoning (o1/o3) |
|-----------|---------------------|-------------------|-------------------|
| **Speed** | ~2-5 seconds | ~1-2 seconds | 5-60 seconds |
| **Cost** | $2.50/$10 per 1M | $0.15/$0.60 per 1M | $1.10/$4.40 per 1M |
| **Complex Reasoning** | Good | Moderate | Excellent |
| **Creative Writing** | Excellent | Good | Poor |
| **Coding** | Very Good | Good | Excellent |
| **Math/Logic** | Good | Good | Exceptional |
| **Multimodal** | Yes | Yes | Limited |
| **Streaming** | Yes | Yes | Limited |
| **Function Calling** | Yes | Yes | Yes (newer versions) |

---

### Use Case Examples

**Use GPT-4o-mini When:**
- Chatbot responses
- Simple data extraction
- Classification tasks
- High-volume queries (1000s/hour)
- Budget < $100/month

**Use GPT-4o/Claude Sonnet When:**
- Complex content generation
- Detailed analysis
- Code generation and review
- Multi-turn conversations
- General-purpose applications

**Use o1/o3/Claude Extended When:**
- Graduate-level STEM problems
- Complex debugging
- Mathematical proofs
- Multi-step strategic planning
- Accuracy > speed

**Source:** Model comparison research, official documentation

---

## Quick Reference Tables

### Prompting Technique Comparison

| Technique | Traditional Models | Reasoning Models | Claude-Specific |
|-----------|-------------------|------------------|-----------------|
| Few-Shot Examples | ✅ Highly effective (2-5 examples) | ❌ Harmful, avoid | ✅ Effective (3-5 examples) |
| Chain-of-Thought | ✅ Explicit "step by step" | ❌ Automatic, don't mention | ✅ Use `<thinking>` tags |
| Temperature Control | ✅ 0.0-1.0 | ❌ Not supported | ✅ 0.0-1.0 (less emphasis) |
| System Messages | ✅ `role: system` | ⚠️ `role: developer` | ✅ `system` parameter |
| XML Tags | ⚠️ Optional | ⚠️ Optional | ✅ **Highly recommended** |
| Prefilling | ❌ Not available | ❌ Not available | ✅ **Unique to Claude** |
| RAG Context | ✅ Maximize relevant docs | ⚠️ Minimize to essentials | ✅ Documents at top |

---

### Temperature Quick Reference

| Temperature | Determinism | Use Cases | Models |
|-------------|-------------|-----------|---------|
| 0.0 | Maximum | Data extraction, Q&A, classification | GPT-4o, GPT-4o-mini, Claude |
| 0.3 | High | Factual summaries, analysis | GPT-4o, GPT-4o-mini, Claude |
| 0.7 | Moderate | General content, balanced creativity | GPT-4o, GPT-4o-mini, Claude |
| 0.9 | Low | Creative writing, brainstorming | GPT-4o, GPT-4o-mini, Claude |
| N/A | Fixed | Reasoning tasks | o1, o3 (not configurable) |

---

### Model Capabilities Matrix

| Feature | GPT-4o-mini | GPT-4o | o1/o3 | Claude Sonnet 4.5 | Claude Opus 4 |
|---------|------------|--------|-------|-------------------|---------------|
| Context Window | 128K | 128K | Varies | 200K (1M beta) | 200K |
| Output Tokens | 16K | 16K | 65K | Varies | Varies |
| Vision | ✅ | ✅ | ⚠️ Limited | ✅ | ✅ |
| Function Calling | ✅ | ✅ | ✅ (newer) | ✅ | ✅ |
| Streaming | ✅ | ✅ | ⚠️ Limited | ✅ | ✅ |
| JSON Mode | ✅ | ✅ | ✅ | ✅ | ✅ |
| Structured Output | ✅ | ✅ | ✅ | ✅ | ✅ |
| Extended Thinking | ❌ | ❌ | ✅ Built-in | ✅ Optional | ✅ Optional |
| Prompt Caching | ❌ | ❌ | ❌ | ✅ | ✅ |

---

### Anti-Pattern Checklist

**Before Deploying a Prompt, Check:**

- [ ] Is the instruction clear and specific?
- [ ] Have I provided necessary context?
- [ ] Am I using the right technique for this model type?
- [ ] Have I tested with representative data?
- [ ] Did I include 2-5 examples (if non-reasoning model)?
- [ ] Is output format explicitly specified?
- [ ] Have I set appropriate temperature (if applicable)?
- [ ] Did I avoid "think step by step" for reasoning models?
- [ ] Am I validating outputs programmatically?
- [ ] Is there a fallback strategy for failures?
- [ ] Have I versioned this prompt?
- [ ] Are success metrics defined?

---

## Complete Sources

### Anthropic Claude

1. **Claude 4 Best Practices**: https://docs.claude.com/en/docs/build-with-claude/prompt-engineering/claude-4-best-practices
2. **XML Tags Guide**: https://docs.claude.com/en/docs/build-with-claude/prompt-engineering/use-xml-tags
3. **Chain-of-Thought**: https://docs.claude.com/en/docs/build-with-claude/prompt-engineering/chain-of-thought
4. **Few-Shot (Multishot)**: https://docs.claude.com/en/docs/build-with-claude/prompt-engineering/multishot-prompting
5. **System Prompts**: https://docs.claude.com/en/docs/build-with-claude/prompt-engineering/system-prompts
6. **Prefilling**: https://docs.claude.com/en/docs/build-with-claude/prompt-engineering/prefill-claudes-response
7. **Long Context Tips**: https://docs.claude.com/en/docs/long-context-window-tips
8. **Extended Thinking**: https://docs.claude.com/en/docs/build-with-claude/extended-thinking
9. **Prompt Caching**: https://docs.claude.com/en/docs/build-with-claude/prompt-caching
10. **Anthropic Cookbook**: https://github.com/anthropics/claude-cookbooks

### OpenAI

11. **Prompt Engineering Guide**: https://platform.openai.com/docs/guides/prompt-engineering
12. **Reasoning Models**: https://platform.openai.com/docs/guides/reasoning
13. **Reasoning Best Practices**: https://platform.openai.com/docs/guides/reasoning-best-practices
14. **Structured Outputs**: https://platform.openai.com/docs/guides/structured-outputs
15. **GPT-4o-mini**: https://platform.openai.com/docs/models/gpt-4o-mini
16. **GPT-4o**: https://platform.openai.com/docs/models/gpt-4o
17. **o1 Models**: https://platform.openai.com/docs/models/o1
18. **Temperature Parameter**: https://platform.openai.com/docs/guides/text-generation
19. **OpenAI Cookbook**: https://cookbook.openai.com/

### Research & Guides

20. **The Prompt Report** (arXiv:2406.06608): https://arxiv.org/abs/2406.06608
21. **Chain-of-Thought Paper** (arXiv:2201.11903): https://arxiv.org/abs/2201.11903
22. **PromptingGuide.ai**: https://www.promptingguide.ai/
23. **Microsoft Azure Reasoning Models**: https://learn.microsoft.com/en-us/azure/ai-foundry/openai/how-to/reasoning
24. **Vellum AI - Prompting o1**: https://www.vellum.ai/blog/how-to-prompt-the-openai-o1-model
25. **DigitalOcean Few-Shot Guide**: https://www.digitalocean.com/community/tutorials/_few-shot-prompting-techniques-examples-best-practices

### Additional Resources

26. **Humanloop Structured Outputs**: https://humanloop.com/blog/structured-outputs
27. **Portkey Retries & Fallbacks**: https://portkey.ai/blog/retries-fallbacks-and-circuit-breakers-in-llm-apps/
28. **LaunchDarkly Versioning**: https://launchdarkly.com/blog/prompt-versioning-and-management/
29. **Datadog LLM Evaluation**: https://www.datadoghq.com/blog/llm-evaluation-framework-best-practices/
30. **Google Prompt Engineering**: https://cloud.google.com/blog/products/application-development/five-best-practices-for-prompt-engineering

---

## Conclusion

This reference guide synthesizes official documentation from Anthropic and OpenAI, validated by academic research and industry best practices. Key takeaways:

1. **Model type determines technique**: Reasoning models require completely different prompting than traditional models
2. **XML tags are powerful for Claude**: Trained specifically on them, yields 20-30% improvements
3. **Few-shot is powerful for traditional models**: But harmful for reasoning models
4. **Simplicity wins for reasoning models**: Over-engineering hurts performance
5. **Always validate and iterate**: First attempts rarely achieve optimal results

**Last Updated:** 2025-11-04
**Maintained By:** Research synthesis from official sources
**Version:** 1.0
