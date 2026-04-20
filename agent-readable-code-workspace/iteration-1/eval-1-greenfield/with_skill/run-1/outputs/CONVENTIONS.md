# Conventions

Optimized for a service maintained mostly by Claude Code and Cursor. The guiding heuristic: **someone grepping a single file should be able to act correctly without reading the rest of the repo.** If a rule below doesn't pay rent toward that, drop it.

## 1. Organize by feature, not by layer

- Every feature lives in `src/features/<feature>/` and owns its routes, service, schema, types, errors, and tests. No top-level `controllers/`, `services/`, or `models/` directories.
- A feature is the unit an agent can load as one coherent chunk. If you fix a bug in `billing`, you should not have to touch four sibling directories.
- Cross-feature code is rare and goes in `src/platform/`. If `platform/` grows a file that's really about one feature, move it back.
- Features do not import from each other's internals. They talk through the exported service functions in `<feature>.service.ts` or published events. If `auth` needs a user, it calls `users.service.ts`; it does not reach into `users.queries.ts`.

## 2. Naming

- **File names:** `kebab-case.ts`, always suffixed by role: `.routes.ts`, `.service.ts`, `.schema.ts`, `.types.ts`, `.errors.ts`, `.test.ts`. A file's role must be greppable from its name alone.
- **Exported functions are verbs with a domain object:** `chargeSubscription`, `issueSession`, `purgeUserData`. Not `process`, `handle`, `doWork`, `run`.
- **Banned name fragments in new code:** `Manager`, `Service` as a class suffix (files are fine — see below), `Helper`, `Util`, `Handler`, `Common`, `Misc`, `Stuff`, `process`, `handle`.
- **No dumping-ground files.** No `utils.ts`, `helpers.ts`, `common.ts`, `misc.ts`, `shared.ts`. If a utility has no obvious home, it probably belongs inside the one feature that uses it.
- **`.service.ts` is a file-role suffix, not a class.** Export free functions. Don't create `UserService` classes.
- **Rename aggressively when behavior changes.** A name that used to be accurate is worse than a name that was always vague — the agent will trust it.

## 3. File size and shape

- **Hard ceiling: 400 lines per file.** Soft target: 250. Files over 400 reliably break apply-model edits and burn context. Split by verb (`billing.checkout.ts` + `billing.webhook.ts`) before you split by noun.
- **No line over 200 characters** except in generated files. Break long Drizzle chains, long error messages, long type unions across lines.
- **One exported concept per file when practical.** A file called `auth.middleware.ts` exports middleware. If you find yourself adding an unrelated helper, it goes in its own file.
- **Keep generated output out of `src/`.** Drizzle migrations live in `src/db/migrations/` and are never hand-edited. Build artifacts go to `dist/` and are gitignored.

## 4. Dependency rules (what an agent can trace with grep)

- **Explicit imports only.** No barrel `index.ts` files that re-export a directory. Barrels hide the real source and force the agent to chase two hops instead of one.
- **No metaprogramming in application code.** No `Proxy`, no `Reflect.defineProperty` for behavior, no runtime monkey-patching, no dynamic `import()` of application modules. If a library (e.g. Drizzle, Zod) uses these internally, that's fine — your code should not.
- **No inheritance deeper than one level.** Compose via functions and plain objects. A class hierarchy the agent can't read in one file is a class hierarchy the agent will fabricate methods into.
- **No dependency-injection container.** Pass dependencies as function arguments or import them directly. Control flow must be visible to grep.
- **Third-party SDKs are wrapped in exactly one file per feature.** Stripe is imported in `billing.stripe.ts`, nowhere else. Resend in `<feature>.email.ts`. This gives the agent a single seam to mock and a single file to update on a breaking change.
- **`src/env.ts` is the only file that reads `process.env` / `Bun.env`.** Every other file imports typed values from it.

## 5. Types and errors at the seams

- **Public function signatures are fully typed.** No `any`, no implicit return types on exported functions. Internal helpers can be inferred.
- **Domain types live in `<feature>.types.ts`** and are imported by siblings. Don't re-declare `User` in three places.
- **Errors are named classes in `<feature>.errors.ts`**: `InvalidCredentialsError`, `SubscriptionNotFoundError`. The HTTP mapping lives in `platform/http/error-handler.ts`. Routes throw domain errors; they do not call `c.json(..., 401)` directly.
- **Zod schemas for every external boundary:** request bodies, webhook payloads, env vars. Infer TS types from the Zod schema (`z.infer<typeof X>`) — do not maintain parallel type declarations.

## 6. Comments and docstrings

- **Comment the *why*, never the *what*.** The code shows what. If a comment would just restate the code, delete it.
- **A wrong comment is worse than no comment.** When you change behavior, update or delete adjacent comments in the same commit. Stale doc comments are load-bearing lies to an agent.
- **Required comments:** non-obvious invariants ("Stripe sends `subscription.updated` before `invoice.paid` on trial conversion — order matters"), workarounds with a dated reference, and any place correctness depends on something outside the file.

## 7. Tests

- **Tests live next to the code they test.** `foo.service.ts` has `foo.service.test.ts` in the same directory. No top-level `tests/` tree. An agent editing `foo.service.ts` must see the test file in the same directory listing.
- **One verifiable command:** `bun run check` runs typecheck + lint + tests. It must exit non-zero on any failure. Agents use this as the feedback loop; protect it.
- **Route-level tests hit the Hono app in-process** (`app.request(...)`), not over the network. They're the fastest honest integration test and live in `<feature>.routes.test.ts`.
- **Use an ephemeral Neon branch per test run**, driven by `src/testing/db.ts`. No mocking of Drizzle or the DB; mock only external HTTP (Stripe, Resend).
- **Fixtures are named factories**, not JSON blobs: `makeUser({ email: ... })`. Blobs go stale; factories read like the code they test.

## 8. Route/service/schema boundaries

- **Routes** (`*.routes.ts`): parse + validate input with Zod, call one service function, map its result or error to a response. No business logic, no direct DB calls.
- **Services** (`*.service.ts`): business logic, DB access through Drizzle, throws domain errors. No knowledge of HTTP. Exported functions are the feature's public surface to the rest of the app.
- **Schema** (`*.schema.ts`): Drizzle table definitions and nothing else. Imported by `src/db/schema.ts` which re-exports the union for drizzle-kit.

## 9. AGENTS.md is part of the code

- Keep `AGENTS.md` at the repo root with: the verify command, the feature-module template, the "do not touch" list (migrations, generated files), and one canonical feature to imitate (point at `users/`).
- Update it in the same PR as the convention change. An outdated AGENTS.md is the same failure mode as a stale comment, scaled up.

## 10. When to break these rules

- Drizzle schema files may be long and repetitive — tables are inherently shaped that way. Don't abstract them for DRY; let them be boring.
- Migration files are generated and write-once. The 400-line rule doesn't apply.
- Throwaway scripts in `scripts/` may skip the test-colocation and naming rules. They have a reader count of ~1.
- If a Hono or Drizzle idiom conflicts with a rule here, the framework wins. Document the exception in `AGENTS.md` so the next agent doesn't "fix" it.
