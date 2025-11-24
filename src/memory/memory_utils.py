"""
Utility functions for memory management.
"""

import re
from typing import List, Dict, Any, Optional
from datetime import datetime

from src.models.memory import MemoryChunk, MemoryMetadata
from src.memory.memory_types import Memory


def chunk_text(text: str, chunk_size: int = 500, chunk_overlap: int = 50) -> List[str]:
    """
    Split text into chunks with overlap.
    
    Args:
        text: Text to chunk
        chunk_size: Maximum chunk size in characters
        chunk_overlap: Overlap between chunks
    
    Returns:
        List of text chunks
    """
    if len(text) <= chunk_size:
        return [text]
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        
        # Try to break at sentence boundary
        if end < len(text):
            # Look for sentence endings
            sentence_endings = ['. ', '! ', '? ', '\n\n', '\n']
            for ending in sentence_endings:
                last_ending = text.rfind(ending, start, end)
                if last_ending != -1:
                    end = last_ending + len(ending)
                    break
        
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        
        # Move start position with overlap
        start = max(end - chunk_overlap, start + 1)
        
        # Prevent infinite loop
        if start >= len(text):
            break
    
    return chunks


def calculate_importance_score(
    content: str,
    memory_type: str = "conversation",
    tags: Optional[List[str]] = None,
    has_emotion: bool = False,
    relationship_change: bool = False,
) -> float:
    """
    Calculate importance score for a memory chunk.
    
    Args:
        content: Memory content
        memory_type: Type of memory (conversation, event, relationship, etc.)
        tags: Optional tags
        has_emotion: Whether memory contains emotional content
        relationship_change: Whether memory indicates relationship change
    
    Returns:
        Importance score between 0.0 and 1.0
    """
    base_score = 0.5
    
    # Memory type weights
    type_weights = {
        "relationship": 0.9,
        "event": 0.8,
        "goal": 0.7,
        "conversation": 0.5,
        "fact": 0.3,
    }
    base_score = type_weights.get(memory_type, base_score)
    
    # Emotional content increases importance
    if has_emotion:
        base_score += 0.2
    
    # Relationship changes are very important
    if relationship_change:
        base_score += 0.3
    
    # Check for important keywords
    important_keywords = [
        "promise", "secret", "plan", "betrayal", "love", "hate",
        "important", "critical", "remember", "never forget",
    ]
    content_lower = content.lower()
    keyword_count = sum(1 for keyword in important_keywords if keyword in content_lower)
    base_score += min(keyword_count * 0.05, 0.15)
    
    # Length penalty (very short or very long memories might be less important)
    length_factor = len(content)
    if length_factor < 50:
        base_score -= 0.1  # Too short might be less important
    elif length_factor > 1000:
        base_score -= 0.05  # Too long might be less focused
    
    # Normalize to [0.0, 1.0]
    base_score = max(0.0, min(1.0, base_score))
    
    return base_score


def consolidate_memories(memories: List[Memory], similarity_threshold: float = 0.8) -> List[Memory]:
    """
    Consolidate similar memories to reduce redundancy.
    
    Args:
        memories: List of memories to consolidate
        similarity_threshold: Similarity threshold for consolidation (0.0 to 1.0)
    
    Returns:
        Consolidated list of memories
    """
    if not memories:
        return []
    
    # Sort by score (keep most important)
    sorted_memories = sorted(memories, key=lambda m: m.score, reverse=True)
    consolidated = []
    used_indices = set()
    
    for i, memory in enumerate(sorted_memories):
        if i in used_indices:
            continue
        
        # Find similar memories
        similar_memories = [memory]
        for j, other_memory in enumerate(sorted_memories[i+1:], start=i+1):
            if j in used_indices:
                continue
            
            # Calculate similarity (simple content similarity)
            similarity = _calculate_similarity(memory.content, other_memory.content)
            
            if similarity >= similarity_threshold:
                similar_memories.append(other_memory)
                used_indices.add(j)
        
        # Merge similar memories
        if len(similar_memories) > 1:
            # Combine content and metadata
            combined_content = " | ".join([m.content for m in similar_memories])
            max_score = max(m.score for m in similar_memories)
            
            # Merge metadata
            merged_metadata = memory.metadata.copy()
            for other_memory in similar_memories[1:]:
                # Merge tags
                if "tags" in other_memory.metadata:
                    tags_str = other_memory.metadata.get("tags", "")
                    if tags_str:
                        existing_tags = merged_metadata.get("tags", "")
                        if existing_tags:
                            merged_metadata["tags"] = f"{existing_tags},{tags_str}"
                        else:
                            merged_metadata["tags"] = tags_str
            
            merged_memory = Memory(
                chunk_id=memory.chunk_id,
                content=combined_content[:500],  # Limit length
                metadata=merged_metadata,
                score=max_score,
                timestamp=memory.timestamp,
            )
            consolidated.append(merged_memory)
        else:
            consolidated.append(memory)
        
        used_indices.add(i)
    
    return consolidated


def _calculate_similarity(text1: str, text2: str) -> float:
    """
    Calculate simple similarity between two texts.
    
    Uses word overlap as a simple similarity metric.
    For production, use proper embeddings-based similarity.
    
    Args:
        text1: First text
        text2: Second text
    
    Returns:
        Similarity score between 0.0 and 1.0
    """
    # Tokenize (simple word split)
    words1 = set(re.findall(r'\w+', text1.lower()))
    words2 = set(re.findall(r'\w+', text2.lower()))
    
    if not words1 or not words2:
        return 0.0
    
    # Calculate Jaccard similarity
    intersection = len(words1.intersection(words2))
    union = len(words1.union(words2))
    
    if union == 0:
        return 0.0
    
    return intersection / union


def build_context_from_memories(
    memories: List[Memory],
    max_tokens: int = 4000,
    chars_per_token: float = 4.0,
) -> str:
    """
    Build context string from retrieved memories.
    
    Args:
        memories: List of memories to include
        max_tokens: Maximum token budget
        chars_per_token: Approximate characters per token
    
    Returns:
        Formatted context string
    """
    max_chars = int(max_tokens * chars_per_token)
    context_parts = []
    current_size = 0
    
    # Sort by relevance (already sorted by score)
    for memory in memories:
        # Format memory
        timestamp_str = memory.timestamp.strftime("%Y-%m-%d %H:%M") if memory.timestamp else "Unknown"
        npc_id = memory.metadata.get("npc_id", "Unknown")
        
        memory_text = f"[{timestamp_str}] {npc_id}: {memory.content}"
        memory_size = len(memory_text)
        
        if current_size + memory_size <= max_chars:
            context_parts.append(memory_text)
            current_size += memory_size
        else:
            # Try to fit a truncated version
            remaining = max_chars - current_size - 50  # Reserve space for "..."
            if remaining > 50:
                truncated = memory.content[:remaining] + "..."
                context_parts.append(f"[{timestamp_str}] {npc_id}: {truncated}")
            break
    
    return "\n\n".join(context_parts)


def filter_memories_by_importance(
    memories: List[Memory],
    min_importance: float = 0.3,
) -> List[Memory]:
    """
    Filter memories by importance score.
    
    Args:
        memories: List of memories
        min_importance: Minimum importance score (0.0 to 1.0)
    
    Returns:
        Filtered list of memories
    """
    filtered = []
    for memory in memories:
        importance = float(memory.metadata.get("importance_score", "0.5"))
        if importance >= min_importance:
            filtered.append(memory)
    
    return filtered


def apply_memory_decay(memories: List[Memory], decay_hours: float = 168.0) -> List[Memory]:
    """
    Apply decay to older memories to reduce their relevance.
    
    Args:
        memories: List of memories
        decay_hours: Hours after which memories start decaying significantly (default: 7 days)
    
    Returns:
        List of memories with decayed scores
    """
    now = datetime.now()
    
    for memory in memories:
        if memory.timestamp:
            age_hours = (now - memory.timestamp).total_seconds() / 3600
            
            if age_hours > decay_hours:
                # Apply exponential decay
                import math
                decay_factor = math.exp(-(age_hours - decay_hours) / decay_hours)
                memory.score = memory.score * decay_factor
    
    # Re-sort by decayed score
    memories.sort(key=lambda m: m.score, reverse=True)
    
    return memories

