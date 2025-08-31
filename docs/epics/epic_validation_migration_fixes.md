# Epic: Popravki Migracije Validacij in Optimizacija - Brownfield Enhancement

## Epic Goal
Odpraviti napake, ki so nastale pri migraciji validacij iz starega form_renderer sistema v novo unified lot arhitekturo ter optimizirati obstoječe validacije za boljšo uporabniško izkušnjo.

## Epic Description

### Existing System Context:
- **Trenutno stanje**: Nova forma arhitektura je delno implementirana (FormController, unified lot handling)
- **Technology stack**: Python, Streamlit, SQLite
- **Integration points**: 
  - `utils/validations.py` - obstoječe validacije
  - `ui/controllers/form_controller.py` - nov sistem
  - `ui/form_renderer_compat.py` - compatibility layer
  - Session state management

### Enhancement Details:
- **Kaj popravljamo**: Napake pri migraciji validacij iz starega v nov sistem
- **Kako**: 
  - Pregled vseh validate_* metod v ValidationManager
  - Uskladitev z unified lot konceptom (vse je sklop)
  - Popravki napak v conditional validaciji
  - Optimizacija sporočil napak
- **Success criteria**: 
  - Vse validacije delujejo v novi arhitekturi
  - Pogojne validacije se pravilno prikazujejo
  - Unified lot handling deluje konsistentno
  - Jasna sporočila napak v slovenščini

## Stories

### Story 1: Popravki Core Validacij in Unified Lot Handling
**Opis**: Popraviti osnovne validacije da pravilno delujejo z unified lot konceptom
- Pregled in popravek `validate_screen_5_lots()` 
- Zagotoviti da naročilo brez sklopov = 1 virtualni sklop
- Popraviti `validate_order_type()` za unified handling
- Optimizirati sporočila napak

### Story 2: Popravki Conditional Validacij in Required Polj
**Opis**: Odpraviti napake v pogojnih validacijah in dinamičnem označevanju obveznih polj
- Popraviti render_if evaluacijo
- Dinamične zvezdice (*) za pogojno obvezna polja
- Array validacije (clients, lots, cofinancers)
- Real-time re-evaluacija ob spremembi trigger polj

### Story 3: Optimizacija Cross-Field Validacij in CPV Omejitev
**Opis**: Optimizirati kompleksne validacije in CPV-based omejitve
- Validacija meril in točk (vsota = 100)
- CPV omejitve (cena ne sme biti edino merilo, socialna merila)
- Tiebreaker validacija
- Datumski razponi in format validacije

## Compatibility Requirements
- [x] Obstoječe ValidationManager metode ostanejo, samo optimizirane
- [x] Session state struktura ostane kompatibilna
- [x] UI stiliranje že implementirano, ne spreminjamo
- [x] Unified lot koncept že deluje, samo popravki

## Risk Mitigation
- **Primary Risk**: Pokvarimo delujočo novo arhitekturo
- **Mitigation**: 
  - Testiranje vsake spremembe posebej
  - Ohranimo backup trenutnega stanja
  - Spremembe samo v validacijskih metodah
- **Rollback Plan**: Git revert na posamezne commite

## Definition of Done
- [ ] Vse validacije delujejo v novi unified lot arhitekturi
- [ ] Napake iz migracije odpravljene
- [ ] Pogojne validacije delujejo pravilno
- [ ] Sporočila napak v slovenščini in jasna
- [ ] Ni regresij v obstoječi funkcionalnosti
- [ ] Testiranje vseh korakov forme

## Tehnični Detajli

### Ključne Napake za Popravek:
1. **Unified Lot Handling**:
   - `validate_screen_5_lots()` mora razumeti da brez sklopov = 1 sklop
   - Order type validacija mora delovati za virtualni sklop

2. **Conditional Validacije**:
   - Pogojno obvezna polja se ne označujejo pravilno
   - Array minimum validacije ne delujejo (clients, lots)
   - Sofinancerji validacija

3. **Cross-Field Validacije**:
   - Datum razponi (start <= end)
   - Merila točke vsota != 100
   - CPV omejitve se ne preverjajo

### Obseg Sprememb:
- **NE SPREMINJAMO**: UI komponente, stiliranje, FormController arhitekturo
- **SPREMINJAMO SAMO**: Validacijske metode v `utils/validations.py`
- **ODSTRANIMO**: Finančne validacije (IBAN, SWIFT) - bo v ločenem storiju

### Prioritete:
1. **VISOKA**: Popravki ki blokirajo normalno uporabo (required polja, unified lots)
2. **SREDNJA**: Optimizacije sporočil in conditional validacije
3. **NIZKA**: Edge cases in nice-to-have izboljšave

## Časovna Ocena
- Story 1: 3-4 ure (core validacije)
- Story 2: 4-5 ur (conditional sistem)
- Story 3: 3-4 ure (cross-field in CPV)
- **Skupaj**: 10-13 ur

## Dependencies
- Nova FormController arhitektura mora ostati nespremenjena
- Session state struktura mora ostati kompatibilna
- Obstoječe UI komponente se ne smejo pokvariti

## Notes
- Finančne validacije (IBAN, SWIFT, Bank) bodo v ločenem storiju
- Fokus je na popravkih migracijskih napak, ne dodajanju novih features
- Stari form_renderer je samo referenca, ne kopiramo direktno