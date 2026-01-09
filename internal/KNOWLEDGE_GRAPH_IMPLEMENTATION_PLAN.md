# Knowledge Graph Implementation Plan

## Architecture Analysis

### Current State

#### Backend
- **Models**: `Annotation` stores KG results in JSONB `value` field
- **Schema**: Knowledge Graph schema defined in `initial_data.py`:
  ```python
  document:
    entities: [{id: int, name: str, type: str}]
    triplets: [{source_id: int, target_id: int, predicate: str, description: str}]
  ```
- **Adapter**: `GraphAggregatorAdapter` exists but NOT registered in DB
- **Pattern**: Follows factory/provider pattern - adapters registered in `AnalysisAdapter` table

#### Frontend
- **Schema Editor**: `AnnotationSchemaEditor.tsx` uses adapter pattern
  - `adaptSchemaReadToSchemaFormData` in `adapters.ts` DOES parse nested array<object>
  - Lines 166-170 handle `items.properties` 
  - **Issue**: UI doesn't display/edit these nested properties
- **Table Display**: `AnnotationResultsTable.tsx` uses `getAnnotationFieldValue` utility
- **Graph Viz**: `AnnotationResultsGraph.tsx` calls graph_aggregator endpoint (404)
- **Panel System**: `PanelRenderer.tsx` manages view configs (stores settings in panel.settings)

### Root Causes

1. **404 Error**: `graph_aggregator` not in `AnalysisAdapter` DB table
2. **Schema Editor**: Nested properties parsed but not rendered in UI
3. **Utility Gap**: No specific helpers for KG data extraction
4. **Edit Storage**: No pattern yet for storing manual graph edits

## Solution Design

### Design Principles (from user requirements)
✓ Use existing patterns (factories, providers, registries)
✓ Don't focus everything on this feature - elegant integration
✓ Long-term maintainable, nice developer experience
✓ Consistent mental model across codebase

### Phase 1: Immediate Fixes (Get Basic KG Working)

#### 1.1 Register Graph Adapter (Backend)
**File**: `backend/app/core/db.py`
**Change**: Add graph_aggregator registration in `init_db()`
```python
# After existing adapter registrations
graph_adapter = session.exec(
    select(AnalysisAdapter).where(AnalysisAdapter.name == "graph_aggregator")
).first()
if not graph_adapter:
    graph_adapter = AnalysisAdapter(
        name="graph_aggregator",
        description="Aggregates graph entities and triplets from annotations",
        module_path="app.api.analysis.adapters.graph_aggregator_adapter.GraphAggregatorAdapter",
        adapter_type="graph",
        is_public=True,
        creator_user_id=user.id,
    )
    session.add(graph_adapter)
```

#### 1.2 KG Utility Functions (Frontend)
**File**: `frontend/src/lib/annotations/utils.ts`
**Add**:
```typescript
// Knowledge Graph specific utilities
export function isKnowledgeGraphField(fieldKey: string, fieldValue: any): boolean {
  return (fieldKey === 'entities' || fieldKey === 'triplets') && Array.isArray(fieldValue);
}

export function extractEntities(annotationValue: any): Array<{id: number, name: string, type: string}> {
  const entities = getAnnotationFieldValue(annotationValue, 'document.entities');
  return Array.isArray(entities) ? entities : [];
}

export function extractTriplets(annotationValue: any): Array<{source_id: number, target_id: number, predicate: string, description?: string}> {
  const triplets = getAnnotationFieldValue(annotationValue, 'document.triplets');
  return Array.isArray(triplets) ? triplets : [];
}

// Get entity by ID from entities array
export function getEntityById(entities: any[], entityId: number): any | null {
  return entities.find(e => e.id === entityId) || null;
}

// Format triplet as human-readable string
export function formatTriplet(triplet: any, entities: any[]): string {
  const source = getEntityById(entities, triplet.source_id);
  const target = getEntityById(entities, triplet.target_id);
  if (!source || !target) return 'Invalid triplet';
  return `${source.name} → ${triplet.predicate} → ${target.name}`;
}
```

#### 1.3 Table Display Enhancement
**File**: `AnnotationResultDisplay.tsx` (or create KGResultDisplay component)
**Pattern**: Follow existing display pattern for complex structures
- Detect KG schema by checking for entities/triplets fields
- Render entities as badges with type colors
- Render triplets as relationship chips
- Make them clickable for inspection

### Phase 2: Schema Editor Enhancement

#### 2.1 UI for Nested Array<Object> Fields
**File**: `AnnotationSchemaEditor.tsx`
**Current**: PropertyInspector shows field properties
**Enhancement**: When field.type === 'array' && field.items?.type === 'object':
1. Show collapsible "Array Item Properties" section
2. List `field.items.properties` with ability to add/edit/remove
3. Each nested property has: name, type, description, required
4. Use recursive pattern - same AdvancedSchemeField structure

**Pattern** (existing in codebase):
```typescript
// In PropertyInspector, after array type handling
{field.type === 'array' && field.items?.type === 'object' && (
  <Accordion type="single" collapsible>
    <AccordionItem value="array-item-properties">
      <AccordionTrigger>Array Item Properties</AccordionTrigger>
      <AccordionContent>
        <div className="space-y-2">
          {field.items.properties?.map(prop => (
            <NestedFieldEditor 
              key={prop.id}
              field={prop}
              onUpdate={(updates) => {
                // Update field.items.properties
              }}
              onRemove={() => {
                // Remove from field.items.properties
              }}
            />
          ))}
          <Button onClick={() => {
            // Add new property to field.items.properties
          }}>
            Add Property
          </Button>
        </div>
      </AccordionContent>
    </AccordionItem>
  </Accordion>
)}
```

### Phase 3: Graph Manual Editing

#### 3.1 Edit Storage Pattern
**Follow existing pattern**: Like geocoding cache in `PanelRenderer.tsx`
**Storage location**: `panel.settings.graphEdits`
**Structure**:
```typescript
interface GraphEdits {
  mergedNodes: {
    targetNodeId: string;  // Keep this node
    mergedNodeIds: string[];  // Merge these into target
    mergedAt: Date;
  }[];
  deletedNodes: {
    nodeId: string;
    deletedAt: Date;
  }[];
  deletedEdges: {
    edgeId: string;
    deletedAt: Date;
  }[];
  customEdges: {
    id: string;
    source: string;
    target: string;
    label: string;
    createdAt: Date;
  }[];
  nodeLabels: {
    nodeId: string;
    customLabel: string;
  }[];
}
```

#### 3.2 Graph Visualization Integration
**File**: `AnnotationResultsGraph.tsx`
**Enhancement**:
1. Load `panel.settings.graphEdits` from parent
2. Apply edits to graph data before rendering:
   - Filter out deleted nodes/edges
   - Merge nodes (combine frequencies, merge edges)
   - Add custom edges
   - Apply custom labels
3. Provide edit UI:
   - Right-click context menu on nodes/edges
   - Merge dialog (select target node)
   - Delete confirmation
   - Manual edge creation dialog

#### 3.3 Edit Persistence
**Pattern**: Like geocoding in `PanelRenderer.tsx`
```typescript
const handleGraphEdit = useCallback((editType: string, editData: any) => {
  const currentEdits = panel.settings?.graphEdits || {
    mergedNodes: [],
    deletedNodes: [],
    deletedEdges: [],
    customEdges: [],
    nodeLabels: []
  };
  
  // Apply edit based on type
  const updatedEdits = applyGraphEdit(currentEdits, editType, editData);
  
  // Persist to panel settings
  onUpdatePanel(panel.id, {
    settings: {
      ...panel.settings,
      graphEdits: updatedEdits
    }
  });
}, [panel, onUpdatePanel]);
```

### Phase 4: Export Integration

#### 4.1 Include Graph Edits in Export
**Pattern**: Follow existing export patterns (backups, CSV export)
- Include `graphEdits` in panel view configs when exporting
- Document format includes edited graph state
- Import applies edits automatically

### Implementation Order

1. **✅ Register Adapter** (5 min) - Fixes 404 immediately
2. **✅ Add KG Utilities** (15 min) - Foundation for all KG operations
3. **✅ Enhance Table Display** (30 min) - Show KG data properly
4. **⏳ Schema Editor UI** (1-2 hours) - Edit nested properties
5. **⏳ Graph Edit Storage** (30 min) - Setup data structures
6. **⏳ Graph Edit UI** (2-3 hours) - Implement edit operations
7. **⏳ Export Integration** (30 min) - Include edits in exports

### Long-term Considerations

1. **Auto-merging**: ML-based entity resolution (separate feature)
2. **Graph Algorithms**: Path finding, centrality, clustering (separate adapters)
3. **Graph Diff**: Compare graphs across runs (separate view)
4. **Graph Templates**: Reusable graph patterns (separate feature)

## Testing Strategy

### Phase 1
- [ ] Verify graph_aggregator returns 200
- [ ] Check entities/triplets display in table
- [ ] Verify utility functions extract correct data

### Phase 2
- [ ] Create KG schema with nested properties
- [ ] Edit nested properties (add, remove, modify)
- [ ] Verify output_contract JSON is correct

### Phase 3
- [ ] Delete node, verify it's filtered from graph
- [ ] Merge two nodes, verify edges are consolidated
- [ ] Create custom edge, verify it appears in graph
- [ ] Export and import, verify edits persist

## Migration Notes

- No DB migrations needed (using existing JSONB fields)
- Backward compatible (graphs without edits work as before)
- Panel settings schema is flexible (no breaking changes)

## Code Locations Reference

### Backend
- Adapter: `backend/app/api/analysis/adapters/graph_aggregator_adapter.py`
- Models: `backend/app/models.py` (AnnotationSchema, Annotation)
- Init: `backend/app/core/db.py` (adapter registration)
- Schema: `backend/app/core/initial_data.py` (KG schema definition)

### Frontend
- Schema Editor: `frontend/src/components/collection/annotation/AnnotationSchemaEditor.tsx`
- Table: `frontend/src/components/collection/annotation/AnnotationResultsTable.tsx`
- Graph: `frontend/src/components/collection/annotation/AnnotationResultsGraph.tsx`
- Panel: `frontend/src/components/collection/annotation/PanelRenderer.tsx`
- Utils: `frontend/src/lib/annotations/utils.ts`
- Adapters: `frontend/src/lib/annotations/adapters.ts`
- Types: `frontend/src/lib/annotations/types.ts`

