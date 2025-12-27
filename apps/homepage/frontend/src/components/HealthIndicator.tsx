import { Activity, CheckCircle, AlertTriangle, XCircle } from 'lucide-react'
import { useHealth } from '@/hooks/useHealth'
import { cn } from '@/lib/utils'

const statusConfig = {
  healthy: {
    icon: CheckCircle,
    color: 'text-green-500',
    bgColor: 'bg-green-50',
    label: 'All Systems Operational',
  },
  degraded: {
    icon: AlertTriangle,
    color: 'text-yellow-500',
    bgColor: 'bg-yellow-50',
    label: 'Some Services Degraded',
  },
  unhealthy: {
    icon: XCircle,
    color: 'text-red-500',
    bgColor: 'bg-red-50',
    label: 'System Issues Detected',
  },
}

interface HealthIndicatorProps {
  showLabel?: boolean
  className?: string
}

export function HealthIndicator({ showLabel = false, className }: HealthIndicatorProps) {
  const { data: health, isLoading, error } = useHealth()

  if (isLoading) {
    return (
      <div className={cn('flex items-center gap-2', className)}>
        <Activity className="w-4 h-4 text-slate-400 animate-pulse" />
        {showLabel && <span className="text-sm text-slate-400">Checking...</span>}
      </div>
    )
  }

  if (error || !health) {
    return (
      <div className={cn('flex items-center gap-2', className)}>
        <XCircle className="w-4 h-4 text-red-500" />
        {showLabel && <span className="text-sm text-red-500">Offline</span>}
      </div>
    )
  }

  const config = statusConfig[health.status]
  const Icon = config.icon

  return (
    <div
      className={cn(
        'flex items-center gap-2 px-2 py-1 rounded-full',
        config.bgColor,
        className
      )}
      title={config.label}
    >
      <Icon className={cn('w-4 h-4', config.color)} />
      {showLabel && (
        <span className={cn('text-sm font-medium', config.color)}>
          {config.label}
        </span>
      )}
    </div>
  )
}

export function HealthDashboard() {
  const { data: health, isLoading, error } = useHealth()

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg border border-slate-200 p-4">
        <div className="animate-pulse flex items-center gap-2">
          <div className="w-4 h-4 bg-slate-200 rounded-full" />
          <div className="h-4 bg-slate-200 rounded w-32" />
        </div>
      </div>
    )
  }

  if (error || !health) {
    return (
      <div className="bg-red-50 rounded-lg border border-red-200 p-4">
        <div className="flex items-center gap-2 text-red-700">
          <XCircle className="w-5 h-5" />
          <span className="font-medium">Unable to connect to gateway</span>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg border border-slate-200 p-4">
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-semibold text-slate-900">System Health</h3>
        <HealthIndicator />
      </div>
      
      <div className="space-y-3">
        <div className="flex items-center justify-between text-sm">
          <span className="text-slate-600">Version</span>
          <span className="font-mono text-slate-900">{health.version}</span>
        </div>

        <div className="border-t border-slate-100 pt-3">
          <span className="text-xs font-medium text-slate-500 uppercase">Tools</span>
          <div className="mt-2 space-y-2">
            {Object.entries(health.tools).map(([tool, status]) => (
              <div key={tool} className="flex items-center justify-between text-sm">
                <span className="text-slate-700 capitalize">{tool}</span>
                <ToolStatusBadge status={status} />
              </div>
            ))}
          </div>
        </div>

        {health.storage && (
          <div className="border-t border-slate-100 pt-3">
            <span className="text-xs font-medium text-slate-500 uppercase">Storage</span>
            <div className="mt-2 grid grid-cols-3 gap-2 text-sm">
              <div>
                <div className="text-slate-500">DataSets</div>
                <div className="font-medium text-slate-900">{health.storage.datasets}</div>
              </div>
              <div>
                <div className="text-slate-500">Pipelines</div>
                <div className="font-medium text-slate-900">{health.storage.pipelines}</div>
              </div>
              <div>
                <div className="text-slate-500">Size</div>
                <div className="font-medium text-slate-900">{health.storage.total_size_mb.toFixed(1)} MB</div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

function ToolStatusBadge({ status }: { status: string }) {
  const configs: Record<string, { label: string; className: string }> = {
    available: { label: 'Available', className: 'bg-green-100 text-green-700' },
    coming_soon: { label: 'Coming Soon', className: 'bg-slate-100 text-slate-600' },
    maintenance: { label: 'Maintenance', className: 'bg-yellow-100 text-yellow-700' },
    error: { label: 'Error', className: 'bg-red-100 text-red-700' },
  }

  const config = configs[status] || configs.error

  return (
    <span className={cn('px-2 py-0.5 rounded-full text-xs font-medium', config.className)}>
      {config.label}
    </span>
  )
}
