# Dynevi: API Documentation

## Overview

This document describes the internal API interfaces for the Dynevi system components.

## NPC Agent API

### `initialize(npc_id: str, profile: NPCProfile) -> None`
Initialize an NPC agent with its profile.

**Parameters:**
- `npc_id`: Unique identifier for the NPC
- `profile`: NPC profile containing personality, backstory, goals, etc.

### `generate_response(context: ConversationContext) -> str`
Generate a dialog response for the NPC.

**Parameters:**
- `context`: Current conversation context including history, memories, world state

**Returns:**
- `str`: Generated dialog text

### `update_memory(conversation: Conversation) -> None`
Store a new conversation in the NPC's memory.

**Parameters:**
- `conversation`: Conversation object with messages and metadata

## Story Orchestrator API

### `start_story(story_config: StoryConfig) -> StoryState`
Initialize a new story session.

**Parameters:**
- `story_config`: Story configuration including NPCs, initial world state

**Returns:**
- `StoryState`: Initial story state

### `progress_story(player_input: str, story_state: StoryState) -> StoryState`
Process player input and advance the story.

**Parameters:**
- `player_input`: Player's message or action
- `story_state`: Current story state

**Returns:**
- `StoryState`: Updated story state

### `get_state(story_id: str) -> StoryState`
Retrieve current story state.

**Parameters:**
- `story_id`: Story session identifier

**Returns:**
- `StoryState`: Current story state

## Memory System API

### `store(collection: str, content: str, metadata: Dict) -> str`
Store a memory chunk in ChromaDB.

**Parameters:**
- `collection`: Collection name (e.g., "npc_memories")
- `content`: Text content to store
- `metadata`: Metadata dictionary (NPC ID, timestamp, etc.)

**Returns:**
- `str`: Memory chunk ID

### `retrieve(collection: str, query: str, n_results: int = 5) -> List[Memory]`
Retrieve relevant memories using semantic search.

**Parameters:**
- `collection`: Collection name
- `query`: Search query text
- `n_results`: Number of results to return

**Returns:**
- `List[Memory]`: List of relevant memory chunks

### `update(memory_id: str, content: str, metadata: Dict) -> None`
Update an existing memory chunk.

**Parameters:**
- `memory_id`: Memory chunk identifier
- `content`: Updated content
- `metadata`: Updated metadata

### `search(collection: str, filters: Dict, n_results: int = 5) -> List[Memory]`
Search memories using metadata filters.

**Parameters:**
- `collection`: Collection name
- `filters`: Metadata filters
- `n_results`: Number of results to return

**Returns:**
- `List[Memory]`: List of matching memory chunks

## TTS Service API

### `generate_audio(text: str, voice_config: VoiceConfig) -> str`
Generate audio file from text using TTS.

**Parameters:**
- `text`: Text to convert to speech
- `voice_config`: Voice configuration (voice ID, speed, pitch, etc.)

**Returns:**
- `str`: Path to generated audio file

### `get_voice_config(npc_id: str) -> VoiceConfig`
Get voice configuration for an NPC.

**Parameters:**
- `npc_id`: NPC identifier

**Returns:**
- `VoiceConfig`: Voice configuration object

### `stream_audio(text: str, voice_config: VoiceConfig) -> AudioStream`
Stream audio generation (for long dialogs).

**Parameters:**
- `text`: Text to convert to speech
- `voice_config`: Voice configuration

**Returns:**
- `AudioStream`: Audio stream object

## GUI Event System

### Events

- `dialog_started(npc_id: str, dialog_text: str)`: Emitted when an NPC starts speaking
- `dialog_ended(npc_id: str)`: Emitted when an NPC finishes speaking
- `character_speaking(npc_id: str, audio_path: str)`: Emitted during TTS playback

### Callbacks

- `on_player_input(text: str)`: Handle player text input
- `on_story_state_changed(state: StoryState)`: Handle story state updates

---

*This document will be expanded as APIs are implemented.*

