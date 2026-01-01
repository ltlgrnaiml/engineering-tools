import { lazy, Suspense, useState, useRef, useCallback, useEffect, useMemo } from 'react'
import { Layers, Box } from 'lucide-react'
import { cn } from '@/lib/utils'
import { useArtifactGraph } from '@/hooks/useWorkflowApi'
import type { ArtifactType, GraphNode, GraphEdge } from './types'

// Lazy load 3D component to avoid bundle bloat
const ForceGraph3D = lazy(() => import('react-force-graph-3d'))

// Tier colors per DISC-001
const TYPE_COLORS: Record<ArtifactType, string> = {
  discussion: '#3B82F6',
  adr: '#22C55E',
  spec: '#EAB308',
  contract: '#A855F7',
  plan: '#EF4444',
}

const TYPE_LABELS: Record<ArtifactType, string> = {
  discussion: 'Discussion',
  adr: 'ADR',
  spec: 'SPEC',
  contract: 'Contract',
  plan: 'Plan',
}

interface ExtendedGraphNode extends GraphNode {
  x?: number
  y?: number
  z?: number
  __highlighted?: boolean
}

interface ExtendedGraphEdge extends GraphEdge {
  __highlighted?: boolean
}

interface ArtifactGraph3DProps {
  onNodeClick?: (nodeId: string, type: ArtifactType) => void
  selectedNodeId?: string
  className?: string
}

export function ArtifactGraph3D({ onNodeClick, selectedNodeId, className }: ArtifactGraph3DProps) {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const graphRef = useRef<any>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  const { data: graphData, loading } = useArtifactGraph()
  const [hoveredNode, setHoveredNode] = useState<ExtendedGraphNode | null>(null)
  const [is3D, setIs3D] = useState(false)
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 })

  // Track container dimensions
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

  // Center on selected node
  useEffect(() => {
    if (!selectedNodeId || !graphRef.current || !graphData) return

    const node = graphData.nodes.find(n => n.id === selectedNodeId) as ExtendedGraphNode | undefined
    if (node && node.x !== undefined && node.y !== undefined) {
      if (is3D && node.z !== undefined) {
        graphRef.current.cameraPosition(
          { x: node.x * 2, y: node.y * 2, z: node.z * 2 },
          node,
          1000
        )
      } else {
        graphRef.current.centerAt(node.x, node.y, 500)
        graphRef.current.zoom(2, 500)
      }
    }
  }, [selectedNodeId, graphData, is3D])

  // Keyboard shortcuts: 2/3 toggle
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === '2') {
        setIs3D(false)
      } else if (e.key === '3') {
        setIs3D(true)
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [])

  const handleNodeClick = useCallback((node: ExtendedGraphNode) => {
    onNodeClick?.(node.id, node.type)
    
    if (graphRef.current && node.x !== undefined && node.y !== undefined) {
      if (is3D && node.z !== undefined) {
        graphRef.current.cameraPosition(
          { x: node.x * 2, y: node.y * 2, z: node.z * 2 },
          node,
          1000
        )
      } else {
        graphRef.current.centerAt(node.x, node.y, 500)
        graphRef.current.zoom(2, 500)
      }
    }
  }, [onNodeClick, is3D])

  const handleNodeHover = useCallback((node: ExtendedGraphNode | null) => {
    setHoveredNode(node)
  }, [])

  const isNodeHighlighted = useCallback((node: ExtendedGraphNode): boolean => {
    if (!hoveredNode && !selectedNodeId) return false
    const activeId = hoveredNode?.id || selectedNodeId
    if (!activeId) return false
    if (node.id === activeId) return true
    const neighbors = adjacencyMap.get(activeId)
    return neighbors?.has(node.id) ?? false
  }, [hoveredNode, selectedNodeId, adjacencyMap])

  const isLinkHighlighted = useCallback((link: ExtendedGraphEdge): boolean => {
    if (!hoveredNode && !selectedNodeId) return false
    const activeId = hoveredNode?.id || selectedNodeId
    if (!activeId) return false
    const sourceId = typeof link.source === 'object' ? (link.source as ExtendedGraphNode).id : link.source
    const targetId = typeof link.target === 'object' ? (link.target as ExtendedGraphNode).id : link.target
    return sourceId === activeId || targetId === activeId
  }, [hoveredNode, selectedNodeId])

  const nodeColor = useCallback((node: ExtendedGraphNode) => {
    const isHighlighted = isNodeHighlighted(node)
    const baseColor = TYPE_COLORS[node.type] || '#6B7280'
    
    if ((hoveredNode || selectedNodeId) && !isHighlighted) {
      return '#374151'
    }
    return baseColor
  }, [hoveredNode, selectedNodeId, isNodeHighlighted])

  const linkColor = useCallback((link: ExtendedGraphEdge) => {
    if (isLinkHighlighted(link)) return '#FFFFFF'
    if (hoveredNode || selectedNodeId) return '#1F2937'
    
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
  }, [hoveredNode, selectedNodeId, isLinkHighlighted])

  const linkWidth = useCallback((link: ExtendedGraphEdge) => {
    return isLinkHighlighted(link) ? 2.5 : 1
  }, [isLinkHighlighted])

  // Shared graph props for both 2D and 3D
  const graphProps = {
    graphData: graphData ? { nodes: graphData.nodes, links: graphData.edges } : { nodes: [], links: [] },
    nodeLabel: (node: ExtendedGraphNode) => `${TYPE_LABELS[node.type]}: ${node.id} (${node.status})`,
    nodeColor,
    linkColor,
    linkWidth,
    linkDirectionalArrowLength: 6,
    linkDirectionalArrowRelPos: 1,
    linkDirectionalParticles: (link: ExtendedGraphEdge) => isLinkHighlighted(link) ? 2 : 0,
    linkDirectionalParticleWidth: 2,
    linkDirectionalParticleSpeed: 0.005,
    onNodeClick: handleNodeClick,
    onNodeHover: handleNodeHover,
  }

  if (loading || !graphData) {
    return (
      <div className={cn('w-full h-full bg-zinc-950 flex items-center justify-center', className)}>
        <div className="text-zinc-500">Loading graph...</div>
      </div>
    )
  }

  return (
    <div ref={containerRef} className={cn('w-full h-full bg-zinc-950 relative overflow-hidden', className)}>
      {/* 2D/3D Toggle Button */}
      <div className="absolute top-4 right-4 z-10 flex gap-2">
        <button
          onClick={() => setIs3D(false)}
          className={cn(
            'flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-all',
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
            'flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-all',
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

      {/* Graph Component */}
      {is3D ? (
        <Suspense fallback={<div className="flex items-center justify-center h-full"><div className="text-zinc-500">Loading 3D...</div></div>}>
          <ForceGraph3D
            ref={graphRef}
            width={dimensions.width}
            height={dimensions.height}
            {...graphProps}
            backgroundColor="#09090b"
          />
        </Suspense>
      ) : (
        <div className="w-full h-full">
          {/* 2D implementation would import from original ArtifactGraph.tsx */}
          <div className="flex items-center justify-center h-full text-zinc-500">
            Switch to ArtifactGraph component for 2D
          </div>
        </div>
      )}

      {/* Hover Info Bar */}
      {hoveredNode && (
        <div className="absolute top-2 left-1/2 -translate-x-1/2 bg-zinc-800/95 border border-zinc-700 rounded-lg shadow-xl px-4 py-2 backdrop-blur-sm z-10">
          <span className="text-zinc-400 text-sm">{TYPE_LABELS[hoveredNode.type]}:</span>
          <span className="text-white text-sm ml-2 font-medium">{hoveredNode.id}</span>
          <span className="text-zinc-500 text-xs ml-3">({hoveredNode.status})</span>
        </div>
      )}

      {/* Legend */}
      <div className="absolute bottom-4 left-4 bg-zinc-900/95 border border-zinc-800 rounded-lg p-3 backdrop-blur-sm z-10">
        <div className="text-xs text-zinc-400 mb-2 font-medium">Artifact Types</div>
        <div className="space-y-1.5">
          {Object.entries(TYPE_COLORS).map(([type, color]) => (
            <div key={type} className="flex items-center gap-2 text-xs">
              <div 
                className="w-2.5 h-2.5 rounded-full"
                style={{ backgroundColor: color }}
              />
              <span className="text-zinc-300">{TYPE_LABELS[type as ArtifactType]}</span>
            </div>
          ))}
        </div>
        
        <div className="text-xs text-zinc-400 mt-3 mb-2 font-medium">Relationships</div>
        <div className="space-y-1.5">
          <div className="flex items-center gap-2 text-xs">
            <div className="w-4 h-0.5 bg-green-500" />
            <span className="text-zinc-300">Implements</span>
          </div>
          <div className="flex items-center gap-2 text-xs">
            <div className="w-4 h-0.5 bg-blue-500" style={{ backgroundImage: 'repeating-linear-gradient(to right, currentColor 0, currentColor 2px, transparent 2px, transparent 4px)' }} />
            <span className="text-zinc-300">Creates</span>
          </div>
          <div className="flex items-center gap-2 text-xs">
            <div className="w-4 h-0.5 bg-gray-500" style={{ backgroundImage: 'repeating-linear-gradient(to right, currentColor 0, currentColor 2px, transparent 2px, transparent 6px)' }} />
            <span className="text-zinc-300">References</span>
          </div>
        </div>
        
        <div className="text-xs text-zinc-500 mt-3 pt-2 border-t border-zinc-800">
          Press <kbd className="px-1 py-0.5 bg-zinc-800 rounded">2</kbd> or <kbd className="px-1 py-0.5 bg-zinc-800 rounded">3</kbd> to toggle
        </div>
      </div>
    </div>
  )
}
