"""
LangGraph-based NPC Agent implementation.

Implements the NPCAgent interface using LangGraph for orchestration,
with nodes for memory retrieval, context building, response generation,
and memory storage.
"""

import json
from typing import TypedDict, Optional, List, Dict, Any, Annotated
from datetime import datetime

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from src.agents.npc_agent import NPCAgent
from src.models.npc_profile import NPCProfile
from src.models.conversation import ConversationContext, Message, Conversation
from src.models.memory import MemoryMetadata
from src.memory.memory_system import MemorySystem
from src.memory.chromadb_memory_system import ChromaDBMemorySystem
from src.memory.memory_types import Memory
from src.services.gemini_service import GeminiService
from src.services.logging_service import get_logger
from src.memory.memory_utils import build_context_from_memories


class NPCState(TypedDict):
    """State for NPC agent graph."""
    
    npc_id: str
    npc_profile: NPCProfile
    current_context: str
    conversation_history: Annotated[List[Message], "append"]
    retrieved_memories: List[Memory]
    world_state: Dict[str, Any]
    player_input: Optional[str]
    response: Optional[str]
    error: Optional[str]


class LangGraphAgent(NPCAgent):
    """
    LangGraph-based NPC Agent implementation.
    
    Uses LangGraph to orchestrate the conversation flow:
    1. Retrieve relevant memories
    2. Build context from memories and history
    3. Generate response using Gemini
    4. Store new conversation in memory
    5. Update world state (if needed)
    """
    
    def __init__(
        self,
        memory_system: MemorySystem,
        gemini_service: GeminiService,
        max_context_tokens: int = 2000,
    ):
        """
        Initialize LangGraph agent.
        
        Args:
            memory_system: Memory system for storing/retrieving memories
            gemini_service: Gemini service for response generation
            max_context_tokens: Maximum tokens for context window
        """
        self.memory_system = memory_system
        self.gemini_service = gemini_service
        self.max_context_tokens = max_context_tokens
        self.logger = get_logger("langgraph_agent")
        
        self._npc_id: Optional[str] = None
        self._profile: Optional[NPCProfile] = None
        
        # Build LangGraph workflow
        self.graph = self._build_graph()
        
        # Initialize checkpoint memory (in-memory for now, can be upgraded to persistent)
        self.checkpointer = MemorySaver()
        self.app = self.graph.compile(checkpointer=self.checkpointer)
        
        self.logger.info("LangGraph agent initialized")
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow."""
        workflow = StateGraph(NPCState)
        
        # Add nodes
        workflow.add_node("retrieve_memory", self._retrieve_memory_node)
        workflow.add_node("build_context", self._build_context_node)
        workflow.add_node("generate_response", self._generate_response_node)
        workflow.add_node("store_memory", self._store_memory_node)
        workflow.add_node("handle_error", self._handle_error_node)
        
        # Define edges
        workflow.set_entry_point("retrieve_memory")
        workflow.add_edge("retrieve_memory", "build_context")
        workflow.add_edge("build_context", "generate_response")
        workflow.add_edge("generate_response", "store_memory")
        workflow.add_edge("store_memory", END)
        
        # Error handling
        workflow.add_edge("handle_error", END)
        
        return workflow
    
    def initialize(self, npc_id: str, profile: NPCProfile) -> None:
        """Initialize the agent with an NPC profile."""
        self._npc_id = npc_id
        self._profile = profile
        
        # Store profile embedding in ChromaDB
        self._store_profile_embedding(profile)
        
        self.logger.info(f"Initialized agent for NPC: {npc_id} ({profile.name})")
    
    def _store_profile_embedding(self, profile: NPCProfile) -> None:
        """Store NPC profile as embedding in ChromaDB."""
        try:
            # Create profile text representation for embedding
            profile_text = self._profile_to_text(profile)
            
            # Store in character_profiles collection
            metadata = MemoryMetadata(
                npc_id=profile.npc_id,
                memory_type="character_profile",
                importance_score=1.0,  # Profiles are always important
                conversation_id=None,
                additional_metadata={
                    "name": profile.name,
                    "profile_version": "1.0",
                    "stored_at": datetime.now().isoformat(),
                }
            )
            
            # Get collection name
            collection_name = (
                ChromaDBMemorySystem.COLLECTION_CHARACTER_PROFILES
                if isinstance(self.memory_system, ChromaDBMemorySystem)
                else "character_profiles"
            )
            
            # Check if profile already exists (update if it does)
            existing = self.memory_system.retrieve(
                collection=collection_name,
                query=profile.npc_id,
                n_results=1,
                filter_metadata={"npc_id": profile.npc_id},
            )
            
            if existing:
                # Update existing profile
                chunk_id = existing[0].chunk_id
                self.memory_system.update(
                    collection=collection_name,
                    chunk_id=chunk_id,
                    content=profile_text,
                    metadata=metadata,
                )
                self.logger.info(f"Updated profile embedding for NPC: {profile.npc_id}")
            else:
                # Store new profile
                self.memory_system.store(
                    collection=collection_name,
                    content=profile_text,
                    metadata=metadata,
                )
                self.logger.info(f"Stored profile embedding for NPC: {profile.npc_id}")
        except Exception as e:
            self.logger.error(f"Error storing profile embedding: {e}")
            # Don't fail initialization if profile storage fails
    
    def _profile_to_text(self, profile: NPCProfile) -> str:
        """Convert NPC profile to text representation for embedding."""
        parts = [
            f"Name: {profile.name}",
            f"NPC ID: {profile.npc_id}",
            f"Backstory: {profile.backstory}",
        ]
        
        if profile.personality.traits:
            parts.append(f"Personality Traits: {', '.join(profile.personality.traits)}")
        
        if profile.personality.big_five:
            parts.append(f"Big Five: {json.dumps(profile.personality.big_five)}")
        
        if profile.goals:
            parts.append(f"Goals: {', '.join(profile.goals)}")
        
        if profile.quirks:
            parts.append(f"Quirks: {', '.join(profile.quirks)}")
        
        if profile.speech_patterns:
            parts.append(f"Speech Tone: {profile.speech_patterns.tone}")
            parts.append(f"Formality: {profile.speech_patterns.formality}")
            if profile.speech_patterns.vocabulary:
                parts.append(f"Vocabulary: {', '.join(profile.speech_patterns.vocabulary)}")
        
        if profile.relationships:
            parts.append(f"Relationships: {json.dumps(profile.relationships)}")
        
        return "\n".join(parts)
    
    def generate_response(self, context: ConversationContext) -> str:
        """
        Generate a response using LangGraph workflow.
        
        Args:
            context: Conversation context with history, memories, world state
        
        Returns:
            Generated response text
        """
        if not self._npc_id or not self._profile:
            raise ValueError("Agent not initialized. Call initialize() first.")
        
        if context.npc_id != self._npc_id:
            raise ValueError(f"Context NPC ID ({context.npc_id}) doesn't match agent NPC ID ({self._npc_id})")
        
        # Prepare initial state
        initial_state: NPCState = {
            "npc_id": self._npc_id,
            "npc_profile": self._profile,
            "current_context": "",
            "conversation_history": context.conversation_history.copy(),
            "retrieved_memories": [],
            "world_state": context.world_state.copy(),
            "player_input": context.player_input,
            "response": None,
            "error": None,
        }
        
        # Run graph
        try:
            config = {"configurable": {"thread_id": f"npc_{self._npc_id}_{datetime.now().timestamp()}"}}
            final_state = self.app.invoke(initial_state, config=config)
            
            if final_state.get("error"):
                raise Exception(f"Graph execution error: {final_state['error']}")
            
            response = final_state.get("response")
            if not response:
                raise Exception("No response generated by graph")
            
            return response
        except Exception as e:
            self.logger.error(f"Error generating response: {e}")
            raise
    
    def update_memory(self, conversation: Conversation) -> None:
        """
        Store a conversation in memory.
        
        This is called automatically by the graph's store_memory node,
        but can also be called manually.
        """
        if not self._npc_id:
            raise ValueError("Agent not initialized")
        
        # Store conversation chunks
        for message in conversation.messages:
            if message.role == "npc" or message.role == "user":
                metadata = MemoryMetadata(
                    npc_id=self._npc_id,
                    memory_type="conversation",
                    importance_score=conversation.importance_score,
                    conversation_id=conversation.conversation_id,
                    additional_metadata={
                        "role": message.role,
                        "timestamp": message.timestamp.isoformat(),
                    }
                )
                
                # Get collection name
                collection_name = (
                    ChromaDBMemorySystem.COLLECTION_NPC_MEMORIES
                    if isinstance(self.memory_system, ChromaDBMemorySystem)
                    else "npc_memories"
                )
                
                self.memory_system.store(
                    collection=collection_name,
                    content=message.content,
                    metadata=metadata,
                )
        
        self.logger.info(f"Stored conversation {conversation.conversation_id} in memory")
    
    def get_npc_id(self) -> str:
        """Get the NPC ID."""
        if not self._npc_id:
            raise ValueError("Agent not initialized")
        return self._npc_id
    
    def get_profile(self) -> NPCProfile:
        """Get the NPC profile."""
        if not self._profile:
            raise ValueError("Agent not initialized")
        return self._profile
    
    # Graph node implementations
    
    def _retrieve_memory_node(self, state: NPCState) -> NPCState:
        """Retrieve relevant memories from ChromaDB."""
        try:
            # Build query from player input and recent conversation
            query_parts = []
            if state.get("player_input"):
                query_parts.append(state["player_input"])
            
            # Add recent conversation context
            recent_messages = state["conversation_history"][-3:]  # Last 3 messages
            for msg in recent_messages:
                query_parts.append(msg.content)
            
            query = " ".join(query_parts) if query_parts else "general conversation"
            
            # Get collection name
            collection_name = (
                ChromaDBMemorySystem.COLLECTION_NPC_MEMORIES
                if isinstance(self.memory_system, ChromaDBMemorySystem)
                else "npc_memories"
            )
            
            # Retrieve memories - use npc_id parameter if available, otherwise use filter_metadata
            if isinstance(self.memory_system, ChromaDBMemorySystem):
                memories = self.memory_system.retrieve(
                    collection=collection_name,
                    query=query,
                    n_results=5,
                    npc_id=state["npc_id"],
                )
            else:
                memories = self.memory_system.retrieve(
                    collection=collection_name,
                    query=query,
                    n_results=5,
                    filter_metadata={"npc_id": state["npc_id"]},
                )
            
            state["retrieved_memories"] = memories
            self.logger.debug(f"Retrieved {len(memories)} memories for NPC {state['npc_id']}")
            
        except Exception as e:
            self.logger.error(f"Error retrieving memories: {e}")
            state["error"] = f"Memory retrieval error: {str(e)}"
            state["retrieved_memories"] = []
        
        return state
    
    def _build_context_node(self, state: NPCState) -> NPCState:
        """Build context from memories and conversation history."""
        try:
            # Build context from retrieved memories
            context_parts = []
            
            # Add profile information
            profile_context = self._build_profile_context(state["npc_profile"])
            context_parts.append(profile_context)
            
            # Add retrieved memories
            if state["retrieved_memories"]:
                memory_context = build_context_from_memories(
                    state["retrieved_memories"],
                    max_tokens=self.max_context_tokens // 2,  # Reserve half for conversation
                )
                context_parts.append(f"\nRelevant Past Conversations:\n{memory_context}")
            
            # Add recent conversation history
            if state["conversation_history"]:
                recent_context = self._format_conversation_history(
                    state["conversation_history"][-10:]  # Last 10 messages
                )
                context_parts.append(f"\nRecent Conversation:\n{recent_context}")
            
            # Add world state if available
            if state.get("world_state"):
                world_context = self._format_world_state(state["world_state"])
                context_parts.append(f"\nCurrent World State:\n{world_context}")
            
            state["current_context"] = "\n".join(context_parts)
            
        except Exception as e:
            self.logger.error(f"Error building context: {e}")
            state["error"] = f"Context building error: {str(e)}"
        
        return state
    
    def _generate_response_node(self, state: NPCState) -> NPCState:
        """Generate response using Gemini API."""
        try:
            if state.get("error"):
                # Skip generation if there's an error
                state["response"] = "I'm having trouble processing that right now."
                return state
            
            # Build system prompt from profile
            system_prompt = self._build_system_prompt(state["npc_profile"])
            
            # Build user prompt with context
            user_prompt = self._build_user_prompt(
                state["current_context"],
                state.get("player_input"),
            )
            
            # Generate response
            response = self.gemini_service.generate_response(
                prompt=user_prompt,
                system_instruction=system_prompt,
                temperature=0.8,  # Slightly creative for character personality
            )
            
            state["response"] = response
            self.logger.debug(f"Generated response for NPC {state['npc_id']}: {response[:50]}...")
            
        except Exception as e:
            self.logger.error(f"Error generating response: {e}")
            state["error"] = f"Response generation error: {str(e)}"
            state["response"] = "I'm having trouble responding right now. Could you try again?"
        
        return state
    
    def _store_memory_node(self, state: NPCState) -> NPCState:
        """Store the conversation in memory."""
        try:
            if not state.get("response"):
                return state
            
            # Create conversation object
            messages = state["conversation_history"].copy()
            
            # Add player input if available
            if state.get("player_input"):
                messages.append(Message(
                    role="user",
                    content=state["player_input"],
                    timestamp=datetime.now(),
                ))
            
            # Add NPC response
            messages.append(Message(
                role="npc",
                content=state["response"],
                timestamp=datetime.now(),
                npc_id=state["npc_id"],
            ))
            
            conversation = Conversation(
                conversation_id=f"conv_{datetime.now().timestamp()}",
                npc_id=state["npc_id"],
                messages=messages,
                importance_score=0.5,  # Default importance
            )
            
            # Store in memory
            self.update_memory(conversation)
            
        except Exception as e:
            self.logger.error(f"Error storing memory: {e}")
            # Don't fail the workflow if memory storage fails
        
        return state
    
    def _handle_error_node(self, state: NPCState) -> NPCState:
        """Handle errors in the workflow."""
        error = state.get("error", "Unknown error")
        self.logger.error(f"Graph error: {error}")
        state["response"] = "I encountered an error. Please try again."
        return state
    
    # Helper methods for context building
    
    def _build_profile_context(self, profile: NPCProfile) -> str:
        """Build context string from NPC profile."""
        parts = [
            f"You are {profile.name}.",
            f"Backstory: {profile.backstory}",
        ]
        
        if profile.personality.traits:
            parts.append(f"Personality: {', '.join(profile.personality.traits)}")
        
        if profile.goals:
            parts.append(f"Current Goals: {', '.join(profile.goals)}")
        
        if profile.quirks:
            parts.append(f"Quirks: {', '.join(profile.quirks)}")
        
        if profile.speech_patterns:
            parts.append(f"Speech Style: {profile.speech_patterns.tone}, {profile.speech_patterns.formality}")
            if profile.speech_patterns.vocabulary:
                parts.append(f"Characteristic words: {', '.join(profile.speech_patterns.vocabulary)}")
        
        return "\n".join(parts)
    
    def _format_conversation_history(self, messages: List[Message]) -> str:
        """Format conversation history for context."""
        lines = []
        for msg in messages:
            speaker = msg.npc_id or msg.role
            lines.append(f"{speaker}: {msg.content}")
        return "\n".join(lines)
    
    def _serialize_datetime_objects(self, obj: Any) -> Any:
        """Recursively serialize datetime objects to ISO format strings."""
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, dict):
            return {key: self._serialize_datetime_objects(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._serialize_datetime_objects(item) for item in obj]
        elif isinstance(obj, tuple):
            return tuple(self._serialize_datetime_objects(item) for item in obj)
        else:
            return obj
    
    def _format_world_state(self, world_state: Dict[str, Any]) -> str:
        """Format world state for context."""
        # Serialize datetime objects before JSON encoding
        serialized_state = self._serialize_datetime_objects(world_state)
        return json.dumps(serialized_state, indent=2, default=str)
    
    def _build_system_prompt(self, profile: NPCProfile) -> str:
        """Build system prompt for Gemini API."""
        return f"""You are {profile.name}, a character in an interactive story.

{self._build_profile_context(profile)}

IMPORTANT GUIDELINES:
- Stay in character at all times
- Use your personality traits, quirks, and speech patterns
- Remember past conversations and events
- Respond naturally and conversationally
- Keep responses concise (1-3 sentences typically)
- Show personality through word choice and tone
- If you remember something from the past, reference it naturally"""
    
    def _build_user_prompt(self, context: str, player_input: Optional[str]) -> str:
        """Build user prompt with context."""
        parts = [context]
        
        if player_input:
            parts.append(f"\nPlayer says: {player_input}")
            parts.append("\nHow do you respond?")
        else:
            parts.append("\nWhat do you say?")
        
        return "\n".join(parts)

