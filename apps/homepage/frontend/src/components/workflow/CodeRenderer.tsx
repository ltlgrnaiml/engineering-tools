import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism'
import { cn } from '@/lib/utils'

interface CodeRendererProps {
  code: string
  language: string
  className?: string
}

export function CodeRenderer({ code, language, className }: CodeRendererProps) {
  return (
    <div className={cn('text-sm rounded overflow-hidden', className)}>
      <SyntaxHighlighter language={language} style={oneDark} customStyle={{ margin: 0, borderRadius: 8 }}>
        {code}
      </SyntaxHighlighter>
    </div>
  )
}
