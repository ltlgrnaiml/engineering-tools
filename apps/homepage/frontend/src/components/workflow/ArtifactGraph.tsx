import { useRef, useCallback, useState, useEffect, useMemo } from 'react'
import ForceGraph2D from 'react-force-graph-2d'
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

// Different shapes for each artifact type
type ShapeType = 'circle' | 'square' | 'diamond' | 'triangle' | 'hexagon'
const TYPE_SHAPES: Record<ArtifactType, ShapeType> = {
  discussion: 'circle',
  adr: 'hexagon',
  spec: 'diamond',
  contract: 'square',
  plan: 'triangle',
}


// Helper to draw different shapes
function drawShape(
  ctx: CanvasRenderingContext2D,
  x: number,
  y: number,
  size: number,
  shape: ShapeType
) {
  ctx.beginPath()
  switch (shape) {
    case 'circle':
      ctx.arc(x, y, size, 0, 2 * Math.PI)
      break
    case 'square':
      ctx.rect(x - size, y - size, size * 2, size * 2)
      break
    case 'diamond':
      ctx.moveTo(x, y - size * 1.2)
      ctx.lineTo(x + size, y)
      ctx.lineTo(x, y + size * 1.2)
      ctx.lineTo(x - size, y)
      ctx.closePath()
      break
    case 'triangle':
      ctx.moveTo(x, y - size * 1.1)
      ctx.lineTo(x + size, y + size * 0.8)
      ctx.lineTo(x - size, y + size * 0.8)
      ctx.closePath()
      break
    case 'hexagon':
      for (let i = 0; i < 6; i++) {
        const angle = (Math.PI / 3) * i - Math.PI / 2
        const px = x + size * Math.cos(angle)
        const py = y + size * Math.sin(angle)
        if (i === 0) ctx.moveTo(px, py)
        else ctx.lineTo(px, py)
      }
      ctx.closePath()
      break
  }
}

// Truncate label for display
function truncateLabel(label: string, maxLen: number): string {
  if (label.length <= maxLen) return label
  return label.slice(0, maxLen - 2) + '..'
}

interface ArtifactGraphProps {
  onNodeClick?: (nodeId: string, type: ArtifactType) => void
  selectedNodeId?: string
  className?: string
}

interface ExtendedGraphNode extends GraphNode {
  x?: number
  y?: number
  __highlighted?: boolean
}

interface ExtendedGraphEdge extends GraphEdge {
  __highlighted?: boolean
}

export function ArtifactGraph({ onNodeClick, selectedNodeId, className }: ArtifactGraphProps) {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const graphRef = useRef<any>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  const { data: graphData, loading } = useArtifactGraph()
  const [hoveredNode, setHoveredNode] = useState<ExtendedGraphNode | null>(null)
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 })

  // Track container dimensions only - NO auto zoom to prevent drift
  useEffect(() => {
    const container = containerRef.current
    if (!container) return

    const updateDimensions = () => {
      setDimensions({
        width: container.clientWidth,
        height: container.clientHeight,
      })
    }

    updateDimensions()
    const resizeObserver = new ResizeObserver(updateDimensions)
    resizeObserver.observe(container)

    return () => resizeObserver.disconnect()
  }, [])

  // Build adjacency map for highlighting connected nodes
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

  // Center on selected node when it changes
  useEffect(() => {
    if (!selectedNodeId || !graphRef.current || !graphData) return

    const node = graphData.nodes.find(n => n.id === selectedNodeId) as ExtendedGraphNode | undefined
    if (node && node.x !== undefined && node.y !== undefined) {
      graphRef.current.centerAt(node.x, node.y, 500)
      graphRef.current.zoom(2, 500)
    }
  }, [selectedNodeId, graphData])

  const handleNodeClick = useCallback((node: ExtendedGraphNode) => {
    onNodeClick?.(node.id, node.type)
    
    // Center on clicked node
    if (graphRef.current && node.x !== undefined && node.y !== undefined) {
      graphRef.current.centerAt(node.x, node.y, 500)
      graphRef.current.zoom(2, 500)
    }
  }, [onNodeClick])

  const handleNodeHover = useCallback((node: ExtendedGraphNode | null) => {
    setHoveredNode(node)
  }, [])

  // Check if node should be highlighted
  const isNodeHighlighted = useCallback((node: ExtendedGraphNode): boolean => {
    if (!hoveredNode && !selectedNodeId) return false
    
    const activeId = hoveredNode?.id || selectedNodeId
    if (!activeId) return false
    
    if (node.id === activeId) return true
    
    const neighbors = adjacencyMap.get(activeId)
    return neighbors?.has(node.id) ?? false
  }, [hoveredNode, selectedNodeId, adjacencyMap])

  // Check if link should be highlighted
  const isLinkHighlighted = useCallback((link: ExtendedGraphEdge): boolean => {
    if (!hoveredNode && !selectedNodeId) return false
    
    const activeId = hoveredNode?.id || selectedNodeId
    if (!activeId) return false
    
    const sourceId = typeof link.source === 'object' ? (link.source as ExtendedGraphNode).id : link.source
    const targetId = typeof link.target === 'object' ? (link.target as ExtendedGraphNode).id : link.target
    
    return sourceId === activeId || targetId === activeId
  }, [hoveredNode, selectedNodeId])

  const nodeCanvasObject = useCallback((node: ExtendedGraphNode, ctx: CanvasRenderingContext2D, globalScale: number) => {
    const isHighlighted = isNodeHighlighted(node)
    const isSelected = node.id === selectedNodeId
    const baseColor = TYPE_COLORS[node.type] || '#6B7280'
    const shape = TYPE_SHAPES[node.type] || 'circle'
    
    // Dynamic node size based on zoom
    const baseSize = 8
    const nodeSize = isHighlighted ? baseSize + 2 : baseSize
    
    // Draw shape
    drawShape(ctx, node.x!, node.y!, nodeSize, shape)
    
    // Fill color - dim non-highlighted nodes
    if ((hoveredNode || selectedNodeId) && !isHighlighted) {
      ctx.fillStyle = '#374151'
    } else {
      ctx.fillStyle = baseColor
    }
    ctx.fill()
    
    // Draw border for better visibility
    ctx.strokeStyle = isHighlighted ? '#FFFFFF' : baseColor
    ctx.lineWidth = 1.5 / globalScale
    ctx.stroke()
    
    // Draw selection ring
    if (isSelected) {
      drawShape(ctx, node.x!, node.y!, nodeSize + 5, shape)
      ctx.strokeStyle = '#FFFFFF'
      ctx.lineWidth = 2.5 / globalScale
      ctx.stroke()
    }
    
    // Dynamic label sizing and truncation based on zoom level
    // Only show labels when zoomed in enough
    if (globalScale > 0.4) {
      const baseFontSize = Math.max(8, Math.min(14, 10 / globalScale))
      const maxLabelLen = globalScale > 1.5 ? 30 : globalScale > 0.8 ? 18 : 12
      const label = truncateLabel(node.id, maxLabelLen)
      
      ctx.font = `${baseFontSize}px -apple-system, BlinkMacSystemFont, sans-serif`
      ctx.textAlign = 'center'
      ctx.textBaseline = 'top'
      ctx.fillStyle = isHighlighted ? '#FFFFFF' : '#9CA3AF'
      ctx.fillText(label, node.x!, node.y! + nodeSize + 3)
    }
  }, [hoveredNode, selectedNodeId, isNodeHighlighted])

  const linkColor = useCallback((link: ExtendedGraphEdge) => {
    if (isLinkHighlighted(link)) {
      return '#FFFFFF'
    }
    if (hoveredNode || selectedNodeId) {
      return '#1F2937' // dim when something is highlighted
    }
    return '#4B5563'
  }, [hoveredNode, selectedNodeId, isLinkHighlighted])

  const linkWidth = useCallback((link: ExtendedGraphEdge) => {
    return isLinkHighlighted(link) ? 2 : 1
  }, [isLinkHighlighted])

  if (loading || !graphData) {
    return (
      <div className={cn('w-full h-full bg-zinc-950 flex items-center justify-center', className)}>
        <div className="text-zinc-500">Loading graph...</div>
      </div>
    )
  }

  return (
    <div ref={containerRef} className={cn('w-full h-full bg-zinc-950 relative overflow-hidden', className)}>
      <ForceGraph2D
        ref={graphRef}
        width={dimensions.width}
        height={dimensions.height}
        graphData={{ nodes: graphData.nodes, links: graphData.edges }}
        nodeCanvasObject={nodeCanvasObject}
        nodePointerAreaPaint={(node: ExtendedGraphNode, color, ctx) => {
          ctx.beginPath()
          ctx.arc(node.x!, node.y!, 10, 0, 2 * Math.PI)
          ctx.fillStyle = color
          ctx.fill()
        }}
        onNodeClick={handleNodeClick}
        onNodeHover={handleNodeHover}
        linkColor={linkColor}
        linkWidth={linkWidth}
        linkDirectionalArrowLength={6}
        linkDirectionalArrowRelPos={1}
        linkDirectionalParticles={2}
        linkDirectionalParticleWidth={(link: ExtendedGraphEdge) => isLinkHighlighted(link) ? 3 : 0}
        linkDirectionalParticleSpeed={0.005}
        backgroundColor="#09090b"
        cooldownTicks={100}
        onEngineStop={() => {
          // Zoom to fit after initial layout
          if (graphRef.current) {
            graphRef.current.zoomToFit(400, 50)
          }
        }}
      />

      {/* Simple info bar at top instead of floating tooltip */}
      {hoveredNode && (
        <div className="absolute top-2 left-1/2 -translate-x-1/2 bg-zinc-800/95 border border-zinc-700 rounded-lg shadow-xl px-4 py-2 backdrop-blur-sm">
          <span className="text-zinc-400 text-sm">{TYPE_LABELS[hoveredNode.type]}:</span>
          <span className="text-white text-sm ml-2 font-medium">{hoveredNode.id}</span>
          <span className="text-zinc-500 text-xs ml-3">({hoveredNode.status})</span>
        </div>
      )}

      {/* Legend with shapes */}
      <div className="absolute bottom-4 left-4 bg-zinc-900/95 border border-zinc-800 rounded-lg p-3 backdrop-blur-sm">
        <div className="text-xs text-zinc-400 mb-2 font-medium">Artifact Types</div>
        <div className="space-y-1.5">
          {Object.entries(TYPE_COLORS).map(([type, color]) => {
            const shapeClass = {
              discussion: 'rounded-full',
              adr: 'rotate-45 rounded-sm',
              spec: 'rotate-45',
              contract: '',
              plan: '',
            }[type] || ''
            const isTriangle = type === 'plan'
            const isDiamond = type === 'spec'
            return (
              <div key={type} className="flex items-center gap-2 text-xs">
                {isTriangle ? (
                  <div 
                    className="w-0 h-0 border-l-[5px] border-r-[5px] border-b-[8px] border-l-transparent border-r-transparent"
                    style={{ borderBottomColor: color }}
                  />
                ) : isDiamond ? (
                  <div 
                    className="w-2.5 h-2.5 rotate-45"
                    style={{ backgroundColor: color }}
                  />
                ) : (
                  <div 
                    className={`w-2.5 h-2.5 ${shapeClass}`}
                    style={{ backgroundColor: color }}
                  />
                )}
                <span className="text-zinc-300">{TYPE_LABELS[type as ArtifactType]}</span>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
