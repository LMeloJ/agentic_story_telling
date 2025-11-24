#!/usr/bin/env python
"""
Script to load sample memories into ChromaDB for testing and visualization.

This script creates sample NPC memories with different types, importance scores,
and NPCs to help test the memory system and visualization notebook.
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import List

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.memory.chromadb_memory_system import ChromaDBMemorySystem
from src.models.memory import MemoryMetadata


def create_sample_memories() -> List[dict]:
    """Create a list of sample memories with diverse characteristics."""
    
    # Get current time
    now = datetime.now()
    
    sample_memories = [
        # NPC 1 - Recent important memories
        {
            "npc_id": "alice",
            "conversation_id": "conv_alice_1",
            "content": "Player asked about the ancient ruins and the lost treasure. I told them about the legend of the Golden Chalice hidden deep within the catacombs.",
            "importance_score": 0.9,
            "memory_type": "conversation",
            "tags": ["quest", "location", "legend"],
            "timestamp": now - timedelta(hours=2),
        },
        {
            "npc_id": "alice",
            "conversation_id": "conv_alice_1",
            "content": "Player mentioned they're looking for a map to the catacombs. I suggested they talk to the old librarian in the town square.",
            "importance_score": 0.7,
            "memory_type": "conversation",
            "tags": ["quest", "npc_reference"],
            "timestamp": now - timedelta(hours=1, minutes=30),
        },
        {
            "npc_id": "alice",
            "conversation_id": "conv_alice_2",
            "content": "Player returned and showed me the map. I warned them about the guardian spirits that protect the catacombs. They must be prepared.",
            "importance_score": 0.85,
            "memory_type": "conversation",
            "tags": ["quest", "warning", "lore"],
            "timestamp": now - timedelta(minutes=30),
        },
        
        # NPC 2 - Relationship memories
        {
            "npc_id": "bob",
            "conversation_id": "conv_bob_1",
            "content": "Player helped me fix my broken cart. I'm very grateful and will remember this kindness. They seem trustworthy.",
            "importance_score": 0.8,
            "memory_type": "relationship",
            "tags": ["relationship", "trust", "kindness"],
            "timestamp": now - timedelta(days=1),
        },
        {
            "npc_id": "bob",
            "conversation_id": "conv_bob_2",
            "content": "Player asked about trading routes. I shared some valuable information about the northern trade path that's less dangerous.",
            "importance_score": 0.6,
            "memory_type": "conversation",
            "tags": ["information", "trading"],
            "timestamp": now - timedelta(hours=6),
        },
        {
            "npc_id": "bob",
            "conversation_id": "conv_bob_3",
            "content": "Player mentioned they're heading north. I reminded them about the safer trade route and offered to provide supplies if needed.",
            "importance_score": 0.75,
            "memory_type": "conversation",
            "tags": ["helpful", "relationship"],
            "timestamp": now - timedelta(hours=3),
        },
        
        # NPC 1 - Old memories (lower importance)
        {
            "npc_id": "alice",
            "conversation_id": "conv_alice_old_1",
            "content": "Player asked about the weather. I mentioned it's been unusually warm this season.",
            "importance_score": 0.3,
            "memory_type": "conversation",
            "tags": ["small_talk"],
            "timestamp": now - timedelta(days=5),
        },
        {
            "npc_id": "alice",
            "conversation_id": "conv_alice_old_2",
            "content": "Player asked for directions to the marketplace. I gave them simple directions.",
            "importance_score": 0.2,
            "memory_type": "conversation",
            "tags": ["directions"],
            "timestamp": now - timedelta(days=7),
        },
        
        # NPC 2 - Event memories
        {
            "npc_id": "bob",
            "conversation_id": "event_bob_1",
            "content": "The market festival happened last week. Player participated in the trading competition and did well.",
            "importance_score": 0.65,
            "memory_type": "event",
            "tags": ["festival", "achievement"],
            "timestamp": now - timedelta(days=3),
        },
        
        # NPC 3 - Character with different memory patterns
        {
            "npc_id": "charlie",
            "conversation_id": "conv_charlie_1",
            "content": "Player asked me about my past. I shared a secret - I used to be a royal guard before the kingdom fell. This is very personal.",
            "importance_score": 0.95,
            "memory_type": "relationship",
            "tags": ["secret", "personal", "backstory"],
            "timestamp": now - timedelta(hours=12),
        },
        {
            "npc_id": "charlie",
            "conversation_id": "conv_charlie_2",
            "content": "Player mentioned they're also interested in the kingdom's history. I promised to share more stories next time we meet.",
            "importance_score": 0.7,
            "memory_type": "conversation",
            "tags": ["promise", "future"],
            "timestamp": now - timedelta(hours=8),
        },
        {
            "npc_id": "charlie",
            "conversation_id": "conv_charlie_3",
            "content": "Player asked if I know anything about the king's sword. I hesitated but confirmed I might know its location. Very dangerous topic.",
            "importance_score": 0.9,
            "memory_type": "conversation",
            "tags": ["danger", "secret", "artifact"],
            "timestamp": now - timedelta(hours=4),
        },
        
        # Mixed NPC memories - relationships between NPCs
        {
            "npc_id": "alice",
            "conversation_id": "world_1",
            "content": "I mentioned to the player that Bob and I have been friends since childhood. We grew up in the same village.",
            "importance_score": 0.5,
            "memory_type": "relationship",
            "tags": ["relationship", "npc_relationship"],
            "timestamp": now - timedelta(days=2),
        },
        {
            "npc_id": "bob",
            "conversation_id": "world_1",
            "content": "Player asked about my relationship with Alice. I confirmed we've been friends for years and trust each other completely.",
            "importance_score": 0.5,
            "memory_type": "relationship",
            "tags": ["relationship", "npc_relationship"],
            "timestamp": now - timedelta(days=2),
        },
        
        # More diverse content for better visualization
        {
            "npc_id": "alice",
            "conversation_id": "conv_alice_3",
            "content": "Player discovered a hidden passage in the library. I'm very interested in what they might find there. This could be important for my research.",
            "importance_score": 0.8,
            "memory_type": "conversation",
            "tags": ["discovery", "research", "location"],
            "timestamp": now - timedelta(minutes=15),
        },
        {
            "npc_id": "bob",
            "conversation_id": "conv_bob_4",
            "content": "I saw player talking with Charlie. That's unusual - Charlie rarely talks to anyone. I wonder what they discussed.",
            "importance_score": 0.6,
            "memory_type": "conversation",
            "tags": ["observation", "curiosity"],
            "timestamp": now - timedelta(hours=2),
        },
        {
            "npc_id": "charlie",
            "conversation_id": "conv_charlie_4",
            "content": "Player helped me recover an old artifact from my past. I'm eternally grateful. This changes everything.",
            "importance_score": 1.0,
            "memory_type": "relationship",
            "tags": ["gratitude", "artifact", "life_changing"],
            "timestamp": now - timedelta(minutes=5),
        },
    ]
    
    return sample_memories


def load_sample_memories(clear_existing: bool = False):
    """
    Load sample memories into ChromaDB.
    
    Args:
        clear_existing: If True, clear existing memories before loading
    """
    print("Initializing ChromaDB memory system...")
    memory_system = ChromaDBMemorySystem()
    
    # Get collection info
    collection = memory_system.COLLECTION_NPC_MEMORIES
    info = memory_system.get_collection_info(collection)
    existing_count = info['count']
    
    print(f"\nCurrent state:")
    print(f"  Collection: {collection}")
    print(f"  Existing memories: {existing_count}")
    
    if clear_existing and existing_count > 0:
        print(f"\n⚠️  Clearing {existing_count} existing memories...")
        # Get all IDs and delete them
        coll = memory_system._get_collection(collection)
        all_ids = coll.get()['ids']
        for memory_id in all_ids:
            memory_system.delete(collection, memory_id)
        print(f"  ✓ Cleared all existing memories")
    
    # Load sample memories
    sample_memories = create_sample_memories()
    print(f"\n📝 Loading {len(sample_memories)} sample memories...")
    
    loaded_count = 0
    for i, memory_data in enumerate(sample_memories, 1):
        metadata = MemoryMetadata(
            npc_id=memory_data["npc_id"],
            conversation_id=memory_data["conversation_id"],
            timestamp=memory_data["timestamp"],
            importance_score=memory_data["importance_score"],
            memory_type=memory_data["memory_type"],
            tags=memory_data["tags"],
        )
        
        chunk_id = memory_system.store_conversation_chunk(
            npc_id=memory_data["npc_id"],
            conversation_id=memory_data["conversation_id"],
            content=memory_data["content"],
            importance_score=memory_data["importance_score"],
            tags=memory_data["tags"],
        )
        
        loaded_count += 1
        print(f"  [{i}/{len(sample_memories)}] Loaded memory for {memory_data['npc_id']} "
              f"(importance: {memory_data['importance_score']:.2f})")
    
    # Verify
    info = memory_system.get_collection_info(collection)
    final_count = info['count']
    
    print(f"\n✅ Successfully loaded {loaded_count} sample memories!")
    print(f"\nFinal state:")
    print(f"  Total memories in collection: {final_count}")
    
    # Show breakdown by NPC
    print(f"\nBreakdown by NPC:")
    for npc_id in ["alice", "bob", "charlie"]:
        try:
            memories = memory_system.retrieve_npc_memories(
                npc_id=npc_id,
                query="test",
                n_results=100,
            )
            print(f"  {npc_id}: {len(memories)} memories")
        except Exception:
            print(f"  {npc_id}: 0 memories")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Load sample memories into ChromaDB for testing"
    )
    parser.add_argument(
        "--clear",
        action="store_true",
        help="Clear existing memories before loading new ones"
    )
    
    args = parser.parse_args()
    
    try:
        load_sample_memories(clear_existing=args.clear)
        print("\n✨ Done! You can now use the visualization notebook.")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

