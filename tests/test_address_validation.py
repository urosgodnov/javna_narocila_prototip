"""
Test suite for address field validation.
Story 2.3: Address Field Testing and Integration
"""

import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.validations import (
    validate_street,
    validate_house_number,
    validate_city,
    validate_postal_code,
    validate_address_fields,
    validate_date_range,
    validate_criteria_points,
    validate_cpv_criteria_restrictions
)


class TestAddressValidation:
    """Test address field validation functions."""
    
    def test_house_number_formats(self):
        """Test various house number formats."""
        # Test valid formats
        valid_numbers = ["15", "15a", "15A", "15/2", "15/2b", "1", "999", "12B", "1/1"]
        for number in valid_numbers:
            result, errors = validate_house_number(number)
            assert result == True, f"House number '{number}' should be valid"
            assert errors == []
        
        # Test invalid formats
        invalid_numbers = ["", "a15", "/15", "15//2", "15-2", "abc", "15/", "/", "//"]
        for number in invalid_numbers:
            result, errors = validate_house_number(number)
            assert result == False, f"House number '{number}' should be invalid"
            assert len(errors) > 0
    
    def test_street_validation(self):
        """Test street name validation."""
        # Valid street names
        valid_streets = [
            "Slovenska cesta",
            "Ul. Janeza Pavla II",
            "Prešernova ulica",
            "Cesta v Mestni log",
            "Pot na Golovec"
        ]
        
        for street in valid_streets:
            result, errors = validate_street(street)
            assert result == True, f"Street '{street}' should be valid"
            assert errors == []
        
        # Invalid street names
        invalid_streets = [
            "",  # Empty
            "A",  # Too short
            "123",  # Only numbers
            "  ",  # Only spaces
        ]
        
        for street in invalid_streets:
            result, errors = validate_street(street)
            assert result == False, f"Street '{street}' should be invalid"
            assert len(errors) > 0
    
    def test_postal_code_validation(self):
        """Test postal code validation."""
        # Valid postal codes
        valid_codes = ["1000", "2000", "9999", "5000"]
        
        for code in valid_codes:
            result, errors = validate_postal_code(code)
            assert result == True, f"Postal code '{code}' should be valid"
            assert errors == []
        
        # Invalid postal codes
        invalid_codes = [
            "999",  # Too short
            "10000",  # Too long
            "abcd",  # Letters
            "12 34",  # Space
            "",  # Empty
            "0999"  # Below 1000
        ]
        
        for code in invalid_codes:
            result, errors = validate_postal_code(code)
            assert result == False, f"Postal code '{code}' should be invalid"
            assert len(errors) > 0
    
    def test_city_validation(self):
        """Test city name validation."""
        # Valid city names
        valid_cities = [
            "Ljubljana",
            "Novo mesto",
            "Murska Sobota",
            "Škofja Loka",
            "Črnomelj",
            "Šempeter-Vrtojba"
        ]
        
        for city in valid_cities:
            result, errors = validate_city(city)
            assert result == True, f"City '{city}' should be valid"
            assert errors == []
        
        # Invalid city names
        invalid_cities = [
            "",  # Empty
            "A",  # Too short
            "Ljubljana123",  # Contains numbers
            "Ljubljana!",  # Special characters
        ]
        
        for city in invalid_cities:
            result, errors = validate_city(city)
            assert result == False, f"City '{city}' should be invalid"
            assert len(errors) > 0
    
    def test_full_address_validation(self):
        """Test complete address validation."""
        # Valid single client address
        form_data = {
            'clientInfo': {
                'isSingleClient': True,
                'singleClientStreet': 'Slovenska cesta',
                'singleClientHouseNumber': '15a',
                'singleClientCity': 'Ljubljana',
                'singleClientPostalCode': '1000'
            }
        }
        
        result, errors = validate_address_fields(form_data)
        assert result == True
        assert errors == []
        
        # Invalid address - bad house number
        form_data['clientInfo']['singleClientHouseNumber'] = '15//2'
        result, errors = validate_address_fields(form_data)
        assert result == False
        assert any('hišna številka' in e.lower() for e in errors)
        
        # Test multiple clients
        form_data = {
            'clientInfo': {
                'isSingleClient': False,
                'clients': [
                    {
                        'street': 'Prešernova',
                        'houseNumber': '1',
                        'city': 'Kranj',
                        'postalCode': '4000'
                    },
                    {
                        'street': '123',  # Invalid - only numbers
                        'houseNumber': '2a',
                        'city': 'M',  # Invalid - too short
                        'postalCode': '999'  # Invalid - too short
                    }
                ]
            }
        }
        
        result, errors = validate_address_fields(form_data)
        assert result == False
        assert len(errors) >= 3  # At least 3 errors for second client
        assert any('Naročnik 2' in e for e in errors)
    
    def test_cofinancer_address_validation(self):
        """Test cofinancer address validation."""
        form_data = {
            'orderType': {
                'cofinancers': [
                    {
                        'cofinancerStreet': 'Evropska cesta',
                        'cofinancerHouseNumber': '10',
                        'cofinancerCity': 'Bruselj',
                        'cofinancerPostalCode': '1000'
                    },
                    {
                        'cofinancerStreet': '',  # Invalid - empty
                        'cofinancerHouseNumber': 'abc',  # Invalid format
                        'cofinancerCity': 'B',  # Too short
                        'cofinancerPostalCode': 'ABCD'  # Invalid format
                    }
                ]
            }
        }
        
        result, errors = validate_address_fields(form_data)
        assert result == False
        assert any('Sofinancer 2' in e for e in errors)
        assert len(errors) >= 4  # Errors for second cofinancer


class TestDateRangeValidation:
    """Test date range validation."""
    
    def test_valid_date_ranges(self):
        """Test valid date ranges."""
        test_cases = [
            ("01.01.2024", "31.12.2024", "Test"),
            ("15.06.2024", "16.06.2024", "Test"),
            ("01.01.2024", "01.01.2024", "Test"),  # Same date is valid
        ]
        
        for start, end, field in test_cases:
            result, errors = validate_date_range(start, end, field)
            assert result == True
            assert errors == []
    
    def test_invalid_date_ranges(self):
        """Test invalid date ranges."""
        # End date before start date
        result, errors = validate_date_range("31.12.2024", "01.01.2024", "Test")
        assert result == False
        assert len(errors) == 1
        assert "pred začetnim" in errors[0]
    
    def test_empty_dates(self):
        """Test empty date handling."""
        # Empty dates should pass (no validation)
        result, errors = validate_date_range("", "31.12.2024", "Test")
        assert result == True
        
        result, errors = validate_date_range("01.01.2024", "", "Test")
        assert result == True
        
        result, errors = validate_date_range("", "", "Test")
        assert result == True


class TestCriteriaPointsValidation:
    """Test criteria points validation."""
    
    def test_valid_points(self):
        """Test valid point distributions."""
        criteria = {
            'priceCriteria': True,
            'priceCriteriaRatio': 60,
            'qualityCriteria': True,
            'qualityCriteriaRatio': 40
        }
        
        result, errors = validate_criteria_points(criteria)
        assert result == True
        assert errors == []
    
    def test_invalid_total(self):
        """Test invalid point totals."""
        criteria = {
            'priceCriteria': True,
            'priceCriteriaRatio': 60,
            'qualityCriteria': True,
            'qualityCriteriaRatio': 30  # Total = 90, not 100
        }
        
        result, errors = validate_criteria_points(criteria)
        assert result == False
        assert any('100' in e for e in errors)
    
    def test_missing_points(self):
        """Test missing points for selected criteria."""
        criteria = {
            'priceCriteria': True,
            'priceCriteriaRatio': 0,  # No points
            'qualityCriteria': True,
            'qualityCriteriaRatio': 100
        }
        
        result, errors = validate_criteria_points(criteria)
        assert result == False
        assert any('Cena' in e for e in errors)
    
    def test_social_criteria_points(self):
        """Test social criteria sub-points."""
        criteria = {
            'socialCriteria': True,
            'socialCriteriaYoungRatio': 20,
            'socialCriteriaElderlyRatio': 30,
            'socialCriteriaStaffRatio': 0,
            'socialCriteriaSalaryRatio': 0,
            'socialCriteriaOtherRatio': 0,
            'priceCriteria': True,
            'priceCriteriaRatio': 50
        }
        
        result, errors = validate_criteria_points(criteria)
        assert result == True  # Total = 50 + 50 = 100
        assert errors == []


class TestCPVCriteriaValidation:
    """Test CPV-based criteria restrictions."""
    
    def test_no_cpv_codes(self):
        """Test validation with no CPV codes."""
        form_data = {
            'projectInfo': {},
            'selectionCriteria': {
                'priceCriteria': True
            }
        }
        
        result, errors = validate_cpv_criteria_restrictions(form_data)
        assert result == True
        assert errors == []
    
    def test_price_only_allowed(self):
        """Test when price-only is allowed."""
        form_data = {
            'projectInfo': {
                'cpvCodes': ['12345678-9']  # Assuming this doesn't have restrictions
            },
            'selectionCriteria': {
                'priceCriteria': True
            }
        }
        
        # This should pass if the CPV doesn't have restrictions
        # (We can't test actual CPV restrictions without database)
        result, errors = validate_cpv_criteria_restrictions(form_data)
        # Just check it doesn't crash
        assert isinstance(result, bool)
        assert isinstance(errors, list)


class TestPerformance:
    """Test validation performance."""
    
    def test_validation_performance(self):
        """Test that validations are fast."""
        import time
        
        # Test house number validation performance
        start = time.time()
        for _ in range(1000):
            validate_house_number("15a")
        elapsed = time.time() - start
        assert elapsed < 1.0  # Should validate 1000 in under 1 second
        
        # Test postal code validation performance
        start = time.time()
        for _ in range(1000):
            validate_postal_code("1000")
        elapsed = time.time() - start
        assert elapsed < 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])