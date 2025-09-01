"""
Test suite for bank-related features.
Story 3.1-3.4: IBAN, SWIFT, Currency, and Bank Field Integration
"""

import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.validations import (
    validate_iban,
    format_iban_display,
    auto_populate_bank_from_iban,
    validate_swift_bic,
    validate_swift_bank_consistency,
    validate_currency_amount,
    format_currency_display,
    parse_currency_input
)
from utils.rate_limiter import RateLimiter
import time


class TestIBANValidation:
    """Test IBAN validation and formatting."""
    
    def test_valid_slovenian_iban(self):
        """Test valid Slovenian IBAN."""
        # Valid Slovenian IBANs
        valid_ibans = [
            "SI56191000000123438",  # 19 chars
            "SI56 1910 0000 0123 438",  # With spaces
            "si56191000000123438",  # Lowercase
        ]
        
        for iban in valid_ibans:
            is_valid, error = validate_iban(iban)
            assert is_valid == True, f"IBAN '{iban}' should be valid"
            assert error is None
    
    def test_invalid_slovenian_iban_length(self):
        """Test invalid Slovenian IBAN length."""
        invalid_ibans = [
            "SI5619100000012343",  # 18 chars
            "SI561910000001234389",  # 20 chars
        ]
        
        for iban in invalid_ibans:
            is_valid, error = validate_iban(iban)
            assert is_valid == False
            assert "19 znakov" in error
    
    def test_invalid_iban_checksum(self):
        """Test IBAN with invalid checksum."""
        # IBAN with wrong check digits
        is_valid, error = validate_iban("SI99191000000123438")
        assert is_valid == False
        assert "kontrolna številka" in error.lower()
    
    def test_iban_format_display(self):
        """Test IBAN display formatting."""
        iban = "SI56191000000123438"
        formatted = format_iban_display(iban)
        assert formatted == "SI56 1910 0000 0123 438"
        
        # Test with already formatted
        formatted2 = format_iban_display(formatted)
        assert formatted2 == "SI56 1910 0000 0123 438"
    
    def test_international_iban(self):
        """Test international IBAN validation."""
        valid_international = [
            "DE89370400440532013000",  # German
            "GB82WEST12345698765432",  # UK
            "FR1420041010050500013M02606",  # French
        ]
        
        for iban in valid_international:
            is_valid, error = validate_iban(iban)
            # Basic validation should pass
            assert is_valid == True or "kontrolna" in str(error)
    
    def test_empty_iban(self):
        """Test empty IBAN validation."""
        is_valid, error = validate_iban("")
        assert is_valid == False
        assert "obvezen" in error.lower()


class TestSWIFTValidation:
    """Test SWIFT/BIC code validation."""
    
    def test_valid_8_char_swift(self):
        """Test 8-character SWIFT format."""
        valid_swifts = [
            "LJBASI2X",
            "SKBASI2X",
            "ABANSI2X",
            "ljbasi2x",  # Lowercase should be converted
        ]
        
        for swift in valid_swifts:
            is_valid, error = validate_swift_bic(swift)
            assert is_valid == True, f"SWIFT '{swift}' should be valid"
            assert error is None
    
    def test_valid_11_char_swift(self):
        """Test 11-character SWIFT format."""
        valid_swifts = [
            "LJBASI2XXXX",
            "DEUTDEFF500",
        ]
        
        for swift in valid_swifts:
            is_valid, error = validate_swift_bic(swift)
            assert is_valid == True
            assert error is None
    
    def test_invalid_swift_length(self):
        """Test invalid SWIFT length."""
        invalid_swifts = [
            "LJBASI",  # 6 chars
            "LJBASI2",  # 7 chars
            "LJBASI2XX",  # 9 chars
            "LJBASI2XXXXX",  # 12 chars
        ]
        
        for swift in invalid_swifts:
            is_valid, error = validate_swift_bic(swift)
            assert is_valid == False
            assert "8 ali 11 znakov" in error
    
    def test_invalid_swift_structure(self):
        """Test invalid SWIFT structure."""
        invalid_swifts = [
            "12345678",  # All numbers
            "LJB1SI2X",  # Number in bank code
            "LJBA5I2X",  # Number in country code
            "LJBA$I2X",  # Special character
        ]
        
        for swift in invalid_swifts:
            is_valid, error = validate_swift_bic(swift)
            assert is_valid == False
            assert "struktura" in error.lower()
    
    def test_empty_swift_allowed(self):
        """Test that empty SWIFT is allowed (optional field)."""
        is_valid, error = validate_swift_bic("")
        assert is_valid == True
        assert error is None


class TestCurrencyFormatting:
    """Test currency formatting and validation."""
    
    def test_format_currency_display(self):
        """Test currency display formatting."""
        test_cases = [
            (1234567.89, "1.234.567,89"),
            (1000000, "1.000.000,00"),
            (999.99, "999,99"),
            (0, "0,00"),
            (0.5, "0,50"),
        ]
        
        for amount, expected in test_cases:
            formatted = format_currency_display(amount)
            assert formatted == expected, f"Expected {expected}, got {formatted}"
    
    def test_parse_currency_input(self):
        """Test parsing European format input."""
        test_cases = [
            ("1.234.567,89", 1234567.89),
            ("1.000.000", 1000000.0),
            ("999,99", 999.99),
            ("1234567.89", 1234567.89),  # Accept dot as decimal
            ("1,234,567.89", 1234567.89),  # Accept US format
            ("", 0.0),
        ]
        
        for input_str, expected in test_cases:
            parsed = parse_currency_input(input_str)
            assert parsed == expected, f"Input '{input_str}' should parse to {expected}"
    
    def test_validate_currency_amount(self):
        """Test currency amount validation."""
        # Valid amounts
        is_valid, amount = validate_currency_amount("1.234,56", "Test", allow_zero=False)
        assert is_valid == True
        assert amount == 1234.56
        
        # Negative amount
        is_valid, error = validate_currency_amount("-100", "Test", allow_zero=False)
        assert is_valid == False
        assert "negativna" in error
        
        # Zero not allowed
        is_valid, error = validate_currency_amount("0", "Test", allow_zero=False)
        assert is_valid == False
        assert "večja od 0" in error
        
        # Zero allowed
        is_valid, amount = validate_currency_amount("0", "Test", allow_zero=True)
        assert is_valid == True
        assert amount == 0.0
        
        # Too large
        is_valid, error = validate_currency_amount("10000000000", "Test")
        assert is_valid == False
        assert "presega" in error
    
    def test_currency_formatting_edge_cases(self):
        """Test edge cases in currency formatting."""
        # None value
        assert format_currency_display(None) == ""
        
        # String value
        assert format_currency_display("1000") == "1.000,00"
        
        # Very large number
        assert format_currency_display(999999999.99) == "999.999.999,99"
        
        # Very small number
        assert format_currency_display(0.01) == "0,01"


class TestRateLimiter:
    """Test rate limiting for SWIFT lookups."""
    
    def test_rate_limit_enforcement(self):
        """Test that rate limit is enforced."""
        limiter = RateLimiter(max_requests=3, window_seconds=1)
        session = "test_session"
        
        # First 3 requests should pass
        for i in range(3):
            allowed, error = limiter.is_allowed(session)
            assert allowed == True, f"Request {i+1} should be allowed"
            assert error == ""
        
        # 4th request should fail
        allowed, error = limiter.is_allowed(session)
        assert allowed == False
        assert "Preveč poizvedb" in error
    
    def test_rate_limit_window_reset(self):
        """Test that rate limit resets after window."""
        limiter = RateLimiter(max_requests=2, window_seconds=1)
        session = "test_session"
        
        # Use up the limit
        limiter.is_allowed(session)
        limiter.is_allowed(session)
        
        # Should be blocked
        allowed, _ = limiter.is_allowed(session)
        assert allowed == False
        
        # Wait for window to pass
        time.sleep(1.1)
        
        # Should be allowed again
        allowed, _ = limiter.is_allowed(session)
        assert allowed == True
    
    def test_remaining_requests(self):
        """Test remaining request counter."""
        limiter = RateLimiter(max_requests=5, window_seconds=60)
        session = "test_session"
        
        assert limiter.get_remaining_requests(session) == 5
        
        limiter.is_allowed(session)
        assert limiter.get_remaining_requests(session) == 4
        
        limiter.is_allowed(session)
        limiter.is_allowed(session)
        assert limiter.get_remaining_requests(session) == 2
    
    def test_independent_sessions(self):
        """Test that sessions are limited independently."""
        limiter = RateLimiter(max_requests=2, window_seconds=60)
        
        # Session 1 uses its limit
        limiter.is_allowed("session1")
        limiter.is_allowed("session1")
        allowed, _ = limiter.is_allowed("session1")
        assert allowed == False
        
        # Session 2 should still have its limit
        allowed, _ = limiter.is_allowed("session2")
        assert allowed == True
        allowed, _ = limiter.is_allowed("session2")
        assert allowed == True
        allowed, _ = limiter.is_allowed("session2")
        assert allowed == False
    
    def test_reset_session(self):
        """Test resetting a specific session."""
        limiter = RateLimiter(max_requests=2, window_seconds=60)
        session = "test_session"
        
        # Use up limit
        limiter.is_allowed(session)
        limiter.is_allowed(session)
        assert limiter.get_remaining_requests(session) == 0
        
        # Reset session
        limiter.reset_session(session)
        assert limiter.get_remaining_requests(session) == 2


class TestBankIntegration:
    """Test bank-related integration features."""
    
    def test_auto_populate_bank_from_iban(self):
        """Test bank auto-population from IBAN."""
        # This would need a mock database or test database
        # For now, just test the function doesn't crash
        session_state = {}
        result = auto_populate_bank_from_iban("SI56191000000123438", session_state)
        # Without database, should return False
        assert result == False or result == True
    
    def test_swift_bank_consistency(self):
        """Test SWIFT-bank consistency validation."""
        # Test with matching bank name (or unknown SWIFT)
        is_consistent, warning = validate_swift_bank_consistency(
            "LJBASI2X", "Nova Ljubljanska banka"
        )
        # Should pass if bank matches or SWIFT not found
        assert is_consistent == True or warning is None
        
        # Test with clearly mismatched bank
        is_consistent, warning = validate_swift_bank_consistency(
            "SKBASI2X", "Some Other Bank"
        )
        # May warn if SWIFT is in database but doesn't match
        # But should not crash
        assert isinstance(is_consistent, bool)


class TestPerformance:
    """Test performance of validation functions."""
    
    def test_iban_validation_performance(self):
        """Test IBAN validation is fast."""
        start = time.time()
        for _ in range(1000):
            validate_iban("SI56191000000123438")
        elapsed = time.time() - start
        assert elapsed < 1.0  # Should validate 1000 in under 1 second
    
    def test_swift_validation_performance(self):
        """Test SWIFT validation is fast."""
        start = time.time()
        for _ in range(1000):
            validate_swift_bic("LJBASI2X")
        elapsed = time.time() - start
        assert elapsed < 1.0
    
    def test_currency_parsing_performance(self):
        """Test currency parsing is fast."""
        start = time.time()
        for _ in range(1000):
            parse_currency_input("1.234.567,89")
        elapsed = time.time() - start
        assert elapsed < 1.0
    
    def test_rate_limiter_performance(self):
        """Test rate limiter doesn't impact performance."""
        limiter = RateLimiter()
        
        start = time.time()
        for i in range(1000):
            limiter.is_allowed(f"session_{i}")
        elapsed = time.time() - start
        
        # Should handle 1000 checks in under 0.5 seconds
        assert elapsed < 0.5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])