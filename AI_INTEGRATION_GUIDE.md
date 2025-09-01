# AI Suggestion Transfer - Integration Guide

## Quick Start

To enable AI suggestions in your form, add these two lines to your `app.py`:

```python
# At the top of app.py, after other imports
from patches.ai_integration_patch import apply_ai_integration, inject_ai_into_renderer

# After form initialization, before rendering
apply_ai_integration()

# When creating a section renderer
section_renderer = SectionRenderer(context)
inject_ai_into_renderer(section_renderer)  # Add this line
```

## Features Implemented

### 1. AI Suggestion Service (`services/ai_suggestion_service.py`)
- Collects full form context (project, cofinancers, lots, all fields)
- Queries Qdrant knowledge base first
- Falls back to OpenAI if no good KB results
- Returns multiple suggestions with confidence scores

### 2. AI Field Renderer (`ui/renderers/ai_field_renderer.py`)
- Supports three trigger types:
  - **Dropdown**: "prosim za predlog AI" option
  - **Checkbox**: "Uporabi AI za predlog" above text areas
  - **Button**: "AI predlog" next to input fields
- Shows suggestion source (knowledge base vs AI generated)
- Allows users to accept or reject suggestions
- Option to generate more suggestions

### 3. Integration Helper (`ui/renderers/ai_integration_helper.py`)
- Automatically detects fields that should have AI
- Priority fields include:
  - Cofinancer requirements (ALL procurement types)
  - Price formation fields
  - Negotiation terms
  - Evaluation criteria "drugo" fields
  - Participation conditions "drugo" fields

## Field Priority

### High Priority (Always Available)
1. **Cofinancer Requirements** - Available for ALL procurement types
   - `posebne_zahteve_sofinancerja`
   - `specialRequirements`
   - `cofinancer_requirements`

2. **Price Information**
   - Price fixation options
   - Custom price formation

3. **Negotiation Fields**
   - Special negotiation requests

### Medium Priority
- Social criteria "drugo" options
- Environmental criteria "drugo" options
- Professional suitability "drugo" fields
- Economic status "drugo" fields
- Technical capability "drugo" fields

## How It Works

1. **User triggers AI** via dropdown/checkbox/button
2. **System collects context**:
   - Project title and description
   - Cofinancers and funding programs
   - Current lot information
   - All previously filled fields
3. **Searches knowledge base** with context-aware query
4. **Falls back to AI** if no good KB results
5. **Shows suggestions** with source indicators
6. **User can**:
   - Accept suggestion (transfers to field)
   - Reject and regenerate
   - Manually edit transferred text

## Configuration

The system automatically detects which fields should have AI based on:
- Field name patterns (e.g., "drugo", "requirements", "special")
- JSON schema hints (`ai_enabled: true`)
- Enum options containing "prosim za predlog AI"

## Testing

To test the implementation:

```python
# Run test script
python tests/test_ai_integration.py

# Or manually test in app:
1. Start the app
2. Navigate to any form with cofinancing
3. Look for AI triggers (checkboxes, buttons, dropdown options)
4. Click/select AI option
5. Review suggestions with context
6. Accept or reject suggestions
```

## Troubleshooting

### AI not showing up
- Check if field name contains AI-enabled patterns
- Verify OpenAI API key is configured
- Ensure Qdrant is running if using knowledge base

### No suggestions generated
- Check form context is being collected
- Verify API keys are valid
- Check logs for errors

### Suggestions not relevant
- Ensure full form context is filled
- Check if knowledge base has relevant documents
- Review context being sent to AI (shown in UI)

## Environment Variables

Required for full functionality:
```bash
OPENAI_API_KEY=your_api_key
OPENAI_MODEL=gpt-4o-mini  # or gpt-4
QDRANT_HOST=localhost
QDRANT_PORT=6333
```

## Next Steps

1. **Populate knowledge base** with relevant procurement documents
2. **Train field-specific models** for better suggestions
3. **Add user feedback loop** to improve suggestions
4. **Implement suggestion analytics** to track usage

## Support

For issues or questions about the AI integration:
1. Check logs in `app.log`
2. Review context shown in AI suggestion panel
3. Verify all services are running (Qdrant, OpenAI)
4. Contact development team with error details