import { useState, useEffect, useCallback } from 'react'
import { Plus, Trash2 } from 'lucide-react'
import { cn } from '@/lib/utils'

interface PlanEditorFormProps {
  content: string
  onChange: (content: string) => void
  className?: string
}

interface Milestone {
  id: string
  title: string
  status: 'pending' | 'in_progress' | 'completed'
  tasks: string[]
}

export function PlanEditorForm({ content, onChange, className }: PlanEditorFormProps) {
  const [title, setTitle] = useState('')
  const [status, setStatus] = useState('draft')
  const [objective, setObjective] = useState('')
  const [scope, setScope] = useState('')
  const [milestones, setMilestones] = useState<Milestone[]>([])
  const [acceptanceCriteria, setAcceptanceCriteria] = useState('')
  const [risks, setRisks] = useState('')

  useEffect(() => {
    // Parse markdown content
    const lines = content.split('\n')
    let currentSection = ''
    let currentMilestone: Milestone | null = null
    const parsedMilestones: Milestone[] = []

    for (const line of lines) {
      if (line.startsWith('# ')) {
        setTitle(line.replace('# ', ''))
      } else if (line.toLowerCase().includes('status:')) {
        const match = line.match(/status:\s*(\w+)/i)
        if (match) setStatus(match[1].toLowerCase())
      } else if (line.startsWith('## Objective')) {
        currentSection = 'objective'
      } else if (line.startsWith('## Scope')) {
        currentSection = 'scope'
      } else if (line.startsWith('## Milestones')) {
        currentSection = 'milestones'
      } else if (line.startsWith('### M')) {
        if (currentMilestone) parsedMilestones.push(currentMilestone)
        const match = line.match(/### (M\d+):\s*(.+)/)
        currentMilestone = {
          id: match?.[1] || `M${parsedMilestones.length + 1}`,
          title: match?.[2] || '',
          status: 'pending',
          tasks: [],
        }
      } else if (line.startsWith('## Acceptance Criteria')) {
        if (currentMilestone) parsedMilestones.push(currentMilestone)
        currentMilestone = null
        currentSection = 'acceptance'
      } else if (line.startsWith('## Risks')) {
        currentSection = 'risks'
      } else if (currentSection === 'objective' && line.trim()) {
        setObjective((prev) => (prev ? prev + '\n' + line : line))
      } else if (currentSection === 'scope' && line.trim()) {
        setScope((prev) => (prev ? prev + '\n' + line : line))
      } else if (currentMilestone && line.startsWith('- ')) {
        currentMilestone.tasks.push(line.replace('- ', '').replace(/^\[.\]\s*/, ''))
      } else if (currentSection === 'acceptance' && line.startsWith('- ')) {
        setAcceptanceCriteria((prev) => (prev ? prev + '\n' + line : line))
      } else if (currentSection === 'risks' && line.startsWith('- ')) {
        setRisks((prev) => (prev ? prev + '\n' + line : line))
      }
    }

    if (currentMilestone) parsedMilestones.push(currentMilestone)
    if (parsedMilestones.length > 0) setMilestones(parsedMilestones)
  }, [content])

  const generateMarkdown = useCallback(() => {
    const parts = [
      `# ${title}`,
      '',
      `**Status**: ${status}`,
      '',
      '## Objective',
      '',
      objective,
      '',
      '## Scope',
      '',
      scope,
      '',
      '## Milestones',
      '',
    ]

    milestones.forEach((m) => {
      parts.push(`### ${m.id}: ${m.title}`)
      parts.push('')
      m.tasks.forEach((task) => {
        const checkbox = m.status === 'completed' ? '[x]' : '[ ]'
        parts.push(`- ${checkbox} ${task}`)
      })
      parts.push('')
    })

    if (acceptanceCriteria) {
      parts.push('## Acceptance Criteria', '', acceptanceCriteria, '')
    }
    if (risks) {
      parts.push('## Risks', '', risks, '')
    }

    return parts.join('\n')
  }, [title, status, objective, scope, milestones, acceptanceCriteria, risks])

  useEffect(() => {
    const newContent = generateMarkdown()
    if (newContent !== content) {
      onChange(newContent)
    }
  }, [generateMarkdown, onChange, content])

  const addMilestone = () => {
    setMilestones([...milestones, { id: `M${milestones.length + 1}`, title: '', status: 'pending', tasks: [] }])
  }

  const updateMilestone = (index: number, updates: Partial<Milestone>) => {
    const updated = [...milestones]
    updated[index] = { ...updated[index], ...updates }
    setMilestones(updated)
  }

  const removeMilestone = (index: number) => {
    setMilestones(milestones.filter((_, i) => i !== index))
  }

  const addTask = (milestoneIndex: number) => {
    const updated = [...milestones]
    updated[milestoneIndex].tasks.push('')
    setMilestones(updated)
  }

  const updateTask = (milestoneIndex: number, taskIndex: number, value: string) => {
    const updated = [...milestones]
    updated[milestoneIndex].tasks[taskIndex] = value
    setMilestones(updated)
  }

  const removeTask = (milestoneIndex: number, taskIndex: number) => {
    const updated = [...milestones]
    updated[milestoneIndex].tasks = updated[milestoneIndex].tasks.filter((_, i) => i !== taskIndex)
    setMilestones(updated)
  }

  const inputClass = 'w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded focus:outline-none focus:border-blue-500 text-sm'
  const labelClass = 'block text-sm text-zinc-400 mb-1'

  return (
    <div className={cn('p-4 space-y-6 overflow-auto h-full', className)}>
      {/* Header */}
      <section>
        <h3 className="text-lg font-medium text-zinc-200 mb-3 border-b border-zinc-700 pb-2">Plan Details</h3>
        <div>
          <label htmlFor="plan-title" className={labelClass}>Title</label>
          <input
            id="plan-title"
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            className={inputClass}
            aria-label="Plan title"
          />
        </div>
        <div className="mt-4">
          <label htmlFor="plan-status" className={labelClass}>Status</label>
          <select
            id="plan-status"
            value={status}
            onChange={(e) => setStatus(e.target.value)}
            className={inputClass}
            aria-label="Plan status"
          >
            <option value="draft">Draft</option>
            <option value="active">Active</option>
            <option value="completed">Completed</option>
            <option value="on_hold">On Hold</option>
          </select>
        </div>
      </section>

      {/* Objective */}
      <section>
        <h3 className="text-lg font-medium text-zinc-200 mb-3 border-b border-zinc-700 pb-2">Objective</h3>
        <textarea
          value={objective}
          onChange={(e) => setObjective(e.target.value)}
          rows={4}
          className={inputClass}
          placeholder="What this plan aims to achieve..."
          aria-label="Objective"
        />
      </section>

      {/* Scope */}
      <section>
        <h3 className="text-lg font-medium text-zinc-200 mb-3 border-b border-zinc-700 pb-2">Scope</h3>
        <textarea
          value={scope}
          onChange={(e) => setScope(e.target.value)}
          rows={3}
          className={inputClass}
          placeholder="What's in and out of scope..."
          aria-label="Scope"
        />
      </section>

      {/* Milestones */}
      <section>
        <h3 className="text-lg font-medium text-zinc-200 mb-3 border-b border-zinc-700 pb-2">Milestones</h3>
        <div className="space-y-4">
          {milestones.map((milestone, mIndex) => (
            <div key={mIndex} className="p-3 bg-zinc-800/50 rounded border border-zinc-700">
              <div className="flex gap-2 mb-2">
                <input
                  type="text"
                  value={milestone.id}
                  onChange={(e) => updateMilestone(mIndex, { id: e.target.value })}
                  className={cn(inputClass, 'w-20')}
                  placeholder="M1"
                  aria-label="Milestone ID"
                />
                <input
                  type="text"
                  value={milestone.title}
                  onChange={(e) => updateMilestone(mIndex, { title: e.target.value })}
                  className={cn(inputClass, 'flex-1')}
                  placeholder="Milestone title"
                  aria-label="Milestone title"
                />
                <select
                  value={milestone.status}
                  onChange={(e) => updateMilestone(mIndex, { status: e.target.value as Milestone['status'] })}
                  className={cn(inputClass, 'w-32')}
                  aria-label="Milestone status"
                >
                  <option value="pending">Pending</option>
                  <option value="in_progress">In Progress</option>
                  <option value="completed">Completed</option>
                </select>
                <button
                  type="button"
                  onClick={() => removeMilestone(mIndex)}
                  className="p-2 text-red-400 hover:bg-zinc-700 rounded"
                  aria-label="Remove milestone"
                >
                  <Trash2 size={16} />
                </button>
              </div>
              <div className="ml-4 space-y-2">
                {milestone.tasks.map((task, tIndex) => (
                  <div key={tIndex} className="flex gap-2">
                    <input
                      type="text"
                      value={task}
                      onChange={(e) => updateTask(mIndex, tIndex, e.target.value)}
                      className={cn(inputClass, 'flex-1')}
                      placeholder="Task description"
                      aria-label={`Task ${tIndex + 1}`}
                    />
                    <button
                      type="button"
                      onClick={() => removeTask(mIndex, tIndex)}
                      className="p-2 text-red-400 hover:bg-zinc-700 rounded"
                      aria-label="Remove task"
                    >
                      <Trash2 size={14} />
                    </button>
                  </div>
                ))}
                <button
                  type="button"
                  onClick={() => addTask(mIndex)}
                  className="flex items-center gap-1 text-sm text-blue-400 hover:text-blue-300"
                >
                  <Plus size={14} /> Add task
                </button>
              </div>
            </div>
          ))}
          <button
            type="button"
            onClick={addMilestone}
            className="flex items-center gap-1 text-sm text-blue-400 hover:text-blue-300"
          >
            <Plus size={14} /> Add milestone
          </button>
        </div>
      </section>

      {/* Acceptance Criteria */}
      <section>
        <h3 className="text-lg font-medium text-zinc-200 mb-3 border-b border-zinc-700 pb-2">Acceptance Criteria</h3>
        <textarea
          value={acceptanceCriteria}
          onChange={(e) => setAcceptanceCriteria(e.target.value)}
          rows={4}
          className={inputClass}
          placeholder="- AC-01: Criteria description&#10;- AC-02: Criteria description"
          aria-label="Acceptance criteria"
        />
      </section>

      {/* Risks */}
      <section>
        <h3 className="text-lg font-medium text-zinc-200 mb-3 border-b border-zinc-700 pb-2">Risks & Mitigations</h3>
        <textarea
          value={risks}
          onChange={(e) => setRisks(e.target.value)}
          rows={4}
          className={inputClass}
          placeholder="- Risk: Description → Mitigation"
          aria-label="Risks"
        />
      </section>
    </div>
  )
}
