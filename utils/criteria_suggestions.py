"""Suggestions for criteria selection based on CPV codes."""
from typing import List, Dict, Set


def analyze_cpv_categories(cpv_codes: List[str]) -> Set[str]:
    """
    Determine service categories from CPV codes.
    
    Args:
        cpv_codes: List of CPV codes
        
    Returns:
        Set of service categories
    """
    categories = set()
    
    for code in cpv_codes:
        if not code:
            continue
            
        # Get first 2 digits of CPV code
        prefix = code[:2] if len(code) >= 2 else ""
        
        # Map CPV prefixes to categories
        if prefix in ['70', '71', '72', '73', '74']:
            # Architecture, engineering, R&D, technical services
            categories.add('intellectual_services')
        elif prefix == '45':
            # Construction work
            categories.add('construction')
        elif prefix == '85':
            # Health and social work services
            categories.add('social_services')
        elif prefix in ['79', '48']:
            # Business services, software
            categories.add('intellectual_services')
        elif prefix == '90':
            # Environmental services
            categories.add('environmental_services')
        elif prefix in ['50', '51']:
            # Repair and maintenance services
            categories.add('technical_services')
        elif prefix == '80':
            # Education and training services
            categories.add('education_services')
        elif prefix in ['92', '98']:
            # Recreational, cultural, sporting services
            categories.add('cultural_services')
    
    return categories


def get_suggested_criteria_for_cpv(cpv_codes: List[str]) -> Dict:
    """
    Get suggested additional criteria based on CPV code categories.
    
    Args:
        cpv_codes: List of CPV codes
        
    Returns:
        Dictionary with recommendations
    """
    suggestions = {
        'recommended': [],
        'commonly_used': [],
        'explanation': '',
        'category': None
    }
    
    if not cpv_codes:
        return suggestions
    
    # Analyze CPV codes to determine service types
    service_types = analyze_cpv_categories(cpv_codes)
    
    # Provide suggestions based on service type
    if 'intellectual_services' in service_types:
        suggestions['recommended'] = [
            'additionalReferences',  # Past experience matters
            'additionalTechnicalRequirements'  # Technical expertise
        ]
        suggestions['commonly_used'] = [
            'environmentalCriteria'  # For sustainable solutions
        ]
        suggestions['explanation'] = (
            "Intelektualne in strokovne storitve zahtevajo oceno "
            "strokovnosti, izkušenj in kakovosti pristopa"
        )
        suggestions['category'] = 'intellectual_services'
        
    elif 'construction' in service_types:
        suggestions['recommended'] = [
            'shorterDeadline',  # Time efficiency
            'longerWarranty',  # Quality assurance
        ]
        suggestions['commonly_used'] = [
            'environmentalCriteria',  # Sustainability in construction
            'additionalTechnicalRequirements'  # Technical capabilities
        ]
        suggestions['explanation'] = (
            "Gradbena dela pogosto zahtevajo upoštevanje rokov, "
            "garancij in okoljskih standardov"
        )
        suggestions['category'] = 'construction'
        
    elif 'social_services' in service_types:
        suggestions['recommended'] = [
            'socialCriteria',  # Social impact
            'additionalReferences'  # Experience with vulnerable groups
        ]
        suggestions['commonly_used'] = [
            'additionalTechnicalRequirements'  # Specific methodologies
        ]
        suggestions['explanation'] = (
            "Socialne storitve zahtevajo posebno pozornost "
            "družbenim vidikom in izkušnjam z ranljivimi skupinami"
        )
        suggestions['category'] = 'social_services'
        
    elif 'environmental_services' in service_types:
        suggestions['recommended'] = [
            'environmentalCriteria',  # Environmental impact
            'additionalTechnicalRequirements'  # Environmental tech
        ]
        suggestions['commonly_used'] = [
            'additionalReferences',  # Past environmental projects
            'longerWarranty'  # Long-term reliability
        ]
        suggestions['explanation'] = (
            "Okoljske storitve zahtevajo dokazila o okoljski "
            "učinkovitosti in trajnostnih praksah"
        )
        suggestions['category'] = 'environmental_services'
        
    elif 'education_services' in service_types:
        suggestions['recommended'] = [
            'additionalReferences',  # Teaching experience
            'additionalTechnicalRequirements'  # Pedagogical approach
        ]
        suggestions['commonly_used'] = [
            'socialCriteria'  # Inclusive education
        ]
        suggestions['explanation'] = (
            "Izobraževalne storitve zahtevajo oceno pedagoških "
            "kompetenc in preteklih uspehov"
        )
        suggestions['category'] = 'education_services'
        
    elif 'technical_services' in service_types:
        suggestions['recommended'] = [
            'additionalTechnicalRequirements',  # Technical capabilities
            'longerWarranty'  # Service reliability
        ]
        suggestions['commonly_used'] = [
            'shorterDeadline',  # Quick response times
            'additionalReferences'  # Service track record
        ]
        suggestions['explanation'] = (
            "Tehnične storitve zahtevajo dokazila o tehnični "
            "usposobljenosti in zanesljivosti"
        )
        suggestions['category'] = 'technical_services'
        
    else:
        # Generic suggestions for unspecified service types
        suggestions['recommended'] = [
            'additionalReferences',
            'additionalTechnicalRequirements'
        ]
        suggestions['explanation'] = (
            "Priporočamo upoštevanje dodatnih meril za "
            "celovito oceno ponudb"
        )
        suggestions['category'] = 'general'
    
    return suggestions


def get_criteria_help_text() -> Dict[str, str]:
    """
    Get help text for each criterion.
    
    Returns:
        Dictionary mapping criterion keys to help text
    """
    return {
        'price': 'Osnovno merilo - primerjava cen ponudb. Najnižja cena dobi najvišje število točk.',
        'additionalReferences': (
            'Zahteva dokazila o preteklih uspešno izvedenih podobnih projektih. '
            'Ponudniki morajo predložiti reference z opisom projektov, vrednostmi in kontakti naročnikov.'
        ),
        'additionalTechnicalRequirements': (
            'Posebne tehnične zahteve glede opreme, kadra ali metodologije. '
            'Vključuje certifikate, standarde kakovosti ali specifične tehnične zmožnosti.'
        ),
        'shorterDeadline': (
            'Nagrajuje ponudnike, ki lahko projekt izvedejo hitreje od zahtevanega roka. '
            'Uporabno pri nujnih projektih ali sezonskih delih.'
        ),
        'longerWarranty': (
            'Vrednosti ponudbe z daljšo garancijsko dobo od minimalno zahtevane. '
            'Zagotavlja dolgoročno kakovost in zmanjšuje tveganja.'
        ),
        'environmentalCriteria': (
            'Upošteva okoljske vidike kot so emisije CO2, energetska učinkovitost, '
            'uporaba recikliranih materialov ali okoljski certifikati.'
        ),
        'socialCriteria': (
            'Vključuje socialne vidike kot so zaposlovanje ranljivih skupin, '
            'spodbujanje lokalnega gospodarstva ali družbena odgovornost.'
        )
    }


def get_criteria_display_names() -> Dict[str, str]:
    """
    Get display names for criteria.
    
    Returns:
        Dictionary mapping criterion keys to display names with icons
    """
    return {
        'price': '💰 Cena',
        'additionalReferences': '📋 Dodatne reference',
        'additionalTechnicalRequirements': '⚙️ Dodatne tehnične zahteve',
        'shorterDeadline': '⏱️ Krajši rok izvedbe',
        'longerWarranty': '🛡️ Daljša garancijska doba',
        'environmentalCriteria': '🌱 Okoljska merila',
        'socialCriteria': '👥 Socialna merila'
    }