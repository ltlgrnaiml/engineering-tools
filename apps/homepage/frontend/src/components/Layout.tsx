import { ReactNode } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { Home, Database, GitBranch, FileSpreadsheet, BarChart3, Presentation } from 'lucide-react'
import { cn } from '@/lib/utils'
import { HealthIndicator } from './HealthIndicator'

interface LayoutProps {
  children: ReactNode
}

const navItems = [
  { path: '/', label: 'Home', icon: Home },
  { path: '/datasets', label: 'DataSets', icon: Database },
  { path: '/pipelines', label: 'Pipelines', icon: GitBranch },
]

const toolItems = [
  { path: '/tools/dat', label: 'Data Aggregator', icon: FileSpreadsheet, color: 'text-emerald-600' },
  { path: '/tools/pptx', label: 'PPTX Generator', icon: Presentation, color: 'text-orange-600' },
  { path: '/tools/sov', label: 'SOV Analyzer', icon: BarChart3, color: 'text-purple-600' },
]

export function Layout({ children }: LayoutProps) {
  const location = useLocation()

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="bg-white border-b border-slate-200 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-8">
              <Link to="/" className="flex items-center gap-2">
                <div className="w-8 h-8 bg-primary-600 rounded-lg flex items-center justify-center">
                  <span className="text-white font-bold text-sm">ET</span>
                </div>
                <span className="font-semibold text-slate-900">Engineering Tools</span>
              </Link>

              <nav className="hidden md:flex items-center gap-1">
                {navItems.map((item) => (
                  <Link
                    key={item.path}
                    to={item.path}
                    className={cn(
                      'flex items-center gap-2 px-3 py-2 rounded-md text-sm font-medium transition-colors',
                      location.pathname === item.path
                        ? 'bg-primary-50 text-primary-700'
                        : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
                    )}
                  >
                    <item.icon className="w-4 h-4" />
                    {item.label}
                  </Link>
                ))}
              </nav>
            </div>

            <div className="flex items-center gap-4">
              <HealthIndicator />
              <div className="flex items-center gap-2">
              {toolItems.map((item) => (
                <Link
                  key={item.path}
                  to={item.path}
                  className={cn(
                    'flex items-center gap-2 px-3 py-2 rounded-md text-sm font-medium transition-colors',
                    location.pathname.startsWith(item.path)
                      ? 'bg-slate-100 text-slate-900'
                      : 'text-slate-600 hover:bg-slate-100'
                  )}
                >
                  <item.icon className={cn('w-4 h-4', item.color)} />
                  <span className="hidden lg:inline">{item.label}</span>
                </Link>
              ))}
              </div>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {children}
      </main>
    </div>
  )
}
