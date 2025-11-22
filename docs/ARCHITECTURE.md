# Dynevi: System Architecture

## Overview

Dynevi is built on an agent-based architecture using LangGraph for orchestration, ChromaDB for memory management, and Gemini API for character dialog generation.

## Core Components

### 1. NPC Agent System
- Individual character agents managed by LangGraph
- Each agent maintains personality, backstory, and goals
- Agents generate contextual responses using Gemini API

### 2. Story Orchestrator
- Manages narrative flow and story progression
- Coordinates multi-NPC interactions
- Handles world state updates

### 3. Memory System (ChromaDB + RAG)
- Semantic search for relevant past conversations
- Multi-level memory (immediate, recent, long-term)
- Memory importance scoring and consolidation

### 4. Dialog Engine
- Handles conversation generation
- Context assembly from retrieved memories
- Response validation and filtering

### 5. World State Manager
- Tracks story progression
- Manages locations, events, and timeline
- Handles relationship updates

### 6. GUI Application
- Theater-of-the-mind interface
- Background video playback
- Dialog icon system
- Text-to-speech integration

## Data Flow

```
User Input → Story Orchestrator → NPC Agent
                                    ↓
                            Memory Retrieval (ChromaDB)
                                    ↓
                            Context Assembly
                                    ↓
                            Gemini API (Response Generation)
                                    ↓
                            Memory Storage
                                    ↓
                            TTS Service → GUI Display
```

## Technology Stack

- **LangGraph**: Agent orchestration and state management
- **ChromaDB**: Vector database for semantic memory storage
- **Google Gemini API**: LLM for character dialog generation
- **PyQt6/PySide6**: Desktop GUI framework
- **Python 3.10+**: Core application language

## Design Patterns

- **Agent Pattern**: Each NPC is an independent agent
- **Orchestrator Pattern**: Story orchestrator coordinates agents
- **Repository Pattern**: Memory system abstracts data access
- **Observer Pattern**: Event system for GUI updates

## Memory Strategy

- **Hybrid Approach**: ChromaDB for semantic search + structured storage for metadata
- **Multi-level Memory**: Immediate (last N messages), Recent (last session), Long-term (important events)
- **Importance Scoring**: Memories scored based on emotional impact, story relevance, relationship changes

## Context Assembly

- **Dynamic Retrieval**: Top K relevant memories per conversation turn
- **Context Window Management**: Summarization for histories exceeding token limits
- **Priority System**: Recent memories + high-importance memories always included

---

*This document will be expanded as the system architecture evolves.*

