# Brownfield Story: AI Suggestions for Negotiations Special Requirements

## Story Title
**AI Negotiations Suggestions** - Brownfield Addition

## User Story
As a **procurement officer**,  
I want **to choose between manual input or AI suggestions for special negotiation requirements**,  
So that **I can get intelligent recommendations for negotiation terms while maintaining control**.

## Story Context

**Existing System Integration:**
- Integrates with: `negotiationsInfo.specialNegotiationWishes` field in the multi-step form  
- Technology: Streamlit, OpenAI GPT-4, existing AI field renderer pattern
- Follows pattern: Existing AI suggestion fields (like `procurementObject.description`)
- Touch points: `ui/renderers/ai_field_renderer.py`, `ui/ai_manager.py` (prompt already exists as `pogajanja_posebne_zelje_pogajanja`)

## Acceptance Criteria

**Functional Requirements:**
1. Add radio button choice for `negotiationsInfo.specialNegotiationWishes` field:
   - Option 1: "Vnesem sam" (Manual input)
   - Option 2: "Drugo, prosim za predlog AI" (AI suggestion)
2. When AI option selected, generate context-aware suggestions for negotiation requirements
3. User can edit AI-generated suggestions before saving

**Integration Requirements:**
4. Follow existing AI field pattern from `ai_field_renderer.py`
5. Add field configuration to AI manager
6. Integrate with existing OpenAI service
7. Maintain current field validation and storage

**Quality Requirements:**
8. AI prompt generates relevant Slovenian language suggestions
9. Response time under 3 seconds
10. Graceful fallback if AI service unavailable

## Technical Notes

**Integration Approach:**
Add the field to AI-enabled fields list following existing pattern in `ai_manager.py`

**Existing Pattern Reference:**
Follow the exact implementation pattern from other AI-enabled fields like:
- `procurementObject.description`
- `technicalSpecifications.performanceRequirements`

**Implementation Pattern:**

1. **The prompt already exists in AI Manager (`ui/ai_manager.py` line 2399):**
```python
'pogajanja_posebne_zelje_pogajanja': """
Ti si AI asistent za javna naročila. Generiraj predloge za posebne želje v zvezi s pogajanji.
Predlogi morajo biti:
- Realistični in izvedljivi
- V skladu s postopkom pogajanj
- Usmerjeni v optimizacijo ponudb
- Napisani v slovenščini
Odgovori samo s konkretnimi predlogi.
"""
```

2. **Need to add field mapping in AI field renderer to connect field with prompt:**
```python
# In ai_field_renderer.py, add to AI_ENABLED_FIELDS or similar config:
'negotiationsInfo.specialNegotiationWishes': {
    'prompt_key': 'pogajanja_posebne_zelje_pogajanja',
    'show_radio': True,
    'label_manual': 'Vnesem sam',
    'label_ai': 'Drugo, prosim za predlog AI'
}
```

3. **Radio Button Integration:**
The existing `ai_field_renderer.py` already handles radio button pattern - just need to add field to configuration.

## Definition of Done

- [ ] Field added to AI manager configuration
- [ ] Prompt created and tested for quality suggestions
- [ ] Radio buttons appear for the field ("Vnesem sam" / "Drugo, prosim za predlog AI")
- [ ] AI generates relevant negotiation requirements in Slovenian
- [ ] User can edit generated text
- [ ] Field saves correctly to database
- [ ] No regression in existing AI fields
- [ ] Error handling for AI service failures

## Risk and Compatibility Assessment

**Minimal Risk Assessment:**
- **Primary Risk:** AI service timeout or unavailability
- **Mitigation:** Fallback to manual input mode
- **Rollback:** Remove field from AI configuration

**Compatibility Verification:**
- ✅ No breaking changes - adding to existing pattern
- ✅ No database changes required
- ✅ UI follows existing AI field patterns
- ✅ Performance impact minimal (async AI call)

## Validation Checklist

**Scope Validation:**
- ✅ Story can be completed in one development session (1-2 hours)
- ✅ Uses existing AI integration pattern exactly
- ✅ No new architecture or design required
- ✅ Simple configuration addition

**Clarity Check:**
- ✅ Requirements are unambiguous
- ✅ Integration points clear (`ai_manager.py`, existing AI renderer)
- ✅ Success criteria testable
- ✅ Simple rollback (remove configuration)

## Estimated Effort
**1-2 hours** of focused development work

## Implementation Steps
1. Add field mapping in `ui/renderers/ai_field_renderer.py` to connect `negotiationsInfo.specialNegotiationWishes` with existing prompt
2. Verify radio buttons appear in form when viewing negotiations section
3. Test AI generation for negotiations requirements using existing prompt
4. Verify save/load functionality
5. Test error handling scenarios (AI service timeout, etc.)

## Sample Prompt Output Example
```
Posebne zahteve za izvedbo pogajanj:

1. **Način pogajanj**: Pogajanja se izvedejo v dveh krogih - prvi krog pisno preko elektronskih sredstev, drugi krog ustno na sedežu naročnika.

2. **Minimalne zahteve**: O naslednjih elementih se ne pogaja:
   - Tehnične specifikacije iz razpisne dokumentacije
   - Rok izvedbe storitev
   - Garancijski pogoji

3. **Elementi pogajanj**: Pogajanja se vodijo o:
   - Končni ceni (do 15% znižanje)
   - Plačilnih pogojih
   - Dodatnih storitvah

4. **Časovni okvir**: Med prvim in drugim krogom pogajanj mora preteči najmanj 5 delovnih dni.

5. **Dokumentacija**: Vsa pogajanja se dokumentirajo z zapisnikom, ki ga podpišejo vsi prisotni.
```

## Notes
- This follows the exact pattern of existing AI fields
- The prompt should generate practical, legally appropriate suggestions
- All text must be in Slovenian
- This is a configuration addition, not new functionality