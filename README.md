# Dynevi: Immersive Storytelling System

An immersive storytelling experience where NPC characters have AI-generated dialogs that maintain context and personality throughout the narrative.

## Overview

Dynevi is a theater-of-the-mind storytelling application that combines:
- **AI-Powered NPCs**: Characters with persistent personalities and memories using Gemini API
- **Advanced Memory System**: ChromaDB with RAG techniques for long-term context retention
- **LangGraph Orchestration**: Agent-based architecture for managing character interactions
- **Immersive GUI**: Background video with dialog icons and text-to-speech integration

## Features

- 🤖 **Intelligent NPCs**: Each character maintains personality, backstory, and relationships
- 🧠 **Persistent Memory**: Characters remember past conversations and story events
- 🎭 **Dynamic Storytelling**: Story progression adapts based on player interactions
- 🎬 **Theater-of-the-Mind UI**: Immersive background video with character dialog indicators
- 🔊 **Text-to-Speech**: Unique voices for each NPC character
- 📚 **Advanced RAG**: Semantic search and context assembly for relevant memory retrieval

## Technology Stack

- **Python 3.10+**: Core application language
- **LangGraph**: Agent orchestration and workflow management
- **ChromaDB**: Vector database for memory storage and retrieval
- **Google Gemini API**: Character dialog generation
- **Kivy**: GUI framework for desktop application
- **uv**: Python package and environment management

## Project Structure

```
dynevi/
├── src/
│   ├── agents/              # NPC agents and LangGraph definitions
│   ├── memory/              # ChromaDB and RAG implementation
│   ├── orchestration/       # Story orchestrator
│   ├── gui/                 # Python GUI components
│   ├── services/            # TTS, logging, etc.
│   ├── models/              # Data models and schemas
│   └── config/              # Configuration management
├── tests/
├── scripts/                 # Utility scripts
├── data/                    # ChromaDB storage, backups
├── assets/                  # Media assets (icons, etc.)
├── background/              # Background video assets
├── docs/                    # Documentation
├── config/                  # Configuration files
└── requirements.txt
```

## Getting Started

### Prerequisites

- Python 3.10 or higher
- [uv](https://github.com/astral-sh/uv) for package management
- Google Gemini API key (for character dialog generation)
- TTS service API key (optional, for text-to-speech)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd dynevi
```

2. Set up Python environment using `uv`:
```bash
# Install uv if not already installed
# See: https://github.com/astral-sh/uv

# Create virtual environment
uv venv

# Activate virtual environment
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate

# Install dependencies
uv pip install -r requirements.txt
```

3. Configure environment variables:
```bash
# Copy example environment file
cp .env.example .env

# Edit .env and add your API keys
# GEMINI_API_KEY=your_gemini_api_key_here
# TTS_API_KEY=your_tts_api_key_here (if using cloud TTS)
```

4. Run the application:
```bash
python -m src.gui.main_window
```

## Configuration

Configuration files are located in the `config/` directory:
- NPC profiles and character definitions
- World state initializations
- TTS voice configurations
- System settings

See `docs/ARCHITECTURE.md` for detailed system architecture and `docs/API.md` for API documentation.

## Development

See `PLAN.md` for the comprehensive development plan and `EXECUTION_PLAN.md` for current progress.

### Development Setup

1. Install development dependencies:
```bash
uv pip install -r requirements-dev.txt  # If available
```

2. Run tests:
```bash
pytest tests/
```

3. Check code quality:
```bash
# Add linting/formatting commands as configured
```

## Documentation

- [PLAN.md](PLAN.md): Comprehensive development plan
- [EXECUTION_PLAN.md](EXECUTION_PLAN.md): Current execution progress
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md): System architecture details
- [docs/API.md](docs/API.md): API documentation

## License

[Add license information]

## Contributing

[Add contributing guidelines if applicable]

## Status

🚧 **In Development** - Currently in Phase 0: Project Initialization

See `EXECUTION_PLAN.md` for detailed progress tracking.

