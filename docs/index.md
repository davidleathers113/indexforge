# Welcome to IndexForge

IndexForge is a powerful universal file indexing and processing system that helps you organize, search, and analyze files of any type.

## Features

- 🚀 High-performance FastAPI backend
- 🔍 Universal file type support
- 📊 Advanced search and indexing
- 💾 Efficient storage and retrieval
- 📈 Real-time processing
- 📱 Modern web interface

## Quick Start

```bash
# Install with all dependencies
poetry install

# Run the API
poetry run uvicorn src.api.main:app --reload
```

## Project Structure

The project is organized into several modules:

- `api/` - FastAPI application and endpoints
- `indexing/` - Core indexing and search functionality
- `processors/` - File type-specific processors
- `storage/` - Document storage and retrieval
- `web/` - Web interface and API clients

## Documentation Sections

- **API Reference** - Detailed API documentation
- **User Guide** - Installation and usage instructions
- **Development** - Contributing guidelines and development setup

## Getting Help

If you need help, please:

1. Check the [User Guide](guide/getting-started.md)
2. Review the [API Reference](api/endpoints.md)
3. Read the [Contributing Guidelines](development/contributing.md)
4. Open an issue on [GitHub](https://github.com/yourusername/indexforge)

## License

IndexForge is open-source software licensed under the MIT license.
