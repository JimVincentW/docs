# Flow Architecture Rewrite - Completed

**Started:** 2025-12-15  
**Completed:** 2025-12-15  
**Status:** ✅ COMPLETE (Backend + Frontend)

> **Note:** This is a historical record of the migration. For current architecture, see [`ARCHITECTURE.md`](./ARCHITECTURE.md).

---

## Summary

The Flow architecture rewrite unified three separate abstractions into one:

| Before | After |
|--------|-------|
| `Monitor` (single-step annotation) | `Flow` |
| `IntelligencePipeline` (multi-step) | `Flow` |
| Various trigger mechanisms | `Flow.trigger_mode` |

### Frontend Integration

The frontend was updated to consume the new Flow APIs:

| Component | Status |
|-----------|--------|
| `storeFlows.ts` | ✅ Zustand store for Flow state management |
| `FlowManager.tsx` | ✅ Flow CRUD UI |
| Client SDK | ✅ Regenerated with correct types |
| Sources store | ✅ Works with new streaming model |

---

## What Was Created

### New Models

| Model | Purpose |
|-------|---------|
| `Flow` | Unified processing workflow |
| `FlowExecution` | Single execution record |
| `FlowStatus` enum | draft, active, paused, error |
| `FlowInputType` enum | stream, bundle, manual |
| `FlowTriggerMode` enum | on_arrival, scheduled, manual |
| `FlowStepType` enum | ANNOTATE, FILTER, CURATE, ROUTE, EMBED, ANALYZE |
| `RunType` enum | ONE_OFF, FLOW_STEP |

### New Files

| File | Purpose |
|------|---------|
| `backend/app/api/services/flow_service.py` | Flow execution logic |
| `backend/app/api/routes/flows.py` | Flow API endpoints |
| `backend/app/api/tasks/flow_tasks.py` | Celery tasks for flows |

### Modified Models

- `AnnotationRun`: Added `run_type`, `flow_execution_id`, `tags`
- `Asset`, `Source`, `AnnotationSchema`: Added `tags: List[str]`
- `TaskType`: Added `flow`, `source_poll`, `embed`, `backup`

---

## What Was Removed

### Models (dropped from database)

| Model | Replacement |
|-------|-------------|
| `Monitor` | `Flow` with single ANNOTATE step |
| `MonitorBundleLink` | `Flow.input_bundle_id` |
| `MonitorSchemaLink` | `Flow.steps[0].schema_ids` |
| `MonitorAggregate` | Analysis adapters |
| `IntelligencePipeline` | `Flow` |
| `PipelineStep` | `Flow.steps` (JSONB) |
| `PipelineExecution` | `FlowExecution` |
| `PipelineProcessedAsset` | `Flow.cursor_state` |

### Fields (dropped from database)

| Table | Field | Replacement |
|-------|-------|-------------|
| `source` | `linked_pipeline_id` | `Flow.input_source_id` |
| `source` | `auto_trigger_pipeline` | `Flow.trigger_mode` |
| `sourcepollhistory` | `triggered_pipeline` | Flows handle via `on_arrival` |
| `sourcepollhistory` | `triggered_run_id` | `FlowExecution` |
| `annotationrun` | `monitor_id` | `flow_execution_id` |
| `annotationrun` | `pipeline_execution_id` | `flow_execution_id` |
| `annotationrun` | `triggered_by_source_id` | Derivable from Flow |

### Services

| File | Status |
|------|--------|
| `monitor_service.py` | **DELETED** |
| `pipeline_service.py` | **DELETED** |

### Routes

| File | Status |
|------|--------|
| `monitors.py` | **DELETED** |
| `pipelines.py` | **DELETED** |

### Tasks

| File | Status |
|------|--------|
| `monitor_tasks.py` | **DELETED** |
| `pipeline_tasks.py` | **DELETED** |

### Enums

| Enum | Status |
|------|--------|
| `PipelineStepType` | **DELETED** (replaced by `FlowStepType`) |
| `AnnotationRunTrigger.MONITOR` | **DELETED** |
| `AnnotationRunTrigger.PIPELINE` | **DELETED** |

---

## Migration File

The migration that drops all legacy tables and columns:

```
backend/app/alembic/versions/a1b2c3d4e5f6_remove_legacy_monitor_pipeline.py
```

Run with:
```bash
cd backend && alembic upgrade head
```

---

## What Remains Unchanged

- **One-off annotation runs**: Still fully supported with `run_type=ONE_OFF`
- **AnnotationRun.views_config**: Still available for visualization
- **Source polling**: Works via `stream_source_service.py` (delegated from `SourceService`)
- **Task scheduling**: Still uses `Task` model with cron expressions
- **Embeddings**: Still via `EmbeddingService` and `embed` tasks

---

## Testing Checklist

- [x] One-off annotation run works
- [x] Flow with single ANNOTATE step works
- [x] Flow with multi-step processing works
- [x] Delta tracking via cursor_state works
- [x] Task scheduling of Flows works
- [x] on_arrival trigger works
- [x] Run history correctly shows/hides based on run_type
- [x] Frontend Flow list loads correctly
- [x] Frontend Flow CRUD operations work
- [x] Source polling via Celery works

---

## Gotchas & Fixes Applied

### Router Dependencies Issue

**Problem:** Using `dependencies=[Depends(CurrentUser)]` on APIRouter caused FastAPI to expose spurious `args` and `kwargs` query parameters in the OpenAPI spec.

**Cause:** `CurrentUser` is a type alias (`Annotated[User, Depends(get_current_user)]`), not a callable. Using it in router-level dependencies confused FastAPI's OpenAPI generation.

**Fix:** Removed router-level dependencies from `flows.py`. Each route handler already includes `current_user: CurrentUser` as a parameter, which handles authentication correctly.

```python
# ❌ Bad - causes args/kwargs in OpenAPI
router = APIRouter(
    prefix="/...",
    dependencies=[Depends(CurrentUser)],  # CurrentUser is a type alias!
)

# ✅ Good - no router-level dependencies needed
router = APIRouter(prefix="/...")
```

### Celery Async Pattern

**Problem:** `source_monitoring.py` used `await` directly in Celery tasks, causing `SyntaxError: 'await' outside async function`.

**Fix:** Use `asyncio.run_until_complete()` wrapper for async service methods:

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
```

### Frontend SDK Function Names

**Problem:** After regenerating the client, function names changed from `listFlows` to `flowsListFlows`.

**Cause:** The openapi-ts generator prefixes method names with the service name.

**Fix:** Update all store calls to use the new naming pattern.

---

*For current architecture documentation, see [`ARCHITECTURE.md`](./ARCHITECTURE.md).*
