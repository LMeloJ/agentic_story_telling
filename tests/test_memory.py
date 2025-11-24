"""
Tests for memory system components.
"""

import pytest
import tempfile
from pathlib import Path
from datetime import datetime, timedelta

from src.memory.chromadb_memory_system import ChromaDBMemorySystem
from src.memory.memory_types import Memory
from src.memory.memory_utils import (
    chunk_text,
    calculate_importance_score,
    consolidate_memories,
    build_context_from_memories,
    filter_memories_by_importance,
    apply_memory_decay,
)
from src.models.memory import MemoryMetadata


class TestChromaDBMemorySystem:
    """Tests for ChromaDBMemorySystem."""
    
    def test_initialization(self, mock_env_vars, temp_dir):
        """Test ChromaDBMemorySystem initialization."""
        memory_system = ChromaDBMemorySystem()
        
        assert memory_system is not None
        assert memory_system.client is not None
        assert len(memory_system.collections) == 4
        assert ChromaDBMemorySystem.COLLECTION_NPC_MEMORIES in memory_system.collections
        assert ChromaDBMemorySystem.COLLECTION_WORLD_KNOWLEDGE in memory_system.collections
        assert ChromaDBMemorySystem.COLLECTION_CHARACTER_PROFILES in memory_system.collections
        assert ChromaDBMemorySystem.COLLECTION_RELATIONSHIP_GRAPH in memory_system.collections
    
    def test_store_and_retrieve(self, mock_env_vars, temp_dir):
        """Test storing and retrieving memories."""
        memory_system = ChromaDBMemorySystem()
        
        metadata = MemoryMetadata(
            npc_id="test_npc_1",
            conversation_id="conv_1",
            timestamp=datetime.now(),
            importance_score=0.7,
            memory_type="conversation",
            tags=["important"],
        )
        
        # Store memory
        chunk_id = memory_system.store(
            collection=ChromaDBMemorySystem.COLLECTION_NPC_MEMORIES,
            content="This is a test memory about an important conversation.",
            metadata=metadata,
        )
        
        assert chunk_id is not None
        
        # Retrieve memory (with npc_id for security)
        memories = memory_system.retrieve(
            collection=ChromaDBMemorySystem.COLLECTION_NPC_MEMORIES,
            query="test memory important conversation",
            n_results=5,
            npc_id="test_npc_1",
        )
        
        assert len(memories) > 0
        assert any(m.chunk_id == chunk_id for m in memories)
        found_memory = next(m for m in memories if m.chunk_id == chunk_id)
        assert "test memory" in found_memory.content.lower()
        assert found_memory.metadata.get("npc_id") == "test_npc_1"
    
    def test_store_conversation_chunk(self, mock_env_vars, temp_dir):
        """Test convenience method for storing conversation chunks."""
        memory_system = ChromaDBMemorySystem()
        
        chunk_id = memory_system.store_conversation_chunk(
            npc_id="test_npc_1",
            conversation_id="conv_1",
            content="Player asked about the ancient ruins.",
            importance_score=0.8,
            tags=["quest", "location"],
        )
        
        assert chunk_id is not None
        
        # Verify it was stored
        memories = memory_system.retrieve_npc_memories(
            npc_id="test_npc_1",
            query="ancient ruins",
            n_results=5,
        )
        
        assert len(memories) > 0
        assert any(m.chunk_id == chunk_id for m in memories)
    
    def test_retrieve_npc_memories(self, mock_env_vars, temp_dir):
        """Test retrieving NPC-specific memories."""
        memory_system = ChromaDBMemorySystem()
        
        # Store memories for two different NPCs
        memory_system.store_conversation_chunk(
            npc_id="npc_1",
            conversation_id="conv_1",
            content="NPC 1 said something important.",
        )
        
        memory_system.store_conversation_chunk(
            npc_id="npc_2",
            conversation_id="conv_2",
            content="NPC 2 said something different.",
        )
        
        # Retrieve only NPC 1 memories
        memories = memory_system.retrieve_npc_memories(
            npc_id="npc_1",
            query="important",
            n_results=5,
        )
        
        assert len(memories) > 0
        assert all(m.metadata.get("npc_id") == "npc_1" for m in memories)
        assert any("important" in m.content.lower() for m in memories)
    
    def test_npc_memory_isolation_requires_npc_id(self, mock_env_vars, temp_dir):
        """Test that NPC memory isolation is enforced - requires npc_id."""
        memory_system = ChromaDBMemorySystem()
        
        # Store memories for two different NPCs
        memory_system.store_conversation_chunk(
            npc_id="npc_1",
            conversation_id="conv_1",
            content="NPC 1 secret memory.",
        )
        
        memory_system.store_conversation_chunk(
            npc_id="npc_2",
            conversation_id="conv_2",
            content="NPC 2 secret memory.",
        )
        
        # Attempt to retrieve without npc_id should raise ValueError
        with pytest.raises(ValueError, match="npc_id is required"):
            memory_system.retrieve(
                collection=ChromaDBMemorySystem.COLLECTION_NPC_MEMORIES,
                query="secret",
                n_results=5,
                filter_metadata=None,  # No npc_id in filter
            )
        
        # Should work with npc_id parameter
        memories = memory_system.retrieve(
            collection=ChromaDBMemorySystem.COLLECTION_NPC_MEMORIES,
            query="secret",
            n_results=5,
            npc_id="npc_1",
        )
        
        assert len(memories) > 0
        assert all(m.metadata.get("npc_id") == "npc_1" for m in memories)
        
        # Verify NPC 2 memories are not accessible
        assert not any("npc_2" in m.metadata.get("npc_id", "") for m in memories)
    
    def test_npc_memory_isolation_post_filtering(self, mock_env_vars, temp_dir):
        """Test that post-filtering ensures NPC isolation even if query bypasses filters."""
        memory_system = ChromaDBMemorySystem()
        
        # Store memories for two different NPCs
        memory_system.store_conversation_chunk(
            npc_id="npc_1",
            conversation_id="conv_1",
            content="NPC 1 memory about dragons.",
        )
        
        memory_system.store_conversation_chunk(
            npc_id="npc_2",
            conversation_id="conv_2",
            content="NPC 2 memory about dragons.",
        )
        
        # Retrieve with npc_id - should only get NPC 1 memories
        memories = memory_system.retrieve(
            collection=ChromaDBMemorySystem.COLLECTION_NPC_MEMORIES,
            query="dragons",
            n_results=10,
            npc_id="npc_1",
        )
        
        assert len(memories) > 0
        # Verify all memories belong to npc_1 (post-filtering safety check)
        assert all(m.metadata.get("npc_id") == "npc_1" for m in memories)
        assert not any(m.metadata.get("npc_id") == "npc_2" for m in memories)
    
    def test_update_npc_memory_ownership_verification(self, mock_env_vars, temp_dir):
        """Test that updating NPC memories verifies ownership."""
        memory_system = ChromaDBMemorySystem()
        
        # Store memory for NPC 1
        chunk_id = memory_system.store_conversation_chunk(
            npc_id="npc_1",
            conversation_id="conv_1",
            content="NPC 1 original memory.",
        )
        
        # Try to update with wrong npc_id should fail
        from src.models.memory import MemoryMetadata
        wrong_metadata = MemoryMetadata(
            npc_id="npc_2",  # Wrong NPC
            conversation_id="conv_1",
            timestamp=datetime.now(),
        )
        
        success = memory_system.update(
            collection=ChromaDBMemorySystem.COLLECTION_NPC_MEMORIES,
            chunk_id=chunk_id,
            content="NPC 2 trying to modify NPC 1 memory",
            metadata=wrong_metadata,
        )
        
        assert success is False  # Should fail due to ownership verification
        
        # Update with correct npc_id should succeed
        correct_metadata = MemoryMetadata(
            npc_id="npc_1",
            conversation_id="conv_1",
            timestamp=datetime.now(),
        )
        
        success = memory_system.update(
            collection=ChromaDBMemorySystem.COLLECTION_NPC_MEMORIES,
            chunk_id=chunk_id,
            content="NPC 1 updated memory",
            metadata=correct_metadata,
        )
        
        assert success is True
    
    def test_delete_npc_memory_ownership_verification(self, mock_env_vars, temp_dir):
        """Test that deleting NPC memories verifies ownership."""
        memory_system = ChromaDBMemorySystem()
        
        # Store memories for two NPCs
        chunk_id_1 = memory_system.store_conversation_chunk(
            npc_id="npc_1",
            conversation_id="conv_1",
            content="NPC 1 memory.",
        )
        
        chunk_id_2 = memory_system.store_conversation_chunk(
            npc_id="npc_2",
            conversation_id="conv_2",
            content="NPC 2 memory.",
        )
        
        # Try to delete NPC 1 memory with NPC 2's id should fail
        success = memory_system.delete(
            collection=ChromaDBMemorySystem.COLLECTION_NPC_MEMORIES,
            chunk_id=chunk_id_1,
            npc_id="npc_2",  # Wrong NPC
        )
        
        assert success is False  # Should fail due to ownership verification
        
        # Delete with correct npc_id should succeed
        success = memory_system.delete(
            collection=ChromaDBMemorySystem.COLLECTION_NPC_MEMORIES,
            chunk_id=chunk_id_1,
            npc_id="npc_1",
        )
        
        assert success is True
        
        # Verify memory is actually deleted
        memories = memory_system.retrieve_npc_memories(
            npc_id="npc_1",
            query="memory",
            n_results=5,
        )
        
        assert not any(m.chunk_id == chunk_id_1 for m in memories)
    
    def test_update_memory(self, mock_env_vars, temp_dir):
        """Test updating a memory."""
        memory_system = ChromaDBMemorySystem()
        
        # Store initial memory
        metadata = MemoryMetadata(
            npc_id="test_npc",
            conversation_id="conv_1",
            timestamp=datetime.now(),
            importance_score=0.5,
        )
        
        chunk_id = memory_system.store(
            collection=ChromaDBMemorySystem.COLLECTION_NPC_MEMORIES,
            content="Initial content",
            metadata=metadata,
        )
        
        # Update memory
        updated_metadata = MemoryMetadata(
            npc_id="test_npc",
            conversation_id="conv_1",
            timestamp=datetime.now(),
            importance_score=0.9,
        )
        
        success = memory_system.update(
            collection=ChromaDBMemorySystem.COLLECTION_NPC_MEMORIES,
            chunk_id=chunk_id,
            content="Updated content",
            metadata=updated_metadata,
        )
        
        assert success is True
        
        # Verify update (with npc_id for security)
        memories = memory_system.retrieve(
            collection=ChromaDBMemorySystem.COLLECTION_NPC_MEMORIES,
            query="updated content",
            n_results=5,
            npc_id="test_npc",
        )
        
        assert len(memories) > 0
        found = next((m for m in memories if m.chunk_id == chunk_id), None)
        assert found is not None
        assert "updated content" in found.content.lower()
    
    def test_delete_memory(self, mock_env_vars, temp_dir):
        """Test deleting a memory."""
        memory_system = ChromaDBMemorySystem()
        
        # Store memory
        metadata = MemoryMetadata(
            npc_id="test_npc",
            conversation_id="conv_1",
            timestamp=datetime.now(),
        )
        
        chunk_id = memory_system.store(
            collection=ChromaDBMemorySystem.COLLECTION_NPC_MEMORIES,
            content="Memory to be deleted",
            metadata=metadata,
        )
        
        # Delete memory
        success = memory_system.delete(
            collection=ChromaDBMemorySystem.COLLECTION_NPC_MEMORIES,
            chunk_id=chunk_id,
        )
        
        assert success is True
        
        # Verify deletion (with npc_id for security)
        memories = memory_system.retrieve(
            collection=ChromaDBMemorySystem.COLLECTION_NPC_MEMORIES,
            query="memory to be deleted",
            n_results=5,
            npc_id="test_npc",
        )
        
        assert not any(m.chunk_id == chunk_id for m in memories)
    
    def test_time_weighted_retrieval(self, mock_env_vars, temp_dir):
        """Test time-weighted retrieval prioritizes recent memories."""
        memory_system = ChromaDBMemorySystem()
        
        # Store old memory
        old_metadata = MemoryMetadata(
            npc_id="test_npc",
            conversation_id="conv_1",
            timestamp=datetime.now() - timedelta(days=7),
            importance_score=0.7,
        )
        old_id = memory_system.store(
            collection=ChromaDBMemorySystem.COLLECTION_NPC_MEMORIES,
            content="Old memory from a week ago",
            metadata=old_metadata,
        )
        
        # Store recent memory
        recent_metadata = MemoryMetadata(
            npc_id="test_npc",
            conversation_id="conv_2",
            timestamp=datetime.now(),
            importance_score=0.6,
        )
        recent_id = memory_system.store(
            collection=ChromaDBMemorySystem.COLLECTION_NPC_MEMORIES,
            content="Recent memory from today",
            metadata=recent_metadata,
        )
        
        # Retrieve memories (should prioritize recent, with npc_id for security)
        memories = memory_system.retrieve(
            collection=ChromaDBMemorySystem.COLLECTION_NPC_MEMORIES,
            query="memory",
            n_results=5,
            npc_id="test_npc",
        )
        
        assert len(memories) >= 2
        # Recent memory should have higher score after time weighting
        recent_memory = next((m for m in memories if m.chunk_id == recent_id), None)
        old_memory = next((m for m in memories if m.chunk_id == old_id), None)
        
        if recent_memory and old_memory:
            # Recent memory should rank higher despite lower initial importance
            assert recent_memory.score >= old_memory.score
    
    def test_context_window_management(self, mock_env_vars, temp_dir):
        """Test context window management."""
        memory_system = ChromaDBMemorySystem()
        
        # Create multiple memories
        memories = []
        for i in range(10):
            metadata = MemoryMetadata(
                npc_id="test_npc",
                conversation_id=f"conv_{i}",
                timestamp=datetime.now(),
                importance_score=0.5 + (i * 0.05),
            )
            chunk_id = memory_system.store(
                collection=ChromaDBMemorySystem.COLLECTION_NPC_MEMORIES,
                content=f"Memory {i} with some content " * 10,  # Make it long
                metadata=metadata,
            )
            
            memory = Memory(
                chunk_id=chunk_id,
                content=f"Memory {i} with some content " * 10,
                metadata={},
                score=0.5 + (i * 0.05),
                timestamp=datetime.now(),
            )
            memories.append(memory)
        
        # Manage context window (limit to small size)
        selected = memory_system.context_window_management(
            memories=memories,
            max_tokens=100,
            chars_per_token=4.0,
        )
        
        # Should select only a few memories (those that fit)
        assert len(selected) < len(memories)
        assert len(selected) > 0
    
    def test_get_collection_info(self, mock_env_vars, temp_dir):
        """Test getting collection information."""
        memory_system = ChromaDBMemorySystem()
        
        # Store a few memories
        for i in range(3):
            memory_system.store_conversation_chunk(
                npc_id="test_npc",
                conversation_id=f"conv_{i}",
                content=f"Test memory {i}",
            )
        
        # Get collection info
        info = memory_system.get_collection_info(
            ChromaDBMemorySystem.COLLECTION_NPC_MEMORIES
        )
        
        assert info["name"] == ChromaDBMemorySystem.COLLECTION_NPC_MEMORIES
        assert info["count"] >= 3
    
    def test_health_check(self, mock_env_vars, temp_dir):
        """Test health check functionality."""
        memory_system = ChromaDBMemorySystem()
        
        health = memory_system.health_check()
        
        assert health["status"] in ["healthy", "degraded", "unhealthy"]
        assert "collections" in health
        assert "total_memories" in health
        assert len(health["collections"]) == 4
    
    def test_export_memories(self, mock_env_vars, temp_dir):
        """Test exporting memories."""
        memory_system = ChromaDBMemorySystem()
        
        # Store some memories
        for i in range(3):
            memory_system.store_conversation_chunk(
                npc_id="test_npc",
                conversation_id=f"conv_{i}",
                content=f"Export test memory {i}",
            )
        
        # Export to JSON
        export_path = temp_dir / "test_export.json"
        success = memory_system.export_memories(
            collection=ChromaDBMemorySystem.COLLECTION_NPC_MEMORIES,
            output_path=str(export_path),
            format="json",
        )
        
        assert success is True
        assert export_path.exists()
        assert export_path.stat().st_size > 0
    
    def test_backup_all_collections(self, mock_env_vars, temp_dir):
        """Test backing up all collections."""
        memory_system = ChromaDBMemorySystem()
        
        # Store some test data
        memory_system.store_conversation_chunk(
            npc_id="test_npc",
            conversation_id="conv_1",
            content="Backup test memory",
        )
        
        # Create backup
        backup_dir = temp_dir / "backup"
        results = memory_system.backup_all_collections(str(backup_dir))
        
        assert len(results) == 4
        assert all(isinstance(success, bool) for success in results.values())


class TestMemoryUtils:
    """Tests for memory utility functions."""
    
    def test_chunk_text(self):
        """Test text chunking."""
        text = "This is a test. " * 100  # Long text
        chunks = chunk_text(text, chunk_size=100, chunk_overlap=10)
        
        assert len(chunks) > 1
        assert all(len(chunk) <= 100 for chunk in chunks)
        assert sum(len(chunk) for chunk in chunks) > len(text) - 200  # Account for overlap
    
    def test_chunk_text_short(self):
        """Test chunking short text."""
        text = "Short text"
        chunks = chunk_text(text, chunk_size=100)
        
        assert len(chunks) == 1
        assert chunks[0] == text
    
    def test_calculate_importance_score(self):
        """Test importance score calculation."""
        # High importance: relationship type
        score = calculate_importance_score(
            content="Player promised to help",
            memory_type="relationship",
            has_emotion=True,
        )
        assert 0.7 <= score <= 1.0
        
        # Medium importance: conversation type
        score = calculate_importance_score(
            content="Regular conversation",
            memory_type="conversation",
        )
        assert 0.4 <= score <= 0.6
    
    def test_calculate_importance_score_with_keywords(self):
        """Test importance score with important keywords."""
        score_with_keywords = calculate_importance_score(
            content="This is a secret promise that is very important and critical",
            memory_type="conversation",
        )
        
        score_without = calculate_importance_score(
            content="This is a regular conversation",
            memory_type="conversation",
        )
        
        assert score_with_keywords > score_without
    
    def test_consolidate_memories(self):
        """Test memory consolidation."""
        # Create similar memories
        memories = [
            Memory(
                chunk_id="1",
                content="Player asked about the ancient ruins",
                metadata={},
                score=0.7,
                timestamp=datetime.now(),
            ),
            Memory(
                chunk_id="2",
                content="Player asked about the ancient ruins location",
                metadata={},
                score=0.6,
                timestamp=datetime.now(),
            ),
            Memory(
                chunk_id="3",
                content="Completely different topic about dragons",
                metadata={},
                score=0.8,
                timestamp=datetime.now(),
            ),
        ]
        
        consolidated = consolidate_memories(memories, similarity_threshold=0.5)
        
        # Should reduce similar memories
        assert len(consolidated) <= len(memories)
        assert len(consolidated) >= 1
    
    def test_build_context_from_memories(self):
        """Test building context from memories."""
        memories = [
            Memory(
                chunk_id="1",
                content="First memory",
                metadata={"npc_id": "npc1"},
                score=0.8,
                timestamp=datetime.now(),
            ),
            Memory(
                chunk_id="2",
                content="Second memory",
                metadata={"npc_id": "npc2"},
                score=0.7,
                timestamp=datetime.now(),
            ),
        ]
        
        context = build_context_from_memories(memories, max_tokens=1000)
        
        assert isinstance(context, str)
        assert len(context) > 0
        assert "First memory" in context or "Second memory" in context
    
    def test_filter_memories_by_importance(self):
        """Test filtering memories by importance."""
        memories = [
            Memory(
                chunk_id="1",
                content="High importance",
                metadata={"importance_score": "0.9"},
                score=0.9,
                timestamp=datetime.now(),
            ),
            Memory(
                chunk_id="2",
                content="Low importance",
                metadata={"importance_score": "0.2"},
                score=0.2,
                timestamp=datetime.now(),
            ),
        ]
        
        filtered = filter_memories_by_importance(memories, min_importance=0.5)
        
        assert len(filtered) == 1
        assert filtered[0].chunk_id == "1"
    
    def test_apply_memory_decay(self):
        """Test applying memory decay."""
        now = datetime.now()
        memories = [
            Memory(
                chunk_id="1",
                content="Recent memory",
                metadata={},
                score=0.8,
                timestamp=now,
            ),
            Memory(
                chunk_id="2",
                content="Old memory",
                metadata={},
                score=0.8,
                timestamp=now - timedelta(days=14),  # 2 weeks old
            ),
        ]
        
        decayed = apply_memory_decay(memories, decay_hours=168.0)  # 7 days
        
        # Old memory should have lower score after decay
        old_memory = next(m for m in decayed if m.chunk_id == "2")
        recent_memory = next(m for m in decayed if m.chunk_id == "1")
        
        assert old_memory.score < recent_memory.score

