from typing import Dict, Any, Optional, Tuple, List
import streamlit as st
from datetime import time, date
import re


class FieldTypeManager:
    """Manages field type configurations and rendering"""
    
    def __init__(self):
        self.field_configs = self._initialize_field_configs()
    
    def _initialize_field_configs(self) -> Dict[str, Dict]:
        """Initialize field type configurations"""
        return {
            # Time fields - use wildcard for array items
            'inspectionInfo.inspectionDates.*.time': {
                'type': 'time',
                'label': 'Ura ogleda',
                'help': 'Izberite uro ogleda',
                'default': time(10, 0)
            },
            
            # Currency fields
            'guarantees.tender_amount': {
                'type': 'currency',
                'label': 'Višina zavarovanja za resnost ponudbe',
                'min': 0.0,
                'step': 100.0,
                'format': '%.2f',
                'suffix': 'EUR',
                'help': 'Vnesite znesek v EUR'
            },
            'guarantees.performance_amount': {
                'type': 'currency',
                'label': 'Višina zavarovanja za dobro izvedbo',
                'min': 0.0,
                'step': 100.0,
                'format': '%.2f',
                'suffix': 'EUR'
            },
            'guarantees.warranty_amount': {
                'type': 'currency',
                'label': 'Višina zavarovanja za odpravo napak',
                'min': 0.0,
                'step': 100.0,
                'format': '%.2f',
                'suffix': 'EUR'
            },
            
            # Integer fields
            'negotiations.rounds': {
                'type': 'integer',
                'label': 'Število krogov pogajanj',
                'min': 1,
                'max': 10,
                'step': 1,
                'help': 'Izberite med 1 in 10 krogi'
            },
            'lotInfo.lotCount': {
                'type': 'integer',
                'label': 'Število sklopov',
                'min': 2,
                'max': 50,
                'step': 1,
                'help': 'Najmanj 2 sklopa'
            },
            'pricing.quantities': {
                'type': 'integer',
                'label': 'Količine',
                'min': 0,
                'step': 1
            },
            
            # Text areas
            'negotiationsInfo.specialNegotiationWishes': {
                'type': 'textarea',
                'label': 'Opišite vaše posebne želje v zvezi s pogajanji',
                'rows': 5,
                'max_chars': 2000,
                'help': 'Navedite morebitne posebne zahteve, omejitve ali pojasnila glede poteka pogajanj'
            },
            'contractInfo.extensionReasons': {
                'type': 'textarea',
                'label': 'Razlogi za podaljšanje',
                'rows': 4,
                'max_chars': 1000
            },
            'variants.description': {
                'type': 'textarea',
                'label': 'Opis variantnih ponudb',
                'rows': 5,
                'max_chars': 1500
            },
            'variants.requirements': {
                'type': 'textarea',
                'label': 'Zahteve za variante',
                'rows': 5,
                'max_chars': 1500
            },
            'contractInfo.additionalInfo': {
                'type': 'textarea',
                'label': 'Dodatne informacije in posebne zahteve',
                'rows': 6,
                'max_chars': 3000,
                'help': 'Neobvezno polje'
            },
            
            # Formatted text fields
            'guarantees.tender_trr': {
                'type': 'formatted_text',
                'label': 'TRR račun',
                'placeholder': 'SI56 XXXX XXXX XXXX XXX',
                'pattern': r'^SI\d{2}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{3}$',
                'help': 'Format: SI56 XXXX XXXX XXXX XXX',
                'max_chars': 24
            },
            'guarantees.performance_trr': {
                'type': 'formatted_text',
                'label': 'TRR račun',
                'placeholder': 'SI56 XXXX XXXX XXXX XXX',
                'pattern': r'^SI\d{2}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{3}$',
                'max_chars': 24
            },
            'guarantees.warranty_trr': {
                'type': 'formatted_text',
                'label': 'TRR račun',
                'placeholder': 'SI56 XXXX XXXX XXXX XXX',
                'pattern': r'^SI\d{2}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{3}$',
                'max_chars': 24
            },
            'guarantees.tender_bic': {
                'type': 'formatted_text',
                'label': 'BIC koda',
                'placeholder': 'XXXXXXXX',
                'pattern': r'^[A-Z]{6}[A-Z0-9]{2}([A-Z0-9]{3})?$',
                'max_chars': 11,
                'uppercase': True,
                'help': '8 ali 11 znakov'
            },
            'guarantees.performance_bic': {
                'type': 'formatted_text',
                'label': 'BIC koda',
                'placeholder': 'XXXXXXXX',
                'pattern': r'^[A-Z]{6}[A-Z0-9]{2}([A-Z0-9]{3})?$',
                'max_chars': 11,
                'uppercase': True,
                'help': '8 ali 11 znakov'
            },
            'guarantees.warranty_bic': {
                'type': 'formatted_text',
                'label': 'BIC koda',
                'placeholder': 'XXXXXXXX',
                'pattern': r'^[A-Z]{6}[A-Z0-9]{2}([A-Z0-9]{3})?$',
                'max_chars': 11,
                'uppercase': True,
                'help': '8 ali 11 znakov'
            },
            
            # Short text with limits
            'projectInfo.internalNumber': {
                'type': 'text',
                'label': 'Interna številka javnega naročila',
                'max_chars': 50,
                'required': False,
                'help': 'Neobvezno'
            },
            'contractInfo.competitionFrequency': {
                'type': 'text',
                'label': 'Pogostost odpiranja konkurence',
                'max_chars': 100,
                'placeholder': 'npr. Četrtletno, Mesečno, Po potrebi'
            },
            'contractInfo.frameworkPeriod': {
                'type': 'text',
                'label': 'Obdobje okvirnega sporazuma',
                'max_chars': 50,
                'placeholder': 'npr. 24 mesecev, 2 leti'
            }
        }
    
    def render_field(self, field_key: str, value: Any = None, 
                    disabled: bool = False, **kwargs) -> Any:
        """Render a field with appropriate input type"""
        
        config = self.field_configs.get(field_key, {})
        field_type = config.get('type', 'text')
        
        # Override with kwargs if provided
        label = kwargs.get('label', config.get('label', field_key))
        help_text = kwargs.get('help', config.get('help'))
        
        if field_type == 'time':
            return self._render_time_field(field_key, config, value, disabled, label, help_text)
        
        elif field_type == 'currency':
            return self._render_currency_field(field_key, config, value, disabled, label, help_text)
        
        elif field_type == 'integer':
            return self._render_integer_field(field_key, config, value, disabled, label, help_text)
        
        elif field_type == 'textarea':
            return self._render_textarea_field(field_key, config, value, disabled, label, help_text)
        
        elif field_type == 'formatted_text':
            return self._render_formatted_text_field(field_key, config, value, disabled, label, help_text)
        
        else:  # Default text
            return self._render_text_field(field_key, config, value, disabled, label, help_text)
    
    def _render_time_field(self, key: str, config: dict, value: Any, disabled: bool, label: str, help_text: str) -> time:
        """Render time input field"""
        default_time = config.get('default', time(9, 0))
        
        if value and isinstance(value, str):
            # Parse string time to time object
            try:
                hour, minute = value.split(':')
                value = time(int(hour), int(minute))
            except:
                value = default_time
        
        return st.time_input(
            label,
            value=value or default_time,
            disabled=disabled,
            help=help_text,
            key=key
        )
    
    def _render_currency_field(self, key: str, config: dict, value: Any, disabled: bool, label: str, help_text: str) -> float:
        """Render currency input with EUR suffix"""
        col1, col2 = st.columns([5, 1])
        
        with col1:
            numeric_value = st.number_input(
                label,
                min_value=config.get('min', 0.0),
                step=config.get('step', 1.0),
                value=float(value) if value else config.get('min', 0.0),
                format=config.get('format', '%.2f'),
                disabled=disabled,
                help=help_text,
                key=key
            )
        
        with col2:
            st.write("")  # Spacing
            st.write("")  # More spacing to align
            st.markdown(f"**{config.get('suffix', 'EUR')}**")
        
        return numeric_value
    
    def _render_integer_field(self, key: str, config: dict, value: Any, disabled: bool, label: str, help_text: str) -> int:
        """Render integer number input"""
        return st.number_input(
            label,
            min_value=config.get('min', 0),
            max_value=config.get('max', None),
            step=config.get('step', 1),
            value=int(value) if value else config.get('min', 0),
            disabled=disabled,
            help=help_text,
            key=key
        )
    
    def _render_textarea_field(self, key: str, config: dict, value: Any, disabled: bool, label: str, help_text: str) -> str:
        """Render textarea with dynamic height"""
        rows = config.get('rows', 3)
        height = rows * 30  # Approximate height in pixels
        
        return st.text_area(
            label,
            value=value or '',
            height=height,
            max_chars=config.get('max_chars'),
            disabled=disabled,
            help=help_text,
            key=key
        )
    
    def _render_formatted_text_field(self, key: str, config: dict, value: Any, disabled: bool, label: str, help_text: str) -> str:
        """Render text input with format validation"""
        # Container for field and validation
        container = st.container()
        
        with container:
            text_value = st.text_input(
                label,
                value=value or '',
                max_chars=config.get('max_chars'),
                placeholder=config.get('placeholder', ''),
                disabled=disabled,
                help=help_text,
                key=key
            )
            
            # Real-time validation
            if text_value and config.get('pattern'):
                pattern = config.get('pattern')
                if config.get('uppercase'):
                    text_value = text_value.upper()
                
                if not re.match(pattern, text_value):
                    st.error(f"❌ Neveljaven format. Pričakovan: {config.get('placeholder', 'glej pomoč')}")
                else:
                    st.success("✅ Pravilen format")
        
        return text_value
    
    def _render_text_field(self, key: str, config: dict, value: Any, disabled: bool, label: str, help_text: str) -> str:
        """Render standard text input"""
        return st.text_input(
            label,
            value=value or '',
            max_chars=config.get('max_chars'),
            placeholder=config.get('placeholder', ''),
            disabled=disabled,
            help=help_text,
            key=key
        )
    
    def get_field_config(self, field_key: str) -> Dict:
        """Get configuration for a specific field"""
        # Check direct match
        if field_key in self.field_configs:
            return self.field_configs[field_key]
        
        # Check for array patterns
        import re
        for config_key, config in self.field_configs.items():
            if '*' in config_key:
                # Convert pattern to regex
                pattern = config_key.replace('.', r'\.').replace('*', r'\d+')
                if re.match(f'^{pattern}$', field_key):
                    return config
        
        return {}
    
    def is_enhanced_field(self, field_key: str) -> bool:
        """Check if field has enhanced configuration"""
        # Check direct match
        if field_key in self.field_configs:
            return True
        
        # Check for array patterns (e.g., inspectionDates.0.time matches inspectionDates.*.time)
        import re
        for config_key in self.field_configs:
            if '*' in config_key:
                # Convert pattern to regex (replace * with \d+)
                pattern = config_key.replace('.', r'\.').replace('*', r'\d+')
                if re.match(f'^{pattern}$', field_key):
                    return True
        
        return False


class RealTimeValidator:
    """Provides real-time validation feedback"""
    
    def __init__(self, validation_manager):
        self.validator = validation_manager
    
    def validate_field(self, field_key: str, value: Any) -> Tuple[bool, Optional[str]]:
        """Validate a single field and return status"""
        
        # Field-specific validation rules
        validators = {
            'guarantees.tender_trr': self._validate_trr,
            'guarantees.performance_trr': self._validate_trr,
            'guarantees.warranty_trr': self._validate_trr,
            'guarantees.tender_bic': self._validate_bic,
            'guarantees.performance_bic': self._validate_bic,
            'guarantees.warranty_bic': self._validate_bic,
            'clientInfo.email': self._validate_email,
            'clientInfo.phone': self._validate_phone,
        }
        
        if field_key in validators:
            return validators[field_key](value)
        
        # Default validation (required check)
        if self._is_required_field(field_key):
            if not value or (isinstance(value, str) and not value.strip()):
                return False, "To polje je obvezno"
        
        return True, None
    
    def _validate_trr(self, value: str) -> Tuple[bool, Optional[str]]:
        """Validate TRR format"""
        if not value:
            return True, None  # Empty is ok if not required
        
        # Remove spaces for validation
        value_clean = value.replace(' ', '')
        pattern = r'^SI\d{2}\d{4}\d{4}\d{4}\d{3}$'
        
        if not re.match(pattern, value_clean):
            return False, "Neveljaven TRR format (SI56 XXXX XXXX XXXX XXX)"
        
        return True, None
    
    def _validate_bic(self, value: str) -> Tuple[bool, Optional[str]]:
        """Validate BIC/SWIFT code"""
        if not value:
            return True, None
        
        pattern = r'^[A-Z]{6}[A-Z0-9]{2}([A-Z0-9]{3})?$'
        
        if not re.match(pattern, value.upper()):
            return False, "Neveljaven BIC format (8 ali 11 znakov)"
        
        return True, None
    
    def _validate_email(self, value: str) -> Tuple[bool, Optional[str]]:
        """Validate email format"""
        if not value:
            return True, None
        
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        if not re.match(pattern, value):
            return False, "Neveljaven email naslov"
        
        return True, None
    
    def _validate_phone(self, value: str) -> Tuple[bool, Optional[str]]:
        """Validate phone number"""
        if not value:
            return True, None
        
        # Remove spaces and dashes
        value_clean = value.replace(' ', '').replace('-', '')
        
        # Slovenian phone patterns
        patterns = [
            r'^\+386\d{8}$',  # International
            r'^0\d{8}$',      # Local
            r'^\d{8}$'        # Without prefix
        ]
        
        if not any(re.match(p, value_clean) for p in patterns):
            return False, "Neveljaven format telefonske številke"
        
        return True, None
    
    def _is_required_field(self, field_key: str) -> bool:
        """Check if field is required based on schema"""
        # This would check the schema for required fields
        # For now, returning False as we don't have the full schema integration
        return False