# Graphiti Memory Provider for Hermes Agent

Temporal knowledge graph-based memory using [Graphiti Core](https://github.com/getzep/graphiti-core).
Automatically extracts entities, facts, and relationships from conversations,
stores them with timestamps in a Neo4j graph database, and retrieves relevant
context for future conversations.

## Features

- **Automatic memory recall**: `prefetch()` searches Graphiti before each turn
- **Background persistence**: `sync_turn()` saves conversations non-blocking
- **Explicit search tool**: `graphiti_search` for agent-initiated memory queries
- **Entity deletion**: `graphiti_delete_entity` for removing stale entries
- **Reasoning block stripping**: DeepSeek/Qwen3 `<think>` tags and OWUI reasoning blocks are cleaned before saving
- **Configurable search strategies**: fast (BM25), balanced (BM25+Cosine), quality (Cross-Encoder)
- **Content truncation**: `max_episode_content_chars` prevents oversized episodes

## Setup

### 1. Install dependencies

Add to your Hermes startup command:
```bash
uv pip install --target /opt/data/plugins graphiti-core
```

Or in `docker-compose.yml`:
```yaml
command: sh -c "uv pip install --target /opt/data/plugins graphiti-core && hermes gateway run"
```

### 2. Configure

Run the interactive setup:
```bash
hermes memory setup
```

Or manually create `$HERMES_HOME/graphiti.json`:
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

Set secrets in `$HERMES_HOME/.env`:
```bash
GRAPHITI_API_KEY=sk-your-api-key
GRAPHITI_NEO4J_PASSWORD=your-password
```

### 3. Activate

In `$HERMES_HOME/config.yaml`:
```yaml
memory:
  provider: graphiti
```

### 4. Restart Hermes

## Config Reference (graphiti.json)

| Key | Default | Description |
|-----|---------|-------------|
| `openai_api_url` | `http://litellm:4000/v1` | OpenAI-compatible LLM endpoint |
| `model` | `nvidia/nemotron-3-super-120b-a12b` | Model for entity/fact extraction |
| `small_model` | `nvidia/nemotron-3-super-120b-a12b` | Smaller model for lightweight tasks |
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
| `add_episode_timeout` | `240` | Timeout in seconds for add_episode (0 = disabled) |
| `graphiti_telemetry` | `false` | Enable Graphiti telemetry |
| `semaphore_limit` | `10` | Max concurrent LLM operations in Graphiti |
| `sanitize_search_query` | `true` | Sanitize queries to avoid search engine errors |
| `max_search_message_length` | `512` | Max query length for search |

## Tools

### graphiti_search
Search the knowledge graph for entities and facts.
Parameters: `query` (required), `limit` (optional, default 10)

### graphiti_delete_entity
Delete an entity by UUID from the knowledge graph.
Parameters: `entity_uuid` (required), `entity_name` (optional)
