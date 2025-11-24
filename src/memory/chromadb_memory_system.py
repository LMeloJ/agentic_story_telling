"""
ChromaDB-based memory system implementation.
"""

import uuid
import json
import csv
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path

import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions

from src.memory.memory_system import MemorySystem
from src.memory.memory_types import Memory
from src.models.memory import MemoryChunk, MemoryMetadata
from src.config.config_loader import get_config
from src.services.logging_service import get_logger


class ChromaDBMemorySystem(MemorySystem):
    """
    ChromaDB-based implementation of the Memory System.
    
    Handles storage, retrieval, and management of conversation memories
    using ChromaDB with semantic search capabilities.
    """
    
    # Collection names as per PLAN.md
    COLLECTION_NPC_MEMORIES = "npc_memories"
    COLLECTION_WORLD_KNOWLEDGE = "world_knowledge"
    COLLECTION_CHARACTER_PROFILES = "character_profiles"
    COLLECTION_RELATIONSHIP_GRAPH = "relationship_graph"
    
    def __init__(self, embedding_model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        """
        Initialize ChromaDB memory system.
        
        Args:
            embedding_model_name: Name of the embedding model to use.
                Default uses sentence-transformers for local embeddings.
        """
        self.logger = get_logger("chromadb_memory_system")
        config = get_config()
        
        # Initialize ChromaDB client with persistent storage
        persist_directory = Path(config.chromadb.persist_directory).absolute()
        persist_directory.mkdir(parents=True, exist_ok=True)
        
        # Create ChromaDB client
        self.client = chromadb.PersistentClient(
            path=str(persist_directory),
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True,
            )
        )
        
        # Initialize embedding function
        # Use sentence-transformers for local embeddings (no API key needed)
        # This will automatically download the model on first use
        self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=embedding_model_name
        )
        
        # Initialize collections
        self._initialize_collections()
        
        self.logger.info(
            f"ChromaDB memory system initialized at {persist_directory}"
        )
    
    def close(self) -> None:
        """Close ChromaDB connections and clean up resources."""
        # ChromaDB PersistentClient doesn't require explicit close,
        # but we can reset it if needed
        if hasattr(self, 'client') and self.client:
            try:
                # ChromaDB doesn't have explicit close, but collections are lightweight
                # We'll just clear the collections reference
                self.collections.clear()
            except Exception as e:
                self.logger.warning(f"Error closing ChromaDB client: {e}")
    
    def __del__(self):
        """Cleanup on destruction."""
        try:
            self.close()
        except Exception:
            pass  # Ignore errors during cleanup
    
    def _initialize_collections(self) -> None:
        """Initialize all required collections."""
        collections = [
            self.COLLECTION_NPC_MEMORIES,
            self.COLLECTION_WORLD_KNOWLEDGE,
            self.COLLECTION_CHARACTER_PROFILES,
            self.COLLECTION_RELATIONSHIP_GRAPH,
        ]
        
        self.collections: Dict[str, chromadb.Collection] = {}
        
        for collection_name in collections:
            try:
                # Try to get existing collection
                collection = self.client.get_collection(
                    name=collection_name,
                    embedding_function=self.embedding_function,
                )
            except Exception:
                # Create new collection if it doesn't exist
                collection = self.client.create_collection(
                    name=collection_name,
                    embedding_function=self.embedding_function,
                    metadata={"description": f"Collection for {collection_name}"}
                )
            
            self.collections[collection_name] = collection
        
        self.logger.info(f"Initialized {len(collections)} collections")
    
    def _get_collection(self, collection: str) -> chromadb.Collection:
        """Get a collection by name."""
        if collection not in self.collections:
            raise ValueError(f"Collection '{collection}' does not exist")
        return self.collections[collection]
    
    def _metadata_to_dict(self, metadata: MemoryMetadata) -> Dict[str, Any]:
        """Convert MemoryMetadata to dictionary for ChromaDB."""
        return {
            "npc_id": metadata.npc_id or "",
            "conversation_id": metadata.conversation_id or "",
            "timestamp": metadata.timestamp.isoformat(),
            "importance_score": str(metadata.importance_score),
            "memory_type": metadata.memory_type,
            "tags": ",".join(metadata.tags) if metadata.tags else "",
            **metadata.additional_metadata,
        }
    
    def _dict_to_metadata(self, metadata_dict: Dict[str, Any]) -> MemoryMetadata:
        """Convert ChromaDB metadata dictionary to MemoryMetadata."""
        tags_str = metadata_dict.get("tags", "")
        tags = [tag.strip() for tag in tags_str.split(",") if tag.strip()] if tags_str else []
        
        # Extract additional metadata (everything not in standard fields)
        standard_fields = {"npc_id", "conversation_id", "timestamp", "importance_score", "memory_type", "tags"}
        additional_metadata = {
            k: v for k, v in metadata_dict.items() if k not in standard_fields
        }
        
        return MemoryMetadata(
            npc_id=metadata_dict.get("npc_id") or None,
            conversation_id=metadata_dict.get("conversation_id") or None,
            timestamp=datetime.fromisoformat(metadata_dict.get("timestamp", datetime.now().isoformat())),
            importance_score=float(metadata_dict.get("importance_score", "0.5")),
            memory_type=metadata_dict.get("memory_type", "conversation"),
            tags=tags,
            additional_metadata=additional_metadata,
        )
    
    def store(
        self,
        collection: str,
        content: str,
        metadata: MemoryMetadata,
    ) -> str:
        """
        Store a memory chunk in ChromaDB.
        
        Args:
            collection: Collection name
            content: Text content to store
            metadata: Memory metadata
        
        Returns:
            Memory chunk ID
        """
        coll = self._get_collection(collection)
        
        # Generate unique ID
        chunk_id = str(uuid.uuid4())
        
        # Convert metadata to dict
        metadata_dict = self._metadata_to_dict(metadata)
        metadata_dict["chunk_id"] = chunk_id
        
        # Store in ChromaDB
        coll.add(
            ids=[chunk_id],
            documents=[content],
            metadatas=[metadata_dict],
        )
        
        self.logger.debug(
            f"Stored memory chunk {chunk_id} in collection {collection}"
        )
        
        return chunk_id
    
    def retrieve(
        self,
        collection: str,
        query: str,
        n_results: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None,
        npc_id: Optional[str] = None,  # Explicit NPC ID for security
    ) -> List[Memory]:
        """
        Retrieve relevant memories using semantic search.
        
        Args:
            collection: Collection name
            query: Search query text
            n_results: Number of results to return
            filter_metadata: Optional metadata filters
            npc_id: Required for NPC memory collections to ensure data isolation
        
        Returns:
            List of retrieved memories
        
        Raises:
            ValueError: If npc_id is not provided when querying NPC memories collection
        """
        # SECURITY: Enforce NPC memory isolation
        # For NPC memory collections, require npc_id to prevent cross-NPC memory leaks
        if collection == self.COLLECTION_NPC_MEMORIES:
            # Use explicit npc_id parameter if provided, otherwise check filter_metadata
            if npc_id:
                if filter_metadata is None:
                    filter_metadata = {}
                filter_metadata["npc_id"] = npc_id
            elif not filter_metadata or "npc_id" not in filter_metadata or not filter_metadata["npc_id"]:
                raise ValueError(
                    f"npc_id is required when querying {self.COLLECTION_NPC_MEMORIES} collection "
                    "to ensure NPC memory isolation. Use retrieve_npc_memories() or provide npc_id parameter."
                )
        
        coll = self._get_collection(collection)
        
        # Prepare where clause for filtering
        where = filter_metadata or {}
        
        # Perform semantic search
        results = coll.query(
            query_texts=[query],
            n_results=n_results,
            where=where if where else None,
        )
        
        # Convert results to Memory objects
        memories = []
        if results["ids"] and len(results["ids"]) > 0:
            for i in range(len(results["ids"][0])):
                chunk_id = results["ids"][0][i]
                content = results["documents"][0][i]
                metadata_dict = results["metadatas"][0][i]
                distance = results["distances"][0][i] if "distances" in results else 0.0
                
                # Convert distance to similarity score (1 - normalized distance)
                score = 1.0 - min(distance, 1.0) if distance is not None else 0.0
                
                # Parse metadata
                try:
                    memory_metadata = self._dict_to_metadata(metadata_dict)
                    timestamp = memory_metadata.timestamp
                except Exception as e:
                    self.logger.warning(
                        f"Error parsing metadata for chunk {chunk_id}: {e}"
                    )
                    timestamp = datetime.now()
                
                memory = Memory(
                    chunk_id=chunk_id,
                    content=content,
                    metadata=metadata_dict,
                    score=score,
                    timestamp=timestamp,
                )
                memories.append(memory)
        
        # SECURITY: Post-filter results as a safety measure for NPC memories
        # This ensures even if ChromaDB query somehow bypasses filters, we still filter results
        if collection == self.COLLECTION_NPC_MEMORIES and npc_id:
            expected_npc_id = npc_id
            original_count = len(memories)
            memories = [
                m for m in memories
                if m.metadata.get("npc_id") == expected_npc_id
            ]
            if len(memories) < original_count:
                self.logger.warning(
                    f"Post-filtered {original_count - len(memories)} memories "
                    f"that didn't match npc_id={expected_npc_id} (safety check)"
                )
        
        # Apply time-weighted retrieval (recent memories prioritized)
        memories = self._apply_time_weighting(memories)
        
        self.logger.debug(
            f"Retrieved {len(memories)} memories from collection {collection}"
            + (f" for npc_id={npc_id}" if npc_id else "")
        )
        
        return memories
    
    def _apply_time_weighting(self, memories: List[Memory], decay_hours: float = 24.0) -> List[Memory]:
        """
        Apply time-weighted scoring to prioritize recent memories.
        
        Args:
            memories: List of memories to weight
            decay_hours: Hours after which importance decays significantly
        
        Returns:
            List of memories with adjusted scores
        """
        now = datetime.now()
        
        for memory in memories:
            if memory.timestamp:
                # Calculate age in hours
                age_hours = (now - memory.timestamp).total_seconds() / 3600
                
                # Apply exponential decay: score * exp(-age / decay_hours)
                import math
                time_weight = math.exp(-age_hours / decay_hours)
                
                # Combine semantic similarity with time weight
                memory.score = (memory.score * 0.7) + (time_weight * 0.3)
        
        # Re-sort by combined score
        memories.sort(key=lambda m: m.score, reverse=True)
        
        return memories
    
    def update(
        self,
        collection: str,
        chunk_id: str,
        content: Optional[str] = None,
        metadata: Optional[MemoryMetadata] = None,
        npc_id: Optional[str] = None,  # Required for NPC memories to verify ownership
    ) -> bool:
        """
        Update an existing memory chunk.
        
        Args:
            collection: Collection name
            chunk_id: Memory chunk ID
            content: Updated content (if provided)
            metadata: Updated metadata (if provided)
            npc_id: Required for NPC memory collections to verify ownership
        
        Returns:
            True if update was successful
        """
        coll = self._get_collection(collection)
        
        try:
            # Get existing memory
            results = coll.get(ids=[chunk_id])
            
            if not results["ids"]:
                self.logger.warning(f"Memory chunk {chunk_id} not found")
                return False
            
            # SECURITY: Verify ownership for NPC memory collections
            if collection == self.COLLECTION_NPC_MEMORIES:
                existing_metadata = results["metadatas"][0] if results["metadatas"] else {}
                existing_npc_id = existing_metadata.get("npc_id")
                
                # Use npc_id parameter if provided, otherwise check if metadata matches existing
                if npc_id:
                    if existing_npc_id and existing_npc_id != npc_id:
                        self.logger.error(
                            f"Security violation: Attempted to update memory {chunk_id} "
                            f"owned by npc_id={existing_npc_id} with npc_id={npc_id}"
                        )
                        return False
                elif metadata and metadata.npc_id:
                    # Verify metadata npc_id matches existing
                    if existing_npc_id and existing_npc_id != metadata.npc_id:
                        self.logger.error(
                            f"Security violation: Attempted to update memory {chunk_id} "
                            f"owned by npc_id={existing_npc_id} with npc_id={metadata.npc_id}"
                        )
                        return False
                elif not existing_npc_id:
                    # If no existing npc_id, require one in update
                    if not npc_id and (not metadata or not metadata.npc_id):
                        self.logger.error(
                            f"npc_id required when updating memory in {self.COLLECTION_NPC_MEMORIES} collection"
                        )
                        return False
            
            # Prepare update data
            update_content = content if content is not None else results["documents"][0]
            update_metadata = self._metadata_to_dict(metadata) if metadata else results["metadatas"][0]
            update_metadata["chunk_id"] = chunk_id
            
            # Ensure npc_id is preserved if updating NPC memory
            if collection == self.COLLECTION_NPC_MEMORIES and npc_id:
                update_metadata["npc_id"] = npc_id
            
            # Update in ChromaDB (delete and re-add)
            coll.delete(ids=[chunk_id])
            coll.add(
                ids=[chunk_id],
                documents=[update_content],
                metadatas=[update_metadata],
            )
            
            self.logger.debug(f"Updated memory chunk {chunk_id} in collection {collection}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating memory chunk {chunk_id}: {e}")
            return False
    
    def search(
        self,
        collection: str,
        query: str,
        n_results: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None,
        npc_id: Optional[str] = None,
    ) -> List[Memory]:
        """Search for memories (alias for retrieve, for consistency)."""
        return self.retrieve(collection, query, n_results, filter_metadata, npc_id)
    
    def delete(
        self,
        collection: str,
        chunk_id: str,
        npc_id: Optional[str] = None,  # Required for NPC memories to verify ownership
    ) -> bool:
        """
        Delete a memory chunk.
        
        Args:
            collection: Collection name
            chunk_id: Memory chunk ID
            npc_id: Required for NPC memory collections to verify ownership
        
        Returns:
            True if deletion was successful
        """
        coll = self._get_collection(collection)
        
        try:
            # SECURITY: Verify ownership for NPC memory collections
            if collection == self.COLLECTION_NPC_MEMORIES and npc_id:
                # Get existing memory to verify ownership
                results = coll.get(ids=[chunk_id])
                if results["ids"] and results["metadatas"]:
                    existing_npc_id = results["metadatas"][0].get("npc_id")
                    if existing_npc_id and existing_npc_id != npc_id:
                        self.logger.error(
                            f"Security violation: Attempted to delete memory {chunk_id} "
                            f"owned by npc_id={existing_npc_id} with npc_id={npc_id}"
                        )
                        return False
            
            coll.delete(ids=[chunk_id])
            self.logger.debug(f"Deleted memory chunk {chunk_id} from collection {collection}")
            return True
        except Exception as e:
            self.logger.error(f"Error deleting memory chunk {chunk_id}: {e}")
            return False
    
    def get_collection_info(self, collection: str) -> Dict[str, Any]:
        """
        Get information about a collection.
        
        Args:
            collection: Collection name
        
        Returns:
            Dictionary with collection information
        """
        coll = self._get_collection(collection)
        
        count = coll.count()
        
        return {
            "name": collection,
            "count": count,
            "description": coll.metadata.get("description", ""),
        }
    
    def store_conversation_chunk(
        self,
        npc_id: str,
        conversation_id: str,
        content: str,
        importance_score: float = 0.5,
        tags: Optional[List[str]] = None,
    ) -> str:
        """
        Convenience method to store a conversation chunk.
        
        Args:
            npc_id: NPC ID
            conversation_id: Conversation ID
            content: Conversation content
            importance_score: Importance score (0.0 to 1.0)
            tags: Optional tags
        
        Returns:
            Memory chunk ID
        """
        metadata = MemoryMetadata(
            npc_id=npc_id,
            conversation_id=conversation_id,
            timestamp=datetime.now(),
            importance_score=importance_score,
            memory_type="conversation",
            tags=tags or [],
        )
        
        return self.store(
            collection=self.COLLECTION_NPC_MEMORIES,
            content=content,
            metadata=metadata,
        )
    
    def retrieve_npc_memories(
        self,
        npc_id: str,
        query: str,
        n_results: int = 5,
        conversation_id: Optional[str] = None,
    ) -> List[Memory]:
        """
        Convenience method to retrieve NPC-specific memories.
        
        Args:
            npc_id: NPC ID
            query: Search query
            n_results: Number of results
            conversation_id: Optional conversation ID filter
        
        Returns:
            List of memories
        """
        filter_metadata = {"npc_id": npc_id}
        if conversation_id:
            filter_metadata["conversation_id"] = conversation_id
        
        return self.retrieve(
            collection=self.COLLECTION_NPC_MEMORIES,
            query=query,
            n_results=n_results,
            filter_metadata=filter_metadata,
        )
    
    def context_window_management(
        self,
        memories: List[Memory],
        max_tokens: int = 4000,
        chars_per_token: float = 4.0,
    ) -> List[Memory]:
        """
        Manage context window by selecting most relevant memories.
        
        Args:
            memories: List of memories
            max_tokens: Maximum token budget
            chars_per_token: Approximate characters per token
        
        Returns:
            Filtered and prioritized list of memories
        """
        max_chars = int(max_tokens * chars_per_token)
        selected = []
        current_size = 0
        
        # Sort by score (already time-weighted)
        sorted_memories = sorted(memories, key=lambda m: m.score, reverse=True)
        
        for memory in sorted_memories:
            memory_size = len(memory.content)
            if current_size + memory_size <= max_chars:
                selected.append(memory)
                current_size += memory_size
            else:
                break
        
        return selected
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on ChromaDB.
        
        Returns:
            Dictionary with health check results
        """
        health_status = {
            "status": "healthy",
            "collections": {},
            "total_memories": 0,
            "errors": [],
        }
        
        try:
            # Check each collection
            for collection_name, collection in self.collections.items():
                try:
                    count = collection.count()
                    health_status["collections"][collection_name] = {
                        "count": count,
                        "status": "healthy",
                    }
                    health_status["total_memories"] += count
                except Exception as e:
                    health_status["collections"][collection_name] = {
                        "count": 0,
                        "status": "error",
                        "error": str(e),
                    }
                    health_status["errors"].append(f"{collection_name}: {str(e)}")
                    health_status["status"] = "degraded"
            
            # Check database path
            config = get_config()
            db_path = Path(config.chromadb.persist_directory)
            if not db_path.exists():
                health_status["errors"].append(f"Database path does not exist: {db_path}")
                health_status["status"] = "degraded"
            
        except Exception as e:
            health_status["status"] = "unhealthy"
            health_status["errors"].append(f"Health check failed: {str(e)}")
        
        return health_status
    
    def export_memories(
        self,
        collection: str,
        output_path: str,
        format: str = "json",
    ) -> bool:
        """
        Export memories from a collection to a file.
        
        Args:
            collection: Collection name
            output_path: Output file path
            format: Export format ("json" or "csv")
        
        Returns:
            True if export was successful
        """
        try:
            coll = self._get_collection(collection)
            
            # Get all memories from collection
            results = coll.get()
            
            if format.lower() == "json":
                # Export as JSON
                export_data = []
                for i in range(len(results["ids"])):
                    chunk_id = results["ids"][i]
                    content = results["documents"][i]
                    metadata = results["metadatas"][i]
                    
                    export_data.append({
                        "chunk_id": chunk_id,
                        "content": content,
                        "metadata": metadata,
                    })
                
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            elif format.lower() == "csv":
                # Export as CSV
                with open(output_path, "w", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    writer.writerow(["chunk_id", "content", "metadata"])
                    
                    for i in range(len(results["ids"])):
                        chunk_id = results["ids"][i]
                        content = results["documents"][i]
                        metadata_str = json.dumps(results["metadatas"][i])
                        writer.writerow([chunk_id, content, metadata_str])
            
            else:
                raise ValueError(f"Unsupported format: {format}")
            
            self.logger.info(f"Exported {len(results['ids'])} memories to {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error exporting memories: {e}")
            return False
    
    def backup_all_collections(self, backup_dir: str) -> Dict[str, bool]:
        """
        Backup all collections to a directory.
        
        Args:
            backup_dir: Backup directory path
        
        Returns:
            Dictionary mapping collection names to backup success status
        """
        backup_path = Path(backup_dir)
        backup_path.mkdir(parents=True, exist_ok=True)
        
        results = {}
        
        for collection_name in self.collections.keys():
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = backup_path / f"{collection_name}_{timestamp}.json"
            
            success = self.export_memories(
                collection=collection_name,
                output_path=str(output_path),
                format="json",
            )
            results[collection_name] = success
        
        self.logger.info(f"Backup completed: {sum(1 for v in results.values() if v)}/{len(results)} collections backed up")
        return results

