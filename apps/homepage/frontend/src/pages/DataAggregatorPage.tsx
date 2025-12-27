export function DataAggregatorPage() {
  const isDev = typeof window !== 'undefined' && window.location.hostname === 'localhost'
  const datAppUrl = isDev ? 'http://localhost:5173' : '/dat-app'
  
  return (
    <div className="w-full h-screen">
      <iframe
        src={datAppUrl}
        className="w-full h-full border-0"
        title="Data Aggregator"
        allow="same-origin"
      />
    </div>
  )
}
