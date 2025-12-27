"""DataSet Service - cross-tool DataSet discovery and access.

Provides gateway-level APIs for:
- Listing DataSets from all tools
- Previewing DataSet contents
- DataSet metadata and lineage
"""

from fastapi import APIRouter, HTTPException, Query

from shared.contracts.core.dataset import DataSetManifest, DataSetPreview, DataSetRef
from shared.storage.artifact_store import ArtifactStore

router = APIRouter()

# Singleton store instance
_store: ArtifactStore | None = None


def get_store() -> ArtifactStore:
    """Get or create the artifact store."""
    global _store
    if _store is None:
        _store = ArtifactStore()
    return _store


@router.get("", response_model=list[DataSetRef])
@router.get("/", response_model=list[DataSetRef])
async def list_datasets(
    tool: str | None = Query(None, description="Filter by source tool (dat, sov, pptx)"),
    limit: int = Query(50, ge=1, le=500),
) -> list[DataSetRef]:
    """List all available DataSets, optionally filtered by source tool."""
    store = get_store()
    return await store.list_datasets(tool=tool, limit=limit)


@router.get("/{dataset_id}", response_model=DataSetManifest)
async def get_dataset(dataset_id: str) -> DataSetManifest:
    """Get DataSet manifest (schema, lineage, provenance)."""
    store = get_store()
    try:
        return await store.get_manifest(dataset_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"DataSet not found: {dataset_id}")


@router.get("/{dataset_id}/preview", response_model=DataSetPreview)
async def preview_dataset(
    dataset_id: str,
    rows: int = Query(100, ge=1, le=1000),
) -> DataSetPreview:
    """Preview first N rows of a DataSet."""
    store = get_store()
    
    try:
        manifest = await store.get_manifest(dataset_id)
        df = await store.read_dataset(dataset_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"DataSet not found: {dataset_id}")
    
    # Get preview rows
    preview_df = df.head(rows)
    
    return DataSetPreview(
        dataset_id=dataset_id,
        columns=preview_df.columns,
        rows=preview_df.to_dicts(),
        total_rows=manifest.row_count,
        preview_rows=len(preview_df),
    )


@router.get("/{dataset_id}/lineage")
async def get_dataset_lineage(dataset_id: str) -> dict:
    """Get DataSet lineage (parent and child relationships)."""
    store = get_store()
    
    try:
        manifest = await store.get_manifest(dataset_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"DataSet not found: {dataset_id}")
    
    # Get parent manifests
    parents = []
    for parent_id in manifest.parent_dataset_ids:
        try:
            parent_manifest = await store.get_manifest(parent_id)
            parents.append(DataSetRef(
                dataset_id=parent_manifest.dataset_id,
                name=parent_manifest.name,
                created_at=parent_manifest.created_at,
                created_by_tool=parent_manifest.created_by_tool,
                row_count=parent_manifest.row_count,
                column_count=len(parent_manifest.columns),
                parent_count=len(parent_manifest.parent_dataset_ids),
            ))
        except FileNotFoundError:
            continue
    
    # Find children (datasets that have this as parent)
    all_datasets = await store.list_datasets(limit=500)
    children = []
    for ds_ref in all_datasets:
        if ds_ref.dataset_id == dataset_id:
            continue
        try:
            child_manifest = await store.get_manifest(ds_ref.dataset_id)
            if dataset_id in child_manifest.parent_dataset_ids:
                children.append(ds_ref)
        except FileNotFoundError:
            continue
    
    return {
        "dataset_id": dataset_id,
        "name": manifest.name,
        "parents": parents,
        "children": children,
    }
