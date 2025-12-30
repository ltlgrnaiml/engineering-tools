"""Fast table probing service.

Per ADR-0008: Probe must complete in <1s per table.
Per SPEC-0008: Use adapter.probe_schema(), not full reads.
"""

import asyncio
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING

from shared.contracts.dat.table_status import (
    TableAvailability,
    TableAvailabilityStatus,
)

if TYPE_CHECKING:
    from shared.contracts.dat.adapter import BaseFileAdapter

__version__ = "1.0.0"

PROBE_TIMEOUT_SECONDS = 1.0


async def probe_table(
    adapter: "BaseFileAdapter",
    file_path: str | Path,
    table_name: str | None = None,
) -> TableAvailability:
    """Probe a single table for availability status.

    Per ADR-0008: Fast probe without loading full data.

    Args:
        adapter: File adapter instance.
        file_path: Path to the file.
        table_name: Optional table/sheet name.

    Returns:
        TableAvailability: Status of the table.
    """
    file_path = Path(file_path) if isinstance(file_path, str) else file_path
    table_id = f"{file_path}::{table_name}" if table_name else str(file_path)

    try:
        result = await asyncio.wait_for(
            adapter.probe_schema(str(file_path), table_name),
            timeout=PROBE_TIMEOUT_SECONDS,
        )

        if result.row_count == 0:
            status = TableAvailabilityStatus.EMPTY
        elif result.error:
            status = TableAvailabilityStatus.PARTIAL
        else:
            status = TableAvailabilityStatus.AVAILABLE

        return TableAvailability(
            table_id=table_id,
            status=status,
            column_count=len(result.columns) if result.columns else 0,
            row_estimate=result.row_count,
            probed_at=datetime.now(timezone.utc),
        )

    except asyncio.TimeoutError:
        return TableAvailability(
            table_id=table_id,
            status=TableAvailabilityStatus.ERROR,
            error_message="Probe timeout exceeded",
            probed_at=datetime.now(timezone.utc),
        )

    except FileNotFoundError:
        return TableAvailability(
            table_id=table_id,
            status=TableAvailabilityStatus.MISSING,
            probed_at=datetime.now(timezone.utc),
        )

    except Exception as e:
        return TableAvailability(
            table_id=table_id,
            status=TableAvailabilityStatus.ERROR,
            error_message=str(e),
            probed_at=datetime.now(timezone.utc),
        )


async def probe_tables_batch(
    adapter: "BaseFileAdapter",
    file_path: str | Path,
    table_names: list[str],
) -> list[TableAvailability]:
    """Probe multiple tables in parallel.

    Args:
        adapter: File adapter instance.
        file_path: Path to the file.
        table_names: List of table/sheet names.

    Returns:
        List of TableAvailability results.
    """
    tasks = [
        probe_table(adapter, file_path, table_name)
        for table_name in table_names
    ]
    return await asyncio.gather(*tasks)
