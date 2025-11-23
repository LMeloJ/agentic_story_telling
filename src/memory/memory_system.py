"""
Memory System interface and base implementation.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

from src.memory.memory_types import Memory
from src.models.memory import MemoryChunk, MemoryMetadata


class MemorySystem(ABC):
    """
    Abstract base class for Memory System API.
    
    Handles storage, retrieval, and management of conversation memories
    using ChromaDB and RAG techniques.
    """
    
    @abstractmethod
    def store(
        self,
        collection: str,
        content: str,
        metadata: MemoryMetadata,
    ) -> str:
        """
        Store a memory chunk in ChromaDB.
        
        Args:
            collection: Collection name (e.g., "npc_memories")
            content: Text content to store
            metadata: Memory metadata
        
        Returns:
            Memory chunk ID
        """
        pass
    
    @abstractmethod
    def retrieve(
        self,
        collection: str,
        query: str,
        n_results: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None,
    ) -> List[Memory]:
        """
        Retrieve relevant memories using semantic search.
        
        Args:
            collection: Collection name
            query: Search query text
            n_results: Number of results to return
            filter_metadata: Optional metadata filters
        
        Returns:
            List of retrieved memories
        """
        pass
    
    @abstractmethod
    def update(
        self,
        collection: str,
        chunk_id: str,
        content: Optional[str] = None,
        metadata: Optional[MemoryMetadata] = None,
    ) -> bool:
        """
        Update an existing memory chunk.
        
        Args:
            collection: Collection name
            chunk_id: Memory chunk ID
            content: Updated content (if provided)
            metadata: Updated metadata (if provided)
        
        Returns:
            True if update was successful
        """
        pass
    
    @abstractmethod
    def search(
        self,
        collection: str,
        query: str,
        n_results: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None,
    ) -> List[Memory]:
        """
        Search for memories (alias for retrieve, for consistency).
        
        Args:
            collection: Collection name
            query: Search query text
            n_results: Number of results to return
            filter_metadata: Optional metadata filters
        
        Returns:
            List of retrieved memories
        """
        pass
    
    @abstractmethod
    def delete(
        self,
        collection: str,
        chunk_id: str,
    ) -> bool:
        """
        Delete a memory chunk.
        
        Args:
            collection: Collection name
            chunk_id: Memory chunk ID
        
        Returns:
            True if deletion was successful
        """
        pass
    
    @abstractmethod
    def get_collection_info(self, collection: str) -> Dict[str, Any]:
        """
        Get information about a collection.
        
        Args:
            collection: Collection name
        
        Returns:
            Dictionary with collection information (count, etc.)
        """
        pass

