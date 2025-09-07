import os
import asyncio
import asyncpg
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import json
import logging
from contextlib import asynccontextmanager
from sentence_transformers import SentenceTransformer
import hashlib

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NeonVectorDB:
    """
    Neon PostgreSQL Vector Database for Financial Agent
    Handles vector storage, retrieval, and semantic search for financial data
    """
    
    def __init__(self, connection_string: str = None):
        """
        Initialize Neon Vector Database connection
        
        Args:
            connection_string: PostgreSQL connection string for Neon
        """
        self.connection_string = connection_string or "postgresql://neondb_owner:npg_kpwFaiV39RsI@ep-misty-hall-adhj1gjs-pooler.c-2.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
        self.pool = None
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')  # Lightweight embedding model
        self.embedding_dim = 384  # Dimension of all-MiniLM-L6-v2
        
    async def initialize(self):
        """Initialize database connection pool and create tables"""
        try:
            self.pool = await asyncpg.create_pool(
                self.connection_string,
                min_size=1,
                max_size=10,
                command_timeout=60
            )
            await self._create_tables()
            logger.info("Neon Vector Database initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Neon Vector Database: {e}")
            raise
    
    async def _create_tables(self):
        """Create necessary tables for vector storage"""
        async with self.pool.acquire() as conn:
            # Enable pgvector extension
            await conn.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            
            # Create financial_memories table for storing agent memories
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS financial_memories (
                    id SERIAL PRIMARY KEY,
                    memory_type VARCHAR(50) NOT NULL,
                    ticker VARCHAR(10),
                    content TEXT NOT NULL,
                    embedding vector(384),
                    metadata JSONB,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
            """)
            
            # Create market_analysis table for storing analysis results
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS market_analysis (
                    id SERIAL PRIMARY KEY,
                    ticker VARCHAR(10) NOT NULL,
                    analysis_type VARCHAR(50) NOT NULL,
                    analysis_date DATE NOT NULL,
                    content TEXT NOT NULL,
                    embedding vector(384),
                    sentiment_score FLOAT,
                    confidence_score FLOAT,
                    metadata JSONB,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
            """)
            
            # Create trading_decisions table for storing trading decisions
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS trading_decisions (
                    id SERIAL PRIMARY KEY,
                    ticker VARCHAR(10) NOT NULL,
                    decision_date DATE NOT NULL,
                    decision VARCHAR(20) NOT NULL,
                    confidence FLOAT,
                    reasoning TEXT,
                    embedding vector(384),
                    market_data JSONB,
                    performance_result FLOAT,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
            """)
            
            # Create knowledge_base table for general financial knowledge
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS knowledge_base (
                    id SERIAL PRIMARY KEY,
                    category VARCHAR(50) NOT NULL,
                    title VARCHAR(200) NOT NULL,
                    content TEXT NOT NULL,
                    embedding vector(384),
                    tags TEXT[],
                    relevance_score FLOAT DEFAULT 1.0,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
            """)
            
            # Create indexes for better performance
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_financial_memories_ticker ON financial_memories(ticker);")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_financial_memories_type ON financial_memories(memory_type);")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_market_analysis_ticker ON market_analysis(ticker);")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_market_analysis_date ON market_analysis(analysis_date);")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_trading_decisions_ticker ON trading_decisions(ticker);")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_trading_decisions_date ON trading_decisions(decision_date);")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_knowledge_base_category ON knowledge_base(category);")
            
            logger.info("Database tables created successfully")
    
    def _generate_embedding(self, text: str) -> List[float]:
        """Generate embedding vector for text"""
        try:
            embedding = self.embedding_model.encode(text, normalize_embeddings=True)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            return [0.0] * self.embedding_dim
    
    def _generate_content_hash(self, content: str) -> str:
        """Generate hash for content to avoid duplicates"""
        return hashlib.md5(content.encode()).hexdigest()
    
    async def store_financial_memory(
        self, 
        memory_type: str, 
        content: str, 
        ticker: str = None,
        metadata: Dict = None
    ) -> int:
        """
        Store financial memory with vector embedding
        
        Args:
            memory_type: Type of memory (bull_memory, bear_memory, trader_memory, etc.)
            content: Memory content
            ticker: Stock ticker (optional)
            metadata: Additional metadata
            
        Returns:
            int: ID of stored memory
        """
        try:
            embedding = self._generate_embedding(content)
            
            async with self.pool.acquire() as conn:
                result = await conn.fetchrow("""
                    INSERT INTO financial_memories (memory_type, ticker, content, embedding, metadata)
                    VALUES ($1, $2, $3, $4::vector, $5)
                    RETURNING id;
                """, memory_type, ticker, content, embedding, json.dumps(metadata or {}))
                
                logger.info(f"Stored financial memory with ID: {result['id']}")
                return result['id']
                
        except Exception as e:
            logger.error(f"Failed to store financial memory: {e}")
            raise
    
    async def store_market_analysis(
        self,
        ticker: str,
        analysis_type: str,
        analysis_date: datetime,
        content: str,
        sentiment_score: float = None,
        confidence_score: float = None,
        metadata: Dict = None
    ) -> int:
        """Store market analysis with vector embedding"""
        try:
            embedding = self._generate_embedding(content)
            
            async with self.pool.acquire() as conn:
                result = await conn.fetchrow("""
                    INSERT INTO market_analysis 
                    (ticker, analysis_type, analysis_date, content, embedding, sentiment_score, confidence_score, metadata)
                    VALUES ($1, $2, $3, $4, $5::vector, $6, $7, $8)
                    RETURNING id;
                """, ticker, analysis_type, analysis_date.date(), content, embedding, 
                sentiment_score, confidence_score, json.dumps(metadata or {}))
                
                logger.info(f"Stored market analysis with ID: {result['id']}")
                return result['id']
                
        except Exception as e:
            logger.error(f"Failed to store market analysis: {e}")
            raise
    
    async def store_trading_decision(
        self,
        ticker: str,
        decision_date: datetime,
        decision: str,
        confidence: float,
        reasoning: str,
        market_data: Dict = None,
        performance_result: float = None
    ) -> int:
        """Store trading decision with vector embedding"""
        try:
            embedding = self._generate_embedding(reasoning)
            
            async with self.pool.acquire() as conn:
                result = await conn.fetchrow("""
                    INSERT INTO trading_decisions 
                    (ticker, decision_date, decision, confidence, reasoning, embedding, market_data, performance_result)
                    VALUES ($1, $2, $3, $4, $5, $6::vector, $7, $8)
                    RETURNING id;
                """, ticker, decision_date.date(), decision, confidence, reasoning, 
                embedding, json.dumps(market_data or {}), performance_result)
                
                logger.info(f"Stored trading decision with ID: {result['id']}")
                return result['id']
                
        except Exception as e:
            logger.error(f"Failed to store trading decision: {e}")
            raise
    
    async def semantic_search_memories(
        self,
        query: str,
        memory_type: str = None,
        ticker: str = None,
        limit: int = 5
    ) -> List[Dict]:
        """
        Perform semantic search on financial memories
        
        Args:
            query: Search query
            memory_type: Filter by memory type
            ticker: Filter by ticker
            limit: Maximum number of results
            
        Returns:
            List of relevant memories with similarity scores
        """
        try:
            query_embedding = self._generate_embedding(query)
            
            # Build query with optional filters
            where_clauses = []
            params = [query_embedding, limit]
            param_count = 2
            
            if memory_type:
                param_count += 1
                where_clauses.append(f"memory_type = ${param_count}")
                params.append(memory_type)
            
            if ticker:
                param_count += 1
                where_clauses.append(f"ticker = ${param_count}")
                params.append(ticker)
            
            where_clause = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""
            
            async with self.pool.acquire() as conn:
                results = await conn.fetch(f"""
                    SELECT id, memory_type, ticker, content, metadata, created_at,
                           1 - (embedding <=> $1) as similarity
                    FROM financial_memories
                    {where_clause}
                    ORDER BY embedding <=> $1
                    LIMIT $2;
                """, *params)
                
                return [dict(row) for row in results]
                
        except Exception as e:
            logger.error(f"Failed to perform semantic search: {e}")
            return []
    
    async def semantic_search_analysis(
        self,
        query: str,
        ticker: str = None,
        analysis_type: str = None,
        days_back: int = 30,
        limit: int = 5
    ) -> List[Dict]:
        """Perform semantic search on market analysis"""
        try:
            query_embedding = self._generate_embedding(query)
            
            # Build query with optional filters
            where_clauses = ["analysis_date >= CURRENT_DATE - INTERVAL '%s days'" % days_back]
            params = [query_embedding, limit]
            param_count = 2
            
            if ticker:
                param_count += 1
                where_clauses.append(f"ticker = ${param_count}")
                params.append(ticker)
            
            if analysis_type:
                param_count += 1
                where_clauses.append(f"analysis_type = ${param_count}")
                params.append(analysis_type)
            
            where_clause = "WHERE " + " AND ".join(where_clauses)
            
            async with self.pool.acquire() as conn:
                results = await conn.fetch(f"""
                    SELECT id, ticker, analysis_type, analysis_date, content, 
                           sentiment_score, confidence_score, metadata,
                           1 - (embedding <=> $1) as similarity
                    FROM market_analysis
                    {where_clause}
                    ORDER BY embedding <=> $1
                    LIMIT $2;
                """, *params)
                
                return [dict(row) for row in results]
                
        except Exception as e:
            logger.error(f"Failed to search market analysis: {e}")
            return []
    
    async def get_similar_trading_decisions(
        self,
        query: str,
        ticker: str = None,
        days_back: int = 90,
        limit: int = 10
    ) -> List[Dict]:
        """Get similar trading decisions based on reasoning"""
        try:
            query_embedding = self._generate_embedding(query)
            
            where_clauses = ["decision_date >= CURRENT_DATE - INTERVAL '%s days'" % days_back]
            params = [query_embedding, limit]
            param_count = 2
            
            if ticker:
                param_count += 1
                where_clauses.append(f"ticker = ${param_count}")
                params.append(ticker)
            
            where_clause = "WHERE " + " AND ".join(where_clauses)
            
            async with self.pool.acquire() as conn:
                results = await conn.fetch(f"""
                    SELECT id, ticker, decision_date, decision, confidence, reasoning,
                           performance_result, market_data,
                           1 - (embedding <=> $1) as similarity
                    FROM trading_decisions
                    {where_clause}
                    ORDER BY embedding <=> $1
                    LIMIT $2;
                """, *params)
                
                return [dict(row) for row in results]
                
        except Exception as e:
            logger.error(f"Failed to search trading decisions: {e}")
            return []
    
    async def update_performance_result(self, decision_id: int, performance_result: float):
        """Update performance result for a trading decision"""
        try:
            async with self.pool.acquire() as conn:
                await conn.execute("""
                    UPDATE trading_decisions 
                    SET performance_result = $1, updated_at = NOW()
                    WHERE id = $2;
                """, performance_result, decision_id)
                
                logger.info(f"Updated performance result for decision {decision_id}")
                
        except Exception as e:
            logger.error(f"Failed to update performance result: {e}")
            raise
    
    async def get_ticker_statistics(self, ticker: str, days_back: int = 30) -> Dict:
        """Get statistics for a specific ticker"""
        try:
            async with self.pool.acquire() as conn:
                stats = await conn.fetchrow("""
                    SELECT 
                        COUNT(*) as total_decisions,
                        AVG(confidence) as avg_confidence,
                        AVG(performance_result) as avg_performance,
                        COUNT(CASE WHEN decision = 'BUY' THEN 1 END) as buy_count,
                        COUNT(CASE WHEN decision = 'SELL' THEN 1 END) as sell_count,
                        COUNT(CASE WHEN decision = 'HOLD' THEN 1 END) as hold_count
                    FROM trading_decisions
                    WHERE ticker = $1 AND decision_date >= CURRENT_DATE - INTERVAL '%s days'
                """ % days_back, ticker)
                
                return dict(stats) if stats else {}
                
        except Exception as e:
            logger.error(f"Failed to get ticker statistics: {e}")
            return {}
    
    async def close(self):
        """Close database connection pool"""
        if self.pool:
            await self.pool.close()
            logger.info("Database connection pool closed")

# Global instance for easy access
neon_db = NeonVectorDB()

async def initialize_neon_db():
    """Initialize the global Neon DB instance"""
    await neon_db.initialize()

async def get_neon_db() -> NeonVectorDB:
    """Get the global Neon DB instance"""
    if not neon_db.pool:
        await initialize_neon_db()
    return neon_db
