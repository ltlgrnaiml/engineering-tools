import ReactMarkdown from 'react-markdown'
import { cn } from '@/lib/utils'

interface MarkdownRendererProps {
  content: string
  className?: string
}

export function MarkdownRenderer({ content, className }: MarkdownRendererProps) {
  return (
    <div className={cn('max-w-none text-zinc-300', className)}>
      <ReactMarkdown
        components={{
          h1: ({ children }) => <h1 className="text-2xl font-bold text-white mb-4 mt-6 border-b border-zinc-700 pb-2">{children}</h1>,
          h2: ({ children }) => <h2 className="text-xl font-semibold text-white mb-3 mt-5">{children}</h2>,
          h3: ({ children }) => <h3 className="text-lg font-semibold text-zinc-200 mb-2 mt-4">{children}</h3>,
          h4: ({ children }) => <h4 className="text-base font-medium text-zinc-200 mb-2 mt-3">{children}</h4>,
          p: ({ children }) => <p className="mb-3 leading-relaxed">{children}</p>,
          ul: ({ children }) => <ul className="list-disc list-inside mb-3 space-y-1 ml-2">{children}</ul>,
          ol: ({ children }) => <ol className="list-decimal list-inside mb-3 space-y-1 ml-2">{children}</ol>,
          li: ({ children }) => <li className="text-zinc-300">{children}</li>,
          code: ({ className, children, ...props }) => {
            const isInline = !className
            return isInline ? (
              <code className="bg-zinc-800 text-amber-300 px-1.5 py-0.5 rounded text-sm font-mono">{children}</code>
            ) : (
              <code className={cn('block bg-zinc-900 p-3 rounded-lg text-sm font-mono overflow-x-auto my-3', className)} {...props}>{children}</code>
            )
          },
          pre: ({ children }) => <pre className="bg-zinc-900 rounded-lg overflow-x-auto my-3">{children}</pre>,
          blockquote: ({ children }) => <blockquote className="border-l-4 border-blue-500 pl-4 italic text-zinc-400 my-3">{children}</blockquote>,
          a: ({ href, children }) => <a href={href} className="text-blue-400 hover:text-blue-300 underline">{children}</a>,
          strong: ({ children }) => <strong className="font-semibold text-white">{children}</strong>,
          em: ({ children }) => <em className="italic text-zinc-200">{children}</em>,
          hr: () => <hr className="border-zinc-700 my-6" />,
          table: ({ children }) => <table className="w-full border-collapse my-4">{children}</table>,
          th: ({ children }) => <th className="border border-zinc-700 bg-zinc-800 px-3 py-2 text-left font-semibold text-zinc-200">{children}</th>,
          td: ({ children }) => <td className="border border-zinc-700 px-3 py-2">{children}</td>,
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  )
}
