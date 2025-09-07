import json
import os
import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import chromadb
from chromadb.config import Settings
from openai import OpenAI

# Import the Neon vector database
try:
    from NeonDB.neon import get_neon_db, NeonVectorDB
except ImportError:
    get_neon_db = None
    NeonVectorDB = None

logger = logging.getLogger(__name__)

class EnhancedFinancialMemory:
    """
    Enhanced memory system for financial trading agents
    Combines ChromaDB with Neon Vector Database for comprehensive memory management
    """
    
    def __init__(self, name: str, config: Dict[str, Any]):
        """
        Initialize enhanced memory system
        
        Args:
            name: Memory collection name
            config: Configuration dictionary
        """
        self.name = name
        self.config = config
        self.use_vector_db = config.get("use_vector_db", True)
        
        # Initialize embedding model - prefer local sentence-transformers for efficiency
        self.use_local_embeddings = config.get("use_local_embeddings", True)
        
        if self.use_local_embeddings:
            # Use local sentence-transformers model (same as Neon DB)
            try:
                from sentence_transformers import SentenceTransformer
                self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
                self.client = None  # No need for OpenAI client
                logger.info("Using local sentence-transformers for embeddings")
            except ImportError:
                logger.warning("sentence-transformers not available, falling back to OpenAI")
                self.use_local_embeddings = False
        
        if not self.use_local_embeddings:
            # Fallback to OpenAI embeddings
            if config.get("llm_provider") == "groq" or "groq" in config.get("backend_url", ""):
                self.embedding = "text-embedding-3-small"
                self.client = OpenAI(base_url="https://api.openai.com/v1")
            else:
                self.embedding = "text-embedding-3-small"
                self.client = OpenAI(base_url=config["backend_url"])
        
        # Initialize ChromaDB (existing functionality)
        self.chroma_client = chromadb.Client(Settings(allow_reset=True))
        try:
            self.situation_collection = self.chroma_client.create_collection(name=name)
        except Exception:
            # Collection already exists, get it
            self.situation_collection = self.chroma_client.get_collection(name=name)
        
        # Initialize Neon Vector Database
        self.vector_db = None
        if self.use_vector_db and get_neon_db:
            try:
                asyncio.create_task(self._initialize_vector_db())
            except Exception as e:
                logger.warning(f"Failed to initialize vector DB: {e}")
                self.use_vector_db = False
    
    async def _initialize_vector_db(self):
        """Initialize vector database connection"""
        try:
            self.vector_db = await get_neon_db()
            logger.info(f"Vector database initialized for {self.name}")
        except Exception as e:
            logger.error(f"Failed to initialize vector database: {e}")
            self.use_vector_db = False
    
    def get_embedding(self, text):
        """Get embedding for a text using local model or OpenAI"""
        if self.use_local_embeddings and hasattr(self, 'embedding_model'):
            # Use local sentence-transformers model
            embedding = self.embedding_model.encode(text, normalize_embeddings=True)
            return embedding.tolist()
        else:
            # Fallback to OpenAI embeddings
            response = self.client.embeddings.create(
                model=self.embedding, input=text
            )
            return response.data[0].embedding
    
    def add_situations(self, situations_and_advice):
        """Add financial situations and their corresponding advice. Parameter is a list of tuples (situation, rec)"""
        situations = []
        advice = []
        ids = []
        embeddings = []
        
        offset = self.situation_collection.count()
        
        for i, (situation, recommendation) in enumerate(situations_and_advice):
            situations.append(situation)
            advice.append(recommendation)
            ids.append(str(offset + i))
            embeddings.append(self.get_embedding(situation))
        
        # Add to ChromaDB
        self.situation_collection.add(
            documents=situations,
            metadatas=[{"recommendation": rec} for rec in advice],
            embeddings=embeddings,
            ids=ids,
        )
        
        # Also store in Neon Vector DB if available
        if self.use_vector_db:
            try:
                asyncio.create_task(self._store_situations_vector(situations_and_advice))
            except Exception as e:
                logger.warning(f"Could not schedule vector storage: {e}")
    
    async def _store_situations_vector(self, situations_and_advice):
        """Store situations in vector database"""
        try:
            if not self.vector_db:
                self.vector_db = await get_neon_db()
            
            for situation, recommendation in situations_and_advice:
                content = f"Situation: {situation}\nRecommendation: {recommendation}"
                await self.vector_db.store_financial_memory(
                    memory_type=self.name,
                    content=content,
                    metadata={"situation": situation, "recommendation": recommendation}
                )
        except Exception as e:
            logger.error(f"Failed to store situations in vector DB: {e}")
    
    async def add_memory_async(self, content: str, ticker: str = None, metadata: Dict[str, Any] = None):
        """
        Add a new memory asynchronously with vector storage
        
        Args:
            content: Memory content
            ticker: Stock ticker (optional)
            metadata: Additional metadata
        """
        # Add to vector database if available
        if self.use_vector_db and self.vector_db:
            try:
                await self.vector_db.store_financial_memory(
                    memory_type=self.name,
                    content=content,
                    ticker=ticker,
                    metadata=metadata
                )
            except Exception as e:
                logger.error(f"Failed to store memory in vector DB: {e}")
        
        logger.info(f"Added memory to {self.name}")
    
    def get_memories(self, current_situation, n_matches=1):
        """Find matching recommendations using OpenAI embeddings (ChromaDB)"""
        query_embedding = self.get_embedding(current_situation)
        
        results = self.situation_collection.query(
            query_embeddings=[query_embedding],
            n_results=n_matches,
            include=["metadatas", "documents", "distances"],
        )
        
        matched_results = []
        for i in range(len(results["documents"][0])):
            matched_results.append(
                {
                    "matched_situation": results["documents"][0][i],
                    "recommendation": results["metadatas"][0][i]["recommendation"],
                    "similarity_score": 1 - results["distances"][0][i],
                }
            )
        
        return matched_results
    
    async def semantic_search_async(self, query: str, ticker: str = None, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Perform semantic search on memories using vector database
        
        Args:
            query: Search query
            ticker: Filter by ticker (optional)
            limit: Maximum number of results
            
        Returns:
            List of relevant memories with similarity scores
        """
        if not self.use_vector_db or not self.vector_db:
            return self.get_memories(query, limit)
        
        try:
            if not self.vector_db:
                self.vector_db = await get_neon_db()
            
            results = await self.vector_db.semantic_search_memories(
                query=query,
                memory_type=self.name,
                ticker=ticker,
                limit=limit
            )
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to perform semantic search: {e}")
            return self.get_memories(query, limit)
    
    async def get_relevant_memories(self, context: str, ticker: str = None, limit: int = 3) -> List[Dict[str, Any]]:
        """
        Get memories most relevant to current context
        
        Args:
            context: Current context or situation
            ticker: Stock ticker to filter by
            limit: Maximum number of memories to return
            
        Returns:
            List of relevant memories
        """
        if self.use_vector_db and self.vector_db:
            try:
                return await self.semantic_search_async(context, ticker, limit)
            except Exception as e:
                logger.error(f"Failed to get relevant memories: {e}")
        
        # Fallback to ChromaDB search
        return self.get_memories(context, limit)

class FinancialSituationMemory(EnhancedFinancialMemory):
    """
    Backwards compatible wrapper for existing FinancialSituationMemory
    """
    def __init__(self, name, config):
        super().__init__(name, config)

class EnhancedFinancialMemoryManager:
    """
    Enhanced memory manager that coordinates multiple memory types and vector storage
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize enhanced memory manager"""
        self.config = config
        self.memories = {}
        self.vector_db = None
        
        # Initialize different memory types
        memory_types = ["bull_memory", "bear_memory", "trader_memory", 
                       "invest_judge_memory", "risk_manager_memory"]
        
        for memory_type in memory_types:
            self.memories[memory_type] = EnhancedFinancialMemory(memory_type, config)
    
    async def initialize_vector_db(self):
        """Initialize vector database connection"""
        if get_neon_db:
            try:
                self.vector_db = await get_neon_db()
                logger.info("Enhanced memory manager vector DB initialized")
            except Exception as e:
                logger.error(f"Failed to initialize vector DB in memory manager: {e}")
    
    def get_memory(self, memory_type: str) -> EnhancedFinancialMemory:
        """Get specific memory instance"""
        return self.memories.get(memory_type)
    
    async def store_trading_decision(
        self, 
        ticker: str, 
        decision: str, 
        confidence: float, 
        reasoning: str,
        market_data: Dict = None
    ):
        """Store trading decision in vector database"""
        if not self.vector_db:
            await self.initialize_vector_db()
        
        if self.vector_db:
            try:
                await self.vector_db.store_trading_decision(
                    ticker=ticker,
                    decision_date=datetime.now(),
                    decision=decision,
                    confidence=confidence,
                    reasoning=reasoning,
                    market_data=market_data
                )
            except Exception as e:
                logger.error(f"Failed to store trading decision: {e}")
    
    async def store_market_analysis(
        self,
        ticker: str,
        analysis_type: str,
        content: str,
        sentiment_score: float = None,
        confidence_score: float = None,
        metadata: Dict = None
    ):
        """Store market analysis in vector database"""
        if not self.vector_db:
            await self.initialize_vector_db()
        
        if self.vector_db:
            try:
                await self.vector_db.store_market_analysis(
                    ticker=ticker,
                    analysis_type=analysis_type,
                    analysis_date=datetime.now(),
                    content=content,
                    sentiment_score=sentiment_score,
                    confidence_score=confidence_score,
                    metadata=metadata
                )
            except Exception as e:
                logger.error(f"Failed to store market analysis: {e}")
    
    async def get_similar_decisions(self, reasoning: str, ticker: str = None, limit: int = 5):
        """Get similar trading decisions from vector database"""
        if not self.vector_db:
            await self.initialize_vector_db()
        
        if self.vector_db:
            try:
                return await self.vector_db.get_similar_trading_decisions(
                    query=reasoning,
                    ticker=ticker,
                    limit=limit
                )
            except Exception as e:
                logger.error(f"Failed to get similar decisions: {e}")
        return []
    
    async def get_market_insights(self, query: str, ticker: str = None, analysis_type: str = None, limit: int = 5):
        """Get market analysis insights from vector database"""
        if not self.vector_db:
            await self.initialize_vector_db()
        
        if self.vector_db:
            try:
                return await self.vector_db.semantic_search_analysis(
                    query=query,
                    ticker=ticker,
                    analysis_type=analysis_type,
                    limit=limit
                )
            except Exception as e:
                logger.error(f"Failed to get market insights: {e}")
        return []
    
    def get_all_memory_summaries(self) -> Dict[str, Dict[str, Any]]:
        """Get summaries of all memory types"""
        summaries = {}
        for memory_type, memory in self.memories.items():
            summaries[memory_type] = {
                "memory_type": memory_type,
                "collection_count": memory.situation_collection.count(),
                "name": memory.name
            }
        return summaries

if __name__ == "__main__":
    # Example usage with enhanced functionality
    import asyncio
    
    async def main():
        config = {
            "backend_url": "https://api.openai.com/v1",
            "use_vector_db": True
        }
        
        # Create enhanced memory manager
        manager = EnhancedFinancialMemoryManager(config)
        await manager.initialize_vector_db()
        
        # Example trading decision storage
        await manager.store_trading_decision(
            ticker="AAPL",
            decision="BUY",
            confidence=0.85,
            reasoning="Strong earnings report and positive market sentiment",
            market_data={"price": 150.0, "volume": 1000000}
        )
        
        # Example market analysis storage
        await manager.store_market_analysis(
            ticker="AAPL",
            analysis_type="fundamental",
            content="Apple shows strong financial performance with increasing revenue and profit margins",
            sentiment_score=0.8,
            confidence_score=0.9
        )
        
        # Get similar decisions
        similar_decisions = await manager.get_similar_decisions(
            "Strong earnings and positive sentiment",
            ticker="AAPL"
        )
        
        print(f"Found {len(similar_decisions)} similar decisions")
        for decision in similar_decisions:
            print(f"Decision: {decision['decision']}, Confidence: {decision['confidence']}")
    
    # Run example if this file is executed directly
    # asyncio.run(main())
