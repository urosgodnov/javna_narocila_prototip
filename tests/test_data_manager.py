# tests/test_data_manager.py

import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, date, time
from utils.data_manager import (
    serialize_datetime, deserialize_datetime, prepare_for_json,
    flatten_nested_dict, unflatten_dict, lots_to_fields, 
    fields_to_lots, reconstruct_arrays
)

class TestTypeConversions:
    def test_serialize_datetime(self):
        # Test datetime
        dt = datetime(2024, 1, 15, 10, 30, 45)
        assert serialize_datetime(dt) == '2024-01-15T10:30:45'
        
        # Test date
        d = date(2024, 1, 15)
        assert serialize_datetime(d) == '2024-01-15'
        
        # Test time
        t = time(10, 30, 45)
        assert serialize_datetime(t) == '10:30:45'
        
        # Test None
        assert serialize_datetime(None) is None
    
    def test_deserialize_datetime(self):
        # Test datetime
        dt = deserialize_datetime('2024-01-15T10:30:45', 'datetime')
        assert dt == datetime(2024, 1, 15, 10, 30, 45)
        
        # Test date
        d = deserialize_datetime('2024-01-15', 'date')
        assert d == date(2024, 1, 15)
        
        # Test time
        t = deserialize_datetime('10:30:45', 'time')
        assert t == time(10, 30, 45)
        
        # Test time without seconds
        t = deserialize_datetime('10:30', 'time')
        assert t == time(10, 30)
        
        # Test None/empty
        assert deserialize_datetime(None, 'date') is None
        assert deserialize_datetime('', 'time') is None
        
        # Test invalid
        assert deserialize_datetime('invalid', 'datetime') is None
    
    def test_prepare_for_json(self):
        # Test complex nested structure
        data = {
            'date': date(2024, 1, 15),
            'time': time(10, 30),
            'datetime': datetime(2024, 1, 15, 10, 30),
            'nested': {
                'value': 42,
                'date': date(2024, 2, 20)
            },
            'list': [1, 2, date(2024, 3, 1)]
        }
        result = prepare_for_json(data)
        
        assert result['date'] == '2024-01-15'
        assert result['time'] == '10:30:00'
        assert result['datetime'] == '2024-01-15T10:30:00'
        assert result['nested']['date'] == '2024-02-20'
        assert result['list'][2] == '2024-03-01'

class TestStructureTransformations:
    def test_flatten_nested_dict(self):
        nested = {
            'a': 1,
            'b': {
                'c': 2,
                'd': {
                    'e': 3
                }
            }
        }
        flat = flatten_nested_dict(nested)
        assert flat == {'a': 1, 'b.c': 2, 'b.d.e': 3}
    
    def test_flatten_empty_values(self):
        nested = {'a': {}, 'b': None, 'c': {'d': None}}
        flat = flatten_nested_dict(nested)
        assert flat == {'a': {}, 'b': None, 'c.d': None}
    
    def test_unflatten_dict(self):
        flat = {'a': 1, 'b.c': 2, 'b.d.e': 3}
        nested = unflatten_dict(flat)
        assert nested == {
            'a': 1,
            'b': {
                'c': 2,
                'd': {
                    'e': 3
                }
            }
        }
    
    def test_flatten_unflatten_round_trip(self):
        original = {
            'a': 1,
            'b': {
                'c': 2,
                'd': {
                    'e': 3,
                    'f': [1, 2, 3]
                }
            },
            'g': None
        }
        flattened = flatten_nested_dict(original)
        unflattened = unflatten_dict(flattened)
        assert unflattened == original
    
    def test_lots_to_fields(self):
        lots = [
            {'name': 'Lot 1', 'orderType': {'estimatedValue': 1000}},
            {'name': 'Lot 2', 'orderType': {'estimatedValue': 2000}}
        ]
        fields = lots_to_fields(lots)
        assert fields == {
            'lot_0.name': 'Lot 1',
            'lot_0.orderType.estimatedValue': 1000,
            'lot_1.name': 'Lot 2',
            'lot_1.orderType.estimatedValue': 2000
        }
    
    def test_lots_to_fields_empty(self):
        assert lots_to_fields([]) == {}
        assert lots_to_fields([None, {}, {'name': 'Valid'}]) == {'lot_2.name': 'Valid'}
    
    def test_fields_to_lots(self):
        session = {
            'lot_0.name': 'Lot 1',
            'lot_0.orderType.estimatedValue': 1000,
            'lot_1.name': 'Lot 2',
            'lot_1.orderType.estimatedValue': 2000,
            'other_field': 'ignored'
        }
        lots = fields_to_lots(session)
        assert lots == [
            {'name': 'Lot 1', 'orderType': {'estimatedValue': 1000}},
            {'name': 'Lot 2', 'orderType': {'estimatedValue': 2000}}
        ]
    
    def test_fields_to_lots_empty(self):
        assert fields_to_lots({}) == []
        assert fields_to_lots({'other': 'data'}) == []
    
    def test_lots_round_trip(self):
        original_lots = [
            {
                'name': 'Test Lot',
                'orderType': {
                    'estimatedValue': 50000,
                    'cofinancers': [
                        {'name': 'EU Fund', 'amount': 25000}
                    ]
                },
                'dates': ['2024-01-15', '2024-01-16']
            }
        ]
        
        # Convert to fields and back
        fields = lots_to_fields(original_lots)
        # Add some extra fields to ensure they're ignored
        fields['extra'] = 'ignored'
        fields['lot_99.invalid'] = 'also ignored'
        
        reconstructed = fields_to_lots(fields)
        assert reconstructed == original_lots

class TestArrayReconstruction:
    def test_reconstruct_simple_array(self):
        session = {
            'items.0.name': 'Item 1',
            'items.1.name': 'Item 2',
            'items.2.name': 'Item 3',
            'other': 'value'
        }
        result = reconstruct_arrays(session)
        assert result['items'] == [
            {'name': 'Item 1'},
            {'name': 'Item 2'},
            {'name': 'Item 3'}
        ]
        assert result['other'] == 'value'
    
    def test_reconstruct_nested_arrays(self):
        session = {
            'data.items.0.values.0': 1,
            'data.items.0.values.1': 2,
            'data.items.1.values.0': 3
        }
        result = reconstruct_arrays(session)
        # Note: This creates nested array keys, not nested arrays within arrays
        assert 'data.items' in result
        assert len(result['data.items']) == 2
    
    def test_reconstruct_with_gaps(self):
        session = {
            'items.0.name': 'First',
            'items.2.name': 'Third'  # Gap at index 1
        }
        result = reconstruct_arrays(session)
        assert result['items'] == [
            {'name': 'First'},
            {},  # Empty object for gap
            {'name': 'Third'}
        ]
    
    def test_reconstruct_skip_widget_keys(self):
        session = {
            'widget_field': 'ignored',
            'items.0.name': 'Item',
            'widget_items.0.name': 'also ignored'
        }
        result = reconstruct_arrays(session)
        assert 'widget_field' not in result
        assert 'widget_items' not in result
        assert result['items'] == [{'name': 'Item'}]
    
    def test_reconstruct_direct_values(self):
        session = {
            'items.0': 'Direct value',
            'items.1': 'Another value'
        }
        result = reconstruct_arrays(session)
        assert result['items'] == ['Direct value', 'Another value']

class TestRoundTrips:
    def test_datetime_round_trip(self):
        # Test all datetime types round trip correctly
        dt = datetime(2024, 1, 15, 10, 30, 45, 123456)
        serialized = serialize_datetime(dt)
        deserialized = deserialize_datetime(serialized, 'datetime')
        assert deserialized == dt
        
        d = date(2024, 1, 15)
        serialized = serialize_datetime(d)
        deserialized = deserialize_datetime(serialized, 'date')
        assert deserialized == d
        
        t = time(10, 30, 45)
        serialized = serialize_datetime(t)
        deserialized = deserialize_datetime(serialized, 'time')
        assert deserialized == t
    
    def test_complex_data_round_trip(self):
        # Test complex nested structure with all features
        original = {
            'simple': 'value',
            'nested': {
                'deep': {
                    'value': 42
                }
            },
            'date_field': date(2024, 1, 15),
            'time_field': time(10, 30),
            'array.0.name': 'First',
            'array.1.name': 'Second',
            'lot_0.name': 'Lot One',
            'lot_0.value': 100
        }
        
        # Prepare for JSON
        json_ready = prepare_for_json(original)
        
        # Should be JSON serializable
        import json
        json_str = json.dumps(json_ready)
        reloaded = json.loads(json_str)
        
        # Dates should be strings now
        assert isinstance(reloaded['date_field'], str)
        assert isinstance(reloaded['time_field'], str)
        assert reloaded['date_field'] == '2024-01-15'
        assert reloaded['time_field'] == '10:30:00'

if __name__ == '__main__':
    pytest.main([__file__, '-v'])