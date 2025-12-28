/**
 * Progress Indicator with WebSocket Integration
 *
 * Per SPEC-DAT-0004: Real-time progress updates via WebSocket
 * Per ADR-0040: Large file streaming progress tracking
 *
 * This component connects to the backend WebSocket endpoint
 * to receive real-time progress updates during Parse/Export stages.
 */

import { useEffect, useState, useCallback } from 'react';
import { Loader2, CheckCircle, XCircle, AlertCircle } from 'lucide-react';

export interface ProgressData {
  /** Stage ID being processed */
  stageId: string;
  /** Event type */
  eventType: 'started' | 'progress' | 'chunk_complete' | 'completed' | 'cancelled' | 'error';
  /** Progress percentage (0-100) */
  progressPct: number;
  /** Rows processed so far */
  rowsProcessed: number;
  /** Chunks completed */
  chunksCompleted: number;
  /** Current file being processed */
  currentFile?: string;
  /** Estimated time remaining in ms */
  estimatedRemainingMs?: number;
  /** Status message */
  message?: string;
  /** Timestamp */
  timestamp: string;
}

export interface ProgressIndicatorProps {
  /** Run ID to connect to */
  runId: string;
  /** Whether to show the indicator */
  isActive: boolean;
  /** Callback when progress completes */
  onComplete?: () => void;
  /** Callback on error */
  onError?: (message: string) => void;
  /** Callback on cancel */
  onCancel?: () => void;
  /** WebSocket base URL (defaults to current host) */
  wsBaseUrl?: string;
}

/**
 * Format milliseconds to human-readable time.
 */
function formatTime(ms: number): string {
  if (ms < 1000) return 'less than a second';
  const seconds = Math.floor(ms / 1000);
  if (seconds < 60) return `${seconds}s`;
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = seconds % 60;
  if (minutes < 60) return `${minutes}m ${remainingSeconds}s`;
  const hours = Math.floor(minutes / 60);
  const remainingMinutes = minutes % 60;
  return `${hours}h ${remainingMinutes}m`;
}

/**
 * Format number with commas.
 */
function formatNumber(n: number): string {
  return n.toLocaleString();
}

/**
 * Progress indicator component with WebSocket connection.
 */
export function ProgressIndicator({
  runId,
  isActive,
  onComplete,
  onError,
  onCancel,
  wsBaseUrl,
}: ProgressIndicatorProps) {
  const [progress, setProgress] = useState<ProgressData | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // WebSocket connection
  useEffect(() => {
    if (!isActive || !runId) return;

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = wsBaseUrl || window.location.host;
    const wsUrl = `${protocol}//${host}/ws/dat/runs/${runId}/progress`;

    let ws: WebSocket | null = null;
    let pingInterval: ReturnType<typeof setInterval> | null = null;

    try {
      ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        setIsConnected(true);
        setError(null);
        // Send periodic pings to keep connection alive
        pingInterval = setInterval(() => {
          if (ws?.readyState === WebSocket.OPEN) {
            ws.send('ping');
          }
        }, 25000);
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          
          // Handle heartbeat
          if (data.type === 'heartbeat') return;
          // Handle pong
          if (event.data === 'pong') return;

          // Convert snake_case to camelCase
          const progressData: ProgressData = {
            stageId: data.stage_id,
            eventType: data.event_type,
            progressPct: data.progress_pct,
            rowsProcessed: data.rows_processed,
            chunksCompleted: data.chunks_completed,
            currentFile: data.current_file,
            estimatedRemainingMs: data.estimated_remaining_ms,
            message: data.message,
            timestamp: data.timestamp,
          };

          setProgress(progressData);

          // Handle completion events
          if (progressData.eventType === 'completed') {
            onComplete?.();
          } else if (progressData.eventType === 'error') {
            setError(progressData.message || 'An error occurred');
            onError?.(progressData.message || 'An error occurred');
          } else if (progressData.eventType === 'cancelled') {
            onCancel?.();
          }
        } catch (e) {
          console.error('Failed to parse WebSocket message:', e);
        }
      };

      ws.onerror = () => {
        setError('Connection error');
        setIsConnected(false);
      };

      ws.onclose = () => {
        setIsConnected(false);
      };
    } catch (e) {
      setError('Failed to connect');
    }

    return () => {
      if (pingInterval) clearInterval(pingInterval);
      if (ws) ws.close();
    };
  }, [runId, isActive, wsBaseUrl, onComplete, onError, onCancel]);

  if (!isActive) return null;

  return (
    <div className="bg-white border border-slate-200 rounded-lg p-4 shadow-sm">
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          {progress?.eventType === 'completed' ? (
            <CheckCircle className="w-5 h-5 text-emerald-500" />
          ) : progress?.eventType === 'error' ? (
            <XCircle className="w-5 h-5 text-red-500" />
          ) : progress?.eventType === 'cancelled' ? (
            <AlertCircle className="w-5 h-5 text-amber-500" />
          ) : (
            <Loader2 className="w-5 h-5 text-emerald-500 animate-spin" />
          )}
          <span className="font-medium text-slate-900">
            {progress?.eventType === 'completed'
              ? 'Processing Complete'
              : progress?.eventType === 'error'
              ? 'Processing Failed'
              : progress?.eventType === 'cancelled'
              ? 'Processing Cancelled'
              : 'Processing...'}
          </span>
        </div>
        {isConnected && (
          <span className="text-xs text-emerald-600 flex items-center gap-1">
            <span className="w-2 h-2 bg-emerald-500 rounded-full" />
            Connected
          </span>
        )}
      </div>

      {/* Progress Bar */}
      <div className="mb-3">
        <div className="flex justify-between text-sm text-slate-600 mb-1">
          <span>{progress?.progressPct?.toFixed(1) || 0}%</span>
          {progress?.estimatedRemainingMs && progress.estimatedRemainingMs > 0 && (
            <span>~{formatTime(progress.estimatedRemainingMs)} remaining</span>
          )}
        </div>
        <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
          <div
            className={`
              h-full transition-all duration-300 ease-out
              ${progress?.eventType === 'error' ? 'bg-red-500' : ''}
              ${progress?.eventType === 'cancelled' ? 'bg-amber-500' : ''}
              ${progress?.eventType === 'completed' ? 'bg-emerald-500' : ''}
              ${!['error', 'cancelled', 'completed'].includes(progress?.eventType || '') ? 'bg-emerald-500' : ''}
            `}
            style={{ width: `${progress?.progressPct || 0}%` }}
          />
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-4 text-sm">
        <div>
          <span className="text-slate-500 block">Rows</span>
          <span className="font-medium text-slate-900">
            {formatNumber(progress?.rowsProcessed || 0)}
          </span>
        </div>
        <div>
          <span className="text-slate-500 block">Chunks</span>
          <span className="font-medium text-slate-900">
            {progress?.chunksCompleted || 0}
          </span>
        </div>
        <div>
          <span className="text-slate-500 block">File</span>
          <span className="font-medium text-slate-900 truncate block" title={progress?.currentFile}>
            {progress?.currentFile?.split('/').pop() || '-'}
          </span>
        </div>
      </div>

      {/* Message */}
      {progress?.message && (
        <p className={`
          mt-3 text-sm
          ${progress.eventType === 'error' ? 'text-red-600' : 'text-slate-600'}
        `}>
          {progress.message}
        </p>
      )}

      {/* Error state */}
      {error && !progress?.message && (
        <p className="mt-3 text-sm text-red-600">{error}</p>
      )}
    </div>
  );
}

/**
 * Hook for managing progress state without the UI component.
 * Note: For full WebSocket integration, use the ProgressIndicator component.
 */
export function useProgressState() {
  const [progress, setProgress] = useState<ProgressData | null>(null);
  const [isConnected, setIsConnected] = useState(false);

  const updateProgress = useCallback((data: ProgressData) => {
    setProgress(data);
  }, []);

  const setConnected = useCallback((connected: boolean) => {
    setIsConnected(connected);
  }, []);

  const reset = useCallback(() => {
    setProgress(null);
    setIsConnected(false);
  }, []);

  return {
    progress,
    isConnected,
    isComplete: progress?.eventType === 'completed',
    isError: progress?.eventType === 'error',
    isCancelled: progress?.eventType === 'cancelled',
    updateProgress,
    setConnected,
    reset,
  };
}

export default ProgressIndicator;
