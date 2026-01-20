#!/usr/bin/env python3
"""
Knowledge Graph Plugin - Knowledge Graph Builder
Priority: MEDIUM

Builds knowledge graph from clipboard content:
- Uses spaCy for NLP entity extraction
- Builds relationships between clips
- Uses networkx for graph operations
- Calculates similarity using sentence-transformers
- Stores relationships in metadata
"""

import logging
from typing import Dict, Any, Optional, List, Tuple

from clipstash_core import ClipStashPlugin, ClipItem, PluginPriority

logger = logging.getLogger(__name__)


class KnowledgeGraphPlugin(ClipStashPlugin):
    """
    Builds knowledge graph from clipboard content.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self._name = "KnowledgeGraph"
        self._priority = PluginPriority.MEDIUM
        self._version = "1.0.0"
        
        # Configuration
        self.min_similarity = config.get('min_similarity', 0.5) if config else 0.5
        self.max_relationships = config.get('max_relationships', 10) if config else 10
        self.use_spacy = config.get('use_spacy', True) if config else True
        self.use_transformers = config.get('use_transformers', False) if config else False
        
        # State
        self.nlp = None
        self.similarity_model = None
        self.graph = None
        self.clip_embeddings = {}
    
    async def initialize(self) -> bool:
        """Initialize the knowledge graph builder."""
        # Initialize spaCy
        if self.use_spacy:
            try:
                import spacy
                # Try to load English model
                try:
                    self.nlp = spacy.load('en_core_web_sm')
                    logger.info("Loaded spaCy model: en_core_web_sm")
                except OSError:
                    logger.warning("spaCy model not found. Run: python -m spacy download en_core_web_sm")
                    self.use_spacy = False
            except ImportError:
                logger.warning("spaCy not available for entity extraction")
                self.use_spacy = False
        
        # Initialize sentence transformers
        if self.use_transformers:
            try:
                from sentence_transformers import SentenceTransformer
                self.similarity_model = SentenceTransformer('all-MiniLM-L6-v2')
                logger.info("Loaded sentence transformer model")
            except ImportError:
                logger.warning("sentence-transformers not available")
                self.use_transformers = False
        
        # Initialize networkx graph
        try:
            import networkx as nx
            self.graph = nx.DiGraph()
            logger.info("Initialized knowledge graph")
        except ImportError:
            logger.warning("networkx not available for graph operations")
        
        logger.info(f"{self.name} initialized")
        return True
    
    async def process_clip(self, clip: ClipItem, context: Dict[str, Any]) -> ClipItem:
        """
        Extract entities and build relationships.
        
        Args:
            clip: Clipboard item
            context: Current context
        
        Returns:
            Clip with knowledge graph data
        """
        # Extract entities
        entities = await self._extract_entities(clip.content)
        
        if entities:
            clip.metadata.enrichments['entities'] = entities
            logger.debug(f"Extracted {len(entities)} entities")
        
        # Calculate similarity to existing clips (would need access to history)
        # For now, just prepare the embedding
        if self.use_transformers and self.similarity_model:
            try:
                embedding = self.similarity_model.encode(clip.content)
                self.clip_embeddings[clip.hash] = embedding
                clip.metadata.enrichments['embedding_available'] = True
            except Exception as e:
                logger.debug(f"Error computing embedding: {e}")
        
        # Add to graph
        if self.graph is not None:
            self._add_to_graph(clip, entities)
        
        return clip
    
    async def _extract_entities(self, text: str) -> List[Dict[str, str]]:
        """
        Extract named entities from text.
        
        Args:
            text: Text to analyze
        
        Returns:
            List of entities
        """
        entities = []
        
        if self.use_spacy and self.nlp:
            try:
                doc = self.nlp(text[:1000])  # Limit to first 1000 chars
                
                for ent in doc.ents:
                    entities.append({
                        'text': ent.text,
                        'label': ent.label_,
                        'start': ent.start_char,
                        'end': ent.end_char
                    })
                
                # Limit entities
                entities = entities[:20]
            
            except Exception as e:
                logger.debug(f"Error extracting entities: {e}")
        else:
            # Fallback: simple pattern-based extraction
            entities = self._extract_entities_simple(text)
        
        return entities
    
    def _extract_entities_simple(self, text: str) -> List[Dict[str, str]]:
        """Simple pattern-based entity extraction."""
        import re
        
        entities = []
        
        # Extract URLs
        urls = re.findall(r'https?://[^\s]+', text)
        for url in urls[:5]:
            entities.append({'text': url, 'label': 'URL', 'start': 0, 'end': 0})
        
        # Extract email addresses
        emails = re.findall(r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b', text)
        for email in emails[:5]:
            entities.append({'text': email, 'label': 'EMAIL', 'start': 0, 'end': 0})
        
        # Extract potential names (capitalized words)
        names = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b', text)
        for name in names[:5]:
            entities.append({'text': name, 'label': 'PERSON', 'start': 0, 'end': 0})
        
        # Extract dates
        dates = re.findall(r'\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b', text)
        for date in dates[:3]:
            entities.append({'text': date, 'label': 'DATE', 'start': 0, 'end': 0})
        
        return entities
    
    def _add_to_graph(self, clip: ClipItem, entities: List[Dict[str, str]]):
        """
        Add clip and entities to knowledge graph.
        
        Args:
            clip: Clip to add
            entities: Extracted entities
        """
        try:
            # Add clip node
            self.graph.add_node(
                clip.hash,
                content_preview=clip.preview(50),
                timestamp=clip.timestamp,
                type='clip'
            )
            
            # Add entity nodes and relationships
            for entity in entities:
                entity_id = f"{entity['label']}:{entity['text']}"
                
                # Add entity node
                self.graph.add_node(
                    entity_id,
                    text=entity['text'],
                    label=entity['label'],
                    type='entity'
                )
                
                # Add relationship
                self.graph.add_edge(clip.hash, entity_id, relation='contains')
            
            logger.debug(f"Added clip to graph: {clip.hash} with {len(entities)} entities")
        
        except Exception as e:
            logger.debug(f"Error adding to graph: {e}")
    
    def calculate_similarity(self, clip1: ClipItem, clip2: ClipItem) -> float:
        """
        Calculate similarity between two clips.
        
        Args:
            clip1: First clip
            clip2: Second clip
        
        Returns:
            Similarity score (0.0 to 1.0)
        """
        if self.use_transformers and self.similarity_model:
            try:
                # Get or compute embeddings
                if clip1.hash not in self.clip_embeddings:
                    self.clip_embeddings[clip1.hash] = self.similarity_model.encode(clip1.content)
                
                if clip2.hash not in self.clip_embeddings:
                    self.clip_embeddings[clip2.hash] = self.similarity_model.encode(clip2.content)
                
                # Compute cosine similarity
                from sklearn.metrics.pairwise import cosine_similarity
                import numpy as np
                
                emb1 = self.clip_embeddings[clip1.hash].reshape(1, -1)
                emb2 = self.clip_embeddings[clip2.hash].reshape(1, -1)
                
                similarity = cosine_similarity(emb1, emb2)[0][0]
                return float(similarity)
            
            except Exception as e:
                logger.debug(f"Error calculating similarity: {e}")
        
        # Fallback: simple text-based similarity
        return self._simple_similarity(clip1.content, clip2.content)
    
    def _simple_similarity(self, text1: str, text2: str) -> float:
        """Simple Jaccard similarity."""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0
    
    def find_related_clips(self, clip: ClipItem, all_clips: List[ClipItem]) -> List[Tuple[ClipItem, float]]:
        """
        Find clips related to given clip.
        
        Args:
            clip: Reference clip
            all_clips: All available clips
        
        Returns:
            List of (clip, similarity_score) tuples
        """
        related = []
        
        for other_clip in all_clips:
            if other_clip.hash == clip.hash:
                continue
            
            similarity = self.calculate_similarity(clip, other_clip)
            
            if similarity >= self.min_similarity:
                related.append((other_clip, similarity))
        
        # Sort by similarity
        related.sort(key=lambda x: x[1], reverse=True)
        
        # Limit results
        return related[:self.max_relationships]
    
    async def on_search(self, query: str, results: List[ClipItem]) -> List[ClipItem]:
        """
        Enhance search with knowledge graph relationships.
        
        Args:
            query: Search query
            results: Current results
        
        Returns:
            Enhanced results
        """
        # Could expand search using graph relationships
        # For now, just return original results
        return results
    
    def get_graph_stats(self) -> Dict[str, Any]:
        """Get knowledge graph statistics."""
        if self.graph is None:
            return {}
        
        return {
            'nodes': self.graph.number_of_nodes(),
            'edges': self.graph.number_of_edges(),
            'embeddings': len(self.clip_embeddings)
        }
    
    async def shutdown(self):
        """Cleanup on shutdown."""
        logger.info(f"{self.name} shutdown")
