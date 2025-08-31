"""
Form rendering components for unified lot architecture.
All forms are treated as having lots (minimum one "General" lot).
"""

from .field_renderer import FieldRenderer
from .section_renderer import SectionRenderer
from .lot_manager import LotManager

__all__ = ['FieldRenderer', 'SectionRenderer', 'LotManager']