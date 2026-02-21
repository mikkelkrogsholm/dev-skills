# GEO Platform Principles

## ChatGPT (OpenAI)
- Branded domains cited 11% more than third-party content
- Content updated within 30 days gets 3.2x more citations — keep pages fresh
- Sites with over 350K referring domains average 8.4 citations per query
- Match content format to ChatGPT's conversational response style
- Allow GPTBot and ChatGPT-User in robots.txt

## Perplexity
- Allow PerplexityBot in robots.txt (blocked by default on many sites)
- FAQ schema increases citation rate significantly
- PDF documents are prioritised for citation — host key content as PDFs where appropriate
- Semantic relevance matters more than keyword density
- Direct, factual answers perform best

## Google AI Overview (SGE)
- E-E-A-T: Experience, Expertise, Authority, Trust — all four matter
- Structured data (Schema markup) directly increases appearance in AI Overviews
- Topical authority: build content clusters around a topic with strong internal linking
- Authoritative citations in your content increase your visibility by ~132%
- Page speed and Core Web Vitals still apply

## Microsoft Copilot / Bing
- Bing indexing is required — submit to Bing Webmaster Tools
- Microsoft ecosystem signals help: LinkedIn company page, GitHub presence
- Page speed under 2 seconds
- Clear entity definitions (who you are, what you do, where you are)
- Structured data increases Copilot citation rate

## Anthropic AI
- Uses Brave Search for web retrieval — Brave indexing matters, not just Google
- High factual density: data-rich, specific content preferred over vague claims
- Structural clarity: content that is easy to extract and quote performs better
- Submit site to Brave Search: https://search.brave.com/webmaster
- Allow ClaudeBot and anthropic-ai in robots.txt

## robots.txt — Allow These Bots

```
User-agent: Googlebot
Allow: /

User-agent: Bingbot
Allow: /

User-agent: PerplexityBot
Allow: /

User-agent: ChatGPT-User
Allow: /

User-agent: GPTBot
Allow: /

User-agent: ClaudeBot
Allow: /

User-agent: anthropic-ai
Allow: /
```
