import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Plus, Trash2, GripVertical, Play, Save, ArrowLeft, FileSpreadsheet, BarChart3, Presentation } from 'lucide-react'
import { cn } from '@/lib/utils'
import { useCreatePipeline, type PipelineStep } from '@/hooks/usePipelines'

const STEP_TYPES = [
  { value: 'dat:aggregate', label: 'DAT: Aggregate Data', icon: FileSpreadsheet, color: 'bg-emerald-500' },
  { value: 'dat:export', label: 'DAT: Export', icon: FileSpreadsheet, color: 'bg-emerald-500' },
  { value: 'sov:anova', label: 'SOV: ANOVA Analysis', icon: BarChart3, color: 'bg-purple-500' },
  { value: 'sov:variance_components', label: 'SOV: Variance Components', icon: BarChart3, color: 'bg-purple-500' },
  { value: 'pptx:generate', label: 'PPTX: Generate Report', icon: Presentation, color: 'bg-orange-500' },
  { value: 'pptx:render', label: 'PPTX: Render', icon: Presentation, color: 'bg-orange-500' },
]

interface BuilderStep {
  id: string
  stepType: string
  name: string
  inputRefs: string[]
  config: Record<string, unknown>
}

export function PipelineBuilderPage() {
  const navigate = useNavigate()
  const createPipeline = useCreatePipeline()
  
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [steps, setSteps] = useState<BuilderStep[]>([])
  const [error, setError] = useState<string | null>(null)

  const addStep = (stepType: string) => {
    const stepDef = STEP_TYPES.find(s => s.value === stepType)
    const newStep: BuilderStep = {
      id: `step_${Date.now()}`,
      stepType,
      name: stepDef?.label || stepType,
      inputRefs: [],
      config: {},
    }
    setSteps([...steps, newStep])
  }

  const removeStep = (id: string) => {
    setSteps(steps.filter(s => s.id !== id))
  }

  const updateStepInput = (id: string, inputRef: string) => {
    setSteps(steps.map(s => 
      s.id === id ? { ...s, inputRefs: inputRef ? [inputRef] : [] } : s
    ))
  }

  const handleSave = async (autoExecute: boolean) => {
    if (!name.trim()) {
      setError('Pipeline name is required')
      return
    }
    if (steps.length === 0) {
      setError('At least one step is required')
      return
    }

    setError(null)

    try {
      const pipelineSteps: Omit<PipelineStep, 'state' | 'output_dataset_id'>[] = steps.map((step, index) => ({
        step_index: index,
        step_type: step.stepType,
        name: step.name,
        input_dataset_ids: step.inputRefs,
        config: step.config,
      }))

      await createPipeline.mutateAsync({
        name: name.trim(),
        description: description.trim() || undefined,
        steps: pipelineSteps,
        auto_execute: autoExecute,
      })

      navigate('/pipelines')
    } catch (err) {
      setError('Failed to create pipeline')
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <button
          onClick={() => navigate('/pipelines')}
          className="p-2 hover:bg-slate-100 rounded-lg transition-colors"
        >
          <ArrowLeft className="w-5 h-5 text-slate-500" />
        </button>
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Create Pipeline</h1>
          <p className="text-sm text-slate-500">Chain multiple tools together into an automated workflow</p>
        </div>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
          {error}
        </div>
      )}

      {/* Pipeline Info */}
      <div className="bg-white border border-slate-200 rounded-lg p-6 space-y-4">
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">
            Pipeline Name *
          </label>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="e.g., Full Analysis Report"
            className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">
            Description
          </label>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Optional description of what this pipeline does..."
            rows={2}
            className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
          />
        </div>
      </div>

      {/* Steps */}
      <div className="bg-white border border-slate-200 rounded-lg p-6">
        <h2 className="text-lg font-semibold text-slate-900 mb-4">Pipeline Steps</h2>
        
        {steps.length === 0 ? (
          <div className="text-center py-8 text-slate-500">
            <p className="mb-4">No steps yet. Add steps to build your pipeline.</p>
          </div>
        ) : (
          <div className="space-y-3 mb-6">
            {steps.map((step, index) => {
              const stepDef = STEP_TYPES.find(s => s.value === step.stepType)
              const Icon = stepDef?.icon || FileSpreadsheet
              return (
                <div
                  key={step.id}
                  className="flex items-center gap-3 p-4 bg-slate-50 rounded-lg border border-slate-200"
                >
                  <GripVertical className="w-4 h-4 text-slate-400 cursor-grab" />
                  <div className="w-8 h-8 flex items-center justify-center bg-slate-200 rounded-full text-sm font-medium text-slate-600">
                    {index + 1}
                  </div>
                  <div className={cn('w-8 h-8 rounded-lg flex items-center justify-center', stepDef?.color || 'bg-slate-500')}>
                    <Icon className="w-4 h-4 text-white" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="font-medium text-slate-900">{step.name}</div>
                    <div className="text-xs text-slate-500">{step.stepType}</div>
                  </div>
                  {index > 0 && (
                    <select
                      value={step.inputRefs[0] || ''}
                      onChange={(e) => updateStepInput(step.id, e.target.value)}
                      className="px-3 py-1.5 text-sm border border-slate-300 rounded-md bg-white"
                    >
                      <option value="">No input</option>
                      <option value={`$step_${index - 1}_output`}>← Step {index} output</option>
                      {index > 1 && (
                        <option value={`$step_0_output`}>← Step 1 output</option>
                      )}
                    </select>
                  )}
                  <button
                    onClick={() => removeStep(step.id)}
                    className="p-2 hover:bg-red-100 rounded-lg transition-colors text-slate-400 hover:text-red-600"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              )
            })}
          </div>
        )}

        {/* Add Step Buttons */}
        <div className="border-t border-slate-200 pt-4">
          <p className="text-sm font-medium text-slate-700 mb-3">Add Step</p>
          <div className="flex flex-wrap gap-2">
            {STEP_TYPES.map((stepType) => (
              <button
                key={stepType.value}
                onClick={() => addStep(stepType.value)}
                className="flex items-center gap-2 px-3 py-2 text-sm font-medium text-slate-600 bg-slate-50 hover:bg-slate-100 rounded-lg border border-slate-200 transition-colors"
              >
                <Plus className="w-4 h-4" />
                {stepType.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Actions */}
      <div className="flex items-center justify-between bg-white border border-slate-200 rounded-lg p-4">
        <button
          onClick={() => navigate('/pipelines')}
          className="px-4 py-2 text-sm font-medium text-slate-600 hover:text-slate-900 transition-colors"
        >
          Cancel
        </button>
        <div className="flex items-center gap-3">
          <button
            onClick={() => handleSave(false)}
            disabled={createPipeline.isPending}
            className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-slate-700 bg-slate-100 hover:bg-slate-200 rounded-lg transition-colors disabled:opacity-50"
          >
            <Save className="w-4 h-4" />
            Save Draft
          </button>
          <button
            onClick={() => handleSave(true)}
            disabled={createPipeline.isPending}
            className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 rounded-lg transition-colors disabled:opacity-50"
          >
            <Play className="w-4 h-4" />
            Save & Execute
          </button>
        </div>
      </div>
    </div>
  )
}
