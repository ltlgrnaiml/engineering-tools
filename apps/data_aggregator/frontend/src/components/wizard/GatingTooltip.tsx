/**
 * Gating Tooltip Component
 *
 * Per ADR-0004: Forward gating with stage dependencies
 * Per SPEC-0024: Stage dependencies and requirements
 *
 * This component shows tooltips explaining why a stage is locked
 * and what prerequisites must be met to unlock it.
 */

import { ReactNode, useState } from 'react';
import { Lock } from 'lucide-react';

export interface GatingTooltipProps {
  /** The content to wrap with tooltip */
  children: ReactNode;
  /** Name of the locked stage */
  stageName: string;
  /** Required stages that must be completed first */
  requiredStages: string[];
  /** Whether the stage is currently locked */
  isLocked: boolean;
  /** Optional custom message */
  message?: string;
}

/**
 * Tooltip that explains stage gating requirements.
 *
 * Shows on hover when a stage is locked, explaining what
 * prerequisites must be completed.
 */
export function GatingTooltip({
  children,
  stageName,
  requiredStages,
  isLocked,
  message,
}: GatingTooltipProps) {
  const [isVisible, setIsVisible] = useState(false);

  if (!isLocked) {
    return <>{children}</>;
  }

  return (
    <div
      className="relative inline-block"
      onMouseEnter={() => setIsVisible(true)}
      onMouseLeave={() => setIsVisible(false)}
    >
      {children}

      {/* Tooltip */}
      {isVisible && (
        <div
          className="
            absolute z-50 bottom-full left-1/2 -translate-x-1/2 mb-2
            min-w-[200px] max-w-[280px]
          "
          role="tooltip"
        >
          <div className="bg-slate-900 text-white text-sm rounded-lg shadow-lg p-3">
            {/* Header */}
            <div className="flex items-center gap-2 mb-2">
              <Lock className="w-4 h-4 text-amber-400" />
              <span className="font-medium">Stage Locked</span>
            </div>

            {/* Message */}
            <p className="text-slate-300 text-xs mb-2">
              {message || `Complete the required stages to unlock ${stageName}.`}
            </p>

            {/* Required Stages */}
            {requiredStages.length > 0 && (
              <div>
                <p className="text-slate-400 text-xs mb-1">Required:</p>
                <div className="flex flex-wrap gap-1">
                  {requiredStages.map((stage) => (
                    <span
                      key={stage}
                      className="
                        px-2 py-0.5 bg-slate-700 text-slate-200
                        text-xs rounded
                      "
                    >
                      {stage}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Arrow */}
            <div
              className="
                absolute top-full left-1/2 -translate-x-1/2
                border-8 border-transparent border-t-slate-900
              "
            />
          </div>
        </div>
      )}
    </div>
  );
}

/**
 * Stage dependency map per SPEC-0024.
 */
export const STAGE_DEPENDENCIES: Record<string, string[]> = {
  discovery: [],
  selection: ['Discovery'],
  context: ['Selection'],
  table_availability: ['Selection'],
  table_selection: ['Table Availability'],
  preview: ['Table Selection'],
  parse: ['Table Selection'],
  export: ['Parse'],
};

/**
 * Get human-readable stage name.
 */
export function getStageDisplayName(stageId: string): string {
  const names: Record<string, string> = {
    discovery: 'Discovery',
    selection: 'Selection',
    context: 'Context',
    table_availability: 'Table Availability',
    table_selection: 'Table Selection',
    preview: 'Preview',
    parse: 'Parse',
    export: 'Export',
  };
  return names[stageId] || stageId;
}

/**
 * Get required stages for a given stage.
 */
export function getRequiredStages(stageId: string): string[] {
  return STAGE_DEPENDENCIES[stageId] || [];
}

export default GatingTooltip;
