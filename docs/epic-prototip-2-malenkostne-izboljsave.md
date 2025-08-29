# Epic: Prototip-2-malenkostne-izboljšave - Brownfield Enhancement

## Epic Goal
Dodati ključne izboljšave uporabniške izkušnje in varnosti v obstoječ sistem javnih naročil, vključno s kopiranjem naročil, organizacijsko avtentikacijo, statusom naročil in lepšo vstopno stranjo.

## Epic Description

### Existing System Context:
- **Current functionality:** Streamlit aplikacija za vnos in upravljanje javnih naročil s podporo za skope, validacije in shranjevanje osnutkov
- **Technology stack:** Python, Streamlit, SQLite, MCP integrations
- **Integration points:** mainDB.db baza, admin modul, dashboard, form_renderer

### Enhancement Details:
- **What's being added/changed:** 
  - Direktno kopiranje naročil brez odpiranja forme
  - Password zaščita za organizacije
  - Status management za naročila
  - Login forma z izbiro organizacije
  
- **How it integrates:** Vse funkcionalnosti se gradijo na obstoječih vzorcih in strukturah baze podatkov

- **Success criteria:**
  - Kopiranje deluje z enim klikom
  - Passwordi so varno shranjeni (hashed)
  - Status se lahko spreminja inline v dashboardu
  - Login forma je estetska in funkcionalna

## Stories

### Story 1: Direktno kopiranje naročil
**Opis:** Implementirati funkcionalnost kopiranja naročila, ki ustvari novo naročilo v bazi z imenom "original (kopija)" brez odpiranja vnosne forme.

**Acceptance Criteria:**
- Gumb za kopiranje v dashboard vrstici
- Novo naročilo ima enake podatke kot original
- Ime se avtomatsko nastavi na "{original_name} (kopija)"
- Kopija dobi nov ID in timestamp

### Story 2: Organizacijska avtentikacija in status management
**Opis:** Dodati password polje za organizacije v admin modulu in implementirati inline status upravljanje za naročila.

**Acceptance Criteria:**
- Password polje v admin formi za organizacije
- Passwordi shranjeni z bcrypt/hashlib
- Status dropdown v dashboard vrstici (osnutek/potrjen/zaključen)
- AJAX-style update brez reload strani

### Story 3: Login forma z organizacijsko prijavo
**Opis:** Ustvariti elegantno login formo za izbiro organizacije in vnos passworda, ki se prikaže ob zagonu aplikacije.

**Acceptance Criteria:**
- Login forma pred vstopom v aplikacijo
- Dropdown z vsemi organizacijami
- Default: demo_organizacija
- UI design z MCP magic (21st.dev)
- Naslov "JAvna NAročila - JANA AI"
- Session management za prijavljeno organizacijo

## Compatibility Requirements
- [x] Existing APIs remain unchanged
- [x] Database schema changes are backward compatible (samo dodajanje polj)
- [x] UI changes follow existing Streamlit patterns
- [x] Performance impact is minimal

## Risk Mitigation
- **Primary Risk:** Varnostna ranljivost pri shranjevanju passwordov
- **Mitigation:** Uporaba bcrypt ali hashlib za hashing, nikoli plain text
- **Rollback Plan:** Backup baze pred migracijo, možnost disable login forme preko config flaga

## Definition of Done
- [ ] Vse 3 zgodbe implementirane in testirane
- [ ] Obstoječe funkcionalnosti delujejo nespremenjeno
- [ ] Passwordi varno shranjeni v bazi
- [ ] Login forma estetsko dovršena
- [ ] Dokumentacija posodobljena

---

## Story Manager Handoff:

"Please develop detailed user stories for this brownfield epic. Key considerations:

- This is an enhancement to an existing Streamlit system for public procurement management
- Integration points: mainDB.db SQLite database, admin.py module, dashboard.py, existing session state management
- Existing patterns to follow: Streamlit session state, SQLite with direct queries, existing UI components
- Critical compatibility requirements: All existing procurements must remain accessible, database migrations must be safe
- Each story must include verification that existing functionality remains intact

The epic should maintain system integrity while delivering improved user experience through copy functionality, organization-level security, status management, and an elegant login interface."