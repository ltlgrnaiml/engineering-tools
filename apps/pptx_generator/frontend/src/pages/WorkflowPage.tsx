import { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { Upload, FileText, Database, Settings, Sparkles, CheckCircle } from 'lucide-react'
import { api, configApi } from '../lib/api'
import { FourBarsGate } from '../components/FourBarsGate'
import { EnvironmentProfileSelector } from '../components/EnvironmentProfileSelector'
import { ContextMappingEditor } from '../components/ContextMappingEditor'
import { MetricsMappingEditor } from '../components/MetricsMappingEditor'
import { WorkflowBreadcrumb, StepStatus } from '../components/WorkflowBreadcrumb'
import { ConfirmDialog } from '../components/ConfirmDialog'
import { ConfigEditor } from '../components/ConfigEditor'
import { SlidePreview } from '../components/SlidePreview'
import type { EnvironmentProfile, Project, DRMFile, FourBarsStatus, WorkflowStep, DerivedRequirementsManifest } from '../types'

export function WorkflowPage() {
  const { projectId } = useParams<{ projectId: string }>()
  const [currentStep, setCurrentStep] = useState<WorkflowStep>('template')
  const [loading, setLoading] = useState(false)

  // TOM v2 state
  const [drm, setDrm] = useState<DRMFile | DerivedRequirementsManifest | null>(null)
  const [fourBarsStatus, setFourBarsStatus] = useState<FourBarsStatus | null>(null)
  const [buildingPlan, setBuildingPlan] = useState(false)

  // Rollback state
  const [showConfirmDialog, setShowConfirmDialog] = useState(false)
  const [pendingNavigationStep, setPendingNavigationStep] = useState<WorkflowStep | null>(null)

  const [dataColumns, setDataColumns] = useState<string[] | null>(null);
  const [contextMappings, setContextMappings] = useState<any[]>([]);
  const [metricsMappings, setMetricsMappings] = useState<any[]>([]);

  useEffect(() => {
    if (projectId) {
      loadProject()
    }
  }, [projectId])

  const loadProject = async () => {
    if (!projectId) return

    try {
      const data = await api.getProject(projectId)

      // Restore DRM if template exists (parseTemplateV2 returns cached DRM)
      if (data.template_id) {
        try {
          const parseResult = await api.parseTemplateV2(projectId)
          setDrm(parseResult.drm)
        } catch (error) {
          console.error('Failed to load DRM:', error)
        }
      }

      // Restore data columns if data file exists
      if (data.data_file_id) {
        try {
          const dataFile = await api.getDataFile(projectId)
          setDataColumns(dataFile.column_names || [])
        } catch (error) {
          console.error('Failed to load data columns:', error)
        }
      }

      determineCurrentStep(data)
    } catch (error) {
      console.error('Failed to load project:', error)
    }
  }

  const determineCurrentStep = (proj: Project) => {
    // Determine step based on project status first (for rollback consistency)
    const statusToStep: Record<string, WorkflowStep> = {
      'CREATED': 'template',
      'DRM_EXTRACTED': 'environment',
      'ENVIRONMENT_CONFIGURED': 'data',
      'DATA_UPLOADED': 'context_map',
      'MAPPINGS_CONFIGURED': 'validate',
      'PLAN_FROZEN': 'generate',
    }

    if (proj.status in statusToStep) {
      setCurrentStep(statusToStep[proj.status])
      return
    }

    // Fallback to artifact-based determination for edge cases
    if (!proj.template_id) {
      setCurrentStep('template')
    } else if (!proj.drm_id) {
      setCurrentStep('parse_drm')
    } else if (!proj.environment_profile_id) {
      setCurrentStep('environment')
    } else if (!proj.data_file_id) {
      setCurrentStep('data')
    } else if (!proj.mapping_suggestions_id) {
      setCurrentStep('suggest')
    } else if (!proj.context_mappings_id) {
      setCurrentStep('context_map')
    } else if (!proj.metrics_mappings_id) {
      setCurrentStep('metrics_map')
    } else if (!fourBarsStatus || !fourBarsStatus.is_all_green) {
      setCurrentStep('validate')
    } else if (!proj.plan_artifacts_id) {
      setCurrentStep('plan')
    } else {
      setCurrentStep('generate')
    }
  }

  const handleTemplateUpload = async (file: File) => {
    if (!projectId) return

    setLoading(true)
    try {
      // Upload template
      // const template = await api.uploadTemplate(projectId, file);
      await api.uploadTemplate(projectId, file)

      // Automatically parse and extract DRM
      const parseResult = await api.parseTemplateV2(projectId)
      setDrm(parseResult.drm)

      // Update project and move to next step
      setCurrentStep('environment')

    } catch (error) {
      console.error('Failed to upload and parse template:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleEnvironmentProfileSelect = async (profile: Partial<EnvironmentProfile>) => {
    if (!projectId) return

    setLoading(true)
    try {
      // const envProfile = await api.createEnvironmentProfile(projectId, profile);
      await api.createEnvironmentProfile(projectId, profile)

      setCurrentStep('data')
    } catch (error) {
      console.error('Failed to create environment profile:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleDataUpload = async (file: File) => {
    if (!projectId) return

    setLoading(true)
    try {
      const dataFile = await api.uploadDataFile(projectId, file)

      // Get data columns
      const dataColumns = dataFile.column_names || []

      // Automatically trigger mapping suggestions
      // const suggestions = await api.suggestMappings(projectId);
      await api.suggestMappings(projectId)

      setDataColumns(dataColumns);

      // Auto-load defaults from config
      try {
        const defaults = await api.applyAllDefaults(projectId)
        setContextMappings(defaults.context_mappings)
        setMetricsMappings(defaults.metrics_mappings)
        console.log('Auto-loaded defaults:', defaults)
      } catch (defaultsError) {
        console.warn('Could not auto-load defaults:', defaultsError)
      }

      setCurrentStep('context_map')
    } catch (error) {
      console.error('Failed to upload data and get suggestions:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleBuildPlan = async () => {
    console.log('[DEBUG] handleBuildPlan called')
    if (!projectId) {
      console.log('[DEBUG] No projectId, returning')
      return
    }

    console.log('[DEBUG] Setting buildingPlan to true')
    setBuildingPlan(true)
    try {
      console.log('[DEBUG] Calling api.buildPlan with projectId:', projectId)
      const result = await api.buildPlan(projectId)
      console.log('[DEBUG] api.buildPlan completed successfully:', result)

      console.log('[DEBUG] Setting currentStep to generate')
      setCurrentStep('generate')
      console.log('[DEBUG] currentStep updated to generate')
    } catch (error) {
      console.error('[DEBUG] Failed to build plan:', error)
    } finally {
      console.log('[DEBUG] Setting buildingPlan to false')
      setBuildingPlan(false)
    }
  }

  // Rollback Navigation Logic
  const STEP_ORDER: WorkflowStep[] = [
    'template',
    'parse_drm',
    'environment',
    'data',
    'suggest',
    'context_map',
    'metrics_map',
    'validate',
    'plan',
    'generate',
  ]

  const STEP_LABELS: Record<WorkflowStep, string> = {
    template: 'Template Upload',
    parse_drm: 'Parse Template & Extract DRM',
    environment: 'Environment Profile',
    data: 'Data Upload',
    suggest: 'Auto-Suggest Mappings',
    context_map: 'Context Mappings',
    metrics_map: 'Metrics Mappings',
    validate: 'Four Bars Validation',
    plan: 'Build Execution Plan',
    generate: 'Plan Generation',
  }

  const getInvalidatedSteps = (targetStep: WorkflowStep): WorkflowStep[] => {
    const targetIndex = STEP_ORDER.indexOf(targetStep)
    const currentIndex = STEP_ORDER.indexOf(currentStep)

    if (targetIndex >= currentIndex || targetIndex === -1) {
      return []
    }

    return STEP_ORDER.slice(targetIndex + 1, currentIndex + 1)
  }

  const getStepStatuses = (): Record<WorkflowStep, StepStatus> => {
    const statuses: Record<WorkflowStep, StepStatus> = {
      template: 'locked',
      parse_drm: 'locked',
      environment: 'locked',
      data: 'locked',
      suggest: 'locked',
      context_map: 'locked',
      metrics_map: 'locked',
      validate: 'locked',
      plan: 'locked',
      generate: 'locked',
    }

    const currentIndex = STEP_ORDER.indexOf(currentStep)

    STEP_ORDER.forEach((step, index) => {
      if (index < currentIndex) {
        statuses[step] = 'completed'
      } else if (index === currentIndex) {
        statuses[step] = 'current'
      } else {
        statuses[step] = 'locked'
      }
    })

    // Mark validation as warning if not all green
    if (fourBarsStatus && statuses.validate === 'completed') {
      const allGreen =
        fourBarsStatus.required_context.status === 'green' &&
        fourBarsStatus.required_metrics.status === 'green' &&
        fourBarsStatus.required_data_levels.status === 'green' &&
        fourBarsStatus.required_renderers.status === 'green'

      if (!allGreen) {
        statuses.validate = 'warning'
      }
    }

    return statuses
  }

  const handleStepNavigation = async (targetStep: WorkflowStep) => {
    const invalidatedSteps = getInvalidatedSteps(targetStep)

    if (invalidatedSteps.length === 0) {
      // Already at or before target, just navigate
      setCurrentStep(targetStep)
      return
    }

    // Show confirmation dialog
    setPendingNavigationStep(targetStep)
    setShowConfirmDialog(true)
  }

  const handleConfirmNavigation = async () => {
    if (!pendingNavigationStep || !projectId) return

    console.log('[ROLLBACK] Starting navigation to:', pendingNavigationStep)
    console.log('[ROLLBACK] Current step before:', currentStep)

    const invalidatedSteps = getInvalidatedSteps(pendingNavigationStep)
    console.log('[ROLLBACK] Will clear steps:', invalidatedSteps)

    setLoading(true)

    // Navigate to target step IMMEDIATELY to prevent UI from being stuck
    setCurrentStep(pendingNavigationStep)
    console.log('[ROLLBACK] Set currentStep to:', pendingNavigationStep)

    try {
      // Clear frontend state ONLY for invalidated steps (not the target step)
      if (invalidatedSteps.includes('generate')) {
      }
      if (invalidatedSteps.includes('validate')) {
        setFourBarsStatus(null)
      }
      if (invalidatedSteps.includes('metrics_map')) {
      }
      if (invalidatedSteps.includes('context_map')) {
      }
      if (invalidatedSteps.includes('data')) {
      }
      if (invalidatedSteps.includes('environment')) {
      }
      if (invalidatedSteps.includes('template')) {
        setDrm(null)
      }

      // Call backend to clear stored state
      const stepNameMap: Record<WorkflowStep, string> = {
        template: 'template',
        parse_drm: 'template',
        environment: 'environment',
        data: 'data',
        suggest: 'data',
        context_map: 'mappings',
        metrics_map: 'mappings',
        validate: 'validation',
        plan: 'validation',
        generate: 'validation',
      }

      await api.clearProjectState(projectId, stepNameMap[pendingNavigationStep])
      console.log('[ROLLBACK] Backend state cleared')

      // Reload project data WITHOUT calling determineCurrentStep
      // Removed or commented out unused updatedProject variables
      // const updatedProject = await api.getProject(projectId)
      console.log('[ROLLBACK] Project reloaded')

      // If rolling back to validate step, re-run validation
      if (pendingNavigationStep === 'validate') {
        try {
          const status = await api.getFourBarsStatus(projectId)
          setFourBarsStatus(status)
          console.log('[ROLLBACK] Validation re-run complete')
        } catch (error) {
          console.error('[ROLLBACK] Failed to re-run validation:', error)
        }
      }

      console.log('[ROLLBACK] Navigation complete')
    } catch (error) {
      console.error('[ROLLBACK] Failed to navigate backward:', error)
    } finally {
      setLoading(false)
      setShowConfirmDialog(false)
      setPendingNavigationStep(null)
    }
  }

  const handleCancelNavigation = () => {
    setShowConfirmDialog(false)
    setPendingNavigationStep(null)
  }

  return (
    <div>
      {/* Workflow Breadcrumb Navigation */}
      <WorkflowBreadcrumb
        currentStep={currentStep}
        stepStatuses={getStepStatuses()}
        onStepClick={handleStepNavigation}
      />

      {/* Confirmation Dialog for Backward Navigation */}
      <ConfirmDialog
        isOpen={showConfirmDialog}
        title={`Go back to ${pendingNavigationStep ? STEP_LABELS[pendingNavigationStep] : ''}?`}
        message="Going back will clear all progress in subsequent steps."
        invalidatedItems={
          pendingNavigationStep
            ? getInvalidatedSteps(pendingNavigationStep).map(step => STEP_LABELS[step])
            : []
        }
        onConfirm={handleConfirmNavigation}
        onCancel={handleCancelNavigation}
        destructive={true}
      />

      <div className="max-w-7xl mx-auto px-6 py-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-8">
          Guided Workflow
        </h1>

      <div className="bg-white rounded-lg shadow p-8">
        {currentStep === 'template' && (
          <div className="space-y-8">
            {/* Config File Selection and Editor */}
            <ConfigEditor
              onConfigSelect={(config: any, filename: string) => {
                console.log('Config selected:', filename, config)
              }}
            />

            {/* Template Upload */}
            <div className="text-center border-t pt-8">
              <Upload className="h-16 w-16 text-blue-600 mx-auto mb-4" />
              <h2 className="text-2xl font-bold text-gray-900 mb-2">
                Upload PowerPoint Template
              </h2>
              <p className="text-gray-600 mb-6">
                Upload a .pptx file with labeled shapes that will be populated with
                your data
              </p>
              <input
                type="file"
                accept=".pptx"
                onChange={(e) => {
                  const file = e.target.files?.[0]
                  if (file) handleTemplateUpload(file)
                }}
                className="hidden"
                id="template-upload"
              />
              <label
                htmlFor="template-upload"
                className="inline-flex items-center px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 cursor-pointer disabled:bg-gray-300"
              >
                {loading ? 'Uploading...' : 'Choose Template File'}
              </label>
            </div>
          </div>
        )}

        {currentStep === 'parse_drm' && (
          <div className="text-center">
            <FileText className="h-16 w-16 text-blue-600 mx-auto mb-4" />
            <h2 className="text-2xl font-bold text-gray-900 mb-2">
              Parsing Template & Extracting DRM
            </h2>
            <p className="text-gray-600 mb-6">
              This step happens automatically when you upload a template
            </p>
            <div className="flex items-center justify-center gap-2">
              <CheckCircle className="h-6 w-6 text-green-600" />
              <span className="text-green-600 font-medium">Complete</span>
            </div>
          </div>
        )}

        {currentStep === 'environment' && (
          <EnvironmentProfileSelector
            onSelect={handleEnvironmentProfileSelect}
            loading={loading}
          />
        )}

        {currentStep === 'data' && (
          <div className="text-center">
            <Database className="h-16 w-16 text-blue-600 mx-auto mb-4" />
            <h2 className="text-2xl font-bold text-gray-900 mb-2">
              Upload Data File
            </h2>
            <p className="text-gray-600 mb-6">
              Upload a CSV or Excel file containing the data for your presentation
            </p>
            <input
              type="file"
              accept=".csv,.xlsx,.xls"
              onChange={(e) => {
                const file = e.target.files?.[0]
                if (file) handleDataUpload(file)
              }}
              className="hidden"
              id="data-upload"
            />
            <label
              htmlFor="data-upload"
              className="inline-flex items-center px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 cursor-pointer disabled:bg-gray-300"
            >
              {loading ? 'Uploading...' : 'Choose Data File'}
            </label>
          </div>
        )}

        {currentStep === 'suggest' && (
          <div className="text-center">
            <Sparkles className="h-16 w-16 text-blue-600 mx-auto mb-4" />
            <h2 className="text-2xl font-bold text-gray-900 mb-2">
              Auto-Suggesting Mappings
            </h2>
            <p className="text-gray-600 mb-6">
              This step happens automatically when you upload data
            </p>
            <div className="flex flex-col items-center justify-center gap-4">
              <div className="flex items-center gap-2">
                <CheckCircle className="h-6 w-6 text-green-600" />
                <span className="text-green-600 font-medium">Suggestions Generated</span>
              </div>
              <button
                onClick={() => setCurrentStep('context_map')}
                className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                Continue to Context Mapping
              </button>
            </div>
          </div>
        )}

        {currentStep === 'context_map' && (
          <div>
            {drm ? (
              <>
                <ContextMappingEditor
                  key={`context-mappings-${contextMappings.length}`}
                  drm={drm as DerivedRequirementsManifest}
                  initialMappings={contextMappings}
                  dataColumns={dataColumns || []}
                  onMappingsChange={(mappings) => {
                    setContextMappings(mappings)
                  }}
                  onSave={async () => {
                    if (!projectId) return
                    setLoading(true)
                    try {
                      await api.saveContextMappings(projectId, contextMappings)
                      setCurrentStep('metrics_map')
                    } catch (error) {
                      console.error('Failed to save context mappings:', error)
                    } finally {
                      setLoading(false)
                    }
                  }}
                  onSaveConfig={async (mappings) => {
                    const filename = prompt('Enter config filename (without .yaml extension):', 'custom_config')
                    if (!filename) return
                    try {
                      const result = await configApi.saveConfigMappings({
                        context_mappings: mappings.map(m => ({
                          context_name: m.context_name,
                          source_type: m.source_type,
                          source_column: m.source_column,
                          regex_pattern: m.regex_pattern,
                          default_value: m.default_value,
                          description: m.description,
                        })),
                        metrics_mappings: metricsMappings.map(m => ({
                          metric_name: m.metric_name,
                          source_column: m.source_column,
                          aggregation_semantics: m.aggregation_semantics,
                          data_type: m.data_type,
                          unit: m.unit,
                        })),
                        filename,
                        overwrite: true,
                      })
                      alert(`Config saved to ${result.filepath}`)
                    } catch (error) {
                      console.error('Failed to save config:', error)
                      alert('Failed to save config. See console for details.')
                    }
                  }}
                  saving={loading}
                />
              </>
            ) : (
              <div className="text-center">
                <Settings className="h-16 w-16 text-blue-600 mx-auto mb-4" />
                <h2 className="text-2xl font-bold text-gray-900 mb-2">
                  Context Mapping Data Missing
                </h2>
                <p className="text-gray-600 mb-6">
                  Required data (DRM or mapping suggestions) was cleared. Please re-upload your data file to continue.
                </p>
                <button
                  onClick={() => setCurrentStep('data')}
                  className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                >
                  Go to Data Upload
                </button>
              </div>
            )}
          </div>
        )}

        {currentStep === 'metrics_map' && (
          <div>
            {drm ? (
              <MetricsMappingEditor
                drm={drm as DerivedRequirementsManifest}
                initialMappings={metricsMappings}
                dataColumns={dataColumns || []}
                onMappingsChange={(mappings) => {
                  setMetricsMappings(mappings)
                }}
                onSave={async () => {
                  if (!projectId) return
                  setLoading(true)
                  try {
                    await api.saveMetricsMappings(projectId, metricsMappings)

                    // Run validation after saving metrics
                    const status = await api.getFourBarsStatus(projectId)
                    setFourBarsStatus(status)

                    setCurrentStep('validate')
                  } catch (error) {
                    console.error('Failed to save metrics mappings:', error)
                  } finally {
                    setLoading(false)
                  }
                }}
                onSaveConfig={async (mappings) => {
                  const filename = prompt('Enter config filename (without .yaml extension):', 'custom_config')
                  if (!filename) return
                  try {
                    const result = await configApi.saveConfigMappings({
                      context_mappings: contextMappings.map(m => ({
                        context_name: m.context_name,
                        source_type: m.source_type,
                        source_column: m.source_column,
                        regex_pattern: m.regex_pattern,
                        default_value: m.default_value,
                        description: m.description,
                      })),
                      metrics_mappings: mappings.map(m => ({
                        metric_name: m.metric_name,
                        source_column: m.source_column,
                        aggregation_semantics: m.aggregation_semantics,
                        data_type: m.data_type,
                        unit: m.unit,
                      })),
                      filename,
                      overwrite: true,
                    })
                    alert(`Config saved to ${result.filepath}`)
                  } catch (error) {
                    console.error('Failed to save config:', error)
                    alert('Failed to save config. See console for details.')
                  }
                }}
                saving={loading}
              />
            ) : (
              <div className="text-center">
                <Settings className="h-16 w-16 text-blue-600 mx-auto mb-4" />
                <h2 className="text-2xl font-bold text-gray-900 mb-2">
                  Metrics Mapping Data Missing
                </h2>
                <p className="text-gray-600 mb-6">
                  Required data (DRM or mapping suggestions) was cleared. Please re-upload your data file to continue.
                </p>
                <button
                  onClick={() => setCurrentStep('data')}
                  className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                >
                  Go to Data Upload
                </button>
              </div>
            )}
          </div>
        )}

        {currentStep === 'validate' && (
          <div className="space-y-8">
            {/* Four Bars Validation */}
            <div>
              {fourBarsStatus ? (
                <FourBarsGate
                  status={fourBarsStatus}
                  onBuildPlan={handleBuildPlan}
                  building={buildingPlan}
                />
              ) : (
                <div className="text-center">
                  <CheckCircle className="h-16 w-16 text-blue-600 mx-auto mb-4" />
                  <h2 className="text-2xl font-bold text-gray-900 mb-2">
                    Re-run Validation
                  </h2>
                  <p className="text-gray-600 mb-6">
                    Validation results were cleared during rollback. Click below to re-run validation.
                  </p>
                  <button
                    onClick={async () => {
                      if (!projectId) return
                      setLoading(true)
                      try {
                        const status = await api.getFourBarsStatus(projectId)
                        setFourBarsStatus(status)
                      } catch (error) {
                        console.error('Failed to re-run validation:', error)
                      } finally {
                        setLoading(false)
                      }
                    }}
                    className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300"
                    disabled={loading}
                  >
                    {loading ? 'Re-running...' : 'Re-run Validation'}
                  </button>
                </div>
              )}
            </div>

            {/* Slide Preview - Below 4-bar validation */}
            {projectId && fourBarsStatus && (
              <div className="border-t pt-8">
                <SlidePreview
                  projectId={projectId}
                  onPreviewLoad={(data) => {
                    console.log('Preview loaded:', data)
                  }}
                />
              </div>
            )}
          </div>
        )}

        {currentStep === 'plan' && (
          <div className="text-center">
            <Settings className="h-16 w-16 text-blue-600 mx-auto mb-4" />
            <h2 className="text-2xl font-bold text-gray-900 mb-2">
              Build Plan
            </h2>
            <p className="text-gray-600 mb-6">
              This step happens automatically after validation
            </p>
            <div className="flex items-center justify-center gap-2">
              <CheckCircle className="h-6 w-6 text-green-600" />
              <span className="text-green-600 font-medium">Plan Built</span>
            </div>
          </div>
        )}

        {currentStep === 'generate' && (
          <div className="text-center">
            <Sparkles className="h-16 w-16 text-blue-600 mx-auto mb-4" />
            <h2 className="text-2xl font-bold text-gray-900 mb-2">
              Generate Presentation
            </h2>
            <p className="text-gray-600 mb-6">
              Your project is ready! Click below to generate your PowerPoint presentation.
            </p>
              <button
                onClick={async () => {
                  if (!projectId) return
                  setLoading(true)
                  try {
                    console.log('[GENERATION] Starting generation for project:', projectId)
                    const generation = await api.generatePresentation(projectId)
                    console.log('[GENERATION] Generation response:', generation)

                    // Download the generated file
                    const blob = await api.downloadPresentation(generation.id)
                    const url = window.URL.createObjectURL(blob)
                    const a = document.createElement('a')
                    a.href = url
                    a.download = generation.output_filename || 'presentation.pptx'
                    document.body.appendChild(a)
                    a.click()
                    window.URL.revokeObjectURL(url)
                    document.body.removeChild(a)

                    alert('Presentation generated successfully!')
                  } catch (error: any) {
                    console.error('[GENERATION] Failed to generate presentation:', error)
                    console.error('[GENERATION] Error response:', error.response?.data)
                    const errorMsg = error.response?.data?.detail || error.message || 'Unknown error'
                    alert(`Failed to generate presentation:\n${errorMsg}`)
                  } finally {
                    setLoading(false)
                  }
                }}
                disabled={loading}
                className={`px-8 py-3 rounded-lg font-semibold transition-colors ${
                  loading
                    ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                    : 'bg-green-600 text-white hover:bg-green-700'
                }`}
              >
                {loading ? 'Generating...' : 'Generate Presentation'}
              </button>
          </div>
        )}
      </div>
      </div>
    </div>
  )
}
