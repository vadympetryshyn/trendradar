"use client";

import ReactMarkdown from "react-markdown";
import type { Components } from "react-markdown";

interface MarkdownContentProps {
  content: string;
  citations?: string[];
}

export function MarkdownContent({ content, citations = [] }: MarkdownContentProps) {
  // Replace [1], [2], etc. with clickable markdown links pointing to #source-N
  const processedContent = citations.length > 0
    ? content.replace(/\[(\d+)\]/g, (match, num) => {
        const index = parseInt(num, 10) - 1;
        if (index >= 0 && index < citations.length) {
          return `[\\[${num}\\]](${citations[index]})`;
        }
        return match;
      })
    : content;

  const components: Components = {
    a: ({ href, children, ...props }) => (
      <a
        href={href}
        target="_blank"
        rel="noopener noreferrer"
        className="text-blue-500 hover:text-blue-700 hover:underline"
        {...props}
      >
        {children}
      </a>
    ),
    p: ({ children, ...props }) => (
      <p className="mb-3 last:mb-0" {...props}>{children}</p>
    ),
    ul: ({ children, ...props }) => (
      <ul className="list-disc pl-5 mb-3 space-y-1" {...props}>{children}</ul>
    ),
    ol: ({ children, ...props }) => (
      <ol className="list-decimal pl-5 mb-3 space-y-1" {...props}>{children}</ol>
    ),
    li: ({ children, ...props }) => (
      <li className="text-sm leading-relaxed" {...props}>{children}</li>
    ),
    strong: ({ children, ...props }) => (
      <strong className="font-semibold" {...props}>{children}</strong>
    ),
    h1: ({ children, ...props }) => (
      <h3 className="font-semibold text-base mt-4 mb-2" {...props}>{children}</h3>
    ),
    h2: ({ children, ...props }) => (
      <h3 className="font-semibold text-base mt-4 mb-2" {...props}>{children}</h3>
    ),
    h3: ({ children, ...props }) => (
      <h4 className="font-semibold text-sm mt-3 mb-1" {...props}>{children}</h4>
    ),
    blockquote: ({ children, ...props }) => (
      <blockquote className="border-l-2 border-muted-foreground/30 pl-4 italic text-muted-foreground my-3" {...props}>
        {children}
      </blockquote>
    ),
  };

  return (
    <div className="text-sm leading-relaxed">
      <ReactMarkdown components={components}>
        {processedContent}
      </ReactMarkdown>

      {citations.length > 0 && (
        <div className="mt-6 pt-4 border-t border-border">
          <h4 className="text-sm font-semibold mb-2 text-muted-foreground">Sources</h4>
          <ol className="space-y-1">
            {citations.map((url, i) => (
              <li key={i} className="text-xs flex gap-1.5">
                <span className="text-muted-foreground shrink-0">[{i + 1}]</span>
                <a
                  href={url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-500 hover:text-blue-700 hover:underline truncate"
                >
                  {url}
                </a>
              </li>
            ))}
          </ol>
        </div>
      )}
    </div>
  );
}
