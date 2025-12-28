/**
 * Unlock Confirmation Dialog
 *
 * Per ADR-0002: Artifact Preservation on Unlock
 * Per SPEC-DAT-0001: Unlock cascades to downstream stages
 *
 * This dialog warns users before unlocking a locked stage that:
 * - Downstream stages will also be unlocked (cascade)
 * - Artifacts are preserved (not deleted)
 * - They will need to re-lock affected stages
 */

import { AlertTriangle, Unlock, X } from 'lucide-react';

export interface UnlockConfirmDialogProps {
  /** Whether the dialog is open */
  isOpen: boolean;
  /** Stage being unlocked */
  stageName: string;
  /** Stages that will be affected by cascade unlock */
  affectedStages: string[];
  /** Callback when user confirms unlock */
  onConfirm: () => void;
  /** Callback when user cancels */
  onCancel: () => void;
  /** Whether unlock is in progress */
  isLoading?: boolean;
}

/**
 * Confirmation dialog for unlocking a locked stage.
 *
 * Shows a warning about cascade effects and artifact preservation.
 */
export function UnlockConfirmDialog({
  isOpen,
  stageName,
  affectedStages,
  onConfirm,
  onCancel,
  isLoading = false,
}: UnlockConfirmDialogProps) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/50 backdrop-blur-sm"
        onClick={onCancel}
      />

      {/* Dialog */}
      <div className="relative bg-white rounded-xl shadow-2xl max-w-md w-full mx-4 overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-200">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-amber-100 rounded-lg">
              <Unlock className="w-5 h-5 text-amber-600" />
            </div>
            <h3 className="text-lg font-semibold text-slate-900">
              Unlock Stage?
            </h3>
          </div>
          <button
            onClick={onCancel}
            className="p-1 hover:bg-slate-100 rounded-lg transition-colors"
            title="Close dialog"
            aria-label="Close dialog"
          >
            <X className="w-5 h-5 text-slate-500" />
          </button>
        </div>

        {/* Content */}
        <div className="px-6 py-4">
          <p className="text-slate-700 mb-4">
            You are about to unlock the <strong>{stageName}</strong> stage.
          </p>

          {/* Warning */}
          <div className="flex gap-3 p-4 bg-amber-50 border border-amber-200 rounded-lg mb-4">
            <AlertTriangle className="w-5 h-5 text-amber-500 flex-shrink-0 mt-0.5" />
            <div className="text-sm">
              <p className="font-medium text-amber-800 mb-1">
                Cascade Unlock Warning
              </p>
              <p className="text-amber-700">
                Unlocking this stage will also unlock all downstream stages.
                You will need to re-process these stages.
              </p>
            </div>
          </div>

          {/* Affected Stages */}
          {affectedStages.length > 0 && (
            <div className="mb-4">
              <p className="text-sm font-medium text-slate-700 mb-2">
                Stages that will be unlocked:
              </p>
              <div className="flex flex-wrap gap-2">
                <span className="px-2 py-1 bg-slate-100 text-slate-700 text-sm rounded">
                  {stageName}
                </span>
                {affectedStages.map((stage) => (
                  <span
                    key={stage}
                    className="px-2 py-1 bg-slate-100 text-slate-600 text-sm rounded"
                  >
                    {stage}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Preservation Notice */}
          <div className="flex gap-2 text-sm text-slate-600">
            <span className="text-emerald-500">✓</span>
            <span>Your data and artifacts will be preserved.</span>
          </div>
        </div>

        {/* Actions */}
        <div className="flex justify-end gap-3 px-6 py-4 bg-slate-50 border-t border-slate-200">
          <button
            onClick={onCancel}
            disabled={isLoading}
            className="
              px-4 py-2 text-slate-700 hover:bg-slate-200
              rounded-lg transition-colors
              disabled:opacity-50 disabled:cursor-not-allowed
            "
          >
            Cancel
          </button>
          <button
            onClick={onConfirm}
            disabled={isLoading}
            className="
              px-4 py-2 bg-amber-500 hover:bg-amber-600
              text-white rounded-lg font-medium transition-colors
              disabled:opacity-50 disabled:cursor-not-allowed
              flex items-center gap-2
            "
          >
            {isLoading ? (
              <>
                <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                Unlocking...
              </>
            ) : (
              <>
                <Unlock className="w-4 h-4" />
                Unlock Stage
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}

export default UnlockConfirmDialog;
