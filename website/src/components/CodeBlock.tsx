import { useState } from 'react'

interface CodeBlockProps {
  code: string
  language?: string
  title?: string
  showLineNumbers?: boolean
}

export default function CodeBlock({ code, language = 'bash', title, showLineNumbers = false }: CodeBlockProps) {
  const [copied, setCopied] = useState(false)

  const handleCopy = () => {
    navigator.clipboard.writeText(code)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const lines = code.trim().split('\n')

  return (
    <div className="my-6 rounded-lg overflow-hidden shadow-lg border border-gray-700">
      {/* Terminal Header */}
      <div className="bg-gray-800 px-4 py-2 flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <div className="flex space-x-2">
            <div className="w-3 h-3 rounded-full bg-red-500"></div>
            <div className="w-3 h-3 rounded-full bg-yellow-500"></div>
            <div className="w-3 h-3 rounded-full bg-green-500"></div>
          </div>
          {title && (
            <span className="ml-3 text-sm text-gray-300 font-mono">{title}</span>
          )}
        </div>
        <button
          onClick={handleCopy}
          className="flex items-center space-x-1 text-gray-400 hover:text-white transition-colors"
        >
          {copied ? (
            <>
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7"></path>
              </svg>
              <span className="text-xs">Copied!</span>
            </>
          ) : (
            <>
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 5H6a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2v-1M8 5a2 2 0 002 2h2a2 2 0 002-2M8 5a2 2 0 012-2h2a2 2 0 012 2m0 0h2a2 2 0 012 2v3m2 4H10m0 0l3-3m-3 3l3 3"></path>
              </svg>
              <span className="text-xs">Copy</span>
            </>
          )}
        </button>
      </div>
      
      {/* Code Content */}
      <div className="bg-gray-900 p-4 overflow-x-auto">
        <pre className="text-sm text-gray-300 font-mono">
          {lines.map((line, index) => (
            <div key={index} className="flex">
              {showLineNumbers && (
                <span className="text-gray-500 select-none pr-4 text-right" style={{ minWidth: '2.5rem' }}>
                  {index + 1}
                </span>
              )}
              <span className="flex-1 whitespace-pre">
                {language === 'bash' && line.startsWith('$') ? (
                  <>
                    <span className="text-green-400">$</span>
                    <span>{line.substring(1)}</span>
                  </>
                ) : language === 'bash' && line.startsWith('#') ? (
                  <span className="text-gray-500">{line}</span>
                ) : (
                  line
                )}
              </span>
            </div>
          ))}
        </pre>
      </div>
    </div>
  )
}