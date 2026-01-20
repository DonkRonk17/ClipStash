#!/usr/bin/env python3
"""
Research Assistant Plugin - Research Assistant
Priority: HIGH

Detects research-worthy content and fetches academic papers:
- Detects research-worthy content (academic terms, citations, etc.)
- Searches arXiv API for related papers
- Searches Semantic Scholar API for papers
- Fetches paper metadata (authors, abstract, citations)
- Adds paper recommendations to enrichments
"""

import re
import logging
from typing import Dict, Any, Optional, List

from clipstash_core import ClipStashPlugin, ClipItem, PluginPriority

logger = logging.getLogger(__name__)


class ResearchAssistantPlugin(ClipStashPlugin):
    """
    Assists with research by finding related academic papers.
    """
    
    # Academic keywords that trigger research
    RESEARCH_KEYWORDS = [
        'paper', 'research', 'study', 'analysis', 'experiment', 'methodology',
        'algorithm', 'model', 'dataset', 'neural', 'network', 'machine learning',
        'artificial intelligence', 'deep learning', 'optimization', 'statistical',
        'hypothesis', 'theorem', 'proof', 'arxiv', 'doi', 'journal', 'conference',
        'proceedings', 'citation', 'abstract', 'introduction', 'conclusion'
    ]
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self._name = "ResearchAssistant"
        self._priority = PluginPriority.HIGH
        self._version = "1.0.0"
        
        # Configuration
        self.auto_search = config.get('auto_search', True) if config else True
        self.max_results = config.get('max_results', 3) if config else 3
        self.min_relevance_score = config.get('min_relevance_score', 0.3) if config else 0.3
        self.search_timeout = config.get('search_timeout', 5.0) if config else 5.0
    
    async def initialize(self) -> bool:
        """Initialize the research assistant."""
        logger.info(f"{self.name} initialized")
        return True
    
    async def process_clip(self, clip: ClipItem, context: Dict[str, Any]) -> ClipItem:
        """
        Detect research-worthy content and fetch papers.
        
        Args:
            clip: Clipboard item
            context: Current context
        
        Returns:
            Clip with research data added
        """
        content = clip.content.lower()
        
        # Check if content is research-worthy
        relevance_score = self._calculate_relevance(content)
        
        if relevance_score >= self.min_relevance_score:
            logger.debug(f"Research-worthy content detected (score: {relevance_score:.2f})")
            
            # Extract search query
            query = self._extract_search_query(clip.content)
            
            papers = []
            
            # Search arXiv
            if self.auto_search:
                arxiv_papers = await self._search_arxiv(query)
                papers.extend(arxiv_papers)
            
            # Search Semantic Scholar
            if self.auto_search and len(papers) < self.max_results:
                scholar_papers = await self._search_semantic_scholar(query)
                papers.extend(scholar_papers)
            
            # Limit results
            papers = papers[:self.max_results]
            
            if papers:
                clip.metadata.enrichments['research'] = {
                    'relevance_score': relevance_score,
                    'query': query,
                    'papers': papers,
                    'count': len(papers)
                }
                clip.metadata.tags.append('research')
                logger.info(f"Found {len(papers)} related papers")
        
        return clip
    
    def _calculate_relevance(self, content: str) -> float:
        """
        Calculate research relevance score.
        
        Args:
            content: Content to analyze
        
        Returns:
            Relevance score (0.0 to 1.0)
        """
        score = 0.0
        content_lower = content.lower()
        
        # Check for research keywords
        keyword_count = sum(1 for keyword in self.RESEARCH_KEYWORDS if keyword in content_lower)
        keyword_score = min(keyword_count / 5.0, 1.0)  # Max at 5 keywords
        score += keyword_score * 0.5
        
        # Check for DOI
        if re.search(r'10\.\d{4,}/[^\s]+', content):
            score += 0.3
        
        # Check for arXiv ID
        if re.search(r'arXiv:\d{4}\.\d{4,}', content, re.IGNORECASE):
            score += 0.3
        
        # Check for academic structure (abstract, introduction, etc.)
        structure_keywords = ['abstract', 'introduction', 'methodology', 'results', 'conclusion', 'references']
        structure_count = sum(1 for keyword in structure_keywords if keyword in content_lower)
        if structure_count >= 2:
            score += 0.2
        
        return min(score, 1.0)
    
    def _extract_search_query(self, content: str) -> str:
        """
        Extract search query from content.
        
        Args:
            content: Content to extract from
        
        Returns:
            Search query string
        """
        # Try to find DOI
        doi_match = re.search(r'10\.\d{4,}/[^\s]+', content)
        if doi_match:
            return doi_match.group(0)
        
        # Try to find arXiv ID
        arxiv_match = re.search(r'arXiv:(\d{4}\.\d{4,})', content, re.IGNORECASE)
        if arxiv_match:
            return arxiv_match.group(1)
        
        # Extract first sentence or first 100 chars
        sentences = content.split('.')
        if sentences:
            query = sentences[0].strip()
            if len(query) > 100:
                query = query[:100]
            return query
        
        return content[:100].strip()
    
    async def _search_arxiv(self, query: str) -> List[Dict[str, Any]]:
        """
        Search arXiv for papers.
        
        Args:
            query: Search query
        
        Returns:
            List of paper metadata
        """
        papers = []
        
        try:
            import aiohttp
            import xml.etree.ElementTree as ET
            
            # arXiv API endpoint
            url = "http://export.arxiv.org/api/query"
            params = {
                'search_query': f'all:{query}',
                'start': 0,
                'max_results': self.max_results
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=self.search_timeout)) as response:
                    if response.status == 200:
                        xml_data = await response.text()
                        root = ET.fromstring(xml_data)
                        
                        # Parse entries
                        ns = {'atom': 'http://www.w3.org/2005/Atom'}
                        for entry in root.findall('atom:entry', ns):
                            paper = {}
                            
                            # Title
                            title = entry.find('atom:title', ns)
                            if title is not None:
                                paper['title'] = title.text.strip()
                            
                            # Authors
                            authors = []
                            for author in entry.findall('atom:author', ns):
                                name = author.find('atom:name', ns)
                                if name is not None:
                                    authors.append(name.text)
                            paper['authors'] = authors
                            
                            # Abstract
                            summary = entry.find('atom:summary', ns)
                            if summary is not None:
                                paper['abstract'] = summary.text.strip()[:300] + "..."
                            
                            # Link
                            link = entry.find('atom:id', ns)
                            if link is not None:
                                paper['url'] = link.text
                            
                            # Published date
                            published = entry.find('atom:published', ns)
                            if published is not None:
                                paper['published'] = published.text[:10]
                            
                            paper['source'] = 'arXiv'
                            papers.append(paper)
                        
                        logger.debug(f"Found {len(papers)} papers on arXiv")
        
        except ImportError:
            logger.debug("aiohttp not available for arXiv search")
        except Exception as e:
            logger.debug(f"Error searching arXiv: {e}")
        
        return papers
    
    async def _search_semantic_scholar(self, query: str) -> List[Dict[str, Any]]:
        """
        Search Semantic Scholar for papers.
        
        Args:
            query: Search query
        
        Returns:
            List of paper metadata
        """
        papers = []
        
        try:
            import aiohttp
            
            # Semantic Scholar API endpoint
            url = "https://api.semanticscholar.org/graph/v1/paper/search"
            params = {
                'query': query,
                'limit': self.max_results,
                'fields': 'title,authors,abstract,year,url,citationCount'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=self.search_timeout)) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        for item in data.get('data', []):
                            paper = {
                                'title': item.get('title', 'No title'),
                                'authors': [a.get('name') for a in item.get('authors', [])],
                                'abstract': (item.get('abstract', '')[:300] + "...") if item.get('abstract') else None,
                                'year': item.get('year'),
                                'url': item.get('url'),
                                'citations': item.get('citationCount', 0),
                                'source': 'Semantic Scholar'
                            }
                            papers.append(paper)
                        
                        logger.debug(f"Found {len(papers)} papers on Semantic Scholar")
        
        except ImportError:
            logger.debug("aiohttp not available for Semantic Scholar search")
        except Exception as e:
            logger.debug(f"Error searching Semantic Scholar: {e}")
        
        return papers
    
    async def shutdown(self):
        """Cleanup on shutdown."""
        logger.info(f"{self.name} shutdown")
