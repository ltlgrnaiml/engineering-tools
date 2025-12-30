import { useState, useEffect, useCallback } from 'react'
import { cn } from '@/lib/utils'

interface DiscussionEditorFormProps {
  content: string
  onChange: (content: string) => void
  className?: string
}

export function DiscussionEditorForm({ content, onChange, className }: DiscussionEditorFormProps) {
  const [title, setTitle] = useState('')
  const [status, setStatus] = useState('open')
  const [participants, setParticipants] = useState('')
  const [summary, setSummary] = useState('')
  const [questions, setQuestions] = useState('')
  const [decisions, setDecisions] = useState('')
  const [nextSteps, setNextSteps] = useState('')
  const [body, setBody] = useState('')

  useEffect(() => {
    // Parse markdown content
    const lines = content.split('\n')
    let currentSection = 'body'
    const sections: Record<string, string[]> = {
      body: [],
      summary: [],
      questions: [],
      decisions: [],
      nextSteps: [],
    }

    for (const line of lines) {
      if (line.startsWith('# ')) {
        setTitle(line.replace('# ', ''))
      } else if (line.toLowerCase().includes('status:')) {
        const match = line.match(/status:\s*(\w+)/i)
        if (match) setStatus(match[1].toLowerCase())
      } else if (line.toLowerCase().includes('participants:')) {
        const match = line.match(/participants:\s*(.+)/i)
        if (match) setParticipants(match[1])
      } else if (line.startsWith('## Summary')) {
        currentSection = 'summary'
      } else if (line.startsWith('## Open Questions')) {
        currentSection = 'questions'
      } else if (line.startsWith('## Decisions')) {
        currentSection = 'decisions'
      } else if (line.startsWith('## Next Steps')) {
        currentSection = 'nextSteps'
      } else if (!line.startsWith('## ')) {
        sections[currentSection].push(line)
      }
    }

    setSummary(sections.summary.join('\n').trim())
    setQuestions(sections.questions.join('\n').trim())
    setDecisions(sections.decisions.join('\n').trim())
    setNextSteps(sections.nextSteps.join('\n').trim())
    setBody(sections.body.join('\n').trim())
  }, [content])

  const generateMarkdown = useCallback(() => {
    const parts = [
      `# ${title}`,
      '',
      `**Status**: ${status}`,
      `**Participants**: ${participants}`,
      '',
    ]

    if (summary) {
      parts.push('## Summary', '', summary, '')
    }
    if (questions) {
      parts.push('## Open Questions', '', questions, '')
    }
    if (decisions) {
      parts.push('## Decisions', '', decisions, '')
    }
    if (nextSteps) {
      parts.push('## Next Steps', '', nextSteps, '')
    }
    if (body) {
      parts.push('## Discussion', '', body, '')
    }

    return parts.join('\n')
  }, [title, status, participants, summary, questions, decisions, nextSteps, body])

  useEffect(() => {
    const newContent = generateMarkdown()
    if (newContent !== content) {
      onChange(newContent)
    }
  }, [title, status, participants, summary, questions, decisions, nextSteps, body, generateMarkdown, onChange, content])

  const inputClass = 'w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded focus:outline-none focus:border-blue-500 text-sm'
  const labelClass = 'block text-sm text-zinc-400 mb-1'

  return (
    <div className={cn('p-4 space-y-6 overflow-auto h-full', className)}>
      {/* Header */}
      <section>
        <h3 className="text-lg font-medium text-zinc-200 mb-3 border-b border-zinc-700 pb-2">Discussion Details</h3>
        <div>
          <label htmlFor="disc-title" className={labelClass}>Title</label>
          <input
            id="disc-title"
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            className={inputClass}
            aria-label="Discussion title"
          />
        </div>
        <div className="grid grid-cols-2 gap-4 mt-4">
          <div>
            <label htmlFor="disc-status" className={labelClass}>Status</label>
            <select
              id="disc-status"
              value={status}
              onChange={(e) => setStatus(e.target.value)}
              className={inputClass}
              aria-label="Discussion status"
            >
              <option value="open">Open</option>
              <option value="active">Active</option>
              <option value="resolved">Resolved</option>
              <option value="closed">Closed</option>
            </select>
          </div>
          <div>
            <label htmlFor="disc-participants" className={labelClass}>Participants</label>
            <input
              id="disc-participants"
              type="text"
              value={participants}
              onChange={(e) => setParticipants(e.target.value)}
              className={inputClass}
              placeholder="Team members involved"
              aria-label="Participants"
            />
          </div>
        </div>
      </section>

      {/* Summary */}
      <section>
        <h3 className="text-lg font-medium text-zinc-200 mb-3 border-b border-zinc-700 pb-2">Summary</h3>
        <textarea
          value={summary}
          onChange={(e) => setSummary(e.target.value)}
          rows={4}
          className={inputClass}
          placeholder="Brief summary of the discussion topic..."
          aria-label="Summary"
        />
      </section>

      {/* Open Questions */}
      <section>
        <h3 className="text-lg font-medium text-zinc-200 mb-3 border-b border-zinc-700 pb-2">Open Questions</h3>
        <textarea
          value={questions}
          onChange={(e) => setQuestions(e.target.value)}
          rows={4}
          className={inputClass}
          placeholder="- Question 1?&#10;- Question 2?"
          aria-label="Open questions"
        />
      </section>

      {/* Decisions */}
      <section>
        <h3 className="text-lg font-medium text-zinc-200 mb-3 border-b border-zinc-700 pb-2">Decisions Made</h3>
        <textarea
          value={decisions}
          onChange={(e) => setDecisions(e.target.value)}
          rows={4}
          className={inputClass}
          placeholder="- Decision 1&#10;- Decision 2"
          aria-label="Decisions made"
        />
      </section>

      {/* Next Steps */}
      <section>
        <h3 className="text-lg font-medium text-zinc-200 mb-3 border-b border-zinc-700 pb-2">Next Steps</h3>
        <textarea
          value={nextSteps}
          onChange={(e) => setNextSteps(e.target.value)}
          rows={4}
          className={inputClass}
          placeholder="- [ ] Action item 1&#10;- [ ] Action item 2"
          aria-label="Next steps"
        />
      </section>

      {/* Additional Notes */}
      <section>
        <h3 className="text-lg font-medium text-zinc-200 mb-3 border-b border-zinc-700 pb-2">Additional Notes</h3>
        <textarea
          value={body}
          onChange={(e) => setBody(e.target.value)}
          rows={8}
          className={inputClass}
          placeholder="Any additional discussion notes..."
          aria-label="Additional notes"
        />
      </section>
    </div>
  )
}
