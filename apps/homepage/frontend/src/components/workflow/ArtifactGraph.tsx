import { useRef, useCallback, useState, useEffect } from 'react'
import ForceGraph2D from 'react-force-graph-2d'
import { cn } from '@/lib/utils'
import type { ArtifactType } from './types'

const API_BASE = 'http://localhost:8000/api/devtools'

// Tier colors per ADR-0045
const TYPE_COLORS: Record<ArtifactType, string> = {
  discussion: '#8B5CF6', // purple
  adr: '#3B82F6',        // blue
  spec: '#22C55E',       // green
  plan: '#F59E0B',       // amber
  contract: '#EC4899',   // pink
}

interface GraphNode {
  id: string
  type: ArtifactType
  label: string
  status: string
  file_path: string
}

interface GraphEdge {
  source: string
  target: string
  relationship: string
}

interface GraphData {
  nodes: GraphNode[]
  edges: GraphEdge[]
}

interface ArtifactGraphProps {
  onNodeClick?: (nodeId: string, type: ArtifactType) => void
  selectedNodeId?: string
  className?: string
}

export function ArtifactGraph({ onNodeClick, selectedNodeId: _selectedNodeId, className }: ArtifactGraphProps) {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const graphRef = useRef<any>(null)
  const [graphData, setGraphData] = useState<GraphData>({ nodes: [], edges: [] })
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchGraph = async () => {
      try {
        const res = await fetch(`${API_BASE}/artifacts/graph`)
        if (res.ok) {
          const data = await res.json()
          setGraphData({
            nodes: data.nodes,
            edges: data.edges.map((e: GraphEdge) => ({ ...e, source: e.source, target: e.target }))
          })
        }
      } catch (err) {
        console.error('Failed to fetch graph:', err)
      } finally {
        setLoading(false)
      }
    }
    fetchGraph()
  }, [])

  const handleNodeClick = useCallback((node: GraphNode) => {
    onNodeClick?.(node.id, node.type)
  }, [onNodeClick])

  const nodeColor = useCallback((node: GraphNode) => {
    return TYPE_COLORS[node.type] || '#6B7280'
  }, [])

  const nodeLabel = useCallback((node: GraphNode) => {
    return `${node.id}\n${node.label}`
  }, [])

  if (loading) {
    return <div className="flex items-center justify-center h-full text-zinc-500">Loading graph...</div>
  }

  return (
    <div className={cn('w-full h-full bg-zinc-950', className)}>
      <ForceGraph2D
        ref={graphRef}
        graphData={{ nodes: graphData.nodes, links: graphData.edges }}
        nodeColor={nodeColor}
        nodeLabel={nodeLabel}
        onNodeClick={handleNodeClick}
        linkDirectionalArrowLength={4}
        linkDirectionalArrowRelPos={1}
        linkColor={() => '#4B5563'}
        backgroundColor="#09090b"
      />
    </div>
  )
}
