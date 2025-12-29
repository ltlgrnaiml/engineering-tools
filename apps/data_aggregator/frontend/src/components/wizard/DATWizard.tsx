/**
 * DAT Wizard - Horizontal Stepper Component
 *
 * Per ADR-0041: DAT UI Horizontal Wizard Pattern
 * Per SPEC-DAT-0003: 8-stage pipeline mapped to UI
 *
 * Features:
 * - Horizontal stepper with 8 visible stages
 * - Stage state indicators (pending, active, completed, locked, error)
 * - Forward gating - can only advance when current stage complete
 * - Backward navigation unlocks downstream stages
 * - Optional stages (Context, Preview) can be skipped
 * - Responsive design (mobile-friendly)
 */

import { ReactNode } from 'react';
import {
  Check,
  ChevronRight,
  Lock,
  AlertCircle,
  Circle,
} from 'lucide-react';

/**
 * Stage state for UI rendering.
 */
export type StageState = 'pending' | 'active' | 'completed' | 'locked' | 'error' | 'skipped';

/**
 * Stage configuration.
 */
export interface StageConfig {
  /** Unique stage identifier */
  id: string;
  /** Display label */
  label: string;
  /** Short description */
  description?: string;
  /** Whether stage can be skipped */
  optional?: boolean;
  /** Icon component */
  icon?: ReactNode;
}

/**
 * Props for DATWizard component.
 */
export interface DATWizardProps {
  /** List of stage configurations */
  stages: StageConfig[];
  /** Current active stage ID */
  currentStageId: string;
  /** Map of stage ID to state */
  stageStates: Record<string, StageState>;
  /** Callback when user clicks a stage */
  onStageClick?: (stageId: string) => void;
  /** Callback when user clicks next */
  onNext?: () => void;
  /** Callback when user clicks back */
  onBack?: () => void;
  /** Callback when user skips optional stage */
  onSkip?: (stageId: string) => void;
  /** Whether next button is disabled */
  nextDisabled?: boolean;
  /** Whether navigation is loading */
  isLoading?: boolean;
  /** Child content for current stage */
  children?: ReactNode;
}

/**
 * Get icon for stage state.
 */
function StageIcon({ state, index }: { state: StageState; index: number }) {
  const baseClasses = 'w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium transition-all';

  switch (state) {
    case 'completed':
      return (
        <div className={`${baseClasses} bg-emerald-500 text-white`}>
          <Check className="w-4 h-4" />
        </div>
      );
    case 'active':
      return (
        <div className={`${baseClasses} bg-emerald-500 text-white ring-4 ring-emerald-100`}>
          {index + 1}
        </div>
      );
    case 'error':
      return (
        <div className={`${baseClasses} bg-red-500 text-white`}>
          <AlertCircle className="w-4 h-4" />
        </div>
      );
    case 'locked':
      return (
        <div className={`${baseClasses} bg-slate-200 text-slate-400`}>
          <Lock className="w-3 h-3" />
        </div>
      );
    case 'skipped':
      return (
        <div className={`${baseClasses} bg-slate-100 text-slate-400 border-2 border-dashed border-slate-300`}>
          <Circle className="w-3 h-3" />
        </div>
      );
    case 'pending':
    default:
      return (
        <div className={`${baseClasses} bg-slate-100 text-slate-500 border-2 border-slate-300`}>
          {index + 1}
        </div>
      );
  }
}

/**
 * Connector line between stages.
 */
function StageConnector({ completed }: { completed: boolean }) {
  return (
    <div
      className={`
        hidden sm:block flex-1 h-0.5 mx-2
        ${completed ? 'bg-emerald-500' : 'bg-slate-200'}
        transition-colors
      `}
    />
  );
}

/**
 * Individual stage step in the horizontal stepper.
 */
function StageStep({
  stage,
  index,
  state,
  isLast,
  onClick,
}: {
  stage: StageConfig;
  index: number;
  state: StageState;
  isLast: boolean;
  onClick?: () => void;
}) {
  const canClick = state === 'completed' || state === 'active';

  return (
    <>
      <button
        type="button"
        onClick={() => canClick && onClick?.()}
        disabled={!canClick}
        className={`
          flex flex-col items-center gap-2 min-w-0 flex-shrink-0
          ${canClick ? 'cursor-pointer' : 'cursor-not-allowed'}
          group
        `}
        title={stage.description}
      >
        <StageIcon state={state} index={index} />
        <div className="text-center">
          <span
            className={`
              text-xs font-medium block truncate max-w-[80px]
              ${state === 'active' ? 'text-emerald-700' : ''}
              ${state === 'completed' ? 'text-slate-700' : ''}
              ${state === 'locked' || state === 'pending' ? 'text-slate-400' : ''}
              ${state === 'error' ? 'text-red-600' : ''}
              ${state === 'skipped' ? 'text-slate-400' : ''}
            `}
          >
            {stage.label}
          </span>
          {stage.optional && (
            <span className="text-[10px] text-slate-400 block">Optional</span>
          )}
        </div>
      </button>
      {!isLast && <StageConnector completed={state === 'completed'} />}
    </>
  );
}

/**
 * DAT Wizard - Horizontal Stepper Component
 *
 * Displays an 8-stage horizontal wizard with state indicators,
 * forward gating, and backward navigation support.
 *
 * @example
 * ```tsx
 * <DATWizard
 *   stages={stages}
 *   currentStageId="selection"
 *   stageStates={{ selection: 'active', context: 'pending', ... }}
 *   onStageClick={(id) => navigateTo(id)}
 *   onNext={() => advanceStage()}
 * >
 *   <SelectionPanel />
 * </DATWizard>
 * ```
 */
export function DATWizard({
  stages,
  currentStageId,
  stageStates,
  onStageClick,
  onNext,
  onBack,
  onSkip,
  nextDisabled,
  isLoading,
  children,
}: DATWizardProps) {
  const currentIndex = stages.findIndex((s) => s.id === currentStageId);
  const currentStage = stages[currentIndex];
  const isFirstStage = currentIndex === 0;
  const isLastStage = currentIndex === stages.length - 1;
  const hasNext = typeof onNext === 'function';
  const hasSkip = typeof onSkip === 'function';

  return (
    <div className="flex flex-col min-h-full">
      {/* Horizontal Stepper */}
      <nav
        className="
          bg-white border-b border-slate-200 px-4 py-6
          overflow-x-auto
        "
        aria-label="Progress"
      >
        <ol className="flex items-center justify-between max-w-4xl mx-auto">
          {stages.map((stage, index) => (
            <StageStep
              key={stage.id}
              stage={stage}
              index={index}
              state={stageStates[stage.id] || 'pending'}
              isLast={index === stages.length - 1}
              onClick={() => onStageClick?.(stage.id)}
            />
          ))}
        </ol>
      </nav>

      {/* Stage Content */}
      <div className="flex-1 p-6 bg-slate-50">
        <div className="max-w-4xl mx-auto">
          {/* Stage Header */}
          <div className="mb-6">
            <h2 className="text-2xl font-semibold text-slate-900">
              {currentStage?.label}
            </h2>
            {currentStage?.description && (
              <p className="text-slate-600 mt-1">{currentStage.description}</p>
            )}
          </div>

          {/* Stage Content */}
          <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-6">
            {children}
          </div>

          {/* Navigation Buttons */}
          <div className="flex justify-between items-center mt-6">
            <div>
              {!isFirstStage && (
                <button
                  type="button"
                  onClick={onBack}
                  disabled={isLoading}
                  className="
                    px-4 py-2 text-slate-600 hover:text-slate-900
                    hover:bg-slate-100 rounded-lg transition-colors
                    disabled:opacity-50 disabled:cursor-not-allowed
                  "
                >
                  ← Back
                </button>
              )}
            </div>

            <div className="flex gap-3">
              {hasSkip && currentStage?.optional && (
                <button
                  type="button"
                  onClick={() => onSkip?.(currentStageId)}
                  disabled={isLoading}
                  className="
                    px-4 py-2 text-slate-500 hover:text-slate-700
                    border border-slate-300 rounded-lg transition-colors
                    disabled:opacity-50 disabled:cursor-not-allowed
                  "
                >
                  Skip
                </button>
              )}

              {hasNext && !isLastStage && (
                <button
                  type="button"
                  onClick={onNext}
                  disabled={nextDisabled || isLoading}
                  className="
                    px-6 py-2 bg-emerald-500 hover:bg-emerald-600
                    text-white rounded-lg font-medium transition-colors
                    disabled:opacity-50 disabled:cursor-not-allowed
                    flex items-center gap-2
                  "
                >
                  {isLoading ? (
                    <>
                      <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                      Processing...
                    </>
                  ) : (
                    <>
                      Next
                      <ChevronRight className="w-4 h-4" />
                    </>
                  )}
                </button>
              )}

              {hasNext && isLastStage && (
                <button
                  type="button"
                  onClick={onNext}
                  disabled={nextDisabled || isLoading}
                  className="
                    px-6 py-2 bg-emerald-500 hover:bg-emerald-600
                    text-white rounded-lg font-medium transition-colors
                    disabled:opacity-50 disabled:cursor-not-allowed
                  "
                >
                  {isLoading ? 'Exporting...' : 'Complete Export'}
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

/**
 * Default DAT stages configuration.
 * Per ADR-0041: 8-stage pipeline
 */
export const DEFAULT_DAT_STAGES: StageConfig[] = [
  {
    id: 'discovery',
    label: 'Discovery',
    description: 'Upload and discover files for processing',
  },
  {
    id: 'selection',
    label: 'Selection',
    description: 'Select files to include in the aggregation',
  },
  {
    id: 'context',
    label: 'Context',
    description: 'Provide additional context for extraction',
    optional: true,
  },
  {
    id: 'table_availability',
    label: 'Tables',
    description: 'View available tables in selected files',
  },
  {
    id: 'table_selection',
    label: 'Table Select',
    description: 'Choose which tables to extract',
  },
  {
    id: 'preview',
    label: 'Preview',
    description: 'Preview extracted data before parsing',
    optional: true,
  },
  {
    id: 'parse',
    label: 'Parse',
    description: 'Parse and transform the data',
  },
  {
    id: 'export',
    label: 'Export',
    description: 'Export aggregated data to desired format',
  },
];

export default DATWizard;
