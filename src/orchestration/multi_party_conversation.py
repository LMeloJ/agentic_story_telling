"""
Multi-party conversation management for story orchestration.

Handles turn-taking, conversation flow, and information sharing decisions
for multiple NPCs in a conversation (e.g., around a bonfire).
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field

from src.models.conversation import Message, ConversationContext
from src.models.npc_profile import NPCProfile
from src.agents.npc_agent import NPCAgent
from src.services.gemini_service import GeminiService
from src.services.logging_service import get_logger
from src.orchestration.world_state_utils import serialize_world_state


class ConversationTurn(BaseModel):
    """A single turn in a multi-party conversation."""
    
    turn_id: str = Field(..., description="Unique turn identifier")
    npc_id: str = Field(..., description="NPC speaking in this turn")
    message: str = Field(..., description="Message content")
    timestamp: datetime = Field(default_factory=datetime.now, description="When the turn occurred")
    turn_number: int = Field(..., description="Turn number in the conversation")
    shared_information: Dict[str, Any] = Field(default_factory=dict, description="Information shared in this turn")


class TurnTakingStrategy(str, Enum):
    """Strategies for turn-taking in conversations."""
    ROUND_ROBIN = "round_robin"  # Each NPC speaks in order
    NATURAL = "natural"  # Let NPCs decide when to speak (based on context)
    PRIORITY = "priority"  # NPCs with higher priority speak first
    RANDOM = "random"  # Random order


class MultiPartyConversation:
    """
    Manages multi-party conversations between multiple NPCs.
    
    Handles:
    - Turn-taking
    - Information sharing decisions
    - Conversation flow
    - Context management for each NPC
    """
    
    def __init__(
        self,
        npc_agents: Dict[str, NPCAgent],
        turn_strategy: TurnTakingStrategy = TurnTakingStrategy.NATURAL,
        gemini_service: Optional[GeminiService] = None,
    ):
        """
        Initialize multi-party conversation manager.
        
        Args:
            npc_agents: Dictionary of NPC agents (npc_id -> NPCAgent)
            turn_strategy: Strategy for turn-taking
            gemini_service: Optional Gemini service for information sharing decisions
        """
        self.npc_agents = npc_agents
        self.turn_strategy = turn_strategy
        self.gemini_service = gemini_service
        self.logger = get_logger("multi_party_conversation")
        
        self.conversation_history: List[Message] = []
        self.turns: List[ConversationTurn] = []
        self.current_turn_number = 0
    
    def add_turn(
        self,
        npc_id: str,
        context: ConversationContext,
        world_state: Dict[str, Any],
        expedition_events: Optional[List[Dict[str, Any]]] = None,
    ) -> ConversationTurn:
        """
        Add a turn to the conversation.
        
        Args:
            npc_id: NPC who is speaking
            context: Conversation context for the NPC
            world_state: Current world state
            expedition_events: Optional expedition events that NPC might share
            
        Returns:
            The conversation turn that was added
        """
        if npc_id not in self.npc_agents:
            raise ValueError(f"NPC {npc_id} not found in conversation")
        
        agent = self.npc_agents[npc_id]
        
        # Decide what information to share (if expedition events are available)
        shared_info = {}
        if expedition_events:
            shared_info = self._decide_information_sharing(
                npc_id=npc_id,
                agent=agent,
                expedition_events=expedition_events,
                world_state=world_state,
            )
        
        # Update context with shared information
        enhanced_context = self._enhance_context_with_shared_info(context, shared_info)
        
        # Generate response
        try:
            response = agent.generate_response(enhanced_context)
        except Exception as e:
            self.logger.error(f"Error generating response for {npc_id}: {e}")
            response = "..."
        
        # Create turn
        self.current_turn_number += 1
        turn = ConversationTurn(
            turn_id=f"turn_{self.current_turn_number}_{npc_id}",
            npc_id=npc_id,
            message=response,
            turn_number=self.current_turn_number,
            shared_information=shared_info,
        )
        
        # Add to conversation history
        message = Message(
            role="npc",
            content=response,
            npc_id=npc_id,
            metadata={"turn_number": self.current_turn_number, "shared_info": shared_info},
        )
        self.conversation_history.append(message)
        self.turns.append(turn)
        
        self.logger.info(f"Added turn {self.current_turn_number} from {npc_id}")
        return turn
    
    def get_next_speaker(
        self,
        available_npcs: List[str],
        world_state: Dict[str, Any],
    ) -> Optional[str]:
        """
        Determine the next speaker based on turn-taking strategy.
        
        Args:
            available_npcs: List of NPC IDs available to speak
            world_state: Current world state
            
        Returns:
            NPC ID of next speaker, or None if conversation should end
        """
        if not available_npcs:
            return None
        
        # Ensure fair rotation: no one speaks twice before everyone has spoken once
        if self.turns:
            recent_speakers = [turn.npc_id for turn in self.turns[-len(available_npcs):]]
            # Find NPCs who haven't spoken in recent turns
            not_spoken_recently = [npc for npc in available_npcs if npc not in recent_speakers]
            
            # If there are NPCs who haven't spoken recently, prioritize them
            if not_spoken_recently:
                # Use strategy to pick from those who haven't spoken
                if self.turn_strategy == TurnTakingStrategy.NATURAL:
                    natural_speaker = self._decide_natural_speaker(not_spoken_recently, world_state)
                    # Ensure the natural speaker is in the not_spoken_recently list
                    if natural_speaker in not_spoken_recently:
                        return natural_speaker
                    # Fallback to first available
                    return not_spoken_recently[0]
                else:
                    # Round-robin from those who haven't spoken
                    return not_spoken_recently[0]
            
            # If everyone has spoken recently, prevent immediate repeat
            last_speaker = self.turns[-1].npc_id
            if last_speaker in available_npcs:
                # Get next in rotation, skipping the last speaker
                try:
                    last_index = available_npcs.index(last_speaker)
                    next_index = (last_index + 1) % len(available_npcs)
                    return available_npcs[next_index]
                except ValueError:
                    pass
        
        # First turn or fallback
        if self.turn_strategy == TurnTakingStrategy.ROUND_ROBIN:
            if not self.turns:
                return available_npcs[0]
            last_speaker = self.turns[-1].npc_id
            try:
                last_index = available_npcs.index(last_speaker)
                next_index = (last_index + 1) % len(available_npcs)
                return available_npcs[next_index]
            except ValueError:
                return available_npcs[0]
        
        elif self.turn_strategy == TurnTakingStrategy.NATURAL:
            # Use Gemini to decide who should speak next based on context
            natural_speaker = self._decide_natural_speaker(available_npcs, world_state)
            
            # Prevent immediate repeat
            if self.turns and natural_speaker == self.turns[-1].npc_id:
                # Force next person in round-robin
                last_speaker = self.turns[-1].npc_id
                try:
                    last_index = available_npcs.index(last_speaker)
                    next_index = (last_index + 1) % len(available_npcs)
                    return available_npcs[next_index]
                except ValueError:
                    return available_npcs[0]
            
            return natural_speaker
        
        elif self.turn_strategy == TurnTakingStrategy.PRIORITY:
            # NPCs with higher priority speak first (could be based on role, status, etc.)
            # For now, use round-robin
            if not self.turns:
                return available_npcs[0]
            last_speaker = self.turns[-1].npc_id
            try:
                last_index = available_npcs.index(last_speaker)
                next_index = (last_index + 1) % len(available_npcs)
                return available_npcs[next_index]
            except ValueError:
                return available_npcs[0]
        
        elif self.turn_strategy == TurnTakingStrategy.RANDOM:
            import random
            # Prevent immediate repeat
            if self.turns:
                last_speaker = self.turns[-1].npc_id
                candidates = [npc for npc in available_npcs if npc != last_speaker]
                if candidates:
                    return random.choice(candidates)
            return random.choice(available_npcs)
        
        # Default to round-robin
        return available_npcs[0]
    
    def _decide_natural_speaker(
        self,
        available_npcs: List[str],
        world_state: Dict[str, Any],
    ) -> str:
        """
        Use Gemini to decide who should speak next based on conversation context.
        
        Args:
            available_npcs: List of NPC IDs available to speak
            world_state: Current world state (should be serialized)
            
        Returns:
            NPC ID of next speaker
        """
        if not self.gemini_service:
            # Fallback to round-robin if no Gemini service
            return available_npcs[0] if available_npcs else None
        
        # Serialize world state to ensure datetime objects are handled
        world_state = serialize_world_state(world_state)
        
        # Build prompt to decide next speaker
        recent_turns = self.turns[-3:] if len(self.turns) >= 3 else self.turns
        turn_summary = "\n".join([
            f"- {turn.npc_id}: {turn.message[:100]}..."
            for turn in recent_turns
        ])
        
        prompt = f"""You are managing a conversation between multiple NPCs around a bonfire.

Available NPCs: {', '.join(available_npcs)}
Recent conversation:
{turn_summary if turn_summary else "Conversation just started."}

Who should speak next? Consider:
- Natural conversation flow
- Who has something relevant to say
- Who hasn't spoken recently
- Story context and urgency

Respond with ONLY the NPC ID (one of: {', '.join(available_npcs)})
"""
        
        try:
            response = self.gemini_service.generate_response(
                prompt=prompt,
                temperature=0.3,  # Lower temperature for more deterministic decisions
            )
            
            # Extract NPC ID from response
            response = response.strip()
            for npc_id in available_npcs:
                if npc_id.lower() in response.lower():
                    return npc_id
            
            # Fallback to first available
            return available_npcs[0]
            
        except Exception as e:
            self.logger.warning(f"Error deciding natural speaker: {e}. Using round-robin.")
            return available_npcs[0]
    
    def _decide_information_sharing(
        self,
        npc_id: str,
        agent: NPCAgent,
        expedition_events: List[Dict[str, Any]],
        world_state: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Decide what information an NPC should share about expedition events.
        
        Args:
            npc_id: NPC making the decision
            agent: NPC agent
            expedition_events: List of expedition events the NPC experienced
            world_state: Current world state
            
        Returns:
            Dictionary of information to share (event_id -> shared details)
        """
        if not self.gemini_service or not expedition_events:
            return {}
        
        profile = agent.get_profile()
        
        # Build prompt for information sharing decision
        events_summary = "\n".join([
            f"- {event.get('event_type', 'unknown')}: {event.get('description', '')[:150]}"
            for event in expedition_events
        ])
        
        prompt = f"""You are {profile.name}, a character in a survival story.

Your personality: {profile.personality.traits if profile.personality.traits else 'Not specified'}
Your backstory: {profile.backstory[:200]}...

During a recent expedition, you experienced these events:
{events_summary}

Current situation: The crew is gathered around a bonfire, sharing experiences and planning.

Based on your personality, goals, and the situation, decide:
1. Which events (if any) you want to share with the group
2. How much detail you want to reveal
3. Whether you want to hide or downplay any events

Consider:
- Your personality traits (are you secretive, open, cautious, etc.?)
- The importance of the information to the group's survival
- Your relationships with other crew members
- Whether sharing might help or harm the group

Respond in JSON format:
{{
  "events_to_share": [
    {{
      "event_id": "event_1",
      "share_full_details": true/false,
      "custom_message": "optional custom way to describe it"
    }}
  ],
  "events_to_hide": ["event_id1", "event_id2"],
  "reasoning": "brief explanation of your decision"
}}

If you want to share all events fully, respond with:
{{
  "events_to_share": "all",
  "events_to_hide": [],
  "reasoning": "..."
}}
"""
        
        try:
            response = self.gemini_service.generate_response(
                prompt=prompt,
                temperature=0.7,  # Some creativity in information sharing
            )
            
            # Parse JSON response
            import json
            import re
            
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                decision = json.loads(json_match.group())
            else:
                decision = json.loads(response)
            
            # Build shared information dictionary
            shared_info = {
                "events_to_share": decision.get("events_to_share", []),
                "events_to_hide": decision.get("events_to_hide", []),
                "reasoning": decision.get("reasoning", ""),
            }
            
            return shared_info
            
        except Exception as e:
            self.logger.warning(f"Error deciding information sharing for {npc_id}: {e}")
            # Default: share all events
            return {
                "events_to_share": "all",
                "events_to_hide": [],
                "reasoning": "Default: sharing all information",
            }
    
    def _enhance_context_with_shared_info(
        self,
        context: ConversationContext,
        shared_info: Dict[str, Any],
    ) -> ConversationContext:
        """Enhance conversation context with information the NPC decided to share."""
        if not shared_info:
            return context
        
        # Add shared information to context metadata
        enhanced_metadata = context.metadata.copy()
        enhanced_metadata["shared_information"] = shared_info
        
        # Optionally add a system message about what to share
        if shared_info.get("events_to_share"):
            share_note = f"You have decided to share information about: {shared_info.get('reasoning', 'some events')}"
            enhanced_metadata["sharing_decision"] = share_note
        
        return ConversationContext(
            npc_id=context.npc_id,
            conversation_history=context.conversation_history,
            retrieved_memories=context.retrieved_memories,
            world_state=context.world_state,
            player_input=context.player_input,
            metadata=enhanced_metadata,
        )
    
    def get_conversation_summary(self) -> str:
        """Get a summary of the conversation."""
        if not self.turns:
            return "No conversation yet."
        
        summary_parts = [f"Conversation with {len(self.turns)} turns:"]
        for turn in self.turns:
            summary_parts.append(f"  {turn.npc_id}: {turn.message[:100]}...")
        
        return "\n".join(summary_parts)

