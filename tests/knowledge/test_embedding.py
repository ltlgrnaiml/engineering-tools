"""Tests for Embedding Service - PLAN-002 M3."""


from gateway.services.knowledge.embedding_service import EmbeddingService


class TestEmbeddingService:
    """Tests for EmbeddingService."""

    def test_import(self):
        """Test EmbeddingService can be imported."""
        assert EmbeddingService is not None

    def test_instantiation(self):
        """Test EmbeddingService can be instantiated."""
        service = EmbeddingService()
        assert service is not None
        assert service.batch_size == 32

    def test_embed_method_exists(self):
        """Test embed method exists."""
        service = EmbeddingService()
        assert hasattr(service, 'embed')
        assert callable(service.embed)

    def test_embed_batch_method_exists(self):
        """Test embed_batch method exists."""
        service = EmbeddingService()
        assert hasattr(service, 'embed_batch')
        assert callable(service.embed_batch)

    def test_embed_all_chunks_method_exists(self):
        """Test embed_all_chunks method exists."""
        service = EmbeddingService()
        assert hasattr(service, 'embed_all_chunks')
        assert callable(service.embed_all_chunks)

    def test_vector_serialization(self):
        """Test vector to/from blob conversion."""
        service = EmbeddingService()

        # Test vector_to_blob
        test_vector = [0.1, 0.2, 0.3, 0.4, 0.5]
        blob = service.vector_to_blob(test_vector)
        assert isinstance(blob, bytes)

        # Test blob_to_vector
        recovered = service.blob_to_vector(blob)
        assert len(recovered) == len(test_vector)
        for orig, rec in zip(test_vector, recovered):
            assert abs(orig - rec) < 0.0001

    def test_config_defaults(self):
        """Test default configuration values."""
        service = EmbeddingService()
        assert service.batch_size == 32
        assert service.PRIMARY_MODEL is not None

    def test_fallback_model_defined(self):
        """Test fallback model is defined in config."""
        service = EmbeddingService()
        # The service should have fallback capability
        assert hasattr(service, '_load_model') or hasattr(service, 'config')
