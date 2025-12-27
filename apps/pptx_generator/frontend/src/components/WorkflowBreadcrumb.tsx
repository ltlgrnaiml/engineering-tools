import { CheckCircle, Play, Lock } from 'lucide-react'
import type { WorkflowStep } from '../types'

export type StepStatus = 'locked' | 'available' | 'current' | 'completed' | 'warning'

interface WorkflowStepConfig {
  id: WorkflowStep
  label: string
  description: string
}

interface WorkflowBreadcrumbProps {
  currentStep: WorkflowStep
  stepStatuses: Record<WorkflowStep, StepStatus>
  onStepClick: (step: WorkflowStep) => void
}

const WORKFLOW_STEPS: WorkflowStepConfig[] = [
  { id: 'template', label: 'Template', description: 'Upload PowerPoint template' },
  { id: 'environment', label: 'Environment', description: 'Configure data source' },
  { id: 'data', label: 'Data', description: 'Upload data file' },
  { id: 'context_map', label: 'Context Mapping', description: 'Map context dimensions' },
  { id: 'metrics_map', label: 'Metrics Mapping', description: 'Map metric columns' },
  { id: 'validate', label: 'Validation', description: 'Four Bars validation' },
  { id: 'generate', label: 'Generate', description: 'Build execution plan' },
]

export function WorkflowBreadcrumb({ currentStep, stepStatuses, onStepClick }: WorkflowBreadcrumbProps) {
  const getStepIcon = (status: StepStatus, step: WorkflowStep) => {
    const isActive = step === currentStep;
    const icon = status === 'completed' ? <CheckCircle className="h-5 w-5 text-green-500" /> : (status === 'current' || isActive) ? <Play className="h-5 w-5 text-blue-500" /> : <Lock className="h-5 w-5 text-gray-400" />;
    return icon;
  }

  const getStepClasses = (status: StepStatus, step: WorkflowStep) => {
    const isActive = step === currentStep;
    const baseClasses = 'flex items-center gap-3 px-4 py-3 rounded-lg transition-all'

    if (status === 'current' || isActive) {
      return `${baseClasses} bg-blue-50 border-2 border-blue-500`
    }
    if (status === 'completed') {
      return `${baseClasses} bg-green-50 hover:bg-green-100 cursor-pointer border border-green-300`
    }
    if (status === 'warning') {
      return `${baseClasses} bg-yellow-50 hover:bg-yellow-100 cursor-pointer border border-yellow-300`
    }
    if (status === 'available') {
      return `${baseClasses} bg-gray-50 hover:bg-gray-100 cursor-pointer border border-gray-300`
    }
    return `${baseClasses} bg-gray-50 border border-gray-200 opacity-60 cursor-not-allowed`
  }

  const handleStepClick = (stepId: WorkflowStep, status: StepStatus) => {
    status !== 'locked' && onStepClick(stepId)
  }

  return (
    <div className="bg-white border-b border-gray-200 px-6 py-4">
      <div className="max-w-7xl mx-auto">
        <h2 className="text-sm font-semibold text-gray-700 mb-4">Workflow Progress</h2>
        <div className="grid grid-cols-1 md:grid-cols-7 gap-2">
          {WORKFLOW_STEPS.map((step, index) => {
            const status = stepStatuses[step.id] || 'locked'

            return (
              <div key={step.id} className="relative">
                <div
                  className={getStepClasses(status, step.id)}
                  onClick={() => handleStepClick(step.id, status)}
                  title={step.description}
                >
                  <div className="flex-shrink-0">
                    {getStepIcon(status, step.id)}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className={`text-sm font-medium truncate ${
                      status === 'locked' ? 'text-gray-400' :
                      status === 'current' || step.id === currentStep ? 'text-blue-900' :
                      status === 'completed' ? 'text-green-900' :
                      status === 'warning' ? 'text-yellow-900' :
                      'text-gray-700'
                    }`}>
                      {step.label}
                    </div>
                    <div className="text-xs text-gray-500 truncate hidden md:block">
                      {status === 'locked' ? 'Locked' :
                       status === 'current' || step.id === currentStep ? 'In Progress' :
                       status === 'completed' ? 'Complete' :
                       status === 'warning' ? 'Issues Found' :
                       'Available'}
                    </div>
                  </div>
                </div>

                {index < WORKFLOW_STEPS.length - 1 && (
                  <div className="hidden md:block absolute top-1/2 -right-1 transform -translate-y-1/2 z-10">
                    <div className="w-2 h-2 bg-gray-300 rounded-full" />
                  </div>
                )}
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
