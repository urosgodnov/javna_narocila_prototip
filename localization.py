"""
Centralized localization system for Slovenian translations.
"""

# UI Text Translations
UI_TEXTS = {
    # Page titles and headers
    "app_title": "Generator dokumentacije za javna naročila",
    "form_header": "Obrazec za vnos",
    "admin_header": "Administracija predlog",
    "navigation_header": "Navigacija",
    "drafts_header": "Osnutki",
    
    # Navigation
    "go_to": "Pojdi na",
    "back_button": "Nazaj",
    "next_button": "Naprej", 
    "submit_button": "Pripravi dokumente",
    "previous_step": "Prejšnji korak",
    "next_step": "Naslednji korak",
    
    # Progress and steps
    "step": "Korak",
    "of_total": "od",
    "progress": "Napredek",
    "completed": "Zaključeno",
    "current": "Trenutno",
    "pending": "Čaka",
    
    # Form actions
    "save_draft": "Shrani osnutek",
    "load_draft": "Naloži osnutek", 
    "load_selected_draft": "Naloži izbrani osnutek",
    "delete_draft": "Izbriši osnutek",
    
    # Messages
    "no_drafts": "Ni shranjenih osnutkov.",
    "draft_saved": "Osnutek uspešno shranjen z ID: {draft_id}",
    "draft_loaded": "Osnutek uspešno naložen!",
    "draft_load_error": "Napaka pri nalaganju osnutka.",
    "documents_prepared": "Dokumenti uspešno pripravljeni!",
    "form_submitted_with_data": "Obrazec poslan s podatki:",
    "schema_file_not_found": "Datoteka sheme '{filename}' ni najdena.",
    
    # Validation messages
    "field_required": "To polje je obvezno",
    "invalid_email": "Neveljaven e-poštni naslov",
    "invalid_number": "Neveljaven števil",
    "field_too_short": "Polje je prekratko (minimalno {min_length} znakov)",
    "field_too_long": "Polje je predolgo (maksimalno {max_length} znakov)",
    "invalid_date": "Neveljaven datum",
    "invalid_selection": "Neveljavna izbira",
    "fill_required_field": "Prosimo, izpolnite obvezno polje: {field_name}",
    
    # Form field labels and descriptions
    "optional_field": "(neobvezno)",
    "required_field": "*",
    "select_option": "Izberite možnost...",
    "select_multiple": "Izberite eno ali več možnosti...",
    "upload_file": "Naložite datoteko...",
    "enter_text": "Vnesite besedilo...",
    "enter_number": "Vnesite številko...",
    "select_date": "Izberite datum...",
    
    # Status indicators
    "status_draft": "Osnutek",
    "status_in_progress": "V izdelavi", 
    "status_completed": "Zaključeno",
    "status_submitted": "Poslano",
    "status_error": "Napaka",
    
    # Help and tooltips
    "help": "Pomoč",
    "more_info": "Več informacij",
    "show_help": "Prikaži pomoč",
    "hide_help": "Skrij pomoč",
    "info": "Informacija",
    "warning": "Opozorilo",
    "error": "Napaka",
    "success": "Uspeh",
    
    # File operations
    "file_uploaded": "Datoteka uspešno naložena",
    "file_upload_error": "Napaka pri nalaganju datoteke",
    "file_too_large": "Datoteka je prevelika",
    "invalid_file_type": "Neveljavna vrsta datoteke",
    
    # General actions
    "add": "Dodaj",
    "remove": "Odstrani", 
    "edit": "Uredi",
    "save": "Shrani",
    "cancel": "Prekliči",
    "confirm": "Potrdi",
    "reset": "Ponastavi",
    "clear": "Počisti",
    "search": "Iskanje",
    "filter": "Filter",
    
    # Time and dates
    "today": "Danes",
    "yesterday": "Včeraj", 
    "tomorrow": "Jutri",
    "date_format": "dd.mm.yyyy",
    "time_format": "uu:mm",
}

# Validation error messages
VALIDATION_MESSAGES = {
    "required": "To polje je obvezno",
    "email": "Vnesite veljaven e-poštni naslov",
    "number": "Vnesite veljavno številko", 
    "integer": "Vnesite celo število",
    "decimal": "Vnesite decimalno število",
    "min_length": "Minimalno {min} znakov",
    "max_length": "Maksimalno {max} znakov",
    "min_value": "Minimalna vrednost je {min}",
    "max_value": "Maksimalna vrednost je {max}",
    "date": "Vnesite veljaven datum (dd.mm.yyyy)",
    "time": "Vnesite veljaven čas (uu:mm)",
    "url": "Vnesite veljaven spletni naslov",
    "phone": "Vnesite veljaven telefonsko številko",
    "postal_code": "Vnesite veljavno poštno številko",
}

# Form section progress indicators - updated for 15-step structure
STEP_LABELS = {
    1: "Podatki o naročniku",
    2: "Osnovni podatki naročila", 
    3: "Pravna podlaga",
    4: "Postopek in informacije o sklopih",
    5: "Konfiguracija sklopov",
    6: "Vrsta naročila",
    7: "Tehnične zahteve",
    8: "Roki izvajanja",
    9: "Informacije o ceni",
    10: "Ogledi in pogajanja",
    11: "Pogoji za sodelovanje in razlogi za izključitev", 
    12: "Zavarovanja in ponudbe",
    13: "Merila izbire",
    14: "Sklepanje pogodbe",
    15: "Dodatne informacije"
}

def get_text(key: str, **kwargs) -> str:
    """
    Get localized text by key with optional formatting.
    
    Args:
        key: Translation key
        **kwargs: Format parameters
        
    Returns:
        Localized text string
    """
    text = UI_TEXTS.get(key, key)
    if kwargs:
        try:
            return text.format(**kwargs)
        except (KeyError, ValueError):
            return text
    return text

def get_validation_message(validation_type: str, **kwargs) -> str:
    """
    Get validation error message by type.
    
    Args:
        validation_type: Type of validation error
        **kwargs: Format parameters
        
    Returns:
        Localized validation message
    """
    message = VALIDATION_MESSAGES.get(validation_type, "Neveljavna vrednost")
    if kwargs:
        try:
            return message.format(**kwargs)
        except (KeyError, ValueError):
            return message
    return message

def get_step_label(step_number: int) -> str:
    """
    Get localized step label by step number.
    
    Args:
        step_number: Step number (1-based)
        
    Returns:
        Localized step label
    """
    return STEP_LABELS.get(step_number, f"Korak {step_number}")

def format_step_indicator(current_step: int, total_steps: int) -> str:
    """
    Format step indicator text.
    
    Args:
        current_step: Current step number (0-based)
        total_steps: Total number of steps
        
    Returns:
        Formatted step indicator
    """
    return f"{get_text('step')} {current_step + 1} {get_text('of_total')} {total_steps}"