---
name: pkl
description: "PKL (Pickle) is Apple's open-source, programmable configuration language — a type-safe alternative to YAML/JSON/TOML. Use this skill when writing PKL configuration files, amending PKL modules, defining PKL schemas or classes, generating config output in JSON/YAML/TOML/plist, or integrating PKL into a build pipeline. Triggers on .pkl files, PKL module authoring, amend expressions, typed property definitions, Listing/Mapping usage, or pkl eval/test/project CLI commands."
---

# PKL

> **CRITICAL: Your training data for PKL is unreliable.** APIs change between versions and your memorized patterns may be wrong or deprecated. You MUST fetch and read the live documentation before writing any code. Never assume — verify against current docs first.

PKL (Pickle) is Apple's open-source configuration language that is programmable, type-safe, and outputs to multiple standard formats. It replaces YAML/JSON/TOML with a language that supports types, constraints, inheritance, and code reuse.

## Documentation

- **Primary Docs**: https://pkl-lang.org/main/current/language-reference/index.html
- **Language Tutorial**: https://pkl-lang.org/main/current/language-tutorial/01_basic_config.html
- **CLI Reference**: https://pkl-lang.org/main/current/pkl-cli/index.html

## Key Capabilities

PKL goes beyond static config formats in four ways:

- **Type safety and constraints** — properties are typed, and constraints like `port: UInt16` or `timeout: Duration(isPositive)` are checked at evaluation time, not at runtime.
- **Amend for config inheritance** — `amends "base.pkl"` overrides selected properties while preserving others, enabling layered configs (dev/staging/prod) without duplication.
- **Multi-format output** — one PKL source can render to JSON, YAML, XML, plist, Java properties, or textproto via CLI flags or `output { renderer = ... }` blocks.
- **Computed properties and late binding** — properties can reference other properties and automatically recompute when dependencies are amended, like a typed spreadsheet.

## Best Practices

**Use `amends` to override values; use `extends` only when adding new properties.**
`amends "base.pkl"` creates a new module that changes values but cannot add new properties — the module's type stays fixed. `extends "base.pkl"` creates a new module subclass and allows adding members. Using `extends` when you only want to override values is unnecessary and breaks type guarantees if the base is not declared `open`.

```pkl
// Correct — only changing values
amends "config/base.pkl"
port = 9090

// Only use extends when you need new properties
extends "config/base.pkl"
port = 9090
debugMode = true  // new property not in base
```

**Declare output format explicitly — PKL does not auto-select JSON or YAML.**
Running `pkl eval file.pkl` outputs PCF (PKL's own format) by default, not JSON or YAML. To get JSON output, pass `-f json` on the CLI or declare the renderer inside the module. Omitting this is the most common source of "my output looks wrong" confusion.

```pkl
// Inside a module — explicit renderer
output {
  renderer = new JsonRenderer {}
}

// CLI equivalent
// pkl eval -f json config.pkl
// pkl eval -f yaml -o config.yaml config.pkl
```

**Required properties have no default — they must be provided when amending.**
A typed property without a default value (`name: String` with no `= "..."`) is required. Amending a module that has required properties without supplying them causes a validation error. Provide defaults in base modules or always supply values in every amend chain.

```pkl
// Base module with a required property
class AppConfig {
  host: String          // required — no default
  port: UInt16 = 8080   // optional — has default
}

// Amending module MUST provide host
amends "AppConfig.pkl"
host = "localhost"
// port can be omitted — default 8080 applies
```

**Listing and Mapping are distinct types — they do not coerce into each other.**
`Listing` is an ordered sequence (like a JSON array); `Mapping` is a keyed collection (like a JSON object). PKL does not automatically convert between them. A property typed as `Listing` cannot receive a `Mapping` value, and vice versa. When amending a Listing, add elements with entries inside the amend block; do not assign a new Mapping.

```pkl
// Listing — ordered, integer-indexed
tags: Listing<String> = new {
  "web"
  "api"
}

// Mapping — keyed
labels: Mapping<String, String> = new {
  ["env"] = "prod"
  ["team"] = "platform"
}

// Amending a Listing — add more elements
amends "base.pkl"
tags {
  "extra-tag"   // appended to inherited elements
}
```

**String interpolation uses `\(expression)`, not `${}` or `#{}`.**
PKL's interpolation syntax is a backslash followed by the expression in parentheses. Using JavaScript-style `${}` or Ruby-style `#{}` produces a literal string instead of interpolating the value, with no error thrown.

```pkl
name = "world"
greeting = "Hello, \(name)!"   // correct — "Hello, world!"
wrong1   = "Hello, ${name}!"   // literal string — "Hello, ${name}!"
wrong2   = "Hello, #{name}!"   // literal string — "Hello, #{name}!"
```

**Import stdlib with `pkl:` scheme; import local files with relative paths.**
Standard library modules use the `pkl:` URI scheme (`import "pkl:math"`). Local modules use relative or absolute file URIs. HTTP imports are supported for remote modules. Forgetting the scheme or using wrong path separators causes import resolution failures.

```pkl
import "pkl:math"           // standard library
import "pkl:json"           // JSON renderer helpers
import "./shared/types.pkl" // relative local file
import "package://pkg.pkl.tools/pkl-json@1.0.0#/json.pkl"  // package

result = math.sqrt(16)      // 4.0
```

## CLI Quick Reference

```bash
# Evaluate to stdout (PCF format by default)
pkl eval config.pkl

# Evaluate to specific format
pkl eval -f json config.pkl
pkl eval -f yaml -o output.yaml config.pkl

# Evaluate multiple files, output alongside source
pkl eval -f json -o %{moduleDir}/%{moduleName}.json src/**/*.pkl

# Run tests
pkl test tests/*.pkl
pkl test --junit-reports=reports/ tests/*.pkl

# Manage project dependencies
pkl project resolve
pkl project package --output-path dist/

# Evaluate a single expression from a module
pkl eval -x metadata.version config.pkl
```

## Common Output Formats

| Format | CLI flag | Renderer class |
|--------|----------|----------------|
| JSON | `-f json` | `new JsonRenderer {}` |
| YAML | `-f yaml` | `new YamlRenderer {}` |
| Java properties | `-f properties` | `new PropertiesRenderer {}` |
| plist | `-f plist` | `new PListRenderer {}` |
| XML/textproto | `-f xml` / `-f textproto` | `new XmlRenderer {}` |
