---
name: seo-geo
description: "SEO and GEO (Generative Engine Optimization) for any web project. Use when writing or reviewing page content, meta tags, structured data, or optimizing for search visibility — both traditional search engines (Google, Bing) and AI search engines (ChatGPT, Perplexity, Gemini, Copilot). Applies principles proactively when building landing pages, blog posts, docs sites, product pages, or any public-facing content regardless of framework or language."
---

# SEO / GEO

Two distinct optimization targets:
- **SEO** — ranking in traditional search engines (Google, Bing)
- **GEO** — being *cited* by AI search engines (ChatGPT, Perplexity, Gemini, Copilot)

Key insight: AI search engines do not rank pages — they cite sources. Being cited is the new ranking #1.

## Documentation

- **llms.txt standard**: https://llmstxt.org
- **GEO research**: https://arxiv.org/abs/2311.09735 (Princeton study)
- **Schema reference**: https://schema.org
- **Google guidelines**: https://developers.google.com/search/docs

## Core Principles

Apply these whenever writing or reviewing public-facing content or markup, regardless of framework.

### GEO: The 9 Princeton Methods

From Princeton research on what makes content get cited by AI engines:

| Method | Visibility boost | How to apply |
|--------|-----------------|--------------|
| Cite authoritative sources | +40% | Link to studies, official docs, standards |
| Include specific statistics | +37% | Use real numbers, not vague claims |
| Add expert quotes | +30% | Attribute statements to named sources |
| Authoritative tone | +25% | Write with confidence and precision |
| Readable and clear | +20% | Short paragraphs, plain language |
| Use technical terminology | +18% | Domain-specific terms signal expertise |
| Vocabulary diversity | +15% | Avoid repetition of the same words |
| Fluency optimization | +15-30% | Natural flow, no awkward phrasing |
| Keyword stuffing | **-10%** | Never — hurts both SEO and GEO |

Best combination: fluency + statistics = maximum boost.

### Content Structure for GEO

- **Answer-first**: put the direct answer at the top, then elaborate
- Clear heading hierarchy (H1 > H2 > H3)
- Use bullet points, numbered lists, and comparison tables
- FAQ sections significantly increase AI citation rate
- Short paragraphs (2-3 sentences)

### Traditional SEO Fundamentals

- One H1 per page, containing the primary keyword
- Meta title: 50-60 characters, keyword near the front
- Meta description: 150-160 characters, include keyword and a call to action
- Every image needs descriptive alt text
- Canonical URL on every page
- Sitemap.xml and robots.txt present and correct

## Platform-Specific Behaviour

Each AI engine has different citation preferences. See references/geo-principles.md for full detail.

**ChatGPT**: favours branded domains; content updated within 30 days cited 3.2x more
**Perplexity**: allow PerplexityBot in robots.txt; prioritises PDF documents and FAQ schema
**Google AI Overview**: E-E-A-T signals, structured data, topical authority through content clusters
**Microsoft Copilot**: requires Bing indexing; page speed under 2 seconds; LinkedIn/GitHub mentions help
**Anthropic AI**: uses Brave Search indexing (not Google); prioritises factual density and structural clarity

## llms.txt

`llms.txt` is to AI engines what `robots.txt` is to crawlers — a file at your site root that tells AI systems how to understand your content. Always add it to any public-facing site.

Place at `https://yourdomain.com/llms.txt`. Format is Markdown:

```markdown
# Site or Product Name

> One-paragraph summary of what the site is and who it is for.

Optional additional context (key facts, caveats, important notes).

## Docs

- [Page title](https://yourdomain.com/page.md): What this page covers

## API

- [API reference](https://yourdomain.com/api.md): Endpoint overview

## Optional

- [Changelog](https://yourdomain.com/changelog.md): Recent changes
```

**Key rules:**
- H1 = site/product name (required)
- Blockquote = brief summary of what the site is (required for AI comprehension)
- H2 sections = curated links to your most important pages with descriptions
- Link to `.md` versions of pages where possible — AI engines prefer clean Markdown over HTML
- The `## Optional` section signals lower-priority content that can be skipped in short-context situations
- Keep it concise — this is a navigation aid, not a full content dump

## Structured Data

Always add JSON-LD schema. See references/schema-patterns.md for templates.

Priority schema types:
- **FAQPage** — +40% AI visibility; add to any page with questions and answers
- **Article** — for blog posts and editorial content
- **Organization** — on the homepage and about page
- **Product** — for product pages
- **BreadcrumbList** — for navigation context

## Checklist

Apply when reviewing any public-facing page:

- [ ] `llms.txt` present at site root with H1, summary blockquote, and key page links
- [ ] Unique, keyword-containing H1
- [ ] Meta title and description present and correct length
- [ ] Open Graph tags (og:title, og:description, og:image, og:url)
- [ ] JSON-LD schema appropriate to page type
- [ ] FAQPage schema if page contains Q&A content
- [ ] robots.txt allows relevant bots (including PerplexityBot, GPTBot, ClaudeBot, anthropic-ai)
- [ ] Sitemap includes this page
- [ ] Images have descriptive alt text
- [ ] Answer-first content structure
- [ ] At least one statistic or data point per key claim
- [ ] Mobile-friendly layout
- [ ] Page loads in under 3 seconds
