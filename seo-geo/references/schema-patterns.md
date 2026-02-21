# Schema Markup Patterns

All schema is added as a JSON-LD script tag in the page head or body. Framework-agnostic.

## FAQPage — +40% AI visibility

```json
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "What is [topic]?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "According to [source], [answer with specific data point]."
      }
    }
  ]
}
```

## Article

```json
{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "[Title]",
  "author": {
    "@type": "Person",
    "name": "[Author name]"
  },
  "publisher": {
    "@type": "Organization",
    "name": "[Brand]",
    "logo": {
      "@type": "ImageObject",
      "url": "[Logo URL]"
    }
  },
  "datePublished": "[ISO 8601 date]",
  "dateModified": "[ISO 8601 date]",
  "description": "[150-160 char description]"
}
```

## Organization — homepage and about page

```json
{
  "@context": "https://schema.org",
  "@type": "Organization",
  "name": "[Brand name]",
  "url": "[Homepage URL]",
  "logo": "[Logo URL]",
  "description": "[What you do]",
  "sameAs": [
    "[LinkedIn URL]",
    "[GitHub URL]",
    "[Twitter/X URL]"
  ]
}
```

## Product

```json
{
  "@context": "https://schema.org",
  "@type": "Product",
  "name": "[Product name]",
  "description": "[Description]",
  "brand": {
    "@type": "Brand",
    "name": "[Brand]"
  },
  "offers": {
    "@type": "Offer",
    "price": "[Price]",
    "priceCurrency": "[Currency code]",
    "availability": "https://schema.org/InStock"
  }
}
```

## BreadcrumbList

```json
{
  "@context": "https://schema.org",
  "@type": "BreadcrumbList",
  "itemListElement": [
    {
      "@type": "ListItem",
      "position": 1,
      "name": "Home",
      "item": "[Homepage URL]"
    },
    {
      "@type": "ListItem",
      "position": 2,
      "name": "[Section]",
      "item": "[Section URL]"
    }
  ]
}
```

## Validation

Validate schema at:
- https://search.google.com/test/rich-results
- https://validator.schema.org
