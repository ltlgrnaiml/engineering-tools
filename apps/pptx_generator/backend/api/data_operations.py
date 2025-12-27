"""API endpoints for data operations (derive, join, concat, preview)."""

import logging
from typing import Any
from uuid import UUID

import pandas as pd
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

router = APIRouter()
logger = logging.getLogger(__name__)

# In-memory storage for data files (integrate with actual storage later)
data_files_db: dict[UUID, dict[str, Any]] = {}


class DeriveColumnRequest(BaseModel):
    """Request to create a derived column."""

    source_column: str = Field(..., description="Column to derive from")
    new_column_name: str = Field(..., description="Name for new column")
    derivation_type: str = Field(..., description="Type: regex, expression, lookup")
    pattern: str | None = Field(None, description="Regex pattern")
    expression: str | None = Field(None, description="Python expression")
    lookup_table: dict[str, str] | None = Field(None, description="Lookup table")


class JoinFilesRequest(BaseModel):
    """Request to join two data files."""

    primary_file_id: UUID = Field(..., description="Primary file ID")
    secondary_file_id: UUID = Field(..., description="Secondary file ID")
    join_type: str = Field(default="left", description="Join type")
    primary_column: str = Field(..., description="Primary join column")
    secondary_column: str = Field(..., description="Secondary join column")
    columns_to_include: list[str] = Field(default_factory=list, description="Columns to include")


class ConcatFilesRequest(BaseModel):
    """Request to concatenate data files."""

    file_ids: list[UUID] = Field(..., description="File IDs to concatenate")
    axis: int = Field(default=0, description="Axis: 0=rows, 1=columns")


class ColumnStatsResponse(BaseModel):
    """Statistics for a data column."""

    column_name: str
    data_type: str
    non_null_count: int
    null_count: int
    unique_count: int
    sample_values: list[Any]
    min_value: Any | None = None
    max_value: Any | None = None
    mean_value: float | None = None
    std_value: float | None = None


@router.get("/data/{project_id}/files")
async def list_data_files(project_id: UUID) -> dict[str, Any]:
    """List all data files for a project.

    Args:
        project_id: Project ID.

    Returns:
        List of data files with metadata.
    """
    from apps.pptx_generator.backend.api.data import data_files_db as global_data_files_db

    files: list[dict[str, Any]] = []
    for file_id, file_data in global_data_files_db.items():
        if isinstance(file_data, dict) and file_data.get("project_id") == project_id:
            files.append(
                {
                    "id": str(file_id),
                    "filename": file_data.get("filename", "unknown"),
                    "row_count": file_data.get("row_count", 0),
                    "column_count": len(file_data.get("columns", [])),
                    "columns": file_data.get("columns", []),
                }
            )

    return {"files": files, "count": len(files)}


@router.post("/data/{project_id}/derive-column")
async def derive_column(project_id: UUID, request: DeriveColumnRequest) -> dict[str, Any]:
    """Create a derived column from an existing column.

    Args:
        project_id: Project ID.
        request: Derivation configuration.

    Returns:
        Success message with preview of derived values.
    """
    from apps.pptx_generator.backend.api.data import data_files_db as global_data_files_db

    # Find the project's data file
    project_file: dict[str, Any] | None = None
    for _file_id, file_data in global_data_files_db.items():
        if isinstance(file_data, dict) and file_data.get("project_id") == project_id:
            project_file = file_data
            break

    if not project_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No data file found for project {project_id}",
        )

    df = project_file.get("dataframe")
    if df is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Data file has no dataframe loaded",
        )

    if request.source_column not in df.columns:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Source column '{request.source_column}' not found",
        )

    try:
        if request.derivation_type == "regex":
            if not request.pattern:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Pattern required for regex derivation",
                )
            # Extract using regex
            df[request.new_column_name] = (
                df[request.source_column].astype(str).str.extract(request.pattern, expand=False)
            )

        elif request.derivation_type == "lookup":
            if not request.lookup_table:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Lookup table required for lookup derivation",
                )
            df[request.new_column_name] = df[request.source_column].map(request.lookup_table)

        elif request.derivation_type == "expression":
            # For safety, only allow simple expressions
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="Expression derivation not yet implemented for security reasons",
            )

        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown derivation type: {request.derivation_type}",
            )

        # Update columns list
        if request.new_column_name not in project_file.get("columns", []):
            project_file["columns"].append(request.new_column_name)

        # Get preview
        preview = df[[request.source_column, request.new_column_name]].head(5).to_dict("records")

        logger.info(f"Created derived column '{request.new_column_name}' for project {project_id}")

        return {
            "message": f"Derived column '{request.new_column_name}' created successfully",
            "new_column": request.new_column_name,
            "preview": preview,
            "non_null_count": int(df[request.new_column_name].notna().sum()),
        }

    except Exception as e:
        logger.error(f"Failed to derive column: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to derive column: {str(e)}",
        ) from e


@router.post("/data/{project_id}/join")
async def join_files(project_id: UUID, request: JoinFilesRequest) -> dict[str, Any]:
    """Join two data files.

    Args:
        project_id: Project ID.
        request: Join configuration.

    Returns:
        Success message with joined data info.
    """
    from apps.pptx_generator.backend.api.data import data_files_db as global_data_files_db

    primary_file = global_data_files_db.get(request.primary_file_id)
    secondary_file = global_data_files_db.get(request.secondary_file_id)

    if not primary_file or not isinstance(primary_file, dict):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Primary file {request.primary_file_id} not found",
        )

    if not secondary_file or not isinstance(secondary_file, dict):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Secondary file {request.secondary_file_id} not found",
        )

    df_primary = primary_file.get("dataframe")
    df_secondary = secondary_file.get("dataframe")

    if (
        df_primary is None
        or df_secondary is None
        or not isinstance(df_primary, pd.DataFrame)
        or not isinstance(df_secondary, pd.DataFrame)
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="One or both files have no dataframe loaded",
        )

    try:
        # Select columns from secondary
        if request.columns_to_include:
            cols_to_include = [request.secondary_column] + request.columns_to_include
            df_secondary_subset = df_secondary[cols_to_include]
        else:
            df_secondary_subset = df_secondary

        # Perform join
        how_map = {"left": "left", "right": "right", "inner": "inner", "outer": "outer"}
        how = how_map.get(request.join_type, "left")

        df_joined = df_primary.merge(
            df_secondary_subset,
            left_on=request.primary_column,
            right_on=request.secondary_column,
            how=how,
            suffixes=("", "_joined"),
        )

        # Update primary file
        if isinstance(primary_file, dict):
            primary_file["dataframe"] = df_joined
            primary_file["row_count"] = len(df_joined)
            primary_file["columns"] = list(df_joined.columns)

        logger.info(
            f"Joined files for project {project_id}: "
            f"{len(df_primary)} + {len(df_secondary)} -> {len(df_joined)} rows"
        )

        return {
            "message": "Files joined successfully",
            "result_row_count": len(df_joined),
            "result_columns": list(df_joined.columns),
            "join_type": request.join_type,
        }

    except Exception as e:
        logger.error(f"Failed to join files: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to join files: {str(e)}",
        ) from e


@router.post("/data/{project_id}/concat")
async def concat_files(project_id: UUID, request: ConcatFilesRequest) -> dict[str, Any]:
    """Concatenate multiple data files.

    Args:
        project_id: Project ID.
        request: Concat configuration.

    Returns:
        Success message with concatenated data info.
    """
    from apps.pptx_generator.backend.api.data import data_files_db as global_data_files_db

    if len(request.file_ids) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least 2 files required for concatenation",
        )

    dataframes: list[pd.DataFrame] = []
    for file_id in request.file_ids:
        file_data = global_data_files_db.get(file_id)
        if not file_data or not isinstance(file_data, dict):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"File {file_id} not found",
            )
        df = file_data.get("dataframe")
        if df is None or not isinstance(df, pd.DataFrame):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File {file_id} has no dataframe loaded",
            )
        dataframes.append(df)

    try:
        axis_val = 0 if request.axis not in (0, 1) else request.axis
        df_concat = pd.concat(dataframes, axis=axis_val, ignore_index=True)  # type: ignore[call-overload]

        # Store as new file or update first file
        first_file = global_data_files_db.get(request.file_ids[0])
        if first_file and isinstance(first_file, dict):
            first_file["dataframe"] = df_concat
            first_file["row_count"] = len(df_concat)
            first_file["columns"] = list(df_concat.columns)

        logger.info(f"Concatenated {len(request.file_ids)} files for project {project_id}")

        return {
            "message": "Files concatenated successfully",
            "result_row_count": len(df_concat),
            "result_columns": list(df_concat.columns),
            "files_merged": len(request.file_ids),
        }

    except Exception as e:
        logger.error(f"Failed to concat files: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to concat files: {str(e)}",
        ) from e


@router.get("/data/{project_id}/preview")
async def preview_data(
    project_id: UUID, rows: int = 10, columns: list[str] | None = None
) -> dict[str, Any]:
    """Get a preview of the project's data.

    Args:
        project_id: Project ID.
        rows: Number of rows to preview.
        columns: Optional list of columns to include.

    Returns:
        Preview data with sample rows.
    """
    from apps.pptx_generator.backend.api.data import data_files_db as global_data_files_db

    # Find the project's data file
    project_file: dict[str, Any] | None = None
    for _file_id, file_data in global_data_files_db.items():
        if isinstance(file_data, dict) and file_data.get("project_id") == project_id:
            project_file = file_data
            break

    if not project_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No data file found for project {project_id}",
        )

    df = project_file.get("dataframe")
    if df is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Data file has no dataframe loaded",
        )

    # Select columns if specified
    if columns:
        available = [c for c in columns if c in df.columns]
        df_preview = df[available].head(rows)
    else:
        df_preview = df.head(rows)

    return {
        "rows": df_preview.to_dict("records"),
        "total_rows": len(df),
        "total_columns": len(df.columns),
        "columns": list(df.columns),
    }


@router.get("/data/{project_id}/column-stats/{column_name}")
async def get_column_stats(project_id: UUID, column_name: str) -> ColumnStatsResponse:
    """Get statistics for a specific column.

    Args:
        project_id: Project ID.
        column_name: Column name.

    Returns:
        Column statistics.
    """
    from apps.pptx_generator.backend.api.data import data_files_db as global_data_files_db

    # Find the project's data file
    project_file: dict[str, Any] | None = None
    for _file_id, file_data in global_data_files_db.items():
        if isinstance(file_data, dict) and file_data.get("project_id") == project_id:
            project_file = file_data
            break

    if not project_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No data file found for project {project_id}",
        )

    df = project_file.get("dataframe")
    if df is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Data file has no dataframe loaded",
        )

    if column_name not in df.columns:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Column '{column_name}' not found",
        )

    col = df[column_name]
    stats = ColumnStatsResponse(
        column_name=column_name,
        data_type=str(col.dtype),
        non_null_count=int(col.notna().sum()),
        null_count=int(col.isna().sum()),
        unique_count=int(col.nunique()),
        sample_values=col.dropna().head(5).tolist(),
    )

    # Add numeric stats if applicable
    if pd.api.types.is_numeric_dtype(col):
        stats.min_value = float(col.min()) if col.notna().any() else None
        stats.max_value = float(col.max()) if col.notna().any() else None
        stats.mean_value = float(col.mean()) if col.notna().any() else None
        stats.std_value = float(col.std()) if col.notna().any() else None

    return stats
