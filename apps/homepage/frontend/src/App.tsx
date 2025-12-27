import { Routes, Route } from 'react-router-dom'
import { Layout } from './components/Layout'
import { HomePage } from './pages/HomePage'
import { DatasetsPage } from './pages/DatasetsPage'
import { DataSetDetailsPage } from './pages/DataSetDetailsPage'
import { PipelinesPage } from './pages/PipelinesPage'
import { PipelineBuilderPage } from './pages/PipelineBuilderPage'
import { PipelineDetailsPage } from './pages/PipelineDetailsPage'
import { ToolPlaceholder } from './pages/ToolPlaceholder'

function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/datasets" element={<DatasetsPage />} />
        <Route path="/datasets/:id" element={<DataSetDetailsPage />} />
        <Route path="/pipelines" element={<PipelinesPage />} />
        <Route path="/pipelines/new" element={<PipelineBuilderPage />} />
        <Route path="/pipelines/:id" element={<PipelineDetailsPage />} />
        <Route path="/tools/pptx" element={<ToolPlaceholder tool="pptx" />} />
        <Route path="/tools/dat" element={<ToolPlaceholder tool="dat" />} />
        <Route path="/tools/sov" element={<ToolPlaceholder tool="sov" />} />
      </Routes>
    </Layout>
  )
}

export default App
