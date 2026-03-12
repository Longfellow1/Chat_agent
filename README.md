# Chat Agent Service

A comprehensive AI agent service with multi-LLM support, intent routing, and tool execution capabilities.

## Features

- **Multi-LLM Support**: Ollama, vLLM, OpenAI-compatible, LM Studio
- **Intent Routing**: Unified router with 4B/7B model optimization
- **Tool Execution**: MCP gateway, provider chain, content rewriting
- **Domain Logic**: Location handling, trip planning, web search
- **Comprehensive Testing**: Unit, integration, and smoke tests

## Project Structure

```
agent_service/
├── app/                    # API and orchestration layer
│   ├── api/               # HTTP server and endpoints
│   ├── orchestrator/      # Chat flow and request handling
│   ├── policies/          # Pre/post rules and boundary responses
│   └── schemas/           # Data contracts and models
├── domain/                # Business logic
│   ├── intents/          # Intent routers and classification
│   ├── location/         # Location-based queries
│   ├── tools/            # Tool execution and planning
│   └── trip/             # Trip planning engine
└── infra/                # Infrastructure
    ├── llm_clients/      # LLM provider implementations
    └── tool_clients/     # Tool and MCP integrations
```

## Quick Start

### Installation

```bash
pip install -r requirements.txt
```

### Configuration

Copy and configure environment variables:

```bash
cp .env.llm.example .env.llm
```

### Running the Service

```bash
python -m agent_service.app.api.server
```

## LLM Configuration

Supported providers:
- **Ollama**: Local inference
- **vLLM**: High-throughput serving
- **OpenAI-compatible**: Any OpenAI API-compatible endpoint
- **LM Studio**: Desktop LLM application

Configure via `agent_service/infra/llm_clients/llm_config.py`

## Testing

Run all tests:
```bash
pytest tests/
```

Run specific test suites:
```bash
pytest tests/unit/           # Unit tests
pytest tests/integration/    # Integration tests
pytest tests/smoke/          # Smoke tests
```

## Documentation

- [LLM Integration Guide](docs/llm_integration_guide.md)
- [LLM Service README](docs/LLM_SERVICE_README.md)
- [Provider Chain Usage](docs/provider_chain_usage.md)
- [Baidu MCP Integration](docs/baidu_mcp_integration.md)

## Key Components

### Intent Router
Multi-model intent classification with fallback support:
- `unified_router.py`: Main router implementation
- `router_4b_with_logprobs.py`: 4B model with logprobs
- `unified_router_7b_optimized.py`: 7B model optimization

### Tool Execution
- `executor.py`: Tool execution engine
- `planner.py`: Tool planning and sequencing
- `query_preprocessor.py`: Query normalization

### Location Services
- `intent.py`: Location intent detection
- `capability.py`: Location capability management
- `result_processor.py`: Result ranking and filtering

## Development

### Adding New Providers

1. Create provider class in `agent_service/infra/tool_clients/providers/`
2. Inherit from `ProviderBase`
3. Implement required methods
4. Register in provider chain

### Adding New Intent Types

1. Create router in `agent_service/domain/intents/`
2. Implement intent classification logic
3. Register in unified router
4. Add tests in `tests/unit/`

## License

Proprietary - All rights reserved

## Support

For issues and questions, please refer to the documentation or contact the development team.
