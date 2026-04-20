---
name: react-markdown
description: "react-markdown — React component for rendering Markdown as React elements. Use when rendering Markdown in React, configuring remark/rehype plugins, customizing components, adding syntax highlighting to code blocks, or handling GFM (tables, strikethrough, task lists). Fetch live documentation for up-to-date details."
---

# react-markdown

> **CRITICAL: Your training data for react-markdown is unreliable.** APIs change between versions and memorized patterns may be wrong or deprecated. Before writing any code, you MUST use `WebFetch` to read the current README:
>
> **`WebFetch("https://github.com/remarkjs/react-markdown")`**
>
> If you need a specific remark or rehype plugin, also fetch:
> - **`WebFetch("https://github.com/remarkjs/remark/blob/main/doc/plugins.md")`**
> - **`WebFetch("https://github.com/rehypejs/rehype/blob/main/doc/plugins.md")`**
>
> Do not proceed without fetching first. Never assume prop names or plugin options — verify against current docs.

react-markdown renders Markdown as React elements using a plugin pipeline: Markdown → remark (AST) → rehype (HTML AST) → React components. No `dangerouslySetInnerHTML` — everything is React elements.

## Key Capabilities

- **Safe by default**: No `dangerouslySetInnerHTML` — outputs React elements
- **Plugin ecosystem**: remark plugins transform Markdown AST, rehype plugins transform HTML AST
- **Custom components**: Override any HTML element with a React component
- **GFM support**: Tables, strikethrough, autolinks, task lists via `remark-gfm`
- **Syntax highlighting**: Code block highlighting via `rehype-highlight` or `rehype-pretty-code`

## Essential Setup

The base package renders standard Markdown. For most apps you need two plugins:

```tsx
import Markdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import rehypeHighlight from 'rehype-highlight'

<Markdown
  remarkPlugins={[remarkGfm]}
  rehypePlugins={[rehypeHighlight]}
>
  {markdownContent}
</Markdown>
```

**Packages to install:** `bun add react-markdown remark-gfm rehype-highlight`

Don't forget the highlight.js CSS theme for syntax highlighting:
```tsx
import 'highlight.js/styles/github-dark.css'
```

## Custom Component Overrides

Override any HTML element rendered by Markdown. This is how you add custom styling, clickable links, or interactive elements:

```tsx
<Markdown
  components={{
    // Custom code blocks
    code({ className, children, ...props }) {
      const match = /language-(\w+)/.exec(className || '')
      return match ? (
        <pre className="code-block">
          <code className={className} {...props}>{children}</code>
        </pre>
      ) : (
        <code className="inline-code" {...props}>{children}</code>
      )
    },
    // Custom links — open external in new tab
    a({ href, children, ...props }) {
      const isExternal = href?.startsWith('http')
      return (
        <a href={href} target={isExternal ? '_blank' : undefined} rel={isExternal ? 'noopener noreferrer' : undefined} {...props}>
          {children}
        </a>
      )
    },
    // Custom images
    img({ src, alt, ...props }) {
      return <img src={src} alt={alt} loading="lazy" {...props} />
    },
  }}
>
  {content}
</Markdown>
```

## Best Practices

**Always include `remark-gfm` for user-facing Markdown.** Without it, tables, strikethrough, autolinks, and task lists silently render as plain text. This is the most common "bug" reported by users — the Markdown looks broken because GFM isn't enabled by default.

**The `children` prop must be a string.** Passing JSX or a React element to `<Markdown>` will not work. If your content is in a variable, ensure it's a string type: `<Markdown>{String(content)}</Markdown>`.

**Distinguish inline code from code blocks in component overrides.** The `code` component receives both inline (`code`) and block (` ``` `) code. Check for the presence of `className` (which contains `language-*` for fenced blocks) to differentiate. Inline code has no `className`.

**Plugin order matters.** remark plugins run in array order on the Markdown AST, then rehype plugins run on the HTML AST. If a rehype plugin depends on structure created by a remark plugin, ordering is critical. `remarkGfm` should always come first in remarkPlugins.

**Re-renders on every content change.** react-markdown parses and re-renders the full Markdown tree whenever the `children` string changes. For streaming chat (character-by-character updates), this can be expensive. Consider debouncing updates or using `React.memo` with a custom comparison on the parent component.
