import { ZoomIn, ZoomOut, Maximize2, Download, Box } from 'lucide-react'
import { cn } from '@/lib/utils'

interface GraphToolbarProps {
  onZoomIn: () => void
  onZoomOut: () => void
  onCenter: () => void
  onExport: () => void
  is3D: boolean
  onToggle3D: () => void
  className?: string
}

export function GraphToolbar({
  onZoomIn,
  onZoomOut,
  onCenter,
  onExport,
  is3D,
  onToggle3D,
  className,
}: GraphToolbarProps) {
  const buttonClass = 'p-2 hover:bg-zinc-800 rounded transition-colors'

  return (
    <div className={cn('flex items-center gap-1 p-1 bg-zinc-900 border border-zinc-800 rounded-lg', className)}>
      <button onClick={onZoomIn} className={buttonClass} title="Zoom In">
        <ZoomIn size={16} />
      </button>
      <button onClick={onZoomOut} className={buttonClass} title="Zoom Out">
        <ZoomOut size={16} />
      </button>
      <button onClick={onCenter} className={buttonClass} title="Center">
        <Maximize2 size={16} />
      </button>
      <div className="w-px h-4 bg-zinc-700 mx-1" />
      <button onClick={onToggle3D} className={cn(buttonClass, is3D && 'bg-zinc-800')} title="Toggle 3D">
        <Box size={16} />
      </button>
      <div className="w-px h-4 bg-zinc-700 mx-1" />
      <button onClick={onExport} className={buttonClass} title="Export PNG">
        <Download size={16} />
      </button>
    </div>
  )
}
