import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import App from '../App'

const createTestQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  })

const renderWithProviders = (ui: React.ReactElement) => {
  const queryClient = createTestQueryClient()
  return render(
    <QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>
  )
}

describe('App', () => {
  it('renders the header', () => {
    renderWithProviders(<App />)
    expect(screen.getByText('Data Aggregator')).toBeInTheDocument()
  })

  it('shows create run button when no run is active', () => {
    renderWithProviders(<App />)
    expect(screen.getByText('Create New Run')).toBeInTheDocument()
  })

  it('displays all stage labels in sidebar', () => {
    renderWithProviders(<App />)
    
    const stages = [
      'File Selection',
      'Context',
      'Table Availability',
      'Table Selection',
      'Preview',
      'Parse',
      'Export',
    ]
    
    stages.forEach(stage => {
      expect(screen.getByText(stage)).toBeInTheDocument()
    })
  })
})
