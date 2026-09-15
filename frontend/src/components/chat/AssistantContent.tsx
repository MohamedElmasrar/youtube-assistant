"use client";

import { useMemo } from "react";
import ReactMarkdown, { type Components } from "react-markdown";
import { CitationLink } from "@/components/chat/CitationLink";
import { CITE_PREFIX, linkCitations } from "@/lib/chat/messages";
import type { Citation } from "@/types/chat";

interface AssistantContentProps {
  text: string;
  citations: Citation[];
}

/** Markdown answer with validated `[[chunk_id]]` markers rendered as clickable timestamps. */
export function AssistantContent({ text, citations }: AssistantContentProps) {
  const components = useMemo<Components>(() => {
    const byId = new Map(citations.map((c) => [c.chunk_id, c]));
    return {
      a({ href, children }) {
        if (href?.startsWith(CITE_PREFIX)) {
          const citation = byId.get(href.slice(CITE_PREFIX.length));
          return citation ? <CitationLink citation={citation} /> : null;
        }
        return (
          <a href={href} target="_blank" rel="noopener noreferrer">
            {children}
          </a>
        );
      },
    };
  }, [citations]);

  return (
    <div className="prose prose-sm dark:prose-invert max-w-none break-words prose-p:my-2 prose-ul:my-2 prose-ol:my-2">
      <ReactMarkdown components={components}>{linkCitations(text, citations)}</ReactMarkdown>
    </div>
  );
}
