#!/usr/bin/env python3
"""
Test Suite for ClipMetadata
"""

import pytest
from clipstash_core import ClipMetadata


class TestClipMetadataSerialization:
    """Test metadata serialization and deserialization."""
    
    def test_empty_metadata_serialization(self):
        """Test serializing empty metadata."""
        metadata = ClipMetadata()
        data = metadata.to_dict()
        
        restored = ClipMetadata.from_dict(data)
        
        assert restored.enrichments == {}
        assert restored.predictions == {}
        assert restored.security_flags == []
        assert restored.tags == []
    
    def test_complex_metadata_serialization(self):
        """Test serializing complex metadata."""
        metadata = ClipMetadata()
        metadata.enrichments = {
            'content': {
                'type': 'code',
                'language': 'python',
                'lines': 42
            },
            'security': {
                'risk_score': 0.2,
                'flags': []
            }
        }
        metadata.predictions = {
            'paste_likelihood': 0.8,
            'next_app': 'VSCode'
        }
        metadata.security_flags = ['api_key', 'token']
        metadata.relationships = ['clip123', 'clip456']
        metadata.tags = ['code', 'python', 'important']
        metadata.confidence_scores = {
            'paste': 0.85,
            'sentiment': 0.92
        }
        
        # Serialize
        data = metadata.to_dict()
        
        # Deserialize
        restored = ClipMetadata.from_dict(data)
        
        # Verify all fields
        assert restored.enrichments == metadata.enrichments
        assert restored.predictions == metadata.predictions
        assert restored.security_flags == metadata.security_flags
        assert restored.relationships == metadata.relationships
        assert restored.tags == metadata.tags
        assert restored.confidence_scores == metadata.confidence_scores
    
    def test_partial_metadata_deserialization(self):
        """Test deserializing partial metadata."""
        data = {
            'enrichments': {'test': 'value'},
            # Missing other fields
        }
        
        metadata = ClipMetadata.from_dict(data)
        
        assert metadata.enrichments == {'test': 'value'}
        assert metadata.predictions == {}
        assert metadata.security_flags == []
    
    def test_nested_structures(self):
        """Test deeply nested metadata structures."""
        metadata = ClipMetadata()
        metadata.enrichments = {
            'level1': {
                'level2': {
                    'level3': {
                        'value': 'deep'
                    }
                }
            }
        }
        
        data = metadata.to_dict()
        restored = ClipMetadata.from_dict(data)
        
        assert restored.enrichments['level1']['level2']['level3']['value'] == 'deep'
    
    def test_list_in_enrichments(self):
        """Test lists within enrichments."""
        metadata = ClipMetadata()
        metadata.enrichments = {
            'urls': ['http://example.com', 'http://test.com'],
            'entities': [
                {'type': 'PERSON', 'text': 'John Doe'},
                {'type': 'ORG', 'text': 'Acme Corp'}
            ]
        }
        
        data = metadata.to_dict()
        restored = ClipMetadata.from_dict(data)
        
        assert len(restored.enrichments['urls']) == 2
        assert len(restored.enrichments['entities']) == 2
        assert restored.enrichments['entities'][0]['text'] == 'John Doe'


class TestClipMetadataModification:
    """Test modifying metadata."""
    
    def test_add_enrichment(self):
        """Test adding enrichments."""
        metadata = ClipMetadata()
        metadata.enrichments['content_type'] = 'text'
        
        assert metadata.enrichments['content_type'] == 'text'
    
    def test_add_multiple_tags(self):
        """Test adding multiple tags."""
        metadata = ClipMetadata()
        metadata.tags.extend(['tag1', 'tag2', 'tag3'])
        
        assert len(metadata.tags) == 3
        assert 'tag2' in metadata.tags
    
    def test_update_confidence_scores(self):
        """Test updating confidence scores."""
        metadata = ClipMetadata()
        metadata.confidence_scores['prediction1'] = 0.9
        metadata.confidence_scores['prediction2'] = 0.7
        
        assert metadata.confidence_scores['prediction1'] == 0.9
        assert len(metadata.confidence_scores) == 2
    
    def test_modify_existing_enrichment(self):
        """Test modifying existing enrichments."""
        metadata = ClipMetadata()
        metadata.enrichments['count'] = 1
        metadata.enrichments['count'] += 1
        
        assert metadata.enrichments['count'] == 2
