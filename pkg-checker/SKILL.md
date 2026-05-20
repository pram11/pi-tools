--- 
name: pkg-checker
description: Check latest version, dependencies, and doc links for packages across ecosystems.
---

# pkg-checker

## Supported
| Ecosystem | Registry |
|-----------|----------|
| `crate` | crates.io |
| `pip` | PyPI |
| `npm` | npmjs.org |
| `maven` | Maven Central |

## Usage
```bash
cd /root/.pi/agent/skills/pkg-checker
cargo run --release -- <ecosystem> <package> [<maven-groupId>]
```

## Examples
```bash
cargo run -- crate serde
cargo run -- pip requests
cargo run -- npm express
cargo run -- maven gson com.google.code.gson
```

## Output Format
```
Package: <name>
Ecosystem: <ecosystem>
Latest: <version>
Docs: <url>
Dependencies:
  - <dep1>
  - <dep2>
Dev Dependencies:
  - <dev1>
```
