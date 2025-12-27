export function SOVAnalyzerPage() {
  const isDev = typeof window !== 'undefined' && window.location.hostname === 'localhost'
  const sovAppUrl = isDev ? 'http://localhost:5174' : '/sov-app'
  
  return (
    <div className="w-full h-screen">
      <iframe
        src={sovAppUrl}
        className="w-full h-full border-0"
        title="SOV Analyzer"
        allow="same-origin"
      />
    </div>
  )
}
