import { useState, useEffect } from 'react'
import { Eye, ChevronLeft, ChevronRight, Table, Type, BarChart3, Image, AlertCircle, CheckCircle, RefreshCw } from 'lucide-react'
import { previewApi } from '../lib/api'

interface ShapeInfo {
  name: string
  type: string
  left: number
  top: number
  width: number
  height: number
  has_text?: boolean
  text_preview?: string
  has_table?: boolean
  table_rows?: number
  table_cols?: number
  has_chart?: boolean
}

// Parse shape name to extract renderer info and describe the asset
function parseShapeName(name: string): { renderer: string; metrics: string[]; filters: string[]; description: string } {
  // Format: <renderer>:<data>[@<filter>][|<options>]
  // Examples: "contour:CD@left", "table:CD,LWR,LCDU@both", "kpi:CD|agg=mean"
  
  const result = {
    renderer: 'unknown',
    metrics: [] as string[],
    filters: [] as string[],
    description: name,
  }

  // Try to parse the shape name
  const colonIndex = name.indexOf(':')
  if (colonIndex === -1) {
    return result
  }

  result.renderer = name.slice(0, colonIndex).toLowerCase()
  let remainder = name.slice(colonIndex + 1)

  // Extract options (after |)
  const pipeIndex = remainder.indexOf('|')
  let options = ''
  if (pipeIndex !== -1) {
    options = remainder.slice(pipeIndex + 1)
    remainder = remainder.slice(0, pipeIndex)
  }

  // Extract filters (after @)
  const atIndex = remainder.indexOf('@')
  if (atIndex !== -1) {
    const filterStr = remainder.slice(atIndex + 1)
    result.filters = filterStr.split(',').map(f => f.trim())
    remainder = remainder.slice(0, atIndex)
  }

  // Extract metrics (comma-separated)
  if (remainder) {
    result.metrics = remainder.split(',').map(m => m.trim())
  }

  // Build human-readable description
  const rendererDescriptions: Record<string, string> = {
    'contour': 'Contour Plot',
    'box': 'Box Plot',
    'scatter': 'Scatter Plot',
    'line': 'Line Chart',
    'bar': 'Bar Chart',
    'hist': 'Histogram',
    'heatmap': 'Heat Map',
    'stacked': 'Stacked Chart',
    'table': 'Data Table',
    'text': 'Text Block',
    'kpi': 'KPI Value',
    'sparkline': 'Sparkline',
    'image': 'Image',
    'inert': 'Static Content',
    'link': 'Hyperlink',
  }

  const rendererName = rendererDescriptions[result.renderer] || result.renderer
  const metricsStr = result.metrics.length > 0 ? result.metrics.join(', ') : 'data'
  const filtersStr = result.filters.length > 0 ? ` (${result.filters.join(', ')})` : ''
  
  result.description = `${rendererName}: ${metricsStr}${filtersStr}`
  
  if (options) {
    result.description += ` [${options}]`
  }

  return result
}

interface SlidePreviewData {
  project_id: string
  slide_index: number
  total_slides: number
  slide_width: number
  slide_height: number
  shapes_count: number
  shapes: ShapeInfo[]
  data_preview?: {
    filename: string
    row_count: number
    columns: string[]
  }
  preview_available: boolean
}

interface GenerationSummary {
  project_id: string
  project_name: string
  status: string
  ready_to_generate: boolean
  components: {
    template: {
      filename: string
      slides_count: number
      shapes_per_slide: number[]
    } | null
    data: {
      filename: string
      row_count: number
      column_count: number
    } | null
    mappings: {
      context_configured: boolean
      metrics_configured: boolean
    } | null
  }
  warnings: string[]
}

interface SlidePreviewProps {
  projectId: string
  onPreviewLoad?: (data: SlidePreviewData) => void
}

export function SlidePreview({ projectId, onPreviewLoad }: SlidePreviewProps) {
  const [previewData, setPreviewData] = useState<SlidePreviewData | null>(null)
  const [summary, setSummary] = useState<GenerationSummary | null>(null)
  const [currentSlide, setCurrentSlide] = useState(0)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [selectedShape, setSelectedShape] = useState<ShapeInfo | null>(null)

  useEffect(() => {
    if (projectId) {
      loadPreview()
      loadSummary()
    }
  }, [projectId])

  useEffect(() => {
    if (projectId && previewData) {
      loadSlidePreview(currentSlide)
    }
  }, [currentSlide])

  const loadPreview = async () => {
    await loadSlidePreview(0)
  }

  const loadSlidePreview = async (slideIndex: number) => {
    setLoading(true)
    setError(null)
    try {
      const data = await previewApi.getSlidePreview(projectId, slideIndex)
      setPreviewData(data)
      onPreviewLoad?.(data)
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to load preview')
      console.error('Failed to load preview:', err)
    } finally {
      setLoading(false)
    }
  }

  const loadSummary = async () => {
    try {
      const data = await previewApi.getGenerationSummary(projectId)
      setSummary(data)
    } catch (err) {
      console.error('Failed to load summary:', err)
    }
  }

  const getShapeIcon = (shape: ShapeInfo) => {
    if (shape.has_table) return <Table className="h-4 w-4 text-blue-500" />
    if (shape.has_chart) return <BarChart3 className="h-4 w-4 text-green-500" />
    if (shape.has_text) return <Type className="h-4 w-4 text-purple-500" />
    if (shape.type === 'PICTURE') return <Image className="h-4 w-4 text-orange-500" />
    return <div className="h-4 w-4 bg-gray-300 rounded" />
  }

  const getShapeTypeLabel = (shape: ShapeInfo) => {
    if (shape.has_table) return `Table (${shape.table_rows}x${shape.table_cols})`
    if (shape.has_chart) return 'Chart'
    if (shape.has_text) return 'Text'
    return shape.type
  }

  // Calculate relative positions for the visual preview
  const getShapeStyle = (shape: ShapeInfo) => {
    if (!previewData) return {}
    
    // EMUs to percentage conversion
    const slideW = previewData.slide_width || 9144000 // Default 10 inches
    const slideH = previewData.slide_height || 6858000 // Default 7.5 inches
    
    return {
      left: `${(shape.left / slideW) * 100}%`,
      top: `${(shape.top / slideH) * 100}%`,
      width: `${(shape.width / slideW) * 100}%`,
      height: `${(shape.height / slideH) * 100}%`,
    }
  }

  return (
    <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
      {/* Header */}
      <div className="bg-gray-50 border-b border-gray-200 px-4 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Eye className="h-5 w-5 text-blue-600" />
            <h3 className="text-lg font-semibold text-gray-900">Slide Preview</h3>
          </div>
          <button
            onClick={loadPreview}
            disabled={loading}
            className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg"
            title="Refresh preview"
          >
            <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {error && (
        <div className="p-4 bg-red-50 border-b border-red-200 text-red-700 text-sm">
          {error}
        </div>
      )}

      {/* Generation Summary */}
      {summary && (
        <div className="p-4 border-b border-gray-200 bg-gray-50">
          <div className="flex items-center gap-2 mb-3">
            {summary.ready_to_generate ? (
              <CheckCircle className="h-5 w-5 text-green-500" />
            ) : (
              <AlertCircle className="h-5 w-5 text-yellow-500" />
            )}
            <span className={`font-medium ${summary.ready_to_generate ? 'text-green-700' : 'text-yellow-700'}`}>
              {summary.ready_to_generate ? 'Ready to Generate' : 'Not Ready - Check Warnings'}
            </span>
          </div>

          <div className="grid grid-cols-3 gap-4 text-sm">
            {/* Template info */}
            <div className="bg-white p-3 rounded-lg border border-gray-200">
              <div className="font-medium text-gray-700 mb-1">Template</div>
              {summary.components.template ? (
                <>
                  <div className="text-gray-600 truncate">{summary.components.template.filename}</div>
                  <div className="text-gray-500">{summary.components.template.slides_count} slides</div>
                </>
              ) : (
                <div className="text-red-500">Not uploaded</div>
              )}
            </div>

            {/* Data info */}
            <div className="bg-white p-3 rounded-lg border border-gray-200">
              <div className="font-medium text-gray-700 mb-1">Data</div>
              {summary.components.data ? (
                <>
                  <div className="text-gray-600 truncate">{summary.components.data.filename}</div>
                  <div className="text-gray-500">{summary.components.data.row_count} rows, {summary.components.data.column_count} cols</div>
                </>
              ) : (
                <div className="text-red-500">Not uploaded</div>
              )}
            </div>

            {/* Mappings info */}
            <div className="bg-white p-3 rounded-lg border border-gray-200">
              <div className="font-medium text-gray-700 mb-1">Mappings</div>
              {summary.components.mappings ? (
                <>
                  <div className={summary.components.mappings.context_configured ? 'text-green-600' : 'text-red-500'}>
                    Context: {summary.components.mappings.context_configured ? 'Configured' : 'Missing'}
                  </div>
                  <div className={summary.components.mappings.metrics_configured ? 'text-green-600' : 'text-red-500'}>
                    Metrics: {summary.components.mappings.metrics_configured ? 'Configured' : 'Missing'}
                  </div>
                </>
              ) : (
                <div className="text-red-500">Not configured</div>
              )}
            </div>
          </div>

          {summary.warnings.length > 0 && (
            <div className="mt-3 p-2 bg-yellow-50 border border-yellow-200 rounded-lg">
              <div className="text-sm text-yellow-800 font-medium mb-1">Warnings:</div>
              {summary.warnings.map((warning, idx) => (
                <div key={idx} className="text-sm text-yellow-700">• {warning}</div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Slide navigation */}
      {previewData && previewData.total_slides > 1 && (
        <div className="flex items-center justify-center gap-4 p-3 border-b border-gray-200">
          <button
            onClick={() => setCurrentSlide(Math.max(0, currentSlide - 1))}
            disabled={currentSlide === 0 || loading}
            className="p-2 hover:bg-gray-100 rounded-lg disabled:opacity-50"
          >
            <ChevronLeft className="h-5 w-5" />
          </button>
          <span className="text-sm text-gray-600">
            Slide {currentSlide + 1} of {previewData.total_slides}
          </span>
          <button
            onClick={() => setCurrentSlide(Math.min(previewData.total_slides - 1, currentSlide + 1))}
            disabled={currentSlide === previewData.total_slides - 1 || loading}
            className="p-2 hover:bg-gray-100 rounded-lg disabled:opacity-50"
          >
            <ChevronRight className="h-5 w-5" />
          </button>
        </div>
      )}

      {/* Visual slide preview */}
      {previewData && (
        <div className="p-4">
          <div 
            className="relative bg-white border-2 border-gray-300 rounded-lg shadow-inner mx-auto"
            style={{ 
              aspectRatio: '4 / 3',
              maxWidth: '600px',
            }}
          >
            {/* Render shapes as positioned boxes */}
            {previewData.shapes.map((shape, idx) => (
              <div
                key={idx}
                className={`absolute border rounded cursor-pointer transition-all ${
                  selectedShape?.name === shape.name 
                    ? 'border-blue-500 bg-blue-100 z-10' 
                    : 'border-gray-300 bg-gray-50 hover:border-blue-300 hover:bg-blue-50'
                }`}
                style={getShapeStyle(shape)}
                onClick={() => setSelectedShape(selectedShape?.name === shape.name ? null : shape)}
                title={shape.name}
              >
                <div className="absolute inset-0 flex items-center justify-center text-xs text-gray-500 overflow-hidden p-1">
                  {shape.has_table && <Table className="h-6 w-6 text-blue-400" />}
                  {shape.has_chart && <BarChart3 className="h-6 w-6 text-green-400" />}
                  {!shape.has_table && !shape.has_chart && shape.has_text && (
                    <span className="truncate">{shape.text_preview?.slice(0, 20) || 'Text'}</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Shape list with asset descriptions */}
      {previewData && (
        <div className="border-t border-gray-200">
          <div className="p-3 bg-gray-50 border-b border-gray-200 sticky top-0">
            <span className="text-sm font-medium text-gray-700">
              Output Preview: {previewData.shapes_count} Shapes
            </span>
          </div>
          <div className="divide-y divide-gray-100 max-h-80 overflow-y-auto">
            {previewData.shapes.map((shape, idx) => {
              const parsed = parseShapeName(shape.name)
              const isRenderable = parsed.renderer !== 'unknown'
              
              return (
                <div
                  key={idx}
                  className={`p-3 cursor-pointer transition-colors ${
                    selectedShape?.name === shape.name ? 'bg-blue-50' : 'hover:bg-gray-50'
                  }`}
                  onClick={() => setSelectedShape(selectedShape?.name === shape.name ? null : shape)}
                >
                  <div className="flex items-start gap-3">
                    {getShapeIcon(shape)}
                    <div className="flex-1 min-w-0">
                      {/* Shape name */}
                      <div className="text-sm font-medium text-gray-900 truncate">
                        {shape.name}
                      </div>
                      
                      {/* Asset description */}
                      {isRenderable ? (
                        <div className="mt-1 p-2 bg-green-50 border border-green-200 rounded text-xs">
                          <div className="font-medium text-green-800">
                            Will render: {parsed.description}
                          </div>
                          {parsed.metrics.length > 0 && (
                            <div className="text-green-700 mt-0.5">
                              Metrics: {parsed.metrics.join(', ')}
                            </div>
                          )}
                          {parsed.filters.length > 0 && (
                            <div className="text-green-700 mt-0.5">
                              Filters: {parsed.filters.join(', ')}
                            </div>
                          )}
                        </div>
                      ) : (
                        <div className="mt-1 text-xs text-gray-500">
                          {getShapeTypeLabel(shape)}
                          {shape.has_text && shape.text_preview && (
                            <span className="ml-1">- "{shape.text_preview}"</span>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* Loading state */}
      {loading && !previewData && (
        <div className="p-8 text-center text-gray-500">
          <RefreshCw className="h-8 w-8 animate-spin mx-auto mb-2" />
          <p>Loading preview...</p>
        </div>
      )}
    </div>
  )
}
