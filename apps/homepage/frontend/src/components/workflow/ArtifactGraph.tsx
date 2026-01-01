import { useRef, useCallback, useState, useEffect, useMemo } from 'react'
import ForceGraph2D from 'react-force-graph-2d'
import ForceGraph3D from 'react-force-graph-3d'
import { Layers, Box, Settings, X, RotateCcw } from 'lucide-react'
import { cn } from '@/lib/utils'
import { useArtifactGraph } from '@/hooks/useWorkflowApi'
import type { ArtifactType, GraphNode, GraphEdge } from './types'

// Tier colors per DISC-001
const TYPE_COLORS: Record<ArtifactType, string> = {
  discussion: '#3B82F6', // blue (T0)
  adr: '#22C55E',        // green (T1)
  spec: '#EAB308',       // yellow (T2)
  contract: '#A855F7',   // purple (T3)
  plan: '#EF4444',       // red (T4)
}

const TYPE_LABELS: Record<ArtifactType, string> = {
  discussion: 'Discussion',
  adr: 'ADR',
  spec: 'SPEC',
  contract: 'Contract',
  plan: 'Plan',
}

interface ArtifactGraphProps {
  onNodeClick?: (nodeId: string, type: ArtifactType) => void
  selectedNodeId?: string
  className?: string
}

interface ExtendedGraphNode extends GraphNode {
  x?: number
  y?: number
  z?: number
  fx?: number  // Fixed x position (for pinning after drag)
  fy?: number  // Fixed y position
  fz?: number  // Fixed z position (3D only)
  __highlighted?: boolean
}

interface ExtendedGraphEdge extends GraphEdge {
  __highlighted?: boolean
}

export function ArtifactGraph({ onNodeClick, selectedNodeId, className }: ArtifactGraphProps) {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const graphRef = useRef<any>(null)
  const outerRef = useRef<HTMLDivElement>(null)  // Flex container (for ResizeObserver)
  const containerRef = useRef<HTMLDivElement>(null)  // Inner absolute container (for cursor)
  const initialZoomDone = useRef(false)
  const { data: graphData, loading } = useArtifactGraph()
  const [dimensions, setDimensions] = useState({ width: 0, height: 0 })
  const [is3D, setIs3D] = useState(true) // Default to 3D for better visualization
  const [settingsOpen, setSettingsOpen] = useState(false)
  
  // Graph settings with defaults
  const [settings, setSettings] = useState({
    focusDistance: 400,      // Camera distance on node focus (100-800)
    chargeStrength: -100,    // Node repulsion (-300 to -30)
    linkDistance: 60,        // Target link length (20-150)
    centerStrength: 0.1,     // Pull to center (0-1)
    linkCurvature: 0.15,     // Link curve amount (0-0.5)
    showParticles: true,     // Animated particles on links
    particleSpeed: 0.005,    // Particle animation speed
    shortLabels: false,      // Use short labels in tooltips
    dagMode: null as string | null, // Hierarchical layout mode
  })
  
  const defaultSettings = {
    focusDistance: 400,
    chargeStrength: -100,
    linkDistance: 60,
    centerStrength: 0.1,
    linkCurvature: 0.15,
    showParticles: true,
    particleSpeed: 0.005,
    shortLabels: false,
    dagMode: null as string | null,
  }

  // Reset zoom flag when switching modes
  useEffect(() => {
    initialZoomDone.current = false
  }, [is3D])

  // Keyboard shortcuts: 2/3 to toggle
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) return
      if (e.key === '2') setIs3D(false)
      if (e.key === '3') setIs3D(true)
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [])


  // Track container dimensions - watch OUTER flex container for resize events
  useEffect(() => {
    const outer = outerRef.current
    if (!outer) return

    const updateDimensions = () => {
      const rect = outer.getBoundingClientRect()
      if (rect.width > 0 && rect.height > 0) {
        const newWidth = Math.floor(rect.width)
        const newHeight = Math.floor(rect.height)
        setDimensions(prev => {
          if (prev.width === newWidth && prev.height === newHeight) return prev
          return { width: newWidth, height: newHeight }
        })
      }
    }

    // CRITICAL: Delay initial measurement to allow flex layout to settle
    // Without this delay, we measure before the container has its final size
    // Using 100ms for more reliability across different render timings
    const initialTimeout = setTimeout(updateDimensions, 100)
    
    const resizeObserver = new ResizeObserver(updateDimensions)
    resizeObserver.observe(outer)

    return () => {
      clearTimeout(initialTimeout)
      resizeObserver.disconnect()
    }
  }, [])

  // Build adjacency map for highlighting
  const adjacencyMap = useMemo(() => {
    if (!graphData) return new Map<string, Set<string>>()
    
    const map = new Map<string, Set<string>>()
    graphData.edges.forEach((edge) => {
      const sourceId = typeof edge.source === 'object' ? (edge.source as ExtendedGraphNode).id : edge.source
      const targetId = typeof edge.target === 'object' ? (edge.target as ExtendedGraphNode).id : edge.target
      
      if (!map.has(sourceId)) map.set(sourceId, new Set())
      if (!map.has(targetId)) map.set(targetId, new Set())
      
      map.get(sourceId)!.add(targetId)
      map.get(targetId)!.add(sourceId)
    })
    return map
  }, [graphData])

  // Focus camera on selected node - different API for 2D vs 3D
  useEffect(() => {
    if (!selectedNodeId || !graphRef.current || !graphData) return

    const node = graphData.nodes.find(n => n.id === selectedNodeId) as ExtendedGraphNode | undefined
    if (node && node.x !== undefined && node.y !== undefined) {
      if (is3D) {
        // 3D: Use cameraPosition for orbital camera movement
        const distance = settings.focusDistance
        const distRatio = 1 + distance / Math.hypot(node.x, node.y, node.z || 0)
        graphRef.current.cameraPosition(
          { x: node.x * distRatio, y: node.y * distRatio, z: (node.z || 0) * distRatio },
          node,
          1000
        )
      } else {
        // 2D: Use centerAt + zoom (1.5 = gentler zoom, was 2)
        graphRef.current.centerAt(node.x, node.y, 500)
        graphRef.current.zoom(1.5, 500)
      }
    }
  }, [selectedNodeId, graphData, is3D, settings.focusDistance])

  const handleNodeClick = useCallback((node: ExtendedGraphNode) => {
    onNodeClick?.(node.id, node.type)
    
    // Focus camera on clicked node - API differs between 2D and 3D
    if (graphRef.current && node.x !== undefined && node.y !== undefined) {
      if (is3D) {
        // 3D: Use cameraPosition with user-configurable distance
        const distance = settings.focusDistance
        const distRatio = 1 + distance / Math.hypot(node.x, node.y, node.z || 0)
        graphRef.current.cameraPosition(
          { x: node.x * distRatio, y: node.y * distRatio, z: (node.z || 0) * distRatio },
          node,
          1000
        )
      } else {
        // 2D: Use centerAt + zoom (1.5 = gentler zoom)
        graphRef.current.centerAt(node.x, node.y, 500)
        graphRef.current.zoom(1.5, 500)
      }
    }
  }, [onNodeClick, is3D, settings.focusDistance])

  // NO setState on hover - it causes re-renders that destabilize the simulation
  // The built-in nodeLabel prop handles tooltips without React re-renders
  const handleNodeHover = useCallback((node: ExtendedGraphNode | null) => {
    if (containerRef.current) {
      containerRef.current.style.cursor = node ? 'pointer' : 'grab'
    }
  }, [])

  // Check if link should be highlighted (only for selected node, not hover)
  const isLinkHighlighted = useCallback((link: ExtendedGraphEdge): boolean => {
    if (!selectedNodeId) return false
    const sourceId = typeof link.source === 'object' ? (link.source as ExtendedGraphNode).id : link.source
    const targetId = typeof link.target === 'object' ? (link.target as ExtendedGraphNode).id : link.target
    return sourceId === selectedNodeId || targetId === selectedNodeId
  }, [selectedNodeId])

  // Node color based on type and selection state (no hover - causes re-render issues)
  const nodeColor = useCallback((node: ExtendedGraphNode) => {
    const baseColor = TYPE_COLORS[node.type] || '#6B7280'
    
    if (selectedNodeId) {
      if (node.id === selectedNodeId) return '#FFFFFF'
      const neighbors = adjacencyMap.get(selectedNodeId)
      if (neighbors?.has(node.id)) return baseColor
      return '#374151' // Dim non-connected
    }
    return baseColor
  }, [selectedNodeId, adjacencyMap])

  // Link color based on relationship type
  const linkColor = useCallback((link: ExtendedGraphEdge) => {
    if (isLinkHighlighted(link)) return '#FFFFFF'
    if (selectedNodeId) return '#1F2937'
    
    switch (link.relationship) {
      case 'implements':
        return '#22C55E'
      case 'creates':
        return '#3B82F6'
      case 'references':
        return '#6B7280'
      case 'tracked_by':
        return '#EF4444'
      default:
        return '#4B5563'
    }
  }, [selectedNodeId, isLinkHighlighted])
  
  const linkWidth = useCallback((link: ExtendedGraphEdge) => {
    return isLinkHighlighted(link) ? 3 : 1
  }, [isLinkHighlighted])

  // Enhancement 4: Deselect on background click
  const handleBackgroundClick = useCallback(() => {
    onNodeClick?.('', '' as ArtifactType) // Clear parent selection
  }, [onNodeClick])

  // Enhancement 1: Fix node position after dragging
  const handleNodeDragEnd = useCallback((node: ExtendedGraphNode) => {
    // Pin node in place after drag
    node.fx = node.x
    node.fy = node.y
    if (is3D) node.fz = node.z
  }, [is3D])

  // Early return AFTER all hooks are defined (React hooks rule)
  // Wait for valid dimensions before rendering graph to prevent clipping
  if (loading || !graphData || dimensions.width === 0 || dimensions.height === 0) {
    return (
      <div 
        ref={outerRef}
        className={cn('w-full h-full bg-zinc-950 flex items-center justify-center', className)}
        style={{ minHeight: 0, minWidth: 0 }}
      >
        <div className="text-zinc-500">
          {loading ? 'Loading graph...' : dimensions.width === 0 ? 'Measuring...' : 'Loading...'}
        </div>
      </div>
    )
  }

  // Shared graph props - explicit dimensions required for proper sizing in flex layouts
  // ForceGraph defaults to window size without these, causing clipping
  const graphProps = {
    ref: graphRef,
    width: dimensions.width,
    height: dimensions.height,
    graphData: { nodes: graphData.nodes, links: graphData.edges },
    nodeLabel: (node: ExtendedGraphNode) => {
      const label = settings.shortLabels ? node.id.split('/').pop() || node.id : node.id
      return `<div style="background:#1f2937;padding:4px 8px;border-radius:4px;font-size:12px"><b>${TYPE_LABELS[node.type]}</b>: ${label}<br/><span style="color:#9ca3af">${node.status}</span></div>`
    },
    nodeColor,
    onNodeClick: handleNodeClick,
    onNodeHover: handleNodeHover,
    onBackgroundClick: handleBackgroundClick,  // Enhancement 4
    onNodeDragEnd: handleNodeDragEnd,          // Enhancement 1
    linkColor,
    linkWidth,
    linkCurvature: settings.linkCurvature,
    linkDirectionalArrowLength: 6,
    linkDirectionalArrowRelPos: 1,
    linkDirectionalParticles: (link: ExtendedGraphEdge) => 
      settings.showParticles && isLinkHighlighted(link) ? 2 : 0,
    linkDirectionalParticleWidth: 2,
    linkDirectionalParticleSpeed: settings.particleSpeed,
    backgroundColor: '#09090b',
    enableNodeDrag: true,
    // Force simulation settings - user configurable
    d3Force: (d3: any) => {
      d3.force('charge')?.strength(settings.chargeStrength)
      d3.force('link')?.distance(settings.linkDistance)
      d3.force('center')?.strength(settings.centerStrength)
    },
    dagMode: settings.dagMode,
    dagLevelDistance: 50,
    // Stabilization settings
    cooldownTicks: 100,
    cooldownTime: 3000,
    d3AlphaMin: 0.05,
    d3AlphaDecay: 0.05,
    d3VelocityDecay: 0.4,
    warmupTicks: 100,
    onEngineStop: () => {
      if (graphRef.current && !initialZoomDone.current) {
        initialZoomDone.current = true
        graphRef.current.zoomToFit(400, 100)
      }
    },
  }

  return (
    // Flex-based sizing with explicit dimensions passed to ForceGraph
    <div 
      ref={outerRef}
      className={cn('bg-zinc-950 relative', className)} 
      style={{ 
        width: '100%',
        height: '100%',
        minHeight: 0,
        minWidth: 0,
        overflow: 'hidden',
      }}
    >
      {/* Top Controls Bar */}
      <div className="absolute top-4 right-4 z-20 flex gap-2">
        {/* Settings Toggle */}
        <button
          onClick={() => setSettingsOpen(!settingsOpen)}
          className={cn(
            'flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-all',
            settingsOpen
              ? 'bg-purple-600 text-white shadow-lg'
              : 'bg-zinc-800/90 text-zinc-400 hover:bg-zinc-700 hover:text-white'
          )}
          title="Graph Settings"
        >
          <Settings size={16} />
        </button>
        
        {/* 2D/3D Toggle */}
        <button
          onClick={() => setIs3D(false)}
          className={cn(
            'flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-all',
            !is3D
              ? 'bg-blue-600 text-white shadow-lg'
              : 'bg-zinc-800/90 text-zinc-400 hover:bg-zinc-700 hover:text-white'
          )}
          title="2D View (Press 2)"
        >
          <Layers size={16} />
          2D
        </button>
        <button
          onClick={() => setIs3D(true)}
          className={cn(
            'flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-all',
            is3D
              ? 'bg-blue-600 text-white shadow-lg'
              : 'bg-zinc-800/90 text-zinc-400 hover:bg-zinc-700 hover:text-white'
          )}
          title="3D View (Press 3)"
        >
          <Box size={16} />
          3D
        </button>
      </div>

      {/* Settings Panel */}
      {settingsOpen && (
        <div className="absolute top-16 right-4 z-20 w-72 bg-zinc-900/95 backdrop-blur-sm rounded-xl border border-zinc-700 shadow-2xl overflow-hidden">
          {/* Header */}
          <div className="flex items-center justify-between px-4 py-3 border-b border-zinc-700">
            <span className="text-sm font-semibold text-white">Graph Settings</span>
            <div className="flex gap-2">
              <button
                onClick={() => setSettings(defaultSettings)}
                className="p-1.5 rounded-lg text-zinc-400 hover:text-white hover:bg-zinc-700 transition-colors"
                title="Reset to defaults"
              >
                <RotateCcw size={14} />
              </button>
              <button
                onClick={() => setSettingsOpen(false)}
                className="p-1.5 rounded-lg text-zinc-400 hover:text-white hover:bg-zinc-700 transition-colors"
              >
                <X size={14} />
              </button>
            </div>
          </div>
          
          {/* Settings Content */}
          <div className="p-4 space-y-4 max-h-[60vh] overflow-y-auto">
            {/* Focus Zoom */}
            <div>
              <label className="flex items-center justify-between text-xs text-zinc-400 mb-1.5">
                <span>Focus Distance</span>
                <span className="text-zinc-500">{settings.focusDistance}</span>
              </label>
              <input
                type="range"
                min="100"
                max="800"
                step="50"
                value={settings.focusDistance}
                onChange={(e) => setSettings(s => ({ ...s, focusDistance: Number(e.target.value) }))}
                className="w-full h-1.5 bg-zinc-700 rounded-lg appearance-none cursor-pointer accent-blue-500"
              />
              <div className="flex justify-between text-[10px] text-zinc-600 mt-0.5">
                <span>Close</span>
                <span>Far</span>
              </div>
            </div>

            {/* Node Repulsion */}
            <div>
              <label className="flex items-center justify-between text-xs text-zinc-400 mb-1.5">
                <span>Node Spread</span>
                <span className="text-zinc-500">{Math.abs(settings.chargeStrength)}</span>
              </label>
              <input
                type="range"
                min="-300"
                max="-30"
                step="10"
                value={settings.chargeStrength}
                onChange={(e) => setSettings(s => ({ ...s, chargeStrength: Number(e.target.value) }))}
                className="w-full h-1.5 bg-zinc-700 rounded-lg appearance-none cursor-pointer accent-green-500"
              />
              <div className="flex justify-between text-[10px] text-zinc-600 mt-0.5">
                <span>Tight</span>
                <span>Spread</span>
              </div>
            </div>

            {/* Link Distance */}
            <div>
              <label className="flex items-center justify-between text-xs text-zinc-400 mb-1.5">
                <span>Link Length</span>
                <span className="text-zinc-500">{settings.linkDistance}</span>
              </label>
              <input
                type="range"
                min="20"
                max="150"
                step="10"
                value={settings.linkDistance}
                onChange={(e) => setSettings(s => ({ ...s, linkDistance: Number(e.target.value) }))}
                className="w-full h-1.5 bg-zinc-700 rounded-lg appearance-none cursor-pointer accent-yellow-500"
              />
            </div>

            {/* Link Curvature */}
            <div>
              <label className="flex items-center justify-between text-xs text-zinc-400 mb-1.5">
                <span>Link Curvature</span>
                <span className="text-zinc-500">{settings.linkCurvature.toFixed(2)}</span>
              </label>
              <input
                type="range"
                min="0"
                max="0.5"
                step="0.05"
                value={settings.linkCurvature}
                onChange={(e) => setSettings(s => ({ ...s, linkCurvature: Number(e.target.value) }))}
                className="w-full h-1.5 bg-zinc-700 rounded-lg appearance-none cursor-pointer accent-purple-500"
              />
              <div className="flex justify-between text-[10px] text-zinc-600 mt-0.5">
                <span>Straight</span>
                <span>Curved</span>
              </div>
            </div>

            {/* Toggles Section */}
            <div className="space-y-2 pt-2 border-t border-zinc-700">
              {/* Short Labels */}
              <label className="flex items-center justify-between cursor-pointer group">
                <span className="text-xs text-zinc-400 group-hover:text-zinc-300">Short Labels</span>
                <div className="relative">
                  <input
                    type="checkbox"
                    checked={settings.shortLabels}
                    onChange={(e) => setSettings(s => ({ ...s, shortLabels: e.target.checked }))}
                    className="sr-only peer"
                  />
                  <div className="w-9 h-5 bg-zinc-700 rounded-full peer peer-checked:bg-blue-600 transition-colors"></div>
                  <div className="absolute left-0.5 top-0.5 w-4 h-4 bg-white rounded-full transition-transform peer-checked:translate-x-4"></div>
                </div>
              </label>

              {/* Show Particles */}
              <label className="flex items-center justify-between cursor-pointer group">
                <span className="text-xs text-zinc-400 group-hover:text-zinc-300">Link Particles</span>
                <div className="relative">
                  <input
                    type="checkbox"
                    checked={settings.showParticles}
                    onChange={(e) => setSettings(s => ({ ...s, showParticles: e.target.checked }))}
                    className="sr-only peer"
                  />
                  <div className="w-9 h-5 bg-zinc-700 rounded-full peer peer-checked:bg-blue-600 transition-colors"></div>
                  <div className="absolute left-0.5 top-0.5 w-4 h-4 bg-white rounded-full transition-transform peer-checked:translate-x-4"></div>
                </div>
              </label>
            </div>

            {/* DAG Mode */}
            <div className="pt-2 border-t border-zinc-700">
              <label className="text-xs text-zinc-400 mb-1.5 block">Layout Mode</label>
              <select
                value={settings.dagMode || ''}
                onChange={(e) => setSettings(s => ({ ...s, dagMode: e.target.value || null }))}
                className="w-full bg-zinc-800 border border-zinc-700 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:ring-1 focus:ring-blue-500"
              >
                <option value="">Force-Directed (default)</option>
                <option value="td">Top-Down Hierarchy</option>
                <option value="bu">Bottom-Up Hierarchy</option>
                <option value="lr">Left-Right Hierarchy</option>
                <option value="rl">Right-Left Hierarchy</option>
                <option value="radialout">Radial Outward</option>
                <option value="radialin">Radial Inward</option>
              </select>
            </div>
          </div>
        </div>
      )}

      {/* Render 2D or 3D Graph */}
      {is3D ? (
        <ForceGraph3D
          key="3d-graph"
          {...graphProps}
          controlType="orbit"                  // Enhancement 2: Better camera controls
          nodeOpacity={0.9}
          nodeResolution={16}
          linkOpacity={0.6}
          showNavInfo={false}
          enableNavigationControls={true}
        />
      ) : (
        <ForceGraph2D
          key="2d-graph"
          {...graphProps}
          nodeCanvasObject={(node: ExtendedGraphNode, ctx: CanvasRenderingContext2D, globalScale: number) => {
            const baseColor = TYPE_COLORS[node.type] || '#6B7280'
            const color = nodeColor(node)
            const size = 6
            
            ctx.beginPath()
            ctx.arc(node.x!, node.y!, size, 0, 2 * Math.PI)
            ctx.fillStyle = color
            ctx.fill()
            ctx.strokeStyle = color === '#FFFFFF' ? '#FFFFFF' : baseColor
            ctx.lineWidth = 1.5 / globalScale
            ctx.stroke()
            
            if (globalScale > 0.5) {
              const fontSize = Math.max(8, 10 / globalScale)
              ctx.font = `${fontSize}px sans-serif`
              ctx.textAlign = 'center'
              ctx.textBaseline = 'top'
              ctx.fillStyle = '#9CA3AF'
              const label = node.id.length > 20 ? node.id.slice(0, 18) + '..' : node.id
              ctx.fillText(label, node.x!, node.y! + size + 2)
            }
          }}
        />
      )}

      {/* Legend - tooltips handled by built-in nodeLabel prop (no React re-renders) */}
      <div className="absolute bottom-4 left-4 bg-zinc-900/95 border border-zinc-800 rounded-lg p-3 backdrop-blur-sm max-w-xs z-10">
        <div className="text-xs text-zinc-400 mb-2 font-medium">Artifact Types</div>
        <div className="space-y-1.5">
          {Object.entries(TYPE_COLORS).map(([type, color]) => (
            <div key={type} className="flex items-center gap-2 text-xs">
              <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: color }} />
              <span className="text-zinc-300">{TYPE_LABELS[type as ArtifactType]}</span>
            </div>
          ))}
        </div>
        
        <div className="text-xs text-zinc-400 mt-3 mb-2 font-medium border-t border-zinc-800 pt-2">Relationships</div>
        <div className="space-y-1.5">
          <div className="flex items-center gap-2 text-xs">
            <div className="w-4 h-0.5 bg-green-500" />
            <span className="text-zinc-300">Implements</span>
          </div>
          <div className="flex items-center gap-2 text-xs">
            <div className="w-4 h-0.5 bg-blue-500" />
            <span className="text-zinc-300">Creates</span>
          </div>
          <div className="flex items-center gap-2 text-xs">
            <div className="w-4 h-0.5 bg-gray-500" />
            <span className="text-zinc-300">References</span>
          </div>
        </div>
        
        <div className="text-xs text-zinc-500 mt-3 pt-2 border-t border-zinc-800">
          {is3D ? 'Drag to rotate' : 'Drag to pan'} • Scroll to zoom<br/>
          Press <kbd className="px-1 py-0.5 bg-zinc-800 rounded text-zinc-400">2</kbd> or <kbd className="px-1 py-0.5 bg-zinc-800 rounded text-zinc-400">3</kbd> to toggle
        </div>
      </div>
    </div>
  )
}
