# Open Politics HQ - Architecture Reference

**Version:** 2.0 (Post-Migration)  
**Last Updated:** 2025-12-15  
**Status:** Production Ready (Backend + Frontend)

---

## Overview

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                            OPEN POLITICS HQ - ARCHITECTURE                               │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                          │
│  ╔═══════════════════════════════════════════════════════════════════════════════════╗  │
│  ║                              INFOSPACE (tenant boundary)                           ║  │
│  ╠═══════════════════════════════════════════════════════════════════════════════════╣  │
│  ║                                                                                    ║  │
│  ║   ┌─────────────────────────────────────────────────────────────────────────────┐ ║  │
│  ║   │                           DATA LAYER                                        │ ║  │
│  ║   ├─────────────────────────────────────────────────────────────────────────────┤ ║  │
│  ║   │                                                                             │ ║  │
│  ║   │  SOURCE                        BUNDLE                         ASSET         │ ║  │
│  ║   │  ┌──────────────┐              ┌──────────────┐              ┌───────────┐  │ ║  │
│  ║   │  │ RSS Feed     │─────────────▶│ Raw Articles │─────────────▶│ Document  │  │ ║  │
│  ║   │  │ Search API   │ output_      │ Curated News │  contains    │ Fragment  │  │ ║  │
│  ║   │  │ Web Scrape   │ bundle_id    │ Analysis Out │              │ Webpage   │  │ ║  │
│  ║   │  │ File Upload  │              └──────────────┘              └───────────┘  │ ║  │
│  ║   │  └──────────────┘                     │                           │         │ ║  │
│  ║   │        │                              │                           │         │ ║  │
│  ║   │        │ poll_interval                │ parent/child              │         │ ║  │
│  ║   │        ▼                              ▼                           ▼         │ ║  │
│  ║   │  ┌──────────────┐              ┌──────────────┐         ┌──────────────┐    │ ║  │
│  ║   │  │ Poll History │              │ Nested       │         │ Annotations  │    │ ║  │
│  ║   │  │ Cursor State │              │ Bundles      │         │ (per schema) │    │ ║  │
│  ║   │  └──────────────┘              └──────────────┘         └──────────────┘    │ ║  │
│  ║   │                                                                             │ ║  │
│  ║   └─────────────────────────────────────────────────────────────────────────────┘ ║  │
│  ║                                         │                                          ║  │
│  ║                                         │ feeds into                               ║  │
│  ║                                         ▼                                          ║  │
│  ║   ┌─────────────────────────────────────────────────────────────────────────────┐ ║  │
│  ║   │                        PROCESSING LAYER                                     │ ║  │
│  ║   ├─────────────────────────────────────────────────────────────────────────────┤ ║  │
│  ║   │                                                                             │ ║  │
│  ║   │  FLOW (unified processing abstraction)                                      │ ║  │
│  ║   │  ┌─────────────────────────────────────────────────────────────────────┐   │ ║  │
│  ║   │  │                                                                     │   │ ║  │
│  ║   │  │  input_bundle_id ──▶ ┌────────┬────────┬────────┬────────┬───────┐ │   │ ║  │
│  ║   │  │                      │FILTER  │ANNOTATE│FILTER  │CURATE  │ROUTE  │ │   │ ║  │
│  ║   │  │                      │        │        │        │        │       │ │   │ ║  │
│  ║   │  │  trigger_mode:       │text/   │schema  │annot.  │promote │output │ │   │ ║  │
│  ║   │  │  • on_arrival        │meta    │ids     │values  │fields  │bundle │ │   │ ║  │
│  ║   │  │  • scheduled         │match   │        │filter  │to tags │       │ │   │ ║  │
│  ║   │  │  • manual            └────────┴────────┴────────┴────────┴───────┘ │   │ ║  │
│  ║   │  │                                                        │           │   │ ║  │
│  ║   │  │  cursor_state: tracks processed assets (delta mode)    │           │   │ ║  │
│  ║   │  │                                                        ▼           │   │ ║  │
│  ║   │  │                                          ┌──────────────────────┐  │   │ ║  │
│  ║   │  │                                          │ FLOW EXECUTION       │  │   │ ║  │
│  ║   │  │                                          │ • step_outputs       │  │   │ ║  │
│  ║   │  │                                          │ • input/output IDs   │  │   │ ║  │
│  ║   │  │                                          │ • annotation_runs[]  │  │   │ ║  │
│  ║   │  │                                          └──────────────────────┘  │   │ ║  │
│  ║   │  └─────────────────────────────────────────────────────────────────────┘   │ ║  │
│  ║   │                                                                             │ ║  │
│  ║   │  ANNOTATION RUN (standalone or flow-triggered)                              │ ║  │
│  ║   │  ┌─────────────────────────────────────────────────────────────────────┐   │ ║  │
│  ║   │  │  run_type: ONE_OFF          │  run_type: FLOW_STEP                  │   │ ║  │
│  ║   │  │  ─────────────────          │  ────────────────────                 │   │ ║  │
│  ║   │  │  • Manual via UI/API        │  • Created by Flow execution          │   │ ║  │
│  ║   │  │  • Shows in run history     │  • Linked via flow_execution_id       │   │ ║  │
│  ║   │  │  • views_config for viz     │  • Hidden from main list              │   │ ║  │
│  ║   │  └─────────────────────────────────────────────────────────────────────┘   │ ║  │
│  ║   │                                                                             │ ║  │
│  ║   └─────────────────────────────────────────────────────────────────────────────┘ ║  │
│  ║                                         │                                          ║  │
│  ║                                         │ orchestrated by                          ║  │
│  ║                                         ▼                                          ║  │
│  ║   ┌─────────────────────────────────────────────────────────────────────────────┐ ║  │
│  ║   │                       SCHEDULING LAYER                                      │ ║  │
│  ║   ├─────────────────────────────────────────────────────────────────────────────┤ ║  │
│  ║   │                                                                             │ ║  │
│  ║   │  TASK                               CELERY                                  │ ║  │
│  ║   │  ┌──────────────────────┐          ┌────────────────────────────────────┐  │ ║  │
│  ║   │  │ type: source_poll    │─────────▶│ execute_source_poll.delay()        │  │ ║  │
│  ║   │  │ type: flow           │─────────▶│ execute_flow.delay()               │  │ ║  │
│  ║   │  │ type: embed          │─────────▶│ embed_bundle.delay()               │  │ ║  │
│  ║   │  │                      │          │                                    │  │ ║  │
│  ║   │  │ schedule: cron       │          │ check_on_arrival_flows (1min beat) │  │ ║  │
│  ║   │  │ target_id: int       │          │ check_recurring_tasks (1min beat)  │  │ ║  │
│  ║   │  └──────────────────────┘          └────────────────────────────────────┘  │ ║  │
│  ║   │                                                                             │ ║  │
│  ║   └─────────────────────────────────────────────────────────────────────────────┘ ║  │
│  ║                                                                                    ║  │
│  ╚════════════════════════════════════════════════════════════════════════════════════╝  │
│                                                                                          │
│  ┌──────────────────────────────────────────────────────────────────────────────────┐   │
│  │                          CROSS-CUTTING CONCERNS                                   │   │
│  ├──────────────────────────────────────────────────────────────────────────────────┤   │
│  │  SCHEMAS            EMBEDDINGS           MCP SERVER          SHARING              │   │
│  │  ┌────────────┐    ┌────────────┐       ┌────────────┐      ┌────────────┐       │   │
│  │  │ JSON output│    │ pgvector   │       │ Tool-based │      │ ShareLinks │       │   │
│  │  │ contracts  │    │ chunks     │       │ LLM access │      │ Public API │       │   │
│  │  │ versioned  │    │ semantic   │       │ to assets  │      │ views      │       │   │
│  │  └────────────┘    │ search     │       └────────────┘      └────────────┘       │   │
│  │                    └────────────┘                                                 │   │
│  └──────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                          │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Core Concepts

### 1. Bundles Are the Connectors

**Bundles are the unit of composition.** They connect:
- Sources → Processing (assets land in bundles)
- Processing → More Processing (flows route to bundles)
- Processing → Analysis/Dashboards (bundles feed UIs)

```
Source A ──poll──▶ Bundle "Raw" ──▶ Flow 1 ──▶ Bundle "Filtered" ──▶ Flow 2 ──▶ Bundle "Curated"
```

### 2. Flow = Unified Processing

A **Flow** defines:
- **Input**: What to watch (`input_bundle_id` or `input_source_id`)
- **Steps**: What processing to apply (FILTER, ANNOTATE, CURATE, ROUTE, EMBED, ANALYZE)
- **Trigger**: When to run (`on_arrival`, `scheduled`, `manual`)
- **Cursor**: What's already been processed (delta tracking)

### 3. Two Types of Annotation Runs

| Type | Created By | Shows In History | Use Case |
|------|------------|------------------|----------|
| `ONE_OFF` | User/API manually | ✅ Yes | Ad-hoc analysis, experiments |
| `FLOW_STEP` | Flow execution | ❌ No (shows under Flow) | Automated pipelines |

---

## Flow Step Pipeline

```
VALID STEP SEQUENCES:
─────────────────────

⭐ PRE-ANNOTATION FILTERING (for high-volume streams):
FILTER → ANNOTATE → ROUTE            (filter first, then annotate)
FILTER → ANNOTATE → FILTER → ROUTE   (pre-filter, annotate, post-filter)
FILTER → ANNOTATE → CURATE → ROUTE   (pre-filter, annotate, curate)

POST-ANNOTATION FILTERING:
ANNOTATE → FILTER → ROUTE            (annotate, filter on results, route)
ANNOTATE → CURATE → ROUTE            (annotate, promote facts, route)
ANNOTATE → FILTER → CURATE → ROUTE   (full pipeline)

MULTI-STAGE ANNOTATION:
ANNOTATE → FILTER → ANNOTATE → CURATE    (two-pass annotation)
FILTER → ANNOTATE → FILTER → ANNOTATE    (progressive refinement)

CONSTRAINTS:
───────────
• CURATE requires at least one prior ANNOTATE step
• FILTER can access annotations from ALL prior ANNOTATE steps
• ROUTE should be the final step (outputs to a bundle)
```

### Step Reference

| Step | Input | Output | Config |
|------|-------|--------|--------|
| **FILTER** | Assets | Subset that match | `expression: {field, operator, value}` |
| **ANNOTATE** | Assets | Annotations created | `schema_ids: [1,2], config: {}` |
| **CURATE** | Annotated assets | Fragments promoted | `fields: ["entities", "sentiment"]` |
| **ROUTE** | Assets | Assets in target bundle | `bundle_id: 5` |
| **EMBED** | Assets | Vector chunks created | `model, chunk_config` |
| **ANALYZE** | Assets/Annotations | Aggregated insights | `adapter_id, config` |

---

## Quick Start Examples

### Setting Up a Source → Bundle → Flow Pipeline

```python
# 1. Create a Source that outputs to a Bundle
POST /api/infospaces/{id}/sources
{
  "name": "Reuters RSS",
  "kind": "rss",
  "details": {"feed_url": "https://reuters.com/rss/topnews"},
  "output_bundle_id": 10,
  "is_active": true,
  "poll_interval_seconds": 300
}

# 2. Create a Task to poll the source
POST /api/infospaces/{id}/tasks
{
  "name": "Poll Reuters",
  "type": "source_poll",
  "target_id": 1,  # source_id
  "schedule": "*/5 * * * *"
}

# 3. Create a Flow to process the bundle
POST /api/infospaces/{id}/flows
{
  "name": "News Triage",
  "input_type": "bundle",
  "input_bundle_id": 10,
  "trigger_mode": "on_arrival",
  "steps": [
    {"type": "FILTER", "expression": {"field": "text_length", "operator": ">", "value": 100}},
    {"type": "ANNOTATE", "schema_ids": [1, 2]},
    {"type": "FILTER", "expression": {"field": "sentiment_score", "operator": ">", "value": 0.5}},
    {"type": "CURATE", "fields": ["sentiment", "topics"]},
    {"type": "ROUTE", "bundle_id": 11}
  ]
}

# 4. Activate the Flow
POST /api/infospaces/{id}/flows/{flow_id}/activate
```

### One-off Annotation (Manual Analysis)

```python
# Create a standalone annotation run (appears in run history)
POST /api/infospaces/{id}/annotation-runs
{
  "name": "Manual Sentiment Analysis",
  "target_schema_ids": [1],
  "target_asset_ids": [101, 102, 103],
  "views_config": [{"type": "bar", "field": "sentiment"}]
}
# run_type defaults to ONE_OFF
```

---

## API Reference

### Flow Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/infospaces/{id}/flows` | Create flow |
| GET | `/infospaces/{id}/flows` | List flows |
| GET | `/infospaces/{id}/flows/{flow_id}` | Get flow |
| PUT | `/infospaces/{id}/flows/{flow_id}` | Update flow |
| DELETE | `/infospaces/{id}/flows/{flow_id}` | Delete flow |
| POST | `/infospaces/{id}/flows/{flow_id}/activate` | Activate flow |
| POST | `/infospaces/{id}/flows/{flow_id}/pause` | Pause flow |
| POST | `/infospaces/{id}/flows/{flow_id}/execute` | Manual trigger |
| GET | `/infospaces/{id}/flows/{flow_id}/executions` | List executions |
| GET | `/infospaces/{id}/flows/{flow_id}/pending-assets` | Preview delta |
| POST | `/infospaces/{id}/flows/{flow_id}/reset-cursor` | Reset cursor |

### Task Types

| Type | Target | Description |
|------|--------|-------------|
| `flow` | flow_id | Execute a Flow |
| `source_poll` | source_id | Poll a Source for new content |
| `embed` | bundle_id | Embed assets in a Bundle |
| `backup` | infospace_id | Create backup |

---

## Database Models

### Core Entities

```
Infospace (tenant)
├── Source          # Data ingestion
│   └── output_bundle_id → Bundle
├── Bundle          # Asset container
│   ├── assets: Asset[]
│   └── parent_bundle_id → Bundle (nesting)
├── Asset           # Content unit
│   ├── annotations: Annotation[]
│   └── fragments: Dict (curated facts)
├── AnnotationSchema # Output contract
├── AnnotationRun   # Annotation batch
│   ├── run_type: ONE_OFF | FLOW_STEP
│   └── flow_execution_id → FlowExecution
├── Flow            # Processing definition
│   ├── input_bundle_id / input_source_id
│   ├── steps: JSONB
│   ├── trigger_mode: on_arrival | scheduled | manual
│   └── cursor_state: JSONB
├── FlowExecution   # Single run record
│   ├── step_outputs: JSONB
│   └── annotation_runs: AnnotationRun[]
└── Task            # Scheduling
    ├── type: flow | source_poll | embed | backup
    └── schedule: cron expression
```

### Key Relationships

```
Source.output_bundle_id ───────────────▶ Bundle
Flow.input_bundle_id ──────────────────▶ Bundle
Flow.input_source_id ──────────────────▶ Source
FlowExecution.flow_id ─────────────────▶ Flow
AnnotationRun.flow_execution_id ───────▶ FlowExecution
Task.target_id ────────────────────────▶ Flow | Source | Bundle (based on type)
```

---

## Celery Configuration

### Beat Schedule (in `celery_app.py`)

```python
CELERY_BEAT_SCHEDULE = {
    'check-recurring-tasks': {
        'task': 'app.api.tasks.schedule.check_recurring_tasks',
        'schedule': 60.0,  # Every minute
    },
    'check-on-arrival-flows-every-minute': {
        'task': 'app.api.tasks.flow_tasks.check_on_arrival_flows',
        'schedule': 60.0,  # Every minute
    },
    'poll-active-sources-every-minute': {
        'task': 'app.api.tasks.source_monitoring.poll_active_sources',
        'schedule': 60.0,  # Every minute - checks source.next_poll_at
    },
}
```

### Task Modules

| Module | Tasks |
|--------|-------|
| `flow_tasks.py` | `execute_flow`, `check_on_arrival_flows`, `trigger_flow_by_task` |
| `source_monitoring.py` | `execute_source_poll`, `poll_active_sources`, `bulk_poll_sources` |
| `embed.py` | `embed_asset`, `embed_batch_assets`, `embed_infospace` |
| `annotate.py` | `process_annotation_run`, various annotation tasks |
| `schedule.py` | `check_recurring_tasks` |

### Async Pattern in Tasks

Celery tasks are synchronous, but many services are async. Use this pattern:

```python
def run_async(coro):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()

@celery_app.task
def my_task():
    result = run_async(async_service.method())
    return result
```

---

## File Structure

### Backend

```
backend/app/
├── models.py                          # All SQLModel definitions
├── schemas.py                         # Pydantic schemas
├── api/
│   ├── routes/
│   │   ├── flows.py                   # Flow CRUD + execution
│   │   ├── sources.py                 # Source management + polling
│   │   ├── annotation_runs.py         # Annotation run management
│   │   ├── assets.py                  # Asset CRUD
│   │   ├── bundles.py                 # Bundle management
│   │   └── ...
│   ├── services/
│   │   ├── flow_service.py            # Flow execution logic
│   │   ├── source_service.py          # Source management
│   │   ├── stream_source_service.py   # Polling implementation
│   │   ├── annotation_service.py      # Annotation execution
│   │   └── ...
│   └── tasks/
│       ├── flow_tasks.py              # Celery flow tasks
│       ├── source_monitoring.py       # Source poll tasks
│       ├── annotate.py                # Annotation processing
│       ├── embed.py                   # Embedding tasks
│       └── schedule.py                # Task dispatcher
└── core/
    ├── celery_app.py                  # Celery configuration
    └── config.py                      # App settings
```

### Frontend

```
frontend/src/
├── app/
│   └── hq/
│       └── infospaces/
│           ├── flows/                 # Flow management page
│           │   └── page.tsx
│           ├── asset-manager/         # Asset browser
│           └── monitoring/            # Source monitoring
├── client/
│   ├── sdk.gen.ts                     # Generated API client
│   └── types.gen.ts                   # Generated types
├── components/
│   └── collection/
│       ├── flows/                     # Flow UI components
│       │   └── FlowManager.tsx
│       ├── sources/                   # Source UI components
│       │   └── DataSourceManager.tsx
│       ├── assets/                    # Asset UI components
│       └── annotation/                # Annotation UI components
├── zustand_stores/
│   ├── storeFlows.ts                  # Flow state management
│   ├── storeSources.ts                # Source state management
│   ├── storeInfospace.tsx             # Infospace context
│   └── storeBundles.ts                # Bundle state management
└── hooks/
    ├── useAnnotationSystem.tsx        # Annotation utilities
    └── useSemanticSearch.ts           # Search utilities
```

---

## Frontend Integration

### SDK Client

The frontend uses a generated TypeScript client from the OpenAPI spec:

```bash
# Regenerate after backend changes
cd frontend
npm run generate-client
```

### Store Pattern

All API interactions go through Zustand stores:

```typescript
// frontend/src/zustand_stores/storeFlows.ts
export const useFlowStore = create<FlowState>((set, get) => ({
  flows: [],
  isLoading: false,
  
  fetchFlows: async () => {
    const activeInfospace = useInfospaceStore.getState().activeInfospace;
    if (!activeInfospace) return;
    
    set({ isLoading: true });
    const response = await FlowsService.flowsListFlows({ 
      infospaceId: activeInfospace.id 
    });
    set({ flows: response.data, isLoading: false });
  },
  
  // ... other actions
}));
```

### Component Pattern

```tsx
// Components use stores, not direct API calls
function FlowManager() {
  const { flows, isLoading, fetchFlows, createFlow } = useFlowStore();
  
  useEffect(() => {
    fetchFlows();
  }, [fetchFlows]);
  
  return (
    <div>
      {isLoading ? <Spinner /> : flows.map(f => <FlowCard key={f.id} flow={f} />)}
    </div>
  );
}
```

### SDK Function Naming

After regeneration, SDK functions are prefixed with service name:

| Before | After |
|--------|-------|
| `FlowsService.listFlows()` | `FlowsService.flowsListFlows()` |
| `FlowsService.createFlow()` | `FlowsService.flowsCreateFlow()` |
| `SourcesService.listSources()` | `SourcesService.listSources()` |

---

## Development Guide

### Adding a New Flow Step Type

1. Add to `FlowStepType` enum in `models.py`:
   ```python
   class FlowStepType(str, enum.Enum):
       # ... existing
       MY_NEW_STEP = "MY_NEW_STEP"
   ```

2. Implement in `FlowService._execute_step()`:
   ```python
   elif step_type == FlowStepType.MY_NEW_STEP:
       return await self._execute_my_new_step(step_config, asset_ids, execution, step_index)
   ```

3. Add the implementation method:
   ```python
   def _execute_my_new_step(self, step: Dict, asset_ids: List[int], ...) -> Dict[str, Any]:
       # Your logic here
       return {"processed_count": len(asset_ids), ...}
   ```

### Adding a New Task Type

1. Add to `TaskType` enum in `models.py`
2. Update `TaskService._validate_task_input_config()`
3. Update `schedule.py` dispatcher
4. Create Celery task if needed

### Testing Flows

```bash
# Create a test flow
curl -X POST /api/infospaces/1/flows -d '{
  "name": "Test Flow",
  "input_type": "bundle",
  "input_bundle_id": 1,
  "trigger_mode": "manual",
  "steps": [{"type": "ANNOTATE", "schema_ids": [1]}]
}'

# Activate it
curl -X POST /api/infospaces/1/flows/1/activate

# Trigger manually
curl -X POST /api/infospaces/1/flows/1/execute -d '{"asset_ids": [1,2,3]}'

# Check execution
curl /api/infospaces/1/flows/1/executions
```

---

## Migration Notes

### From Previous Version

The following were **removed** in the 2.0 migration:

| Removed | Replaced By |
|---------|-------------|
| `Monitor` model | `Flow` with single ANNOTATE step |
| `MonitorBundleLink` | `Flow.input_bundle_id` |
| `MonitorSchemaLink` | `Flow.steps[0].schema_ids` |
| `MonitorAggregate` | Analysis adapters |
| `IntelligencePipeline` | `Flow` with multiple steps |
| `PipelineStep` | `Flow.steps` (embedded JSONB) |
| `PipelineExecution` | `FlowExecution` |
| `PipelineProcessedAsset` | `Flow.cursor_state` |
| `Source.linked_pipeline_id` | `Flow.input_source_id` |
| `Source.auto_trigger_pipeline` | `Flow.trigger_mode = on_arrival` |
| `AnnotationRun.monitor_id` | `AnnotationRun.flow_execution_id` |
| `AnnotationRun.pipeline_execution_id` | `AnnotationRun.flow_execution_id` |

### Running the Migration

```bash
cd backend
alembic upgrade head
```

### Regenerating Frontend Client

```bash
cd frontend
pnpm run generate-client
```

---

*This document is the authoritative reference for the Open Politics HQ architecture.*
