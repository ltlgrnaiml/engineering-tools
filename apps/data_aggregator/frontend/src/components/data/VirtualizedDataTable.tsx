/**
 * Virtualized Data Table Component
 *
 * Per ADR-0041: Large file preview support
 * Per SPEC-DAT-0004: Large File Streaming
 *
 * Features:
 * - Virtualization for 100,000+ rows without performance degradation
 * - Column sorting
 * - Column resizing
 * - Column type indicators
 * - Null/empty cell indicators
 * - Row selection support
 * - Responsive horizontal scrolling
 */

import {
  useState,
  useRef,
  useCallback,
  useMemo,
  useEffect,
  ReactNode,
} from 'react';
import {
  ArrowUp,
  ArrowDown,
  Hash,
  Type,
  Calendar,
  ToggleLeft,
  FileQuestion,
  GripVertical,
} from 'lucide-react';

/**
 * Column data type for display.
 */
export type ColumnType =
  | 'integer'
  | 'float'
  | 'string'
  | 'boolean'
  | 'datetime'
  | 'date'
  | 'time'
  | 'binary'
  | 'null'
  | 'unknown';

/**
 * Column configuration.
 */
export interface ColumnConfig {
  /** Column identifier/key */
  key: string;
  /** Display header */
  header: string;
  /** Column width in pixels */
  width?: number;
  /** Minimum width */
  minWidth?: number;
  /** Maximum width */
  maxWidth?: number;
  /** Data type for indicator */
  type?: ColumnType;
  /** Whether column is sortable */
  sortable?: boolean;
  /** Whether column is resizable */
  resizable?: boolean;
  /** Custom cell renderer */
  renderCell?: (value: unknown, row: Record<string, unknown>) => ReactNode;
}

/**
 * Sort direction.
 */
export type SortDirection = 'asc' | 'desc' | null;

/**
 * Sort state.
 */
export interface SortState {
  columnKey: string;
  direction: SortDirection;
}

/**
 * Props for VirtualizedDataTable.
 */
export interface VirtualizedDataTableProps {
  /** Array of data rows */
  data: Record<string, unknown>[];
  /** Column configurations */
  columns: ColumnConfig[];
  /** Row height in pixels */
  rowHeight?: number;
  /** Visible height of table (viewport) */
  height?: number;
  /** Whether rows are selectable */
  selectable?: boolean;
  /** Selected row indices */
  selectedRows?: Set<number>;
  /** Callback when row selection changes */
  onSelectionChange?: (selectedRows: Set<number>) => void;
  /** Callback when sort changes */
  onSortChange?: (sort: SortState | null) => void;
  /** Current sort state */
  sort?: SortState | null;
  /** Loading state */
  isLoading?: boolean;
  /** Empty state message */
  emptyMessage?: string;
  /** Total row count (for virtual scrolling with server data) */
  totalRows?: number;
  /** Callback to load more rows */
  onLoadMore?: (startIndex: number, count: number) => void;
}

/**
 * Get icon for column type.
 */
function TypeIcon({ type }: { type: ColumnType }) {
  const iconClass = 'w-3 h-3 text-slate-400';

  switch (type) {
    case 'integer':
    case 'float':
      return <Hash className={iconClass} />;
    case 'string':
      return <Type className={iconClass} />;
    case 'boolean':
      return <ToggleLeft className={iconClass} />;
    case 'datetime':
    case 'date':
    case 'time':
      return <Calendar className={iconClass} />;
    default:
      return <FileQuestion className={iconClass} />;
  }
}

/**
 * Format cell value for display.
 */
function formatCellValue(value: unknown, _type?: ColumnType): ReactNode {
  if (value === null || value === undefined) {
    return <span className="text-slate-300 italic text-xs">NULL</span>;
  }

  if (value === '') {
    return <span className="text-slate-300 italic text-xs">empty</span>;
  }

  if (typeof value === 'boolean') {
    return (
      <span
        className={`px-1.5 py-0.5 rounded text-xs font-medium ${
          value
            ? 'bg-emerald-100 text-emerald-700'
            : 'bg-slate-100 text-slate-600'
        }`}
      >
        {value ? 'true' : 'false'}
      </span>
    );
  }

  if (typeof value === 'number') {
    return (
      <span className="font-mono text-sm">
        {Number.isInteger(value) ? value.toString() : value.toFixed(2)}
      </span>
    );
  }

  if (value instanceof Date) {
    return (
      <span className="text-sm">{value.toISOString().split('T')[0]}</span>
    );
  }

  return <span className="text-sm truncate">{String(value)}</span>;
}

/**
 * Virtualized Data Table Component
 *
 * High-performance data table that uses virtualization to handle
 * 100,000+ rows efficiently. Supports sorting, column resizing,
 * and row selection.
 *
 * @example
 * ```tsx
 * <VirtualizedDataTable
 *   data={rows}
 *   columns={[
 *     { key: 'id', header: 'ID', type: 'integer', width: 80 },
 *     { key: 'name', header: 'Name', type: 'string' },
 *   ]}
 *   height={400}
 *   selectable
 *   onSelectionChange={setSelected}
 * />
 * ```
 */
export function VirtualizedDataTable({
  data,
  columns,
  rowHeight = 40,
  height = 400,
  selectable = false,
  selectedRows = new Set(),
  onSelectionChange,
  onSortChange,
  sort,
  isLoading = false,
  emptyMessage = 'No data available',
  totalRows,
  onLoadMore,
}: VirtualizedDataTableProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [scrollTop, setScrollTop] = useState(0);
  const [columnWidths, setColumnWidths] = useState<Record<string, number>>({});
  const [resizing, setResizing] = useState<string | null>(null);

  // Calculate visible rows based on scroll position
  const totalHeight = (totalRows ?? data.length) * rowHeight;
  const visibleCount = Math.ceil(height / rowHeight) + 2; // +2 for buffer
  const startIndex = Math.max(0, Math.floor(scrollTop / rowHeight) - 1);
  const endIndex = Math.min(
    (totalRows ?? data.length) - 1,
    startIndex + visibleCount
  );

  // Get visible rows
  const visibleRows = useMemo(() => {
    const rows: Array<{ index: number; data: Record<string, unknown> }> = [];
    for (let i = startIndex; i <= endIndex; i++) {
      if (data[i]) {
        rows.push({ index: i, data: data[i] });
      }
    }
    return rows;
  }, [data, startIndex, endIndex]);

  // Handle scroll
  const handleScroll = useCallback(
    (e: React.UIEvent<HTMLDivElement>) => {
      const newScrollTop = e.currentTarget.scrollTop;
      setScrollTop(newScrollTop);

      // Trigger load more if needed
      if (onLoadMore && totalRows) {
        const loadThreshold = (endIndex + 10) * rowHeight;
        if (newScrollTop + height > loadThreshold) {
          onLoadMore(endIndex + 1, 50);
        }
      }
    },
    [endIndex, height, onLoadMore, rowHeight, totalRows]
  );

  // Handle column resize
  const handleResizeStart = useCallback(
    (columnKey: string, e: React.MouseEvent) => {
      e.preventDefault();
      setResizing(columnKey);

      const startX = e.clientX;
      const startWidth =
        columnWidths[columnKey] ??
        columns.find((c) => c.key === columnKey)?.width ??
        150;

      const handleMouseMove = (moveEvent: MouseEvent) => {
        const delta = moveEvent.clientX - startX;
        const col = columns.find((c) => c.key === columnKey);
        const minWidth = col?.minWidth ?? 50;
        const maxWidth = col?.maxWidth ?? 500;
        const newWidth = Math.max(minWidth, Math.min(maxWidth, startWidth + delta));

        setColumnWidths((prev) => ({ ...prev, [columnKey]: newWidth }));
      };

      const handleMouseUp = () => {
        setResizing(null);
        document.removeEventListener('mousemove', handleMouseMove);
        document.removeEventListener('mouseup', handleMouseUp);
      };

      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
    },
    [columnWidths, columns]
  );

  // Handle sort
  const handleSort = useCallback(
    (columnKey: string) => {
      if (!onSortChange) return;

      if (sort?.columnKey === columnKey) {
        if (sort.direction === 'asc') {
          onSortChange({ columnKey, direction: 'desc' });
        } else if (sort.direction === 'desc') {
          onSortChange(null);
        }
      } else {
        onSortChange({ columnKey, direction: 'asc' });
      }
    },
    [onSortChange, sort]
  );

  // Handle row selection
  const handleRowClick = useCallback(
    (index: number, e: React.MouseEvent) => {
      if (!selectable || !onSelectionChange) return;

      const newSelection = new Set(selectedRows);

      if (e.shiftKey && selectedRows.size > 0) {
        // Range selection
        const lastSelected = Array.from(selectedRows).pop() ?? 0;
        const start = Math.min(lastSelected, index);
        const end = Math.max(lastSelected, index);
        for (let i = start; i <= end; i++) {
          newSelection.add(i);
        }
      } else if (e.ctrlKey || e.metaKey) {
        // Toggle selection
        if (newSelection.has(index)) {
          newSelection.delete(index);
        } else {
          newSelection.add(index);
        }
      } else {
        // Single selection
        newSelection.clear();
        newSelection.add(index);
      }

      onSelectionChange(newSelection);
    },
    [selectable, selectedRows, onSelectionChange]
  );

  // Get column width
  const getColumnWidth = useCallback(
    (col: ColumnConfig) => columnWidths[col.key] ?? col.width ?? 150,
    [columnWidths]
  );

  // Calculate total table width
  const tableWidth = useMemo(
    () => columns.reduce((sum, col) => sum + getColumnWidth(col), 0),
    [columns, getColumnWidth]
  );

  // Cleanup resize listener
  useEffect(() => {
    return () => {
      setResizing(null);
    };
  }, []);

  if (isLoading) {
    return (
      <div
        className="flex items-center justify-center bg-slate-50 rounded-lg border border-slate-200"
        style={{ height }}
      >
        <div className="text-slate-500">Loading data...</div>
      </div>
    );
  }

  if (data.length === 0) {
    return (
      <div
        className="flex items-center justify-center bg-slate-50 rounded-lg border border-slate-200"
        style={{ height }}
      >
        <div className="text-slate-500">{emptyMessage}</div>
      </div>
    );
  }

  return (
    <div
      className="border border-slate-200 rounded-lg overflow-hidden bg-white"
      style={{ height }}
    >
      {/* Header */}
      <div
        className="flex bg-slate-50 border-b border-slate-200 sticky top-0 z-10"
        style={{ width: tableWidth }}
      >
        {columns.map((col) => {
          const width = getColumnWidth(col);
          const isSorted = sort?.columnKey === col.key;

          return (
            <div
              key={col.key}
              className="relative flex items-center px-3 py-2 border-r border-slate-200 last:border-r-0"
              style={{ width, minWidth: width }}
            >
              <button
                onClick={() => col.sortable !== false && handleSort(col.key)}
                disabled={col.sortable === false}
                className={`
                  flex items-center gap-2 flex-1 min-w-0
                  ${col.sortable !== false ? 'hover:text-slate-900 cursor-pointer' : 'cursor-default'}
                `}
              >
                {col.type && <TypeIcon type={col.type} />}
                <span className="font-medium text-sm text-slate-700 truncate">
                  {col.header}
                </span>
                {isSorted && (
                  <span className="text-emerald-500">
                    {sort?.direction === 'asc' ? (
                      <ArrowUp className="w-3 h-3" />
                    ) : (
                      <ArrowDown className="w-3 h-3" />
                    )}
                  </span>
                )}
              </button>

              {/* Resize handle */}
              {col.resizable !== false && (
                <div
                  onMouseDown={(e) => handleResizeStart(col.key, e)}
                  className={`
                    absolute right-0 top-0 bottom-0 w-4 cursor-col-resize
                    flex items-center justify-center
                    hover:bg-slate-200 transition-colors
                    ${resizing === col.key ? 'bg-emerald-200' : ''}
                  `}
                >
                  <GripVertical className="w-3 h-3 text-slate-400" />
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Virtualized body */}
      <div
        ref={containerRef}
        className="overflow-auto"
        style={{ height: height - 40 }} // Subtract header height
        onScroll={handleScroll}
      >
        <div style={{ height: totalHeight, position: 'relative', width: tableWidth }}>
          {visibleRows.map(({ index, data: row }) => {
            const isSelected = selectedRows.has(index);
            const top = index * rowHeight;

            return (
              <div
                key={index}
                onClick={(e) => handleRowClick(index, e)}
                className={`
                  absolute left-0 right-0 flex border-b border-slate-100
                  ${selectable ? 'cursor-pointer' : ''}
                  ${isSelected ? 'bg-emerald-50' : 'hover:bg-slate-50'}
                  transition-colors
                `}
                style={{ top, height: rowHeight, width: tableWidth }}
              >
                {columns.map((col) => {
                  const width = getColumnWidth(col);
                  const value = row[col.key];

                  return (
                    <div
                      key={col.key}
                      className="flex items-center px-3 border-r border-slate-100 last:border-r-0 overflow-hidden"
                      style={{ width, minWidth: width }}
                    >
                      {col.renderCell
                        ? col.renderCell(value, row)
                        : formatCellValue(value, col.type)}
                    </div>
                  );
                })}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

export default VirtualizedDataTable;
