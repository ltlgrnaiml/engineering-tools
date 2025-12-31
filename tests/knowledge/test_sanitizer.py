"""Tests for PII Sanitizer - PLAN-002 M3."""

import pytest

from gateway.services.knowledge.sanitizer import Sanitizer, SanitizationResult


class TestSanitizer:
    """Tests for Sanitizer."""

    @pytest.fixture
    def sanitizer(self):
        return Sanitizer()

    def test_sanitize_email(self, sanitizer):
        """Test email redaction."""
        result = sanitizer.sanitize("Contact me at john@company.com please")
        assert '[EMAIL]' in result.content
        assert 'john@company.com' not in result.content
        assert result.redaction_count == 1

    def test_sanitize_api_key(self, sanitizer):
        """Test API key redaction."""
        result = sanitizer.sanitize("Key: sk-abc123def456ghi789jkl012mno345")
        assert '[API_KEY]' in result.content
        assert 'sk-abc123' not in result.content

    def test_sanitize_aws_key(self, sanitizer):
        """Test AWS key redaction."""
        result = sanitizer.sanitize("AWS: AKIAIOSFODNN7EXAMPLE")
        assert '[AWS_KEY]' in result.content
        assert 'AKIAIOSFODNN7EXAMPLE' not in result.content

    def test_sanitize_phone(self, sanitizer):
        """Test phone number redaction."""
        result = sanitizer.sanitize("Call me at 555-123-4567")
        assert '[PHONE]' in result.content
        assert '555-123-4567' not in result.content

    def test_sanitize_ssn(self, sanitizer):
        """Test SSN redaction."""
        result = sanitizer.sanitize("SSN: 123-45-6789")
        assert '[SSN]' in result.content
        assert '123-45-6789' not in result.content

    def test_sanitize_credit_card(self, sanitizer):
        """Test credit card redaction."""
        result = sanitizer.sanitize("Card: 1234-5678-9012-3456")
        assert '[CARD]' in result.content
        assert '1234-5678-9012-3456' not in result.content

    def test_sanitize_ip_address(self, sanitizer):
        """Test IP address redaction."""
        result = sanitizer.sanitize("Server at 192.168.1.100")
        assert '[IP]' in result.content
        assert '192.168.1.100' not in result.content

    def test_sanitize_bearer_token(self, sanitizer):
        """Test bearer token redaction."""
        result = sanitizer.sanitize("Auth: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9")
        assert '[BEARER_TOKEN]' in result.content

    def test_sanitize_multiple(self, sanitizer):
        """Test multiple redactions in single text."""
        text = "Email: user@corp.com, API: sk-test12345678901234567890, Phone: 555-555-5555"
        result = sanitizer.sanitize(text)
        assert '[EMAIL]' in result.content
        assert '[API_KEY]' in result.content
        assert '[PHONE]' in result.content
        assert result.redaction_count >= 3

    def test_allowlist_preserved(self, sanitizer):
        """Test that allowlisted items are not redacted."""
        # localhost and test@test.com should be in allowlist
        result = sanitizer.sanitize("Host: localhost, Email: test@test.com")
        # These should not be fully redacted
        assert 'localhost' in result.content or result.redaction_count == 0

    def test_sanitize_for_llm(self, sanitizer):
        """Test convenience method returns string."""
        result = sanitizer.sanitize_for_llm("Email: user@corp.com")
        assert isinstance(result, str)
        assert '[EMAIL]' in result

    def test_sanitization_result_structure(self, sanitizer):
        """Test SanitizationResult has correct structure."""
        result = sanitizer.sanitize("Test email: test@example.com")
        assert hasattr(result, 'content')
        assert hasattr(result, 'redactions')
        assert hasattr(result, 'redaction_count')
        assert isinstance(result.redactions, list)

    def test_no_false_positives_on_clean_text(self, sanitizer):
        """Test clean text has no redactions."""
        result = sanitizer.sanitize("This is a clean sentence with no sensitive data.")
        assert result.redaction_count == 0
        assert result.content == "This is a clean sentence with no sensitive data."

    def test_custom_patterns(self):
        """Test custom pattern support."""
        custom = {
            'custom_id': (r'CID-\d{6}', '[CUSTOM_ID]')
        }
        sanitizer = Sanitizer(extra_patterns=custom)
        result = sanitizer.sanitize("Customer: CID-123456")
        assert '[CUSTOM_ID]' in result.content
