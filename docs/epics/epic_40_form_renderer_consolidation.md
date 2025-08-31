# Epic 40: Form Renderer Consolidation & Unified Lot Architecture

## Epic Overview
**ID**: EPIC-40  
**Title**: Konsolidacija form_renderer sistema z uniformnim pristopom sklopov  
**Priority**: HIGH  
**Estimated Effort**: 3-4 sprints  
**Risk Level**: HIGH (jedro sistema)  
**Business Value**: Drastično poenostavljena arhitektura, zmanjšani bugi, lažje dodajanje novih funkcionalnosti  

## Problem Statement

### Trenutne težave
1. **Monolitna datoteka**: `form_renderer.py` ima 1400+ vrstic kode
2. **Pomešana odgovornost**: Ista funkcija renderira preprosta polja IN kompleksne sklope
3. **Nedosledna obravnava sklopov**: Ko imamo več sklopov, stvari "pač ne delajo"
4. **Kompleksnost konteksta**: `lot_context` se prenaša povsod brez jasne strukture
5. **Duplicirana logika**: Podobna koda na več mestih za različne tipe polj
6. **Težko testiranje**: Ni mogoče izolirati in testirati posameznih delov
7. **Session state kaos**: Nedosledno scopiranje ključev na sklope
8. **Dva načina delovanja**: Forme z in brez sklopov se obravnavajo različno

### Posledice
- Developerji se izgubljajo v kodi
- Popravki na enem mestu pokvarijo drugo
- Dodajanje novih tipov polj je kompleksno
- Performance problemi pri velikih formah
- Regression bugi pri spremembah
- Kompleksna if/else logika za različne načine

## Proposed Solution

### Ključna inovacija: Unified Lot Architecture (VSE JE SKLOP)

**Glavni princip**: Vse forme imajo sklope. Forme brez eksplicitnih sklopov dobijo en "General" sklop z indeksom 0.

#### Prednosti uniformnega pristopa:
- **Ena pot za vse** - ni več `if has_lots` preverjanj
- **Konsistenten session state** - vedno `lots[index].field`
- **Enostavnejše testiranje** - samo en flow za testirati
- **Čistejša koda** - brez posebnih primerov
- **Lažja migracija** - avtomatska pretvorba v lot strukturo

### Arhitekturni pristop: Separation of Concerns

```
┌─────────────────────────────────────────┐
│           FormController                 │ ← Orkestrira celoten proces
└─────────────┬───────────────────────────┘
              │
    ┌─────────┴─────────┬──────────────┐
    ▼                   ▼               ▼
┌──────────┐   ┌──────────────┐  ┌─────────────┐
│FormContext│   │SectionRenderer│  │LotManager   │
└──────────┘   └──────────────┘  └─────────────┘
    │                   │               │
    └───────┬───────────┴───────────────┘
            ▼
    ┌──────────────┐
    │FieldRenderer │ ← Renderira posamezna polja
    └──────────────┘
```

### Ključne komponente

1. **FormContext** (`utils/form_context.py`)
   - Centralizirano upravljanje konteksta
   - **NOVO: Avtomatska lot struktura za vse forme**
   - Session state management (vedno lot-scoped)
   - Validation state
   - Uniformno lot scoping (brez if/else)

2. **FieldRenderer** (`ui/renderers/field_renderer.py`)
   - Renderiranje osnovnih tipov polj
   - Validacija na nivoju polja
   - Field-specific widgeti
   - **Vedno uporablja lot-scoped keys**

3. **SectionRenderer** (`ui/renderers/section_renderer.py`)
   - Renderiranje sekcij/objektov
   - Sekcijska validacija
   - Conditional rendering logic
   - **Konsistentno lot-aware renderiranje**

4. **LotManager** (`ui/renderers/lot_manager.py`)
   - Upravljanje sklopov
   - **NOVO: Avtomatski "General" sklop za simple forme**
   - Lot navigation
   - Lot-specific state
   - Migracija legacy podatkov v lot strukturo

5. **FormController** (`ui/form_controller.py`)
   - Glavni orkestrator
   - Step management
   - Form submission
   - **Garantira lot strukturo ob inicializaciji**

## Success Criteria

### Must Have
- [ ] Form_renderer.py razdeljen na manjše module (<300 vrstic vsak)
- [ ] **Uniformni lot pristop implementiran (vse forme imajo sklope)**
- [ ] **Čisti rez - nova implementacija brez legacy kode**
- [ ] Jasna separacija odgovornosti
- [ ] Centralizirano upravljanje session state
- [ ] **Odstranjena vsa if/else logika za has_lots**
- [ ] Unit testi za vsako komponento

### Should Have
- [ ] Dokumentacija nove arhitekture
- [ ] **Clear-cut migration - en korak, brez vmesnih stanj**
- [ ] Performance metrics (before/after)
- [ ] Error handling improvements

### Nice to Have
- [ ] Hot-reload pri razvoju
- [ ] Dev tools za debugging
- [ ] Visual form builder

## Technical Approach

### Faza 1: Priprava (Sprint 1)
- Analiza obstoječe kode
- Identifikacija dependencies
- Priprava test suite
- Setup nove strukture direktorijev
- **NOVO: Design uniformne lot strukture**

### Faza 2: Core Components (Sprint 2)
- Implementacija FormContext **z avtomatsko lot strukturo**
- **Implementacija auto-migration za legacy podatke**
- Implementacija FieldRenderer (lot-aware)
- Basic integration testi

### Faza 3: Complex Components (Sprint 3)
- SectionRenderer (uniformno lot handling)
- LotManager **z General sklop podporo**
- FormController **z garantirano lot strukturo**

### Faza 4: Clean Switch & Testing (Sprint 4)
- **Direkten preklop na novi sistem (brez postopne migracije)**
- **Popolna zamenjava starega sistema**
- Regression testing
- Performance testing
- Bug fixes

## Risks & Mitigation

### Risk 1: Breaking Changes
**Verjetnost**: HIGH  
**Impact**: HIGH  
**Mitigacija**: 
- Feature flags za postopen rollout
- Parallel run (stari in novi sistem)
- Comprehensive test coverage

### Risk 2: Performance Degradation
**Verjetnost**: MEDIUM  
**Impact**: MEDIUM  
**Mitigacija**:
- Performance benchmarks pred spremembo
- Profiling kritičnih poti
- Caching strategy

### Risk 3: Developer Adoption
**Verjetnost**: LOW  
**Impact**: MEDIUM  
**Mitigacija**:
- Jasna dokumentacija
- Pair programming sessions
- Gradual migration

## Dependencies

### Technical Dependencies
- Streamlit 1.28+
- Python 3.10+
- Existing validation system
- Existing lot_utils

### Team Dependencies
- Frontend team za UI testing
- QA team za regression testing
- DevOps za deployment strategy

## Rollback Plan

1. **Git Strategy**: Vse spremembe v ločeni branch
2. **Database**: Ni sprememb v DB shemi
3. **Quick Revert**: `git revert` če kritični problemi
4. **No Feature Flags**: Čisti preklop, brez vmesnih stanj

## Metrics for Success

### Quantitative
- Redukcija vrstic kode: 1400 → <1000 total
- File size: 1 file → 5-7 focused files
- **Odstranjena if/else logika: 100% lot-related preverjanj**
- **Konsistentnost: 100% form uporablja lot strukturo**
- Test coverage: 0% → >80%
- Performance: ≤ current render time
- Bug reduction: 50% manj form-related bugov
- **Redukcija kompleksnosti: Cyclomatic complexity -40%**

### Qualitative
- Developer satisfaction (survey)
- Easier onboarding novim developerjem
- Faster feature development
- Cleaner code reviews
- **"One way to do things" princip**

## Timeline

```
Week 1-2:  [████████] Analiza & Setup
Week 3-4:  [████████] Core Components
Week 5-6:  [████████] Complex Components  
Week 7-8:  [████████] Migration & Testing
Week 9:    [████    ] Buffer & Documentation
```

## Stakeholders

- **Product Owner**: Approval za refactoring
- **Tech Lead**: Architecture review
- **Development Team**: Implementation
- **QA Team**: Testing strategy
- **End Users**: UAT po implementaciji

## Notes & Considerations

1. **Clean Break**: Novi sistem v celoti nadomesti starega
2. **Big Bang Release**: En preklop, brez vmesnih stanj
3. **Documentation First**: Dokumentiramo preden implementiramo
4. **Test Driven**: Pišemo teste pred kodo
5. **Performance Aware**: Merimo performance na vsakem koraku
6. **Unified Approach**: VSE forme imajo sklope (tudi če samo enega)
7. **No Backward Compatibility**: Čisti rez, brez legacy podpore
8. **No Special Cases**: Izogibamo se posebnim primerom in if/else logiki

## Related Documentation

- Current form_renderer.py analysis
- UI Consolidation (January 2025)
- Validation system documentation
- Lot management specifications

---
*Epic created: 2025-01-29*  
*Status: DRAFT*  
*Author: AI Assistant*  
*Review needed by: Tech Lead*