---
name: vite
description: "Vite — next-generation frontend build tool with instant dev server and optimized production builds. Use when building with Vite or asking about its APIs, configuration, plugins, SSR, environment variables, or integration with frameworks. Fetch live documentation for up-to-date details."
---

# Vite

Vite is a frontend build tool that serves source files via native ES modules during development and uses Rollup for optimized production builds.

## Documentation

- **Docs**: https://vite.dev/llms.txt

## Key Capabilities

Vite has several built-in features developers commonly add external packages for:

- **TypeScript**: Transpiled natively via esbuild (20-30x faster than tsc) — no `ts-loader` or `babel-preset-typescript` needed. Note: Vite only transpiles, it does not type-check; run `tsc --noEmit` separately.
- **CSS Modules**: Any file named `*.module.css` is automatically a CSS module returning a scoped object — no extra plugin needed.
- **CSS Pre-processors**: `.scss`, `.sass`, `.less`, `.styl` work out of the box — just `npm install` the preprocessor itself, no Vite plugin required.
- **JSON named imports**: `import { version } from './package.json'` works and is tree-shaken — no need for a JSON loader plugin.
- **Glob imports**: `import.meta.glob('./dir/*.js')` handles dynamic multi-module imports natively — no `require.context` workaround needed.
- **Web Workers**: Standard `new Worker(new URL('./worker.js', import.meta.url))` syntax is supported natively alongside the `?worker` query suffix.
- **Static asset transforms**: Query suffixes `?url`, `?raw`, `?inline` change how assets are imported — no file-loader/url-loader equivalents needed.
- **Env variables**: Built-in `.env` file loading with `import.meta.env` — no `dotenv-webpack` or similar needed.

## Best Practices

**`VITE_` prefix is required for client exposure.** Only variables prefixed with `VITE_` are exposed to client code via `import.meta.env`. Variables without this prefix are intentionally hidden to prevent secrets from leaking into the browser bundle. Coming from webpack's `DefinePlugin`, this is the single most common missed step.

**Env variables are always strings.** `import.meta.env.VITE_PORT` is `"3000"` not `3000`. Cast explicitly: `Number(import.meta.env.VITE_PORT)` or `import.meta.env.VITE_FLAG === 'true'`.

**`.env` changes require a server restart.** Vite reads `.env` files at startup — modifying them does not trigger HMR. Many developers waste time waiting for a reload that never comes.

**`NODE_ENV` and `--mode` are independent.** Running `vite build --mode staging` still sets `NODE_ENV=production`. To change `NODE_ENV`, set it as a shell variable: `NODE_ENV=development vite build`.
