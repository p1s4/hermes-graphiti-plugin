# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-05-27

### Added
- **Initial Graphiti plugin implementation** for Hermes Agent
- **Temporal knowledge graph-based memory** using Graphiti Core
- **Automatic memory injection** (prefetch) before each conversation turn
- **Background persistence** (sync_turn) without blocking conversations
- **`graphiti_search` tool** for explicit knowledge graph queries
- **`graphiti_delete_entity` tool** for removing obsolete entities
- **Reasoning block stripping** support (DeepSeek/Qwen3 `<think>` tags, OWUI reasoning blocks)
- **Three configurable search strategies**: fast (BM25), balanced (BM25+Cosine), quality (Cross-Encoder)
- **Automatic content truncation** to prevent oversized episodes
- **Flexible configuration** via `graphiti.json` and environment variables
- **Detailed logging** for debugging and monitoring
- **Automatic dependency installation** with uv pip
- **Comprehensive documentation** with examples, troubleshooting, and best practices

### Changed
- No changes (initial release)

### Fixed
- No fixes (initial release)

### Security
- Environment variable support for sensitive credentials
- Search query sanitization to prevent errors

---

## Future Releases (Planned)

### [1.1.0] - In Development
- [ ] Multi-user support and isolated sessions
- [ ] Knowledge graph export/import functionality
- [ ] Web dashboard for visualizing entities and facts
- [ ] Batch operations support

### [2.0.0] - Roadmap
- [ ] Multi-language support
- [ ] Integration with other graph databases (Amazon Neptune, JanusGraph)
- [ ] UI plugins for knowledge graph visualization
- [ ] REST API for external knowledge graph access

---

**Note:** Future release dates are indicative and subject to change.
