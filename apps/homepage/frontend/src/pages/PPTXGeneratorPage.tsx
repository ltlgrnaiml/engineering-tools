export function PPTXGeneratorPage() {
  const isDev = typeof window !== 'undefined' && window.location.hostname === 'localhost'
  const pptxAppUrl = isDev ? 'http://localhost:5175' : '/pptx-app'
  
  return (
    <div className="w-full h-screen">
      <iframe
        src={pptxAppUrl}
        className="w-full h-full border-0"
        title="PowerPoint Generator"
        allow="same-origin"
      />
    </div>
  )
}
