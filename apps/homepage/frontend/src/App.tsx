import { Routes, Route, useLocation } from 'react-router-dom'
import { Layout } from './components/Layout'
import { HomePage } from './pages/HomePage'
import { DatasetsPage } from './pages/DatasetsPage'
import { DataSetDetailsPage } from './pages/DataSetDetailsPage'
import { PipelinesPage } from './pages/PipelinesPage'
import { PipelineBuilderPage } from './pages/PipelineBuilderPage'
import { PipelineDetailsPage } from './pages/PipelineDetailsPage'
import { DataAggregatorPage } from './pages/DataAggregatorPage'
import { PPTXGeneratorPage } from './pages/PPTXGeneratorPage'
import { SOVAnalyzerPage } from './pages/SOVAnalyzerPage'
import { DevToolsPage } from './pages/DevToolsPage'
import { WorkflowManagerPage } from './pages/WorkflowManagerPage'

function AppContent() {
  const location = useLocation()
  const isToolPage = location.pathname.startsWith('/tools/')

  const isDevToolsPage = location.pathname.startsWith('/devtools')

  const isWorkflowPage = location.pathname.startsWith('/workflow')

  if (isWorkflowPage) {
    return (
      <Routes>
        <Route path="/workflow" element={<WorkflowManagerPage />} />
      </Routes>
    )
  }

  if (isDevToolsPage) {
    return (
      <Routes>
        <Route path="/devtools" element={<DevToolsPage />} />
      </Routes>
    )
  }

  if (isToolPage) {
    return (
      <Routes>
        <Route path="/tools/dat" element={<DataAggregatorPage />} />
        <Route path="/tools/pptx" element={<PPTXGeneratorPage />} />
        <Route path="/tools/sov" element={<SOVAnalyzerPage />} />
      </Routes>
    )
  }

  return (
    <Layout>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/datasets" element={<DatasetsPage />} />
        <Route path="/datasets/:id" element={<DataSetDetailsPage />} />
        <Route path="/pipelines" element={<PipelinesPage />} />
        <Route path="/pipelines/new" element={<PipelineBuilderPage />} />
        <Route path="/pipelines/:id" element={<PipelineDetailsPage />} />
      </Routes>
    </Layout>
  )
}

function App() {
  return <AppContent />
}

export default App
