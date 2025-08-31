# Epic 40: Form Renderer Consolidation - User Stories

## Sprint 1: Foundation & Analysis

### Story 40.1: Code Analysis & Dependency Mapping with Lot Unification Focus
**Points**: 5  
**Priority**: P0 (Critical)  
**Type**: Technical Task  

**Description**:  
Kot developer želim imeti popoln pregled nad obstoječo kodo in identificirati vso if/else logiko povezano s sklopi.

**Acceptance Criteria**:
- [ ] Dokumentiran seznam vseh funkcij v form_renderer.py
- [ ] **Identificirana vsa mesta z `if has_lots` ali podobno logiko**
- [ ] **Seznam vseh mest kjer se različno obravnavajo forme z/brez sklopov**
- [ ] Dependency graph (kaj kliče kaj)
- [ ] Seznam vseh mest kjer se uporablja render_form()
- [ ] Risk assessment za vsak del kode

**Technical Notes**:
```python
# Potrebna analiza:
- render_form() - glavna funkcija (433 vrstic)
- _should_render() - conditional logic (260 vrstic)
- Session state keys in njihovo scopiranje
- Lot context flow
- Validation touchpoints
```

**Deliverables**:
- analysis_report.md
- dependency_graph.svg
- risk_matrix.xlsx

---

### Story 40.2: Test Suite Setup
**Points**: 8  
**Priority**: P0 (Critical)  
**Type**: Development  

**Description**:  
Kot developer želim imeti comprehensive test suite PREDEN začnem refaktorirati, da lahko zagotovim, da nič ne pokvarim.

**Acceptance Criteria**:
- [ ] Unit testi za vse glavne funkcije current form_renderer.py
- [ ] Integration testi za celoten form flow
- [ ] Snapshot testi za rendered output
- [ ] Performance benchmarks (baseline)
- [ ] Test coverage > 70% za kritične poti

**Implementation**:
```python
# tests/test_form_renderer_baseline.py
class TestFormRendererBaseline:
    def test_simple_string_field(self):
        """Test basic string field rendering"""
        
    def test_object_with_properties(self):
        """Test nested object rendering"""
        
    def test_array_of_objects(self):
        """Test array handling"""
        
    def test_lot_context_scoping(self):
        """Test lot-specific field scoping"""
        
    def test_conditional_rendering(self):
        """Test render_if logic"""
```

---

### Story 40.3: Create New Directory Structure
**Points**: 2  
**Priority**: P0 (Critical)  
**Type**: Setup  

**Description**:  
Kot developer želim imeti jasno strukturo direktorijev za nove komponente.

**Acceptance Criteria**:
- [ ] Nova struktura ustvarjena
- [ ] __init__.py files dodani
- [ ] README.md v vsakem direktoriju
- [ ] Import poti testirane

**Structure**:
```
ui/
├── renderers/
│   ├── __init__.py
│   ├── field_renderer.py      # Basic fields
│   ├── section_renderer.py    # Complex sections
│   ├── lot_manager.py         # Lot handling
│   └── README.md
├── controllers/
│   ├── __init__.py
│   ├── form_controller.py     # Main orchestrator
│   └── README.md
└── form_renderer.py           # Legacy (for transition)

utils/
├── form_context.py            # Context management
└── form_state.py              # State helpers
```

---

## Sprint 2: Core Components

### Story 40.4: Implement Unified FormContext Class
**Points**: 5  
**Priority**: P0 (Critical)  
**Type**: Development  

**Description**:  
Kot developer želim centralizirano upravljanje konteksta z uniformnim lot pristopom, kjer VSE forme imajo sklope.

**Acceptance Criteria**:
- [ ] FormContext class implementiran
- [ ] **Avtomatska lot struktura za vse forme**
- [ ] **Brez podpore za legacy podatke**
- [ ] Session state key resolution (vedno lot-scoped)
- [ ] Validation context
- [ ] Thread-safe za Streamlit
- [ ] 100% test coverage

**Implementation**:
```python
# utils/form_context.py
@dataclass
class FormContext:
    lot_index: int = 0  # Vedno imamo lot index (default 0 za "General")
    current_step: Optional[str] = None
    validation_errors: Dict = field(default_factory=dict)
    session_state: Any = None  # Streamlit session state reference
    
    def __post_init__(self):
        """Ensure lot structure exists"""
        self.ensure_lot_structure()
    
    def ensure_lot_structure(self):
        """Garantira da obstaja lot struktura"""
        if 'lots' not in self.session_state:
            self.session_state['lots'] = [{
                'name': 'General',
                'index': 0
            }]
        elif len(self.session_state['lots']) == 0:
            self.session_state['lots'].append({
                'name': 'General',
                'index': 0
            })
    
    # Brez migrate_legacy_data - čisti začetek
    # Vse forme začnejo z lot strukturo
    
    def get_field_key(self, field_name: str, force_global: bool = False) -> str:
        """VEDNO vrni lot-scoped key (razen za globalne)"""
        if force_global or field_name in GLOBAL_FIELDS:
            return field_name
        
        # VSE ostalo je lot-scoped
        return f"lots.{self.lot_index}.{field_name}"
    
    def get_field_value(self, field_name: str, default: Any = None) -> Any:
        """Get field value from session state"""
        key = self.get_field_key(field_name)
        return self.session_state.get(key, default)
    
    def set_field_value(self, field_name: str, value: Any) -> None:
        """Set field value in session state"""
        key = self.get_field_key(field_name)
        self.session_state[key] = value
```

---

### Story 40.5: Extract Basic Field Rendering
**Points**: 8  
**Priority**: P1 (High)  
**Type**: Development  

**Description**:  
Kot developer želim, da so vsa osnovna polja (string, number, boolean, date) renderirana v ločenem modulu.

**Acceptance Criteria**:
- [ ] FieldRenderer class za osnovne tipe
- [ ] Podpora za vse trenutne field types
- [ ] Validacija integrirana
- [ ] Localization support
- [ ] Backward compatible output

**Implementation**:
```python
# ui/renderers/field_renderer.py
class FieldRenderer:
    def __init__(self, context: FormContext, validator: RealTimeValidator):
        self.context = context
        self.validator = validator
        
    def render_field(self, 
                    field_name: str, 
                    field_schema: dict,
                    parent_key: str = "") -> Any:
        """Main entry point for field rendering"""
        field_type = field_schema.get('type')
        
        if field_type == 'string':
            return self._render_string_field(field_name, field_schema, parent_key)
        elif field_type == 'number':
            return self._render_number_field(field_name, field_schema, parent_key)
        elif field_type == 'boolean':
            return self._render_boolean_field(field_name, field_schema, parent_key)
        # ... etc
        
    def _render_string_field(self, field_name: str, schema: dict, parent_key: str):
        full_key = f"{parent_key}.{field_name}" if parent_key else field_name
        session_key = self.context.get_field_key(full_key)
        
        # Get field properties
        label = schema.get('title', field_name)
        help_text = schema.get('description')
        default = schema.get('default', '')
        
        # Handle different string subtypes
        if schema.get('format') == 'date':
            return self._render_date_picker(session_key, label, help_text, default)
        elif 'enum' in schema:
            return self._render_select_box(session_key, label, schema['enum'], help_text, default)
        else:
            return self._render_text_input(session_key, label, help_text, default)
```

---

### Story 40.6: Create Section Renderer
**Points**: 8  
**Priority**: P1 (High)  
**Type**: Development  

**Description**:  
Kot developer želim ločeno renderiranje sekcij (objektov), da lahko kontroliram njihovo hierarhijo in layout.

**Acceptance Criteria**:
- [ ] SectionRenderer za objekte
- [ ] Podpora za nested objects
- [ ] Conditional rendering (render_if)
- [ ] Section headers in help text
- [ ] Special handling (socialCriteriaOptions indentation)

**Implementation**:
```python
# ui/renderers/section_renderer.py
class SectionRenderer:
    def __init__(self, field_renderer: FieldRenderer, context: FormContext):
        self.field_renderer = field_renderer
        self.context = context
        
    def render_section(self, 
                       section_name: str,
                       section_schema: dict,
                       parent_key: str = "") -> None:
        """Render a section (object type)"""
        
        # Check if should render
        if not self._should_render(section_schema):
            return
            
        full_key = f"{parent_key}.{section_name}" if parent_key else section_name
        
        # Handle $ref
        if "$ref" in section_schema:
            section_schema = self._resolve_ref(section_schema["$ref"])
            
        # Render section header if needed
        if "title" in section_schema:
            st.subheader(section_schema["title"])
            
        # Special handling for specific sections
        if section_name == "socialCriteriaOptions":
            self._render_indented_section(section_schema, full_key)
        else:
            self._render_properties(section_schema.get("properties", {}), full_key)
```

---

## Sprint 3: Complex Components

### Story 40.7: Implement Unified Lot Manager
**Points**: 13  
**Priority**: P1 (High)  
**Type**: Development  

**Description**:  
Kot developer želim centralizirano upravljanje sklopov z garantirano lot strukturo za VSE forme.

**Acceptance Criteria**:
- [ ] LotManager class implementiran
- [ ] **Avtomatski "General" sklop za simple forme**
- [ ] Lot navigation (prev/next)
- [ ] Lot state management
- [ ] Lot context switching
- [ ] Copy data between lots funkcionalnost
- [ ] Lot validation summary
- [ ] **Podpora za dinamično dodajanje/odstranjevanje sklopov**

**Implementation**:
```python
# ui/renderers/lot_manager.py
class LotManager:
    def __init__(self, context: FormContext):
        self.context = context
        # Vedno zagotovi lot strukturo
        self.context.ensure_lot_structure()
        
    def get_current_lot(self) -> dict:
        """Get current lot data - VEDNO vrne lot (nikoli None)"""
        lots = self.context.session_state.get('lots', [])
        
        # Če ni sklopov, ustvari General
        if not lots:
            self.context.ensure_lot_structure()
            lots = self.context.session_state['lots']
        
        # Vedno vrni veljaven lot
        if 0 <= self.context.lot_index < len(lots):
            return lots[self.context.lot_index]
        else:
            # Fallback na prvi lot
            return lots[0]
        
    def switch_to_lot(self, lot_index: int) -> bool:
        """Switch context to different lot"""
        lots = self.context.session_state.get('lots', [])
        if 0 <= lot_index < len(lots):
            self.context.lot_index = lot_index
            return True
        return False
        
    def copy_lot_data(self, from_index: int, to_index: int, fields: List[str]) -> None:
        """Copy specific fields from one lot to another"""
        for field in fields:
            from_key = f"lots.{from_index}.{field}"
            to_key = f"lots.{to_index}.{field}"
            if from_key in self.context.session_state:
                self.context.session_state[to_key] = self.context.session_state[from_key]
```

---

### Story 40.8: Build Form Controller
**Points**: 8  
**Priority**: P1 (High)  
**Type**: Development  

**Description**:  
Kot developer želim glavni orkestrator, ki koordinira vse komponente in upravlja form lifecycle.

**Acceptance Criteria**:
- [ ] FormController implementiran
- [ ] Step management
- [ ] Component coordination
- [ ] Form submission handling
- [ ] Error handling
- [ ] Progress tracking

**Implementation**:
```python
# ui/controllers/form_controller.py
class FormController:
    def __init__(self):
        self.context = FormContext(session_state=st.session_state)
        self.field_renderer = FieldRenderer(self.context, RealTimeValidator())
        self.section_renderer = SectionRenderer(self.field_renderer, self.context)
        self.lot_manager = LotManager(self.context)
        
    def render_form(self, schema: dict, step: str = None) -> None:
        """Main entry point - replaces old render_form()"""
        
        # Set current step in context
        if step:
            self.context.current_step = step
            
        # Get properties for current step
        properties = self._get_step_properties(schema, step)
        
        # Render based on type
        for prop_name, prop_schema in properties.items():
            self._render_property(prop_name, prop_schema)
            
    def _render_property(self, name: str, schema: dict) -> None:
        """Route property to appropriate renderer"""
        prop_type = schema.get('type')
        
        if prop_type == 'object':
            self.section_renderer.render_section(name, schema)
        elif prop_type == 'array':
            self._render_array(name, schema)
        else:
            self.field_renderer.render_field(name, schema)
```

---

## Sprint 4: Migration & Integration

### Story 40.9: Direct System Replacement
**Points**: 5  
**Priority**: P0 (Critical)  
**Type**: Development  

**Description**:  
Kot developer želim direktno zamenjati stari sistem z novim, brez vmesnih stanj.

**Acceptance Criteria**:
- [ ] **Popolna zamenjava render_form() funkcije**
- [ ] **Brez backward compatibility**
- [ ] **Čisti preklop na novi sistem**
- [ ] Logging za monitoring
- [ ] Clear error messages če kaj ne dela

**Implementation**:
```python
# ui/form_renderer.py (NOVA IMPLEMENTACIJA)
def render_form(schema_properties, **kwargs):
    """Completely new implementation - no legacy support"""
    
    # Ignoriraj stare parametre
    # VSE forme imajo sklope
    controller = FormController()
    controller.render_form(schema_properties)

# Stari form_renderer.py se izbriše
# Ni vmesnih stanj, ni feature flags
# Čisti preklop
```

---

### Story 40.10: Implement All Forms with Lot Structure
**Points**: 5  
**Priority**: P1 (High)  
**Type**: Development  

**Description**:  
Kot developer želim implementirati VSE forme z uniformno lot strukturo.

**Acceptance Criteria**:
- [ ] VSE forme uporabljajo lot strukturo
- [ ] **Simple forme dobijo General sklop**
- [ ] **Ni posebne obravnave za forme brez sklopov**
- [ ] Performance primerjava
- [ ] Vsi testi passajo

**Test Plan**:
1. Implementiraj v test branch
2. Run vsi testi
3. Primerjaj performance
4. Deploy v celoti ali rollback
5. Ni postopnega rollout-a

---

### Story 40.11: Migrate Complex Forms with Lots
**Points**: 8  
**Priority**: P1 (High)  
**Type**: Development  

**Description**:  
Kot developer želim migrirati forme s sklopi na novi sistem.

**Acceptance Criteria**:
- [ ] Lot forms identificirane
- [ ] Lot navigation dela
- [ ] Lot scoping dela pravilno
- [ ] Copy between lots dela
- [ ] Validation per lot dela

---

### Story 40.12: Performance Optimization
**Points**: 5  
**Priority**: P2 (Medium)  
**Type**: Optimization  

**Description**:  
Kot developer želim optimizirati performance novega sistema.

**Acceptance Criteria**:
- [ ] Render time ≤ kot stari sistem
- [ ] Memory usage optimiziran
- [ ] Caching implementiran kjer smiselno
- [ ] Lazy loading za velike forme
- [ ] Performance dashboard

**Metrics to Track**:
- Initial render time
- Re-render on change
- Memory usage
- CPU usage
- Network requests (if any)

---

### Story 40.13: Documentation & Training
**Points**: 3  
**Priority**: P2 (Medium)  
**Type**: Documentation  

**Description**:  
Kot developer želim dokumentacijo za novi sistem.

**Acceptance Criteria**:
- [ ] Architecture dokumentacija
- [ ] Migration guide
- [ ] API reference
- [ ] Examples
- [ ] Video walkthrough

**Documentation Structure**:
```markdown
# Form Renderer 2.0 Documentation

## Architecture Overview
- Component diagram
- Data flow
- State management

## Migration Guide
- Step by step
- Common issues
- Rollback procedure

## API Reference
- FormController
- FormContext
- FieldRenderer
- SectionRenderer
- LotManager

## Examples
- Simple form
- Form with sections
- Form with lots
- Custom validators
```

---

### Story 40.14: Cleanup & Deprecation
**Points**: 3  
**Priority**: P3 (Low)  
**Type**: Technical Debt  

**Description**:  
Kot developer želim odstraniti staro kodo, ko je migracija končana.

**Acceptance Criteria**:
- [ ] 100% forms migrated
- [ ] 30 days brez issues
- [ ] Legacy code marked deprecated
- [ ] Cleanup plan approved
- [ ] Legacy code removed

**Cleanup Checklist**:
1. Mark legacy as deprecated (version X)
2. Monitor for 30 days
3. Remove legacy code (version X+1)
4. Update all imports
5. Final testing

---

## Story Dependencies Graph

```
40.1 ─┬─> 40.2 ──┬─> 40.4 ──┬─> 40.7 ──┬─> 40.9 ──┬─> 40.10
      │          │          │          │          │
      └─> 40.3 ──┴─> 40.5 ──┴─> 40.8 ──┘          ├─> 40.11
                 │                                 │
                 └─> 40.6 ─────────────────────────┴─> 40.12
                                                   │
                                                   ├─> 40.13
                                                   │
                                                   └─> 40.14
```

## Risk Register

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Breaking existing forms | HIGH | HIGH | Comprehensive tests, feature flags |
| Performance degradation | MEDIUM | HIGH | Benchmarks, profiling |
| Complex migration | HIGH | MEDIUM | Incremental approach |
| Developer resistance | LOW | MEDIUM | Training, documentation |
| Scope creep | MEDIUM | HIGH | Strict story boundaries |

## Definition of Done

Za vsako storijo:
- [ ] Koda napisana in pregledana
- [ ] **Uniformni lot pristop implementiran (brez if/else za has_lots)**
- [ ] **Legacy podatki uspešno migrirani v lot strukturo**
- [ ] Unit testi napisani (>80% coverage)
- [ ] Integration testi passed
- [ ] Documentation updated
- [ ] Code reviewed by 2 developers
- [ ] Performance benchmarked
- [ ] No regression bugs
- [ ] Deployed to staging
- [ ] Stakeholder sign-off

---
*Stories created: 2025-01-29*  
*Epic: EPIC-40*  
*Total Story Points: 89*  
*Estimated Duration: 4 sprints*