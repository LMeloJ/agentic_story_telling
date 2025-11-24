#!/usr/bin/env python
"""
Script to reset/clear the ChromaDB memory database.

This script allows you to clear all memories from ChromaDB collections,
useful for testing and starting fresh.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.memory.chromadb_memory_system import ChromaDBMemorySystem


def reset_database(collections: list = None, confirm: bool = False):
    """
    Reset ChromaDB database by clearing specified collections.
    
    Args:
        collections: List of collection names to reset. If None, resets all.
        confirm: If True, skip confirmation prompt
    """
    print("Initializing ChromaDB memory system...")
    memory_system = ChromaDBMemorySystem()
    
    # Default to all collections
    if collections is None:
        collections = [
            memory_system.COLLECTION_NPC_MEMORIES,
            memory_system.COLLECTION_WORLD_KNOWLEDGE,
            memory_system.COLLECTION_CHARACTER_PROFILES,
            memory_system.COLLECTION_RELATIONSHIP_GRAPH,
        ]
    
    # Show current state
    print("\nCurrent database state:")
    total_memories = 0
    collection_counts = {}
    
    for collection_name in collections:
        try:
            info = memory_system.get_collection_info(collection_name)
            count = info['count']
            collection_counts[collection_name] = count
            total_memories += count
            print(f"  {collection_name}: {count} memories")
        except Exception as e:
            print(f"  {collection_name}: Error - {e}")
            collection_counts[collection_name] = 0
    
    print(f"\nTotal memories to delete: {total_memories}")
    
    if total_memories == 0:
        print("\n✅ Database is already empty. Nothing to reset.")
        return
    
    # Confirmation
    if not confirm:
        response = input(f"\n⚠️  Are you sure you want to delete all {total_memories} memories? (yes/no): ")
        if response.lower() not in ['yes', 'y']:
            print("❌ Reset cancelled.")
            return
    
    # Reset collections
    print("\n🔄 Resetting collections...")
    deleted_total = 0
    
    for collection_name in collections:
        count = collection_counts.get(collection_name, 0)
        if count == 0:
            print(f"  ⏭️  {collection_name}: Already empty, skipping")
            continue
        
        try:
            # Get all IDs in collection
            coll = memory_system._get_collection(collection_name)
            results = coll.get()
            all_ids = results['ids']
            
            # Delete all memories
            deleted = 0
            for memory_id in all_ids:
                try:
                    memory_system.delete(collection_name, memory_id)
                    deleted += 1
                except Exception as e:
                    print(f"    ⚠️  Warning: Could not delete {memory_id}: {e}")
            
            deleted_total += deleted
            print(f"  ✅ {collection_name}: Deleted {deleted} memories")
            
        except Exception as e:
            print(f"  ❌ {collection_name}: Error - {e}")
    
    # Verify
    print("\n🔍 Verifying reset...")
    remaining_total = 0
    for collection_name in collections:
        try:
            info = memory_system.get_collection_info(collection_name)
            remaining = info['count']
            remaining_total += remaining
            if remaining > 0:
                print(f"  ⚠️  {collection_name}: {remaining} memories still remain")
            else:
                print(f"  ✅ {collection_name}: Empty")
        except Exception as e:
            print(f"  ⚠️  {collection_name}: Could not verify - {e}")
    
    if remaining_total == 0:
        print(f"\n✅ Successfully reset database! Deleted {deleted_total} memories.")
    else:
        print(f"\n⚠️  Reset completed with warnings. {remaining_total} memories still remain.")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Reset ChromaDB memory database"
    )
    parser.add_argument(
        "--collections",
        nargs="+",
        help="Specific collections to reset (default: all collections)",
        choices=[
            "npc_memories",
            "world_knowledge",
            "character_profiles",
            "relationship_graph",
        ]
    )
    parser.add_argument(
        "--yes",
        "-y",
        action="store_true",
        help="Skip confirmation prompt"
    )
    
    args = parser.parse_args()
    
    # Map collection names if provided
    collections = None
    if args.collections:
        memory_system = ChromaDBMemorySystem()
        name_map = {
            "npc_memories": memory_system.COLLECTION_NPC_MEMORIES,
            "world_knowledge": memory_system.COLLECTION_WORLD_KNOWLEDGE,
            "character_profiles": memory_system.COLLECTION_CHARACTER_PROFILES,
            "relationship_graph": memory_system.COLLECTION_RELATIONSHIP_GRAPH,
        }
        collections = [name_map[name] for name in args.collections]
    
    try:
        reset_database(collections=collections, confirm=args.yes)
        print("\n✨ Done!")
    except KeyboardInterrupt:
        print("\n\n❌ Reset cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

