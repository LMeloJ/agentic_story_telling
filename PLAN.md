# Dynevi: Immersive Storytelling System - Development Plan

## Project Overview
Create an immersive storytelling experience where NPC characters have AI-generated dialogs that maintain context and personality throughout the narrative. The system will use Gemini API for character interactions, LangGraph for agent orchestration, and ChromaDB with advanced RAG techniques for memory management.

---

## Phase 0: Project Initialization

### 0.1 Repository Setup
- [ ] **Initialize Git repository:**
  - Set up version control
  - Create `.gitignore` for Python and environment files
  - Initialize README.md with project overview
  - Set up branch strategy (main, develop, feature branches)

- [ ] **Project directory structure:**
  ```
  dynevi/
  ├── src/
  │   ├── agents/              # NPC agents and LangGraph definitions
  │   ├── memory/              # ChromaDB and RAG implementation
  │   ├── orchestration/       # Story orchestrator
  │   ├── gui/                 # Python GUI (PyQt/Kivy/Tkinter)
  │   │   ├── video_player.py  # Video playback component
  │   │   ├── dialog_icons.py  # Dialog icon system
  │   │   ├── audio_player.py  # Audio/TTS playback
  │   │   └── main_window.py   # Main GUI window
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

- [ ] **Documentation structure:**
  - README.md with setup instructions
  - CONTRIBUTING.md (if applicable)
  - ARCHITECTURE.md for system design details
  - API.md for API documentation
  - CHANGELOG.md for version tracking

### 0.2 Configuration Framework
- [ ] **Environment configuration:**
  - Create `.env.example` template
  - Environment-specific configs (`.env.development`, `.env.production`)
  - Configuration validation and schema
  - Default NPC profiles and world states in `config/` directory

- [ ] **Configuration management:**
  - Centralized config loader
  - Config validation on startup
  - Hot-reload support for development
  - Secret management for API keys

---

## Phase 1: Foundation & Architecture Design

### 1.1 System Architecture Design
- [ ] **Define core components:**
  - NPC Agent System (individual character agents)
  - Story Orchestrator (manages narrative flow)
  - Memory System (ChromaDB + RAG for context retention)
  - Dialog Engine (handles conversation generation)
  - World State Manager (tracks story progression)

- [ ] **Design data models:**
  - NPC Profile Schema (personality, backstory, relationships, traits, TTS voice config)
  - Conversation History Schema (messages, context, timestamps)
  - World State Schema (locations, events, story progression)
  - Memory Chunk Schema (embeddings, metadata, retrieval keys)
  - Dialog Event Schema (NPC ID, dialog text, timestamp, audio file path)

- [ ] **Define API interfaces:**
  - NPC Agent API (initialize, generate_response, update_memory)
  - Story Orchestrator API (start_story, progress_story, get_state)
  - Memory System API (store, retrieve, update, search)
  - TTS Service API (generate_audio, get_voice_config, stream_audio)
  - GUI Event System (dialog_started, dialog_ended, character_speaking callbacks/events)

### 1.2 Technology Stack Setup
- [ ] **Environment setup:**
  - **Python environment managed by `uv`** (Python 3.10+)
    - Use `uv` for virtual environment creation and management
    - Use `uv pip` for package installation (faster than pip)
    - Use `uv pip compile` for dependency locking and `requirements.txt` generation
  - Create `requirements.txt` with specific versions (managed via `uv`):
    - `langgraph>=0.2.0`
    - `chromadb>=0.4.0`
    - `google-generativeai>=0.3.0`
    - `langchain>=0.1.0`
    - `python-dotenv>=1.0.0` (for config management)
    - GUI framework: `PyQt6>=6.6.0` or `PySide6>=6.6.0` (recommended), or `kivy>=2.2.0`
    - Video playback: `opencv-python>=4.8.0` or `python-vlc>=3.0.0`
    - Audio playback: `pygame>=2.5.0` or `pydub>=0.25.0`
    - `pydantic>=2.0.0` (for data validation)
    - `uvicorn>=0.24.0` (for ASGI server)
  - TTS libraries: Evaluate and select:
    - `pyttsx3` (offline, cross-platform)
    - `gTTS` (Google TTS, requires internet)
    - Cloud TTS APIs: ElevenLabs, Google Cloud TTS, Azure Speech
  - **Python GUI framework:**
    - Evaluate options: PyQt6/PySide6 (recommended for multimedia), Kivy, or Tkinter
    - Video playback library: OpenCV, VLC Python bindings, or PyQt QMediaPlayer
    - Audio playback library: pygame, pydub, or PyQt QMediaPlayer
  - Package management: All Python packages managed through `uv`

- [ ] **Gemini API Integration:**
  - API key configuration and validation
  - Model selection (Gemini Pro/Ultra for character generation)
  - Version compatibility tracking
  - API wrapper with retry logic and exponential backoff
  - Rate limiting per API key
  - Response formatting and validation
  - Error handling for API failures

- [ ] **Error Handling & Resilience:**
  - Circuit breaker pattern for external APIs (Gemini, TTS)
  - Retry mechanisms with exponential backoff
  - Graceful degradation strategies:
    - Fallback to cached responses when API unavailable
    - Text-only mode when TTS fails
    - Default NPC responses when Gemini unavailable
  - Error recovery strategies for ChromaDB failures
  - Timeout handling for all external calls
  - Dead letter queue for failed operations

- [ ] **Logging & Monitoring Infrastructure:**
  - Structured logging framework (e.g., `structlog` or `loguru`)
  - Log levels configuration (DEBUG, INFO, WARNING, ERROR, CRITICAL)
  - Log rotation and archival
  - Conversation flow tracking (NPC interactions, memory operations)
  - Performance metrics collection:
    - API call latency
    - Memory retrieval time
    - Response generation time
    - TTS generation time
  - Error tracking and alerting
  - Health check endpoints for monitoring
  - Request/response logging (sanitized for sensitive data)

- [ ] **Development & Testing Modes:**
  - Mock NPC system for offline development
  - Test fixtures for NPC profiles (sample characters)
  - Sample conversation datasets for testing
  - Development mode with verbose logging
  - Test mode with deterministic responses
  - Mock TTS service for faster development
  - Mock Gemini API responses for unit tests

- [ ] **Media assets:**
  - Background video: `background/loop.mp4` (provided, loop playback)
  - Character icon assets (dialog indicators)
  - Audio output configuration
  - Asset management system (versioning, optimization)

---

## Phase 2: Memory System Implementation

### 2.1 ChromaDB Setup
- [ ] **Database initialization:**
  - Create persistent ChromaDB instance
  - Define collections:
    - `npc_memories` (per-NPC conversation history)
    - `world_knowledge` (shared story context)
    - `character_profiles` (NPC personality embeddings)
    - `relationship_graph` (NPC-to-NPC relationships)

- [ ] **Embedding strategy:**
  - Select embedding model (compatible with Gemini or separate model)
  - Define chunking strategy for conversations
  - Metadata schema design (NPC ID, timestamp, conversation ID, importance score)

### 2.2 Advanced RAG Implementation
- [ ] **Memory retrieval system:**
  - Implement semantic search for relevant past conversations
  - Time-weighted retrieval (recent memories prioritized)
  - Context window management (summarization for long histories)
  - Multi-query retrieval (expand search with rephrased queries)

- [ ] **Memory storage system:**
  - Conversation chunking and embedding
  - Automatic importance scoring
  - Memory consolidation (merge similar memories)
  - Memory decay mechanism (forget less relevant information over time)

- [ ] **Context assembly:**
  - Dynamic context building from retrieved memories
  - Relevance ranking and filtering
  - Context compression for token limits
  - Multi-level context (immediate, recent, long-term)

### 2.3 Data Persistence & Backup
- [ ] **ChromaDB persistence:**
  - Persistent storage configuration
  - Data directory structure and organization
  - Database health checks and recovery

- [ ] **Backup strategy:**
  - Automated backup schedule (daily, weekly)
  - Backup storage location (local and/or cloud)
  - Backup verification and restoration testing
  - Point-in-time recovery capability

- [ ] **Data export/import:**
  - Export story states (JSON format)
  - Export NPC profiles and configurations
  - Export conversation histories
  - Import functionality for data migration
  - Version compatibility checks for imports

- [ ] **Data versioning:**
  - Schema versioning for ChromaDB collections
  - Migration scripts for schema changes
  - Backward compatibility considerations
  - Data integrity validation

---

## Phase 3: NPC Agent System

### 3.1 NPC Profile System
- [ ] **Character definition:**
  - Create NPC profile template (name, personality, backstory, goals, quirks)
  - Personality trait system (Big Five, custom traits)
  - Relationship mapping (to other NPCs, locations, events)
  - Voice/style definition (speech patterns, vocabulary, tone)
  - **TTS voice configuration** (voice ID, speed, pitch, accent for each NPC)

- [ ] **Profile embedding:**
  - Generate embeddings for NPC profiles
  - Store in ChromaDB `character_profiles` collection
  - Enable profile-based memory filtering

### 3.2 LangGraph Agent Architecture
- [ ] **State definition:**
  - Define `NPCState` TypedDict:
    - `npc_id`: str
    - `current_context`: str
    - `conversation_history`: List[Message]
    - `retrieved_memories`: List[Memory]
    - `world_state`: Dict
    - `response`: Optional[str]

- [ ] **Graph nodes:**
  - `retrieve_memory`: Fetch relevant memories from ChromaDB
  - `build_context`: Assemble context from memories and history
  - `generate_response`: Call Gemini API with context
  - `store_memory`: Save new conversation to ChromaDB
  - `update_world_state`: Update shared world knowledge

- [ ] **Graph edges:**
  - Define workflow: retrieve → build → generate → store → update
  - Add conditional edges for error handling
  - Implement checkpoints for state persistence

### 3.3 Gemini Integration
- [ ] **Prompt engineering:**
  - System prompt template for NPC personality
  - Context injection format
  - Response format constraints
  - Personality consistency mechanisms

- [ ] **Response generation:**
  - Implement Gemini API calls with proper context
  - Handle streaming responses (if needed)
  - Response validation and filtering
  - Fallback mechanisms for API failures

- [ ] **Context management:**
  - Token counting and context window management
  - Smart context truncation (preserve important memories)
  - Context summarization for long histories

---

## Phase 4: Story Orchestration

### 4.1 Story State Management
- [ ] **World state system:**
  - Define world state schema (locations, events, timeline)
  - Implement state persistence
  - State versioning for story branching
  - Event system (triggers, consequences)

- [ ] **Multi-NPC coordination:**
  - NPC interaction scheduling
  - Shared context management
  - Relationship updates based on interactions
  - Conflict resolution for contradictory states

### 4.2 Dialog Flow Management
- [ ] **Conversation orchestration:**
  - Turn-taking system
  - Multi-party conversations
  - Conversation branching based on player choices
  - Narrative pacing control

- [ ] **Story progression:**
  - Event triggers and story beats
  - NPC goal tracking
  - Relationship evolution
  - World state updates from conversations

---

## Phase 5: Advanced Features

### 5.1 Context Preservation
- [ ] **Long-term memory:**
  - Implement memory importance scoring
  - Automatic memory summarization
  - Memory consolidation strategies
  - Forgetting mechanisms (selective memory loss)

- [ ] **Consistency checks:**
  - Personality consistency validation
  - Story continuity verification
  - Relationship consistency maintenance
  - Contradiction detection and resolution

### 5.2 Performance Optimization
- [ ] **Caching strategies:**
  - Response caching for similar queries
  - Memory retrieval caching
  - Profile embedding caching

- [ ] **Async operations:**
  - Async Gemini API calls
  - Parallel memory retrieval
  - Concurrent NPC processing

- [ ] **Token optimization:**
  - Smart context compression
  - Selective memory retrieval
  - Response length management

---

## Phase 6: Testing & Refinement

### 6.1 Unit Testing
- [ ] Test memory storage and retrieval
- [ ] Test NPC response generation
- [ ] Test context assembly
- [ ] Test world state management

### 6.2 Integration Testing
- [ ] Test full conversation flows
- [ ] Test multi-NPC interactions
- [ ] Test long-term memory retention
- [ ] Test story progression

### 6.3 Quality Assurance
- [ ] Personality consistency validation
- [ ] Context relevance verification
- [ ] Response quality assessment
- [ ] Performance benchmarking

### 6.4 MVP/Demo Story
- [ ] **Create minimal demo story:**
  - Design simple narrative with 3 NPCs
  - Create sample NPC profiles
  - Define initial world state
  - Create story flow with key interaction points

- [ ] **End-to-end validation:**
  - Test complete conversation flows
  - Validate memory retention across sessions
  - Verify personality consistency
  - Test multi-NPC interactions

- [ ] **User testing:**
  - Prepare demo for user feedback
  - Collect usability feedback
  - Iterate based on testing results
  - Document lessons learned

---

## Phase 7: Theater-of-the-Mind GUI Application

### 7.1 Application Integration Layer
- [ ] **Event system for story interactions:**
  - Python event/callback system (or Qt signals/slots if using PyQt)
  - Direct function calls for starting conversations
  - Event handlers for sending player messages
  - Event handlers for receiving NPC responses
  - State management integration with GUI
  - Input validation and sanitization:
    - Input length limits
    - Text sanitization for display
    - Validation for user input

- [ ] **Application structure:**
  - Main application entry point
  - GUI thread and background thread management
  - Async/await integration for non-blocking operations
  - Error handling and user feedback
  - Settings persistence (save/load user preferences)

- [ ] **TTS Service & Optimization:**
  - Text-to-speech conversion service
  - Voice mapping (NPC ID → voice configuration)
  - **Audio caching strategy:**
    - Cache generated audio files (hash by text + voice config)
    - Cache storage management (size limits, LRU eviction)
    - Cache invalidation strategy
  - **Pre-generation optimization:**
    - Batch generation for common phrases
    - Pre-generated audio for key story moments
    - Background generation for likely next responses
  - Streaming audio support for long dialogs
  - Audio format optimization (compression, codec selection)
  - Audio quality vs. file size balancing
  - Fallback strategies (multiple TTS providers)

- [ ] **Admin/debugging panel (optional):**
  - Separate debug window or panel for development
  - NPC profile inspection and editing
  - Story state visualization and inspection
  - Memory system querying and debugging
  - Log viewer with filtering
  - Performance metrics display

### 7.2 Theater-of-the-Mind GUI
- [ ] **Background video system:**
  - Fullscreen video player with loop playback (PyQt QMediaPlayer, OpenCV, or VLC)
  - Video file: `background/loop.mp4`
  - Seamless looping (no gaps or jumps)
  - Optional: fade transitions, overlay effects
  - Window resizing support (maintain aspect ratio)
  - Fullscreen toggle option

- [ ] **Dialog icon system:**
  - Character position mapping (NPC ID → screen position)
  - Dialog icon component (speech bubble, character portrait, or custom icon)
  - Animation system:
    - Icon appears when character starts speaking
    - Icon pulses/animates during speech
    - Icon fades out when character finishes
  - Multiple character support (multiple icons visible simultaneously)
  - Icon styling (unique per character, matches personality)

- [ ] **Text-to-Speech integration:**
  - Audio playback synchronized with dialog display
  - Per-character voice configuration
  - Audio queue management (handle overlapping speech)
  - Volume controls and audio settings
  - Fallback to text-only if TTS fails

- [ ] **Dialog display:**
  - Text overlay showing current dialog
  - Character name display
  - Typing indicator (optional, while generating response)
  - Dialog history (optional, scrollable log)
  - Subtle, non-intrusive UI (doesn't distract from video)

- [ ] **User interaction:**
  - Text input widget for player responses (QLineEdit/QTextEdit in PyQt)
  - Keyboard shortcuts for common actions (Enter to send, Esc to pause, etc.)
  - Voice input option (optional, future enhancement)
  - Pause/resume controls (keyboard shortcut and/or button)
  - Settings dialog (volume, text size, video settings, etc.)
  - Window controls (minimize, close, fullscreen)

- [ ] **Visual design:**
  - Immersive, minimal UI with no window decorations (borderless/fullscreen)
  - Dark/ambient theme to complement video
  - Custom styling via Qt stylesheets or framework equivalent
  - Smooth animations and transitions (Qt animations or equivalent)
  - Focus on atmosphere and immersion
  - No traditional game UI elements (health bars, menus, etc.)
  - Overlay UI elements (transparent background, subtle borders)

---

## Implementation Sequence (Recommended Order)

1. **Phase 0** - Project initialization (repository, directory structure, configuration framework)
2. **Phase 1.2** - Set up environment, dependencies, and Gemini API integration
3. **Phase 1** - Complete system architecture design (1.1) and establish logging/monitoring infrastructure
4. **Phase 2.1** - Initialize ChromaDB and collections
5. **Phase 2.2** - Implement basic RAG (simple retrieval first, then advanced)
6. **Phase 2.3** - Set up data persistence and backup strategies
7. **Phase 3.1** - Create NPC profile system
8. **Phase 3.2** - Build LangGraph agent with basic nodes
9. **Phase 3.3** - Integrate Gemini for response generation
10. **Phase 4.1** - Add world state management
11. **Phase 4.2** - Implement story orchestration
12. **Phase 5** - Add advanced features incrementally
13. **Phase 6** - Testing throughout development (including MVP/demo story)
14. **Phase 7** - GUI application with Python framework integration

---

## Key Design Decisions

### Memory Strategy
- **Hybrid approach**: Use ChromaDB for semantic search + structured storage for metadata
- **Multi-level memory**: Immediate (last N messages), Recent (last session), Long-term (important events)
- **Memory importance**: Score memories based on emotional impact, story relevance, relationship changes

### Context Assembly
- **Dynamic retrieval**: Retrieve top K relevant memories per conversation turn
- **Context window management**: Use summarization for histories exceeding token limits
- **Priority system**: Recent memories + high-importance memories always included

### NPC Personality
- **System prompts**: Include personality traits, backstory, current goals in every API call
- **Memory filtering**: Retrieve memories that align with NPC's personality and goals
- **Consistency checks**: Validate responses against personality profile

### Story Progression
- **Event-driven**: Conversations trigger world state updates
- **Relationship tracking**: Update NPC relationships based on interactions
- **Goal evolution**: NPC goals change based on story progression

### UI/UX Design
- **Theater-of-the-mind**: Immersive, minimal interface focusing on atmosphere
- **Background video**: Continuous loop creates ambient environment
- **Dialog icons**: Visual indicators show which character is speaking
- **TTS integration**: Each NPC has unique voice for immersive experience
- **Non-intrusive**: UI elements don't distract from the narrative experience

### Versioning & Migration Strategy
- **Schema versioning**: Version all data schemas (NPC profiles, world state, memory chunks)
- **Migration path**: Provide migration scripts for schema changes
- **Backward compatibility**: Support reading older schema versions during transition
- **Configuration versioning**: Version configuration files and provide migration tools
- **Data migration**: Automated migration tools for ChromaDB schema changes
- **Rollback capability**: Ability to rollback to previous schema versions if needed

---

## Success Metrics

### Functional Metrics
- **Context retention**: NPCs remember past conversations accurately (>90% accuracy in memory retrieval)
- **Personality consistency**: NPCs maintain character throughout story (validated through consistency checks)
- **Response quality**: Dialog feels natural and immersive (subjective quality assessment)
- **Memory efficiency**: System handles 100+ conversation turns per NPC without degradation

### Performance Targets
- **Response generation**: < 3 seconds for typical queries (Gemini API call + context assembly)
- **Memory retrieval**: < 500ms for semantic search queries
- **Context assembly**: < 1 second for building conversation context
- **TTS generation**: < 2 seconds for typical dialog (or instant if cached)
- **Memory storage**: < 200ms for storing new conversation chunks
- **ChromaDB query latency**: < 300ms for collection queries
- **GUI event handling**: < 50ms for UI updates (dialog display, icon animations)
- **Application responsiveness**: GUI remains responsive during background processing

### Scalability Targets
- **NPC count**: Support 50+ unique NPCs per story
- **Memory storage**: Efficiently handle 1000+ conversation turns per NPC
- **Database size**: ChromaDB handles 10,000+ memory chunks per collection

### Quality Targets
- **Error rate**: < 1% for Gemini API calls (excluding rate limit errors)
- **Application stability**: Minimal crashes; graceful error handling with user feedback
- **Data integrity**: 100% consistency in memory storage and retrieval
- **User experience**: Smooth video playback (60fps), responsive UI interactions

---

## Next Steps

1. Review and refine this plan
2. Set up development environment (using `uv` for Python environment management)
3. Begin Phase 1 implementation
4. Iterate based on testing and feedback

---

## Notes & Considerations

### API Costs & Rate Limits
- **Gemini API costs**: Monitor API usage and implement response caching to reduce costs
- **TTS API costs**: Cloud TTS services (ElevenLabs, Google Cloud TTS) should be monitored; implement audio caching to minimize API calls
- **Rate limiting**: Respect API rate limits; implement exponential backoff and retry logic
- **Cost optimization**: Pre-generate audio for common phrases; cache frequently accessed memories

### Scalability & Performance
- **Concurrent stories**: Design for multiple simultaneous story sessions (target: 10+ concurrent)
- **NPC scalability**: Support 50+ unique NPCs per story without performance degradation
- **Memory efficiency**: Optimize ChromaDB queries; implement pagination for large result sets
- **Database growth**: Plan for long-term data growth; implement archival strategies for old conversations

### Security & Privacy
- **API keys**: Never commit API keys to version control; use environment variables and secret management
- **Data privacy**: Consider user data storage and privacy requirements (GDPR compliance if applicable)
- **Input sanitization**: Sanitize all user inputs to prevent injection attacks
- **Authentication**: Implement authentication if multi-user support is required

### Data Management
- **Backup strategy**: Regular automated backups of ChromaDB data; test restoration procedures
- **Data versioning**: Version all schemas; provide migration paths for schema changes
- **Export/import**: Enable data export for user portability and system migration
- **Data integrity**: Implement validation checks to ensure data consistency

### Extensibility & Maintenance
- **NPC addition**: Design system to easily add new NPCs and story elements without code changes
- **Plugin architecture**: Consider plugin system for extending functionality (custom memory strategies, TTS providers, etc.)
- **Configuration-driven**: Use configuration files for NPCs, world states, and system settings
- **GUI extensibility**: Design GUI components modularly to support future features and customizations

### Development & Debugging
- **Logging**: Implement comprehensive structured logging for conversation flows, memory operations, and errors
- **Monitoring**: Set up health checks and monitoring dashboards for production environments
- **Development tools**: Create debugging endpoints and admin tools for inspecting story states and memories
- **Test data**: Maintain test fixtures and sample datasets for development and testing

### Audio & Media
- **TTS quality**: Balance TTS quality vs. generation speed; consider multiple providers with fallback options
- **Audio caching**: Cache generated audio files to reduce regeneration costs and improve response times
- **Audio format**: Optimize audio formats for desktop application playback (consider codec, bitrate, compression for pygame/pydub compatibility)
- **Video performance**: Ensure background video doesn't impact UI responsiveness; optimize video compression and format
- **Media assets**: Version control for media assets; consider CDN for production deployment

### GUI & UX
- **Cross-platform compatibility**: Test GUI on Windows, macOS, and Linux (if needed)
- **Window resizing**: Ensure UI adapts to different screen sizes and aspect ratios
- **Accessibility**: Consider accessibility features (keyboard navigation, screen reader support, subtitles)
- **Performance**: Optimize GUI rendering; ensure smooth video playback and animations
- **Application packaging**: Consider packaging as executable (PyInstaller, cx_Freeze) for distribution

### Reliability & Resilience
- **Error handling**: Implement graceful degradation when services fail (fallback responses, text-only mode)
- **Circuit breakers**: Use circuit breaker pattern for external API calls to prevent cascade failures
- **Health checks**: Implement health check endpoints for all critical services
- **Recovery strategies**: Plan for recovery from ChromaDB failures, API outages, and data corruption

### Testing & Quality Assurance
- **Test coverage**: Aim for high test coverage, especially for critical paths (memory retrieval, context assembly)
- **Integration tests**: Test full conversation flows and multi-NPC interactions
- **Performance tests**: Benchmark system under load; test memory efficiency with long conversation histories
- **User testing**: Conduct user testing with MVP/demo story to validate UX and gather feedback

### Deployment & Operations
- **Environment management**: Separate configurations for development and production
- **Application packaging**: Package as standalone executable for distribution (PyInstaller, cx_Freeze, py2app, py2exe)
- **Distribution**: Plan for distributing the application (local installation, app stores if applicable)
- **Monitoring**: Set up error tracking and logging (application logs, crash reports)
- **Documentation**: Maintain up-to-date documentation for GUI, configuration, and architecture
- **Installation requirements**: Document system requirements (Python version, OS, video codecs, etc.)

