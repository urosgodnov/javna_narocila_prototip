"""AI Summary Service for generating procurement summaries."""

import os
import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class AISummaryService:
    """Service for generating AI-powered summaries of procurement orders."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the AI Summary Service.
        
        Args:
            api_key: OpenAI API key (will use environment variable if not provided)
        """
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        self.model = "gpt-4"  # Default model
        
    def generate_summary(self, procurement_data: Dict[str, Any]) -> str:
        """
        Generate an AI-powered summary of a procurement order.
        
        Args:
            procurement_data: Dictionary containing procurement order data
            
        Returns:
            Generated summary text with recommendations
        """
        # For now, return a mock summary since we don't want to make actual API calls
        # In production, this would call the OpenAI API
        
        summary = self._generate_mock_summary(procurement_data)
        return summary
    
    def _generate_mock_summary(self, data: Dict[str, Any]) -> str:
        """Generate a mock summary for testing purposes."""
        
        naziv = data.get('naziv', 'Neimenovano naročilo')
        vrsta = data.get('vrsta_postopka', 'Neznana')
        vrednost = data.get('ocenjena_vrednost', 'Ni podatka')
        
        summary = f"""## Povzetek naročila

### Osnovni podatki
**Naziv naročila:** {naziv}  
**Vrsta postopka:** {vrsta}  
**Ocenjena vrednost:** {vrednost} EUR

### Ključne ugotovitve
- Naročilo je pripravljeno v skladu z veljavno zakonodajo
- Vsi obvezni elementi so vključeni
- Merila za izbor so jasno opredeljena

### Priporočila za izboljšave
1. **Časovni okvir:** Preverite, ali je rok za oddajo ponudb dovolj dolg glede na kompleksnost naročila
2. **Merila:** Razmislite o dodatnih merilih za bolj celovito ocenjevanje ponudb
3. **Dokumentacija:** Zagotovite, da je vsa tehnična dokumentacija dostopna ponudnikom

### Opozorila
- Preverite skladnost z najnovejšimi spremembami ZJN-3
- Zagotovite pravočasno objavo na portalu javnih naročil

### Zaključek
Naročilo je dobro pripravljeno. Z implementacijo zgornjih priporočil lahko dodatno izboljšate transparentnost in učinkovitost postopka.

---
*Povzetek generiran: {datetime.now().strftime('%d.%m.%Y %H:%M')}*
"""
        
        return summary
    
    def analyze_criteria(self, criteria: list) -> Dict[str, Any]:
        """
        Analyze selection criteria for completeness and balance.
        
        Args:
            criteria: List of selection criteria
            
        Returns:
            Analysis results with recommendations
        """
        # Mock implementation
        return {
            'total_weight': 100,
            'balance': 'good',
            'recommendations': []
        }