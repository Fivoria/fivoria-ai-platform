'use client';

import { useState, useEffect, useRef } from 'react';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Terminal, X, Maximize2, Minimize2 } from 'lucide-react';
import { wsClient } from '@/lib/websocket-client';
import { cn } from '@/lib/utils';

interface TerminalPanelProps {
  projectId: string;
  onClose?: () => void;
}

export function TerminalPanel({ projectId, onClose }: TerminalPanelProps) {
  const [output, setOutput] = useState<string[]>([]);
  const [input, setInput] = useState('');
  const [isMaximized, setIsMaximized] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    // Set up WebSocket listeners for terminal output
    const handleOutput = (data: { project_id: string; output: string }) => {
      if (data.project_id === projectId) {
        setOutput(prev => [...prev, data.output]);
      }
    };

    const handleError = (data: { project_id: string; error: string }) => {
      if (data.project_id === projectId) {
        setOutput(prev => [...prev, `\x1b[31m${data.error}\x1b[0m`]);
      }
    };

    wsClient.onTerminalOutput(handleOutput);
    wsClient.onTerminalError(handleError);

    return () => {
      wsClient.off('terminal.output', handleOutput);
      wsClient.off('terminal.error', handleError);
    };
  }, [projectId]);

  useEffect(() => {
    // Auto-scroll to bottom
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [output]);

  const handleExecute = () => {
    if (!input.trim()) return;

    // Add command to output
    setOutput(prev => [...prev, `$ ${input}`]);

    // Send via WebSocket
    wsClient.sendTerminalInput(projectId, input);

    setInput('');
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleExecute();
    }
  };

  const handleClear = () => {
    setOutput([]);
  };

  return (
    <div className={cn(
      "flex flex-col bg-card border-t",
      isMaximized ? "fixed inset-0 z-50" : "h-48"
    )}>
      {/* Header */}
      <div className="h-10 border-b flex items-center justify-between px-4 bg-muted">
        <div className="flex items-center gap-2">
          <Terminal className="h-4 w-4" />
          <span className="text-sm font-semibold">Terminal</span>
        </div>
        <div className="flex items-center gap-1">
          <Button
            size="icon"
            variant="ghost"
            className="h-7 w-7"
            onClick={() => setIsMaximized(!isMaximized)}
          >
            {isMaximized ? (
              <Minimize2 className="h-3 w-3" />
            ) : (
              <Maximize2 className="h-3 w-3" />
            )}
          </Button>
          <Button
            size="icon"
            variant="ghost"
            className="h-7 w-7"
            onClick={handleClear}
            title="Clear"
          >
            Clear
          </Button>
          {onClose && (
            <Button
              size="icon"
              variant="ghost"
              className="h-7 w-7"
              onClick={onClose}
            >
              <X className="h-3 w-3" />
            </Button>
          )}
        </div>
      </div>

      {/* Output Area */}
      <ScrollArea className="flex-1 p-2 font-mono text-sm bg-muted" ref={scrollRef}>
        <div className="space-y-0.5">
          {output.length === 0 ? (
            <p className="text-muted-foreground">Terminal ready. Type a command to execute.</p>
          ) : (
            output.map((line, idx) => (
              <div key={idx} className="whitespace-pre-wrap break-words">
                {line}
              </div>
            ))
          )}
        </div>
      </ScrollArea>

      {/* Input Area */}
      <div className="p-2 border-t bg-background">
        <div className="flex gap-2">
          <span className="text-green-500 font-mono">$</span>
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Enter command..."
            className="flex-1 bg-transparent outline-none font-mono text-sm"
            disabled={!projectId}
          />
        </div>
      </div>
    </div>
  );
}
