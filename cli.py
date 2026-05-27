"""CLI commands for the Graphiti memory provider plugin.

Adds: hermes graphiti status, hermes graphiti config
"""

import json
import sys
from pathlib import Path


def _get_config_path(args) -> Path:
    """Resolve the hermes_home path for config lookup."""
    hermes_home = getattr(args, 'hermes_home', None) or ''
    if not hermes_home:
        hermes_home = Path.home() / '.hermes'
    return Path(hermes_home) / 'graphiti.json'


def graphiti_command(args):
    """Handler dispatched by argparse."""
    sub = getattr(args, 'graphiti_command', None)
    if sub == 'status':
        _cmd_status(args)
    elif sub == 'config':
        _cmd_config(args)
    else:
        print('Usage: hermes graphiti <status|config>')


def _cmd_status(args):
    """Show Graphiti provider status."""
    config_path = _get_config_path(args)

    print('Graphiti Memory Provider Status')
    print('=' * 40)

    # Config file
    if config_path.exists():
        print(f'✅ Config file: {config_path}')
        try:
            config = json.loads(config_path.read_text())
            print(f'   Neo4j URI:  {config.get("neo4j_uri", "not set")}')
            print(f'   Neo4j User: {config.get("neo4j_user", "not set")}')
            print(f'   API URL:    {config.get("openai_api_url", "not set")}')
            print(f'   Model:      {config.get("model", "not set")}')
            print(f'   Embedding:  {config.get("embedding_model", "not set")}')
            print(f'   Strategy:   {config.get("search_strategy", "not set")}')
        except Exception as e:
            print(f'   ⚠️  Error reading config: {e}')
    else:
        print(f'❌ Config file not found: {config_path}')
        print('   Run: hermes memory setup')

    # Secrets check
    import os
    api_key = os.environ.get('GRAPHITI_API_KEY', '')
    neo4j_pass = os.environ.get('GRAPHITI_NEO4J_PASSWORD', '')
    print()
    print(f'{"✅" if api_key else "❌"} GRAPHITI_API_KEY: {"set" if api_key else "missing"}')
    print(f'{"✅" if neo4j_pass else "❌"} GRAPHITI_NEO4J_PASSWORD: {"set" if neo4j_pass else "missing"}')

    # Active check
    print()
    try:
        # PATCH: Import relativo per evitare il crash sui plugin utente esterni
        from . import GraphitiMemoryProvider
        provider = GraphitiMemoryProvider()
        # Passiamo un dizionario di mock per evitare eccezioni di inizializzazione durante il check statico
        provider.initialize(session_id="status_check", hermes_home=str(config_path.parent))
        available = provider.is_available()
        print(f'{"✅" if available else "❌"} Provider available: {available}')
    except Exception as e:
        print(f'⚠️  Cannot load provider: {e}')


def _cmd_config(args):
    """Show or edit Graphiti config."""
    config_path = _get_config_path(args)

    if not config_path.exists():
        print(f'No config file found at {config_path}')
        print('Run: hermes memory setup')
        return

    try:
        config = json.loads(config_path.read_text())
    except Exception as e:
        print(f'Error reading config: {e}')
        return

    print('Current Graphiti Configuration')
    print('=' * 40)
    print(json.dumps(config, indent=2))
    print()
    print(f'Config file: {config_path}')


def register_cli(subparser) -> None:
    """Build the hermes graphiti argparse tree."""
    subs = subparser.add_subparsers(dest='graphiti_command')
    subs.add_parser('status', help='Show Graphiti provider status')
    subs.add_parser('config', help='Show Graphiti configuration')
    subparser.set_defaults(func=graphiti_command)