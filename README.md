# Graphiti Memory Provider for Hermes Agent

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

**Temporal knowledge graph-based memory** using [Graphiti Core](https://github.com/getzep/graphiti-core). Automatically extracts entities, facts, and relationships from conversations, stores them with timestamps in a Neo4j graph database, and retrieves relevant context for future conversations.

---

## ✨ Features

- **🧠 Automatic Memory Recall**: `prefetch()` searches Graphiti before each turn and injects relevant facts/entities into the system prompt
- **⚡ Background Persistence**: `sync_turn()` saves conversations asynchronously without blocking
- **🔍 Explicit Search Tool**: `graphiti_search` for agent-initiated memory queries
- **🗑️ Entity Deletion**: `graphiti_delete_entity` for removing stale entries
- **🧹 Reasoning Block Stripping**: DeepSeek/Qwen3 `<think>` tags and OWUI reasoning blocks are cleaned before saving
- **🎯 Configurable Search Strategies**: 
  - `fast` (BM25 only)
  - `balanced` (BM25 + Cosine similarity)
  - `quality` (Cross-Encoder reranking)
- **📏 Content Truncation**: `max_episode_content_chars` prevents oversized episodes
- **🔒 Environment Variable Support**: Secure credential management via `.env`

---

## 📦 Installation

### Option 1: Install from GitHub (Recommended)

```bash
hermes plugin install https://github.com/p1s4/hermes-graphiti-plugin.git
```

### Option 2: Manual Installation

```bash
# Clone the repository
git clone https://github.com/p1s4/hermes-graphiti-plugin.git
cd hermes-graphiti-plugin

# Copy to Hermes plugins directory
cp -r graphiti /path/to/hermes/plugins/

# Install dependencies
uv pip install --target /opt/data/plugins graphiti-core
```

### Option 3: Docker Compose

Add to your `docker-compose.yml`:

```yaml
services:
  hermes:
    image: hermes-agent:latest
    command: >
      sh -c "uv pip install --target /opt/data/plugins graphiti-core && 
             hermes gateway run"
    volumes:
      - ./plugins/graphiti:/opt/data/plugins/graphiti
    environment:
      - GRAPHITI_API_KEY=your-api-key
      - GRAPHITI_NEO4J_PASSWORD=your-password
```

---

## ⚙️ Configuration

### Quick Setup (Interactive)

```bash
hermes memory setup
```

Follow the interactive prompts to configure Graphiti.

### Manual Setup

#### 1. Create Configuration File

Create `$HERMES_HOME/graphiti.json`:

```json
{
  "openai_api_url": "http://litellm:4000/v1",
  "model": "nvidia/nemotron-3-super-120b-a12b",
  "small_model": "nvidia/nemotron-3-super-120b-a12b",
  "embedding_model": "nomic-embed-text",
  "embedding_dim": 768,
  "neo4j_uri": "bolt://neo4j:7687",
  "neo4j_user": "neo4j",
  "search_strategy": "balanced",
  "max_episode_content_chars": 2000,
  "max_search_results": 10
}
```

#### 2. Set Secrets

Create or edit `$HERMES_HOME/.env`:

```bash
GRAPHITI_API_KEY=sk-your-api-key
GRAPHITI_NEO4J_PASSWORD=your-neo4j-password
```

#### 3. Activate the Plugin

Edit `$HERMES_HOME/config.yaml`:

```yaml
memory:
  provider: graphiti
```

#### 4. Restart Hermes

```bash
hermes gateway restart
```

---

## 📋 Configuration Reference

### graphiti.json

| Key | Default | Description |
|-----|---------|-------------|
| `openai_api_url` | `http://litellm:4000/v1` | OpenAI-compatible LLM endpoint |
| `model` | `gemini-lite` | Model for entity/fact extraction |
| `small_model` | `gemini-lite` | Smaller model for lightweight tasks |
| `embedding_model` | `nomic-embed-text` | Embedding model for semantic search |
| `embedding_dim` | `768` | Embedding dimension |
| `neo4j_uri` | `bolt://neo4j:7687` | Neo4j connection URI |
| `neo4j_user` | `neo4j` | Neo4j username |
| `search_strategy` | `balanced` | `fast` / `balanced` / `quality` |
| `search_limit` | `10` | Max results from search |
| `max_episode_content_chars` | `2000` | Truncate episodes longer than this (0 = disabled) |
| `max_search_results` | `10` | Max facts+entities to inject in prefetch |
| `inject_facts` | `true` | Include facts in prefetch context |
| `inject_entities` | `true` | Include entities in prefetch context |
| `max_inject_facts` | `10` | Max facts to inject |
| `max_inject_entities` | `10` | Max entities to inject |
| `update_communities` | `false` | Enable community detection (experimental) |
| `add_episode_timeout` | `600` | Timeout in seconds for add_episode (0 = disabled) |
| `graphiti_telemetry` | `false` | Enable Graphiti telemetry |
| `semaphore_limit` | `10` | Max concurrent LLM operations in Graphiti |
| `sanitize_search_query` | `true` | Sanitize queries to avoid search engine errors |
| `max_search_message_length` | `512` | Max query length for search |

### Environment Variables

| Variable | Description |
|----------|-------------|
| `GRAPHITI_API_KEY` | API key for LLM provider |
| `GRAPHITI_NEO4J_PASSWORD` | Password for Neo4j database |

---

## 🛠️ Available Tools

### `graphiti_search`

Search the knowledge graph for entities and facts.

**Parameters:**
- `query` (required): Search query string
- `limit` (optional, default: 10): Maximum number of results

**Example:**
```python
# Agent can call this tool explicitly
result = graphiti_search(query="What do I know about Python programming?", limit=5)
```

### `graphiti_delete_entity`

Delete an entity by UUID from the knowledge graph.

**Parameters:**
- `entity_uuid` (required): UUID of the entity to delete
- `entity_name` (optional): Name of the entity (for logging)

**Example:**
```python
# Delete a specific entity
graphiti_delete_entity(entity_uuid="123e4567-e89b-12d3-a456-426614174000", entity_name="OldProject")
```

---

## 🔍 How It Works

### 1. Automatic Memory Injection (prefetch)

Before each conversation turn, Graphiti automatically:
1. Sanitizes the user query
2. Searches the knowledge graph for relevant facts and entities
3. Injects them into the system prompt within `<graphiti_memory_patched>` tags
4. Logs all operations for debugging

**Example Output:**
```
<graphiti_memory_patched>
# Relevant facts retrieved from Temporal Knowledge Graph:
<FACTS>
  - User prefers Python for backend development (Valid: 2026-05-20 - present)
  - User is working on Hermes plugin system (Valid: 2026-05-25 - present)
</FACTS>

# Relevant entities and their summaries:
<ENTITIES>
  - Python: User's preferred programming language for backend
  - Hermes Agent: AI agent framework being extended
</ENTITIES>
</graphiti_memory_patched>
```

### 2. Background Persistence (sync_turn)

After each turn, Graphiti:
1. Strips reasoning blocks (`<think>`, `<details>`) from the conversation
2. Truncates content if it exceeds `max_episode_content_chars`
3. Extracts entities, facts, and relationships asynchronously
4. Stores them in Neo4j with timestamps

### 3. Search Strategies

- **Fast**: BM25 keyword matching only (fastest, less accurate)
- **Balanced**: BM25 + Cosine similarity (good balance)
- **Quality**: Cross-Encoder reranking (slowest, most accurate)

---

## 🐛 Troubleshooting

### Issue: "graphiti-core missing"

**Solution:**
```bash
uv pip install graphiti-core
```

Or add to your Docker startup command:
```bash
command: sh -c "uv pip install --target /opt/data/plugins graphiti-core && hermes gateway run"
```

### Issue: "Graphiti not initialized"

**Causes:**
- Missing `GRAPHITI_API_KEY` in `.env`
- Incorrect Neo4j credentials
- Neo4j not running

**Solution:**
1. Verify `$HERMES_HOME/.env` contains:
   ```bash
   GRAPHITI_API_KEY=sk-your-key
   GRAPHITI_NEO4J_PASSWORD=your-password
   ```
2. Check Neo4j is accessible:
   ```bash
   curl http://neo4j:7474
   ```
3. Restart Hermes

### Issue: Search returns no results

**Causes:**
- No data in the knowledge graph yet
- Query too specific or too vague
- Wrong search strategy

**Solution:**
1. Have a few conversations to populate the graph
2. Try different search strategies in `graphiti.json`:
   ```json
   {"search_strategy": "quality"}
   ```
3. Use the explicit `graphiti_search` tool to debug

### Issue: Slow performance

**Solution:**
1. Reduce `max_episode_content_chars` to limit episode size
2. Use `fast` search strategy for quicker results
3. Increase `semaphore_limit` if you have multiple concurrent conversations
4. Check Neo4j performance and indexing

---

## 📝 Development

### Local Development Setup

```bash
# Clone the repository
git clone https://github.com/p1s4/hermes-graphiti-plugin.git
cd hermes-graphiti-plugin/graphiti

# Install dependencies
pip install graphiti-core

# Run tests (if available)
pytest

# Make changes and commit
git add .
git commit -m "Your changes"
git push
```

### Code Structure

```
graphiti/
├── __init__.py          # Main plugin implementation
├── cli.py               # Command-line interface
├── plugin.yaml          # Plugin metadata
├── README.md            # This file
├── LICENSE              # MIT License
└── .gitignore           # Git ignore rules
```

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- [Graphiti Core](https://github.com/getzep/graphiti-core) - The underlying knowledge graph library
- [Hermes Agent](https://github.com/hermes-agent) - The agent framework this plugin extends
- [Neo4j](https://neo4j.com/) - The graph database

---

## 📞 Support

For issues, questions, or contributions:
- Open an issue on [GitHub](https://github.com/p1s4/hermes-graphiti-plugin/issues)
- Check existing documentation in the [Wiki](https://github.com/p1s4/hermes-graphiti-plugin/wiki)
