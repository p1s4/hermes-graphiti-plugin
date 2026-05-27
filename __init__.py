"""Graphiti memory plugin MemoryProvider for temporal knowledge graph memory."""

from __future__ import annotations
import asyncio
import json
import logging
import os
import re
import sys
import threading
import time
import subprocess
import warnings
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from agent.memory_provider import MemoryProvider

# Silenzia i warning di serializzazione di Pydantic sui log generali
warnings.filterwarnings("ignore", message="Pydantic serializer warnings")

# --- CONFIGURAZIONE LOGGING ESPLICITA PER DOCKER (STILE EMITTER OPEN-WEBUI) ---
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.propagate = False 

sys_handler = logging.StreamHandler(sys.stdout)
sys_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(message)s')  # Lasciamo il formato pulito gestito dalle stringhe custom
sys_handler.setFormatter(formatter)
logger.handlers.clear()
logger.addHandler(sys_handler)
# -----------------------------------------------------------------------------

_REASONING_DETAIL_RE = re.compile(r'<details[^>]*type=["\']reasoning["\'][^>]*>.*?</details>', re.DOTALL)
_DETAIL_GENERIC_RE = re.compile(r'<details[^>]*>.*?</details>', re.DOTALL)
_THINK_TAG_RE = re.compile(r'<think>.*?</think>', re.DOTALL)

def strip_reasoning_blocks(text: str) -> str:
    text = _REASONING_DETAIL_RE.sub('', text)
    text = _DETAIL_GENERIC_RE.sub('', text)
    text = _THINK_TAG_RE.sub('', text)
    return text.strip()

def truncate_content(text: str, max_chars: int) -> str:
    if max_chars <= 0 or len(text) <= max_chars: return text
    return text[:max_chars] + ''

def sanitize_search_query(query: str) -> str:
    sanitized = re.sub(r'[@:\"()|]', ' ', query)
    return re.sub(r'\s+', ' ', sanitized).strip()

def truncate_text_middle(text: str, max_length: int) -> str:
    if max_length <= 0 or len(text) <= max_length: return text
    if max_length < 10: return text[:max_length]
    ellipsis = '...'
    available = max_length - len(ellipsis)
    return text[:available // 2] + ellipsis + text[-(available - available // 2):]

DEFAULTS = {
    'openai_api_url': 'http://litellm:4000/v1',
    'model': 'gemini-lite',
    'small_model': 'gemini-lite',
    'embedding_model': 'nomic-embed-text',
    'embedding_dim': 768,
    'neo4j_uri': 'bolt://neo4j:7687',
    'neo4j_user': 'neo4j',
    'search_strategy': 'balanced',
    'search_limit': 10,
    'max_episode_content_chars': 2000,
    'max_search_results': 10,
    'inject_facts': True,
    'inject_entities': True,
    'max_inject_facts': 10,
    'max_inject_entities': 10,
    'update_communities': False,
    'add_episode_timeout': 600,
    'graphiti_telemetry': False,
    'semaphore_limit': 10,
    'sanitize_search_query': True,
    'max_search_message_length': 512,
}

SEARCH_SCHEMA = {
    'name': 'graphiti_search',
    'description': 'Search the Graphiti knowledge graph for entities and facts.',
    'parameters': {
        'type': 'object',
        'properties': {
            'query': {'type': 'string', 'description': 'Search query'},
            'limit': {'type': 'integer', 'description': 'Max results'}
        },
        'required': ['query'],
    },
}

DELETE_ENTITY_SCHEMA = {
    'name': 'graphiti_delete_entity',
    'description': 'Delete an entity from the Graphiti knowledge graph by UUID.',
    'parameters': {
        'type': 'object',
        'properties': {
            'entity_uuid': {'type': 'string'},
            'entity_name': {'type': 'string'}
        },
        'required': ['entity_uuid'],
    },
}

class GraphitiMemoryProvider(MemoryProvider):
    @property
    def name(self) -> str:
        return 'graphiti'

    def is_available(self) -> bool:
        return True

    def initialize(self, session_id: str, **kwargs) -> None:
        self._session_id = session_id
        self._hermes_home = kwargs.get('hermes_home', '')
        self._platform = kwargs.get('platform', 'cli')
        self._agent_context = kwargs.get('agent_context', 'primary')

        self._graphiti = None
        self._indices_built = False
        self._initialized = False

        self._sync_thread = None
        self._prefetch_thread = None
        self._prefetch_result = ''
        self._prefetch_lock = threading.Lock()
        self._turn_counter = 0

        # ASYNC WORKER
        self._worker_loop = asyncio.new_event_loop()
        def _start_loop(loop):
            asyncio.set_event_loop(loop)
            loop.run_forever()
        self._worker_thread = threading.Thread(target=_start_loop, args=(self._worker_loop,), daemon=True)
        self._worker_thread.start()

        try:
            import graphiti_core
            logger.info("hermes | [GRAPHITI-PLUGIN] ✅ graphiti-core rilevato correttamente.")
        except ImportError:
            logger.info("hermes | [GRAPHITI-PLUGIN] ⚠️ graphiti-core assente. Installazione automatica con uv...")
            try:
                subprocess.run(['uv', 'pip', 'install', 'graphiti-core'], check=True, capture_output=True, text=True)
                import importlib
                importlib.invalidate_caches()
                logger.info("hermes | [GRAPHITI-PLUGIN] ✅ graphiti-core installato con successo!")
            except Exception as e:
                logger.error(f"hermes | [GRAPHITI-PLUGIN] ❌ Fallimento installazione uv: {e}")
                return

        self._config = self._load_config()
        os.environ['GRAPHITI_TELEMETRY_ENABLED'] = str(self._config.get('graphiti_telemetry', False)).lower()
        os.environ['SEMAPHORE_LIMIT'] = str(self._config.get('semaphore_limit', 10))
        logger.info(f"hermes | [GRAPHITI-PLUGIN] 🚀 Provider inizializzato per la sessione: {session_id}")

    def get_config_schema(self) -> List[Dict[str, Any]]: return []
    def save_config(self, values: Dict[str, Any], hermes_home: str) -> None: pass
    def system_prompt_block(self) -> str:
        return 'Graphiti memory provider is active.' if self._ensure_initialized() else ''

    def prefetch(self, query: str, *, session_id: str = '') -> str:
        if not query.strip(): return ''
        if not self._ensure_initialized():
            logger.warning("hermes | [GRAPHITI-PLUGIN] ⚠️ Impossibile eseguire prefetch: Graphiti non inizializzato.")
            return ''

        search_query = sanitize_search_query(query) if self._config.get('sanitize_search_query', True) else query
        max_len = self._config.get('max_search_message_length', 512)
        if max_len > 0 and len(search_query) > max_len: 
            search_query = truncate_text_middle(search_query, max_len)

        # EMITTER DI APERTURA LOG RICERCA
        logger.info(f"hermes | [GRAPHITI-PLUGIN] 🔍 Iniezione Automatica - Ricerca nel Grafo per: '{search_query[:60]}...'")
        
        search_start = time.time()
        try:
            results = self._run_async(self._search_graphiti(search_query))
        except Exception as e:
            logger.error(f"hermes | [GRAPHITI-PLUGIN] ❌ Errore critico durante la ricerca automatica (prefetch): {e}", exc_info=True)
            return ''

        search_duration = time.time() - search_start
        if not results:
            logger.info(f"hermes | [GRAPHITI-PLUGIN] 🔍 Nessun ricordo rilevante trovato nel grafo ({search_duration:.2f}s).")
            return ''
        
        edges, nodes = results
        if not edges and not nodes:
            logger.info(f"hermes | [GRAPHITI-PLUGIN] 🔍 Nessun nodo o arco estratto dal grafo ({search_duration:.2f}s).")
            return ''

        facts = []
        entities = {}
        if self._config.get('inject_facts', True):
            for edge in edges[:self._config.get('max_inject_facts', 10)]:
                if getattr(edge, 'fact', None): 
                    facts.append((edge.fact, getattr(edge, 'valid_at', None), getattr(edge, 'invalid_at', None)))
        if self._config.get('inject_entities', True):
            for node in nodes[:self._config.get('max_inject_entities', 10)]:
                if getattr(node, 'name', None) and getattr(node, 'summary', None): 
                    entities[node.name] = node.summary

        # EMITTER DI CONTEGGIO RISULTATI TROVATI
        status_parts = []
        if facts: status_parts.append(f"{len(facts)} fatti")
        if entities: status_parts.append(f"{len(entities)} entità")
        logger.info(f"hermes | [GRAPHITI-PLUGIN] 🧠 Trovati e pronti all'iniezione: {' e '.join(status_parts)} ({search_duration:.2f}s)")

        if not facts and not entities: return ''

        # Costruzione del blocco di iniezione
        parts = ['<graphiti_memory_patched>']
        if facts:
            parts.append('# Fatti rilevanti recuperati dal Grafo Temporale:')
            parts.append('<FACTS>')
            for f, v, i in facts: 
                parts.append(f'  - {f} (Valid: {v or "unknown"} - {i or "present"})')
                logger.info(f"hermes | [GRAPHITI-PLUGIN] 📥 Iniettato Fatto: {f}")
            parts.append('</FACTS>')
        if entities:
            if facts: parts.append('')
            parts.append('# Entità rilevanti e loro riassunti:')
            parts.append('<ENTITIES>')
            for n, s in entities.items(): 
                parts.append(f'  - {n}: {s}')
                logger.info(f"hermes | [GRAPHITI-PLUGIN] 📥 Iniettata Entità: {n}")
            parts.append('</ENTITIES>')
        parts.append('</graphiti_memory_patched>')
        
        logger.info("hermes | [GRAPHITI-PLUGIN] 📥 Iniezione automatica nel System Prompt completata con successo.")
        return '\n'.join(parts)

    def sync_turn(self, user_content: str, assistant_content: Any, *, session_id: str = '') -> None:
        if self._agent_context != 'primary': return

        user_str = ""
        if user_content is not None:
            if hasattr(user_content, 'content') and user_content.content: user_str = str(user_content.content)
            elif isinstance(user_content, dict) and 'content' in user_content: user_str = str(user_content['content'])
            else: user_str = str(user_content)

        assistant_str = ""
        if assistant_content is not None:
            if hasattr(assistant_content, 'content') and assistant_content.content: assistant_str = str(assistant_content.content)
            elif isinstance(assistant_content, dict) and 'content' in assistant_content: assistant_str = str(assistant_content['content'])
            elif hasattr(assistant_content, 'model_dump_json'):
                try:
                    data = json.loads(assistant_content.model_dump_json())
                    assistant_str = data.get('content', '') or str(data)
                except: assistant_str = str(assistant_content)
            else: assistant_str = str(assistant_content)

        if not user_str.strip() and not assistant_str.strip(): return

        clean_user = truncate_content(strip_reasoning_blocks(user_str), self._config.get('max_episode_content_chars', 2000))
        clean_assistant = truncate_content(strip_reasoning_blocks(assistant_str), self._config.get('max_episode_content_chars', 2000))
        if not clean_user and not clean_assistant: return
        
        episode_body = f'User: {clean_user}\n\n---\n\nAssistant: {clean_assistant}'

        def _sync():
            logger.info("hermes | [GRAPHITI-PLUGIN] ✍️ Analisi del turno ed estrazione dei fatti in background...")
            sync_start = time.time()
            try:
                add_results = self._run_async(self._add_episode(episode_body))
                self._turn_counter += 1
                duration = time.time() - sync_start
                
                if add_results:
                    logger.info(f"hermes | [GRAPHITI-PLUGIN] ✅ Turno aggiunto al Grafo Temporale ({duration:.2f}s)")
                    if hasattr(add_results, 'edges') and add_results.edges:
                        for idx, edge in enumerate(add_results.edges, 1):
                            emoji = "🔚" if getattr(edge, 'invalid_at', None) else "🔛"
                            logger.info(f"hermes | [GRAPHITI-PLUGIN]   {emoji} Fatto Estratto {idx}/{len(add_results.edges)}: {edge.fact}")
                    if hasattr(add_results, 'nodes') and add_results.nodes:
                        for idx, node in enumerate(add_results.nodes, 1):
                            summary = f" - {node.summary}" if hasattr(node, 'summary') and node.summary else ""
                            logger.info(f"hermes | [GRAPHITI-PLUGIN]   👤 Entità Estratta {idx}/{len(add_results.nodes)}: {node.name}{summary}")
                else:
                    logger.info(f"hermes | [GRAPHITI-PLUGIN] ✅ Turno elaborato, nessun nuovo fatto rilevante da estrarre ({duration:.2f}s).")
            except Exception as e:
                logger.warning(f"hermes | [GRAPHITI-PLUGIN] ❌ Scrittura automatica (sync_turn) fallita: {e}")

        if self._sync_thread and self._sync_thread.is_alive(): self._sync_thread.join(timeout=2.0)
        self._sync_thread = threading.Thread(target=_sync, daemon=True)
        self._sync_thread.start()

    def on_session_end(self, messages: List[Dict[str, Any]]) -> None:
        if self._sync_thread and self._sync_thread.is_alive(): self._sync_thread.join(timeout=10.0)

    def get_tool_schemas(self) -> List[Dict[str, Any]]: return [SEARCH_SCHEMA, DELETE_ENTITY_SCHEMA]
    
    def handle_tool_call(self, tool_name: str, args: Dict[str, Any], **kwargs) -> str:
        if not self._ensure_initialized():
            return json.dumps({"error": "Graphiti memory provider not initialized"})

        if tool_name == 'graphiti_search':
            query = args.get('query', '')
            limit = args.get('limit', self._config.get('search_limit', 10))
            if not query:
                return json.dumps({"error": "Missing query parameter"})
            
            logger.info(f"hermes | [GRAPHITI-PLUGIN] 🛠️ Tool Call - Esecuzione Ricerca esplicita richiesta per: '{query[:60]}...'")
            try:
                results = self._run_async(self._search_graphiti(query, limit))
                if not results:
                    return json.dumps({"facts": [], "entities": {}})
                
                edges, nodes = results
                facts = []
                entities = {}
                
                for edge in edges:
                    if getattr(edge, 'fact', None):
                        facts.append({
                            "fact": edge.fact,
                            "valid_at": str(edge.valid_at) if getattr(edge, 'valid_at', None) else None,
                            "invalid_at": str(edge.invalid_at) if getattr(edge, 'invalid_at', None) else None
                        })
                
                for node in nodes:
                    if getattr(node, 'name', None) and getattr(node, 'summary', None):
                        entities[node.name] = node.summary
                        
                return json.dumps({"facts": facts, "entities": entities}, ensure_ascii=False)
            except Exception as e:
                logger.error(f"hermes | [GRAPHITI-PLUGIN] ❌ Errore durante esecuzione tool search: {e}")
                return json.dumps({"error": str(e)})

        elif tool_name == 'graphiti_delete_entity':
            entity_uuid = args.get('entity_uuid', '')
            entity_name = args.get('entity_name', 'Unknown')
            if not entity_uuid:
                return json.dumps({"error": "Missing entity_uuid parameter"})
                
            logger.info(f"hermes | [GRAPHITI-PLUGIN] 🛠️ Tool Call - Eliminazione esplicita entità richiesta: {entity_name} ({entity_uuid})")
            try:
                from graphiti_core.nodes import EntityNode
                
                async def _delete():
                    await EntityNode.delete_by_uuids(self._graphiti.driver, [entity_uuid])
                
                self._run_async(_delete())
                return json.dumps({"success": True, "message": f"Entity {entity_name} ({entity_uuid}) successfully deleted from graph"})
            except Exception as e:
                logger.error(f"hermes | [GRAPHITI-PLUGIN] ❌ Errore durante esecuzione tool delete: {e}")
                return json.dumps({"error": str(e)})

        return json.dumps({"error": f"Unknown tool name: {tool_name}"})

    def shutdown(self) -> None:
        if self._sync_thread and self._sync_thread.is_alive(): self._sync_thread.join(timeout=10.0)
        if self._graphiti:
            try: self._run_async(self._graphiti.close())
            except: pass
        if hasattr(self, '_worker_loop'):
            self._worker_loop.call_soon_threadsafe(self._worker_loop.stop)

    def _load_config_file(self) -> Dict[str, Any]:
        config_path = Path(self._hermes_home) / 'graphiti.json'
        if config_path.exists():
            try: return json.loads(config_path.read_text())
            except: pass
        return {}

    def _load_config(self) -> Dict[str, Any]:
        config = dict(DEFAULTS)
        config.update(self._load_config_file())
        if os.environ.get('GRAPHITI_API_KEY', ''): config['api_key'] = os.environ.get('GRAPHITI_API_KEY', '')
        if os.environ.get('GRAPHITI_NEO4J_PASSWORD', ''): config['neo4j_password'] = os.environ.get('GRAPHITI_NEO4J_PASSWORD', '')
        return config

    def _ensure_initialized(self) -> bool:
        if self._initialized and self._graphiti is not None: return True
        if not self._config.get('api_key', '').strip(): return False
        try:
            self._init_graphiti(self._config)
            self._initialized = True
            return True
        except Exception as e:
            return False

    def _init_graphiti(self, config: Dict[str, Any]) -> None:
        async def _do_init():
            from graphiti_core import Graphiti
            from graphiti_core.llm_client.config import LLMConfig
            from graphiti_core.llm_client.openai_client import OpenAIClient
            from graphiti_core.embedder.openai import OpenAIEmbedder, OpenAIEmbedderConfig
            from graphiti_core.cross_encoder.openai_reranker_client import OpenAIRerankerClient

            # ── SANIFICAZIONE AMBIENTALE CRITICA ────────────────────────────────
            # Rimuoviamo temporaneamente le variabili globali del container che 
            # costringono Graphiti a usare il modello pesante "hermes" al posto di Gemini.
            env_backup = {}
            for var_name in ['OPENAI_MODEL_NAME', 'OPENAI_MODEL', 'MODEL', 'ZEP_MODEL']:
                if var_name in os.environ:
                    env_backup[var_name] = os.environ[var_name]
                    del os.environ[var_name]
            # ────────────────────────────────────────────────────────────────────

            try:
                # Estraiamo i modelli direttamente dal tuo graphiti.json
                target_model = config.get('model', DEFAULTS['model'])
                target_small_model = config.get('small_model', DEFAULTS['small_model'])

                logger.info(f"hermes | [GRAPHITI-PLUGIN] 🛠️ Configurazione LLM Graphiti - Main: {target_model} | Small: {target_small_model}")

                llm_config = LLMConfig(
                    api_key=config['api_key'], 
                    model=target_model, 
                    small_model=target_small_model, 
                    base_url=config.get('openai_api_url', DEFAULTS['openai_api_url'])
                )
                
                llm_client = OpenAIClient(config=llm_config)
                embedder = OpenAIEmbedder(config=OpenAIEmbedderConfig(api_key=config['api_key'], embedding_model=config.get('embedding_model', DEFAULTS['embedding_model']), embedding_dim=config.get('embedding_dim', DEFAULTS['embedding_dim']), base_url=config.get('openai_api_url', DEFAULTS['openai_api_url'])))
                cross_encoder = OpenAIRerankerClient(config=llm_config)

                self._graphiti = Graphiti(config.get('neo4j_uri', DEFAULTS['neo4j_uri']), config.get('neo4j_user', DEFAULTS['neo4j_user']), config.get('neo4j_password', ''), llm_client=llm_client, embedder=embedder, cross_encoder=cross_encoder)
                if not self._indices_built:
                    await self._graphiti.build_indices_and_constraints()
                    self._indices_built = True
            
            finally:
                # Ripristiniamo le variabili d'ambiente originali per non rompere l'operatività di Hermes Agent
                for var_name, var_value in env_backup.items():
                    os.environ[var_name] = var_value

        self._run_async(_do_init())

    async def _search_graphiti(self, query: str, limit: Optional[int] = None) -> Optional[tuple]:
        from graphiti_core.search.search_config_recipes import COMBINED_HYBRID_SEARCH_RRF, COMBINED_HYBRID_SEARCH_CROSS_ENCODER
        
        strategy = self._config.get('search_strategy', 'balanced').lower()
        if strategy == 'quality':
            base_config = COMBINED_HYBRID_SEARCH_CROSS_ENCODER
        else:
            base_config = COMBINED_HYBRID_SEARCH_RRF
            
        try:
            results = await self._graphiti.search_(query=query, config=base_config.model_copy(update={'limit': limit or 10}))
            return (results.edges, results.nodes)
        except Exception as e:
            raise e

    async def _add_episode(self, episode_body: str) -> Any:
        from graphiti_core.nodes import EpisodeType
        config = self._config
        episode_kwargs = {
            'name': f'turn_{self._turn_counter + 1}',
            'episode_body': episode_body,
            'source': EpisodeType.message,
            'source_description': f'{datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")}',
            'reference_time': datetime.now(timezone.utc),
            'update_communities': False,
        }
        timeout = config.get('add_episode_timeout', 600)
        if timeout > 0:
            return await asyncio.wait_for(self._graphiti.add_episode(**episode_kwargs), timeout=timeout)
        else:
            return await self._graphiti.add_episode(**episode_kwargs)

    def _run_async(self, coro):
        try:
            future = asyncio.run_coroutine_threadsafe(coro, self._worker_loop)
            return future.result(timeout=None)
        except Exception as e:
            raise e

def register(ctx) -> None:
    ctx.register_memory_provider(GraphitiMemoryProvider())