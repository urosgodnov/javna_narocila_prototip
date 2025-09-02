"""Data migration utilities for Epic 3.0 field restructuring."""


def migrate_address_fields(data):
    """
    Migrate old combined address fields to new split structure (Story 3.0.1).
    
    Old: singleClientAddress, clients[].address
    New: singleClientStreetAddress, singleClientPostalCode, clients[].streetAddress, clients[].postalCode
    """
    if not data:
        return data
        
    # Migrate single client address
    if 'clientInfo' in data:
        client_info = data['clientInfo']
        
        # Handle single client address
        if 'singleClientAddress' in client_info and client_info['singleClientAddress']:
            address = client_info['singleClientAddress']
            # Try to split address intelligently
            parts = address.split(',')
            if len(parts) >= 2:
                # Assume format: "Street, Postal Code and City"
                street = parts[0].strip()
                postal = ','.join(parts[1:]).strip()
            else:
                # Can't split, put everything in street
                street = address
                postal = ""
            
            client_info['singleClientStreetAddress'] = street
            client_info['singleClientPostalCode'] = postal
            # Keep old field for backward compatibility but don't use it
            
        # Handle multiple clients array
        if 'clients' in client_info and isinstance(client_info['clients'], list):
            for client in client_info['clients']:
                if 'address' in client and client['address']:
                    address = client['address']
                    # Try to split address
                    parts = address.split(',')
                    if len(parts) >= 2:
                        street = parts[0].strip()
                        postal = ','.join(parts[1:]).strip()
                    else:
                        street = address
                        postal = ""
                    
                    client['streetAddress'] = street
                    client['postalCode'] = postal
                    # Keep old field for backward compatibility
    
    return data


def migrate_cofinancing_fields(data):
    """
    Migrate old combined co-financing fields to new split structure (Story 3.0.3).
    
    Old: name (naziv in naslov), program (naziv, področje in oznaka)
    New: cofinancerName, cofinancerAddress, programName, programArea, programCode
    """
    if not data:
        return data
    
    # Helper function to migrate a cofinancer object
    def migrate_cofinancer(cofinancer):
        if not cofinancer:
            return cofinancer
            
        # Migrate name field (naziv in naslov)
        if 'name' in cofinancer and cofinancer['name']:
            name_parts = cofinancer['name'].split(',')
            if len(name_parts) >= 2:
                cofinancer['cofinancerName'] = name_parts[0].strip()
                cofinancer['cofinancerAddress'] = ','.join(name_parts[1:]).strip()
            else:
                cofinancer['cofinancerName'] = cofinancer['name']
                cofinancer['cofinancerAddress'] = ""
        
        # Migrate program field (naziv, področje in oznaka)
        if 'program' in cofinancer and cofinancer['program']:
            program_parts = cofinancer['program'].split(',')
            if len(program_parts) >= 3:
                cofinancer['programName'] = program_parts[0].strip()
                cofinancer['programArea'] = program_parts[1].strip()
                cofinancer['programCode'] = program_parts[2].strip()
            elif len(program_parts) == 2:
                cofinancer['programName'] = program_parts[0].strip()
                cofinancer['programArea'] = program_parts[1].strip()
                cofinancer['programCode'] = ""
            else:
                cofinancer['programName'] = cofinancer['program']
                cofinancer['programArea'] = ""
                cofinancer['programCode'] = ""
        
        return cofinancer
    
    # Process lots cofinancers (main location)
    if 'lots' in data and isinstance(data['lots'], list):
        for lot in data['lots']:
            if 'cofinancers' in lot and isinstance(lot['cofinancers'], list):
                for i, cofinancer in enumerate(lot['cofinancers']):
                    lot['cofinancers'][i] = migrate_cofinancer(cofinancer)
    
    # Process mixed order components cofinancers
    if 'orderType' in data and 'mixedOrderComponents' in data['orderType']:
        components = data['orderType']['mixedOrderComponents']
        if isinstance(components, list):
            for component in components:
                if 'cofinancers' in component and isinstance(component['cofinancers'], list):
                    for i, cofinancer in enumerate(component['cofinancers']):
                        component['cofinancers'][i] = migrate_cofinancer(cofinancer)
    
    return data


def migrate_lot_mode(data):
    """
    Migrate lot_mode from 'none' to 'single' for unified lot architecture.
    Ensures at least one lot always exists.
    """
    import logging
    
    if not data:
        return data
    
    # Fix lot_mode if it's 'none'
    if data.get('lot_mode') == 'none':
        logging.info("[MIGRATION] Migrating lot_mode from 'none' to 'single'")
        data['lot_mode'] = 'single'
        
    # Ensure lots array exists with at least one lot
    if 'lots' not in data or not data['lots']:
        logging.info("[MIGRATION] No lots found, creating default 'Splošni sklop' lot")
        data['lots'] = [{'name': 'Splošni sklop', 'index': 0}]
        
    # If lot_mode is not set but we have no lots, set to single
    if 'lot_mode' not in data:
        if 'lots' in data and len(data.get('lots', [])) > 1:
            data['lot_mode'] = 'multiple'
        else:
            data['lot_mode'] = 'single'
        logging.info(f"[MIGRATION] Set lot_mode to '{data['lot_mode']}' based on lots count")
    
    return data


def migrate_form_data(data):
    """
    Apply all Epic 3.0 migrations to form data.
    """
    data = migrate_address_fields(data)
    data = migrate_cofinancing_fields(data)
    data = migrate_lot_mode(data)  # Fix lot_mode='none' issue
    return data