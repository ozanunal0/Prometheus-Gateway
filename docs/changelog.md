# Changelog

All notable changes to Prometheus Gateway will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Comprehensive test suite with 90%+ coverage
- Professional documentation site with MkDocs
- GitHub Actions CI/CD pipeline
- Performance monitoring with custom metrics
- Security scanning and vulnerability checks

### Changed
- Improved error handling across all components
- Enhanced logging with structured format
- Updated documentation with detailed examples

### Security
- Added automated security scanning with bandit
- Implemented comprehensive input validation
- Enhanced API key security measures

## [1.0.0] - 2024-01-06

### Added
- **Multi-Provider Support**
  - OpenAI GPT integration (GPT-4, GPT-3.5-turbo)
  - Google Gemini integration (Gemini 2.5 Flash, Pro)
  - Anthropic Claude integration (Claude Sonnet, Opus)
  - Extensible provider architecture

- **Intelligent Routing Engine**
  - Configuration-driven model-to-provider mapping
  - Automatic provider selection based on model names
  - YAML-based configuration with validation

- **Two-Level Caching System**
  - Redis exact cache for identical requests
  - ChromaDB semantic cache for similar queries
  - Configurable TTL and similarity thresholds
  - Cache hit rate monitoring

- **Data Loss Prevention (DLP)**
  - Automatic PII detection using Microsoft Presidio
  - Support for emails, phone numbers, SSNs, credit cards
  - Configurable anonymization strategies
  - Real-time scanning of all requests

- **Security & Authentication**
  - API key management system
  - Secure key generation and hashing
  - Rate limiting per API key (10 requests/minute)
  - Request validation and sanitization

- **Monitoring & Observability**
  - Prometheus metrics integration
  - Custom metrics for requests, latency, and tokens
  - Grafana dashboard templates
  - Health check endpoints

- **Database Integration**
  - SQLModel with SQLite backend
  - API key storage and management
  - Automatic database initialization
  - Migration support

### Infrastructure
- **Docker Support**
  - Multi-service Docker Compose setup
  - Production-ready containers
  - Volume persistence for data
  - Service health checks

- **Development Tools**
  - Comprehensive test suite (pytest)
  - Code quality tools (black, isort, flake8, mypy)
  - Pre-commit hooks
  - Development environment setup

### Documentation
- **API Documentation**
  - OpenAPI/Swagger integration
  - Interactive API explorer
  - Request/response examples
  - Error code documentation

- **User Guides**
  - Installation instructions
  - Configuration reference
  - API usage examples
  - Troubleshooting guide

## [0.3.0] - 2024-01-05

### Added
- Semantic caching with ChromaDB
- Vector similarity search
- Sentence transformer embeddings
- Cache analytics and monitoring

### Changed
- Improved cache key generation
- Enhanced error handling for vector operations
- Updated configuration schema

## [0.2.0] - 2024-01-04

### Added
- Google Gemini provider integration
- Anthropic Claude provider integration
- Provider translation layers
- Configuration-driven routing

### Changed
- Refactored provider architecture
- Improved request/response handling
- Enhanced model compatibility

## [0.1.0] - 2024-01-03

### Added
- Initial release
- OpenAI provider integration
- Basic FastAPI application
- Redis caching support
- Prometheus metrics
- API key authentication
- Rate limiting
- DLP scanning

### Infrastructure
- Docker containerization
- Basic CI/CD pipeline
- SQLite database integration

---

## Version History

| Version | Release Date | Key Features |
|---------|--------------|--------------|
| 1.0.0 | 2024-01-06 | Multi-provider, semantic caching, comprehensive testing |
| 0.3.0 | 2024-01-05 | Semantic caching, vector search |
| 0.2.0 | 2024-01-04 | Google & Anthropic providers |
| 0.1.0 | 2024-01-03 | Initial release, OpenAI integration |

## Contributing

See our [Contributing Guide](development/contributing.md) for information on how to contribute to this project.

## Support

- 📖 [Documentation](https://ozanunal0.github.io/prometheus-gateway)
- 🐛 [Report Issues](https://github.com/ozanunal0/prometheus-gateway/issues)
- 💬 [Community Discussions](https://github.com/ozanunal0/prometheus-gateway/discussions)