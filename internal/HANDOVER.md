# Development & Maintenance Handover

**Last Updated:** 2025-12-15

This document provides guidance for developers maintaining and extending the Open Politics HQ codebase.

---

## Key Architecture Documents

| Document | Purpose |
|----------|---------|
| [`ARCHITECTURE.md`](./ARCHITECTURE.md) | Complete system overview, diagrams, API reference |
| [`FLOW_REWRITE_TRACKER.md`](./FLOW_REWRITE_TRACKER.md) | Historical record of the 2.0 migration |

---

## User Mental Model

```
┌─────────────────────────────────────────────────────────────────┐
│                         INFOSPACE                               │
│  (your workspace - contains all your data and configurations)   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   SOURCES          →    BUNDLES        →    FLOWS               │
│   "Where data        "Collections of     "Automated             │
│    comes from"        content"            processing"           │
│                                                                 │
│   • RSS feeds        • Organize assets   • Watch a bundle       │
│   • Search APIs      • Nest hierarchies  • Filter, annotate     │
│   • File uploads     • Share publicly    • Route to bundles     │
│                                                                 │
│         ↓                   ↓                   ↓               │
│                                                                 │
│   [Source polls]   →  [Assets land]  →  [Flow triggers]         │
│                       [in bundle]       [on new assets]         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Key Mental Models:**

1. **Bundles are connectors** - Sources output to bundles, Flows read from bundles, Flows output to bundles
2. **Flows are pipelines** - Multi-step processing with FILTER → ANNOTATE → CURATE → ROUTE
3. **One-off vs Flow** - Manual analysis runs are `ONE_OFF`, automated runs are `FLOW_STEP`
4. **Delta tracking** - Flows remember what they've processed via `cursor_state`

---

## Development Quick Reference

### Starting the Stack

```bash
# Full stack with Docker
docker compose up

# Backend only (for development)
cd backend && uvicorn app.main:app --reload

# Celery worker
celery -A app.core.celery_app worker --loglevel=info

# Celery beat (scheduler)
celery -A app.core.celery_app beat --loglevel=info
```

### Running Migrations

```bash
cd backend

# Create a new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback one step
alembic downgrade -1
```

### Regenerating Frontend Client

```bash
cd frontend
npm run generate-client   # or: pnpm run generate-client

# After regeneration, check for:
# 1. New function name prefixes (e.g., flowsListFlows vs listFlows)
# 2. Changed type names
# 3. Any args/kwargs pollution (see Gotchas section)
```

---

## Common Development Tasks

### Adding a New Flow Step Type

1. **Add enum value** in `models.py`:
   ```python
   class FlowStepType(str, enum.Enum):
       # existing...
       MY_STEP = "MY_STEP"
   ```

2. **Implement step** in `flow_service.py`:
   ```python
   def _execute_step(self, step_type, ...):
       # ...
       elif step_type == FlowStepType.MY_STEP:
           return self._execute_my_step(step, asset_ids, execution, step_index)
   
   def _execute_my_step(self, step: Dict, asset_ids: List[int], ...) -> Dict:
       # Implementation
       return {"processed": len(asset_ids)}
   ```

3. **Add schema validation** in `schemas.py` if needed

4. **Update documentation** in `ARCHITECTURE.md`

### Adding a New Source Type

1. **Add kind handling** in `stream_source_service.py`:
   ```python
   def _ingest_items(self, source: Source) -> List[Asset]:
       if source.kind == "my_new_kind":
           return self._ingest_my_new_kind(source)
   ```

2. **Add to source creation** in `source_service.py`

3. **Test polling** via the API or task

### Adding a New Task Type

1. **Add enum value** in `models.py`:
   ```python
   class TaskType(str, enum.Enum):
       # existing...
       MY_TASK = "my_task"
   ```

2. **Add validation** in `task_service.py`:
   ```python
   def _validate_task_input_config(self, task_type, target_id, ...):
       if task_type == TaskType.MY_TASK:
           # Validate target exists
   ```

3. **Add dispatcher** in `schedule.py`:
   ```python
   def _dispatch_task(self, task: Task):
       if task.type == TaskType.MY_TASK:
           my_task.delay(task.target_id)
   ```

4. **Create Celery task** if needed

---

## Key Services & Their Responsibilities

| Service | File | Responsibility |
|---------|------|----------------|
| `FlowService` | `flow_service.py` | Flow CRUD, execution, step processing |
| `SourceService` | `source_service.py` | Source CRUD, delegates to StreamSourceService |
| `StreamSourceService` | `stream_source_service.py` | Actual polling/ingestion logic |
| `AnnotationService` | `annotation_service.py` | Annotation runs, results, aggregation |
| `AssetService` | `asset_service.py` | Asset CRUD, fragments |
| `TaskService` | `task_service.py` | Task CRUD, validation |
| `EmbeddingService` | `embedding_service.py` | Vector embeddings |

---

## Celery Tasks Overview

| Task | Module | Purpose |
|------|--------|---------|
| `execute_flow` | `flow_tasks.py` | Execute a FlowExecution |
| `check_on_arrival_flows` | `flow_tasks.py` | Check for flows needing on_arrival trigger |
| `process_annotation_run` | `annotate.py` | Process annotation batch |
| `execute_source_poll` | `source_monitoring.py` | Poll a source for new content |
| `poll_active_sources` | `source_monitoring.py` | Check and queue due polls (beat) |
| `embed_bundle` | `embed.py` | Generate embeddings for bundle assets |
| `check_recurring_tasks` | `schedule.py` | Dispatch due scheduled tasks |

---

## Frontend Architecture

### Zustand Stores

| Store | File | Purpose |
|-------|------|---------|
| `useFlowStore` | `storeFlows.ts` | Flow CRUD, executions |
| `useSourceStore` | `storeSources.ts` | Source CRUD, polling |
| `useInfospaceStore` | `storeInfospace.tsx` | Active infospace context |
| `useBundleStore` | `storeBundles.ts` | Bundle operations |
| `useAnnotationRunStore` | `useAnnotationRunStore.ts` | Annotation runs |

### Key UI Components

| Component | Path | Purpose |
|-----------|------|---------|
| `FlowManager` | `components/collection/flows/` | Flow CRUD UI |
| `DataSourceManager` | `components/collection/sources/` | Source management |
| `AssetManager` | `components/collection/assets/` | Asset browser |
| `AnnotationSchemaManager` | `components/collection/annotation/` | Schema editor |

### SDK Usage Pattern

```typescript
// All SDK calls use the format: ServiceName.methodName({data})
import { FlowsService } from '@/client';

// List flows
const response = await FlowsService.flowsListFlows({ 
  infospaceId: activeInfospace.id 
});

// Create flow
const flow = await FlowsService.flowsCreateFlow({
  infospaceId: activeInfospace.id,
  requestBody: flowData,
});
```

---

## Database Schema Notes

### JSONB Fields (indexed with GIN)

- `Asset.fragments` - Curated annotation fields
- `Asset.source_metadata` - Source-specific metadata
- `Annotation.value` - Annotation results
- `Flow.steps` - Step definitions
- `Flow.cursor_state` - Delta tracking
- `FlowExecution.step_outputs` - Per-step results

### Key Indexes

- `ix_asset_bundle_id` - Asset lookup by bundle
- `ix_annotation_asset_id` - Annotation lookup by asset
- `ix_flow_infospace_status` - Flow filtering
- `ix_annotationrun_flow_execution` - Run lookup by execution

---

## Debugging Tips

### Check Flow Execution Status

```sql
SELECT 
  fe.id, fe.status, fe.error_message,
  fe.input_asset_ids, fe.step_outputs
FROM flowexecution fe
WHERE fe.flow_id = ?
ORDER BY fe.created_at DESC
LIMIT 10;
```

### Check Pending Assets for a Flow

```python
# Via API
GET /api/infospaces/{id}/flows/{flow_id}/pending-assets

# Returns assets not yet in cursor_state.processed_asset_ids
```

### Debug Celery Tasks

```bash
# Watch task execution
celery -A app.core.celery_app worker --loglevel=debug

# Check Redis queue
redis-cli LLEN celery

# Purge stuck tasks
celery -A app.core.celery_app purge
```

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Flow not triggering | `trigger_mode != on_arrival` | Check Flow.trigger_mode |
| Assets not appearing | Source not polling | Check Task schedule, Source.is_active |
| Annotations missing | AnnotationRun failed | Check run status, error_message |
| Delta not working | cursor_state corrupted | Use reset-cursor endpoint |
| 422 on API calls | OpenAPI spec has extra params | Regenerate client, check router deps |
| Celery SyntaxError | `await` in sync task | Use `run_async()` wrapper pattern |
| SDK function not found | Function names changed | Check new prefix pattern after regen |

### Backend Gotchas

**Router Dependencies:**
```python
# ❌ DON'T use type aliases in router dependencies
router = APIRouter(dependencies=[Depends(CurrentUser)])  # CurrentUser is Annotated!

# ✅ DO use the dependency function directly, or rely on parameter injection
router = APIRouter()  # Each route has current_user: CurrentUser
```

**Celery Async Pattern:**
```python
# ❌ DON'T use await in Celery tasks
@celery_app.task
def my_task():
    result = await async_service.method()  # SyntaxError!

# ✅ DO use asyncio wrapper
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

---

## Testing

### Running Backend Tests

```bash
cd backend
pytest app/tests/
```

### Key Test Scenarios

1. **One-off annotation**: Create run with `run_type=ONE_OFF`, verify in history
2. **Flow execution**: Create flow, activate, trigger, verify execution
3. **Delta tracking**: Run flow, add assets, run again, verify only new processed
4. **Step chaining**: Multi-step flow, verify each step output

---

## Deployment Checklist

### Backend Changes

- [ ] Run database migrations: `alembic upgrade head`
- [ ] Restart Celery workers
- [ ] Restart Celery beat
- [ ] Verify on_arrival flows triggering
- [ ] Check scheduled tasks running

### Frontend Changes

- [ ] Fetch latest OpenAPI spec from backend
- [ ] Regenerate client: `npm run generate-client`
- [ ] Check for SDK function name changes
- [ ] Update stores if function signatures changed
- [ ] Verify no TypeScript errors: `npm run typecheck`
- [ ] Rebuild frontend container if using Docker

### Full Stack Deployment

```bash
# 1. Apply migrations
docker compose exec backend alembic upgrade head

# 2. Regenerate frontend client
curl http://localhost:8022/api/v1/openapi.json > frontend/openapi.json
cd frontend && npm run generate-client

# 3. Restart all services
docker compose restart

# 4. Verify
docker compose logs celery_worker --tail 20  # Should show "ready"
curl http://localhost:8022/api/v1/healthz/ready  # Should return 200
```

---

## Contact & Resources

- **Architecture Docs**: `docs/internal/ARCHITECTURE.md`
- **API Docs**: `http://localhost:8000/docs` (FastAPI auto-generated)
- **OpenAPI Spec**: `backend/openapi.json`

---

*This document should be updated as the codebase evolves.*
