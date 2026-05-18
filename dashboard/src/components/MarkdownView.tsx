import { useEffect, useRef } from 'react'
import { marked } from 'marked'

interface Props {
  content: string
  className?: string
}

export default function MarkdownView({ content, className = '' }: Props) {
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (ref.current) {
      ref.current.innerHTML = marked.parse(content) as string
    }
  }, [content])

  return (
    <div
      ref={ref}
      className={`prose prose-invert prose-sm max-w-none
        prose-headings:text-cyan-400 prose-headings:font-mono
        prose-code:text-amber-300 prose-code:bg-slate-800 prose-code:px-1 prose-code:rounded
        prose-pre:bg-slate-800 prose-pre:border prose-pre:border-slate-700
        prose-a:text-cyan-400 prose-a:no-underline hover:prose-a:underline
        prose-strong:text-slate-200
        prose-blockquote:border-cyan-800 prose-blockquote:text-slate-400
        ${className}`}
    />
  )
}
