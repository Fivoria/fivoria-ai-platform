'use client';

import { useState, useRef, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Send, Square, Loader2 } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeHighlight from 'rehype-highlight';
import rehypeRaw from 'rehype-raw';
import { wsClient } from '@/lib/websocket-client';
import type { Message, ToolCall, ReasoningStep, Citation, FileChange } from '@/types';
import 'highlight.js/styles/github-dark.css';

interface ChatInterfaceProps {
  conversationId: string;
  projectId?: string;
  onMessageAdd?: (message: Message) => void;
}

export function ChatInterface({ conversationId, projectId, onMessageAdd }: ChatInterfaceProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [currentResponse, setCurrentResponse] = useState('');
  const [toolCalls, setToolCalls] = useState<ToolCall[]>([]);
  const [reasoningSteps, setReasoningSteps] = useState<ReasoningStep[]>([]);
  const [citations, setCitations] = useState<Citation[]>([]);
  const [fileChanges, setFileChanges] = useState<FileChange[]>([]);
  const scrollRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    // Auto-scroll to bottom when new messages arrive
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, currentResponse]);

  useEffect(() => {
    // Set up WebSocket listeners
    const handleToken = (data: { token: string; conversation_id: string }) => {
      if (data.conversation_id === conversationId) {
        setCurrentResponse(prev => prev + data.token);
      }
    };

    const handleToolCall = (data: { tool_call: ToolCall; conversation_id: string }) => {
      if (data.conversation_id === conversationId) {
        setToolCalls(prev => [...prev, data.tool_call]);
      }
    };

    const handleDone = (data: { response: any; conversation_id: string }) => {
      if (data.conversation_id === conversationId) {
        const assistantMessage: Message = {
          id: `msg-${Date.now()}`,
          role: 'assistant',
          content: data.response.content || currentResponse,
          tool_calls: toolCalls,
          reasoning_steps: reasoningSteps,
          citations: citations,
          files_changed: fileChanges,
          timestamp: new Date().toISOString(),
        };
        
        setMessages(prev => [...prev, assistantMessage]);
        setCurrentResponse('');
        setToolCalls([]);
        setReasoningSteps([]);
        setCitations([]);
        setFileChanges([]);
        setIsStreaming(false);
        
        if (onMessageAdd) {
          onMessageAdd(assistantMessage);
        }
      }
    };

    const handleError = (data: { error: string; conversation_id: string }) => {
      if (data.conversation_id === conversationId) {
        setIsStreaming(false);
        setCurrentResponse('');
        setToolCalls([]);
        setReasoningSteps([]);
        setCitations([]);
        setFileChanges([]);
      }
    };

    wsClient.onChatToken(handleToken);
    wsClient.onChatToolCall(handleToolCall);
    wsClient.onChatDone(handleDone);
    wsClient.onChatError(handleError);

    return () => {
      wsClient.off('chat.token', handleToken);
      wsClient.off('chat.tool_call', handleToolCall);
      wsClient.off('chat.done', handleDone);
      wsClient.off('chat.error', handleError);
    };
  }, [conversationId, toolCalls, reasoningSteps, citations, fileChanges, currentResponse, onMessageAdd]);

  const handleSend = () => {
    if (!input.trim() || isStreaming) return;

    const userMessage: Message = {
      id: `msg-${Date.now()}`,
      role: 'user',
      content: input,
      timestamp: new Date().toISOString(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsStreaming(true);

    // Send via WebSocket
    wsClient.sendChatStart({
      conversation_id: conversationId,
      project_id: projectId,
      message: input,
    });

    if (onMessageAdd) {
      onMessageAdd(userMessage);
    }
  };

  const handleStop = () => {
    wsClient.sendChatStop(conversationId);
    setIsStreaming(false);
    setCurrentResponse('');
    setToolCalls([]);
    setReasoningSteps([]);
    setCitations([]);
    setFileChanges([]);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* Messages Area */}
      <ScrollArea className="flex-1 p-4" ref={scrollRef}>
        <div className="space-y-4">
          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-[80%] rounded-lg p-4 ${
                  message.role === 'user'
                    ? 'text-white'
                    : ''
                }`}
                style={{
                  backgroundColor: message.role === 'user' ? 'var(--accent)' : 'var(--card-bg)'
                }}
              >
                {message.role === 'assistant' ? (
                  <div className="prose prose-sm dark:prose-invert max-w-none">
                    <ReactMarkdown
                      remarkPlugins={[remarkGfm]}
                      rehypePlugins={[rehypeHighlight, rehypeRaw]}
                    >
                      {message.content}
                    </ReactMarkdown>
                    
                    {/* Tool Calls */}
                    {message.tool_calls && message.tool_calls.length > 0 && (
                      <div className="mt-4 space-y-2">
                        <div className="text-xs font-semibold text-muted-foreground">
                          Tool Calls:
                        </div>
                        {message.tool_calls.map((tool, idx) => (
                          <div key={idx} className="text-xs rounded p-2" style={{ backgroundColor: 'var(--dark-bg)' }}>
                            <div className="font-mono">{tool.tool_name}</div>
                            <div className="text-gray-400">
                              {JSON.stringify(tool.inputs, null, 2)}
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                    
                    {/* Citations */}
                    {message.citations && message.citations.length > 0 && (
                      <div className="mt-4 space-y-2">
                        <div className="text-xs font-semibold text-gray-400">
                          Citations:
                        </div>
                        {message.citations.map((citation, idx) => (
                          <div key={idx} className="text-xs">
                            <a
                              href={citation.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="hover:underline"
                              style={{ color: 'var(--accent)' }}
                            >
                              {citation.title || citation.source}
                            </a>
                          </div>
                        ))}
                      </div>
                    )}
                    
                    {/* File Changes */}
                    {message.files_changed && message.files_changed.length > 0 && (
                      <div className="mt-4 space-y-2">
                        <div className="text-xs font-semibold text-gray-400">
                          Files Changed:
                        </div>
                        {message.files_changed.map((change, idx) => (
                          <div key={idx} className="text-xs">
                            <span className={`font-mono ${
                              change.operation === 'create' ? 'text-green-500' :
                              change.operation === 'delete' ? 'text-red-500' :
                              'text-yellow-500'
                            }`}>
                              {change.operation}
                            </span>
                            <span className="ml-2 font-mono">{change.path}</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="whitespace-pre-wrap">{message.content}</div>
                )}
              </div>
            </div>
          ))}
          
          {/* Current Streaming Response */}
          {isStreaming && currentResponse && (
            <div className="flex justify-start">
              <div className="max-w-[80%] rounded-lg p-4" style={{ backgroundColor: 'var(--card-bg)', borderColor: 'var(--border-color)' }}>
                <div className="prose prose-sm dark:prose-invert max-w-none">
                  <ReactMarkdown
                    remarkPlugins={[remarkGfm]}
                    rehypePlugins={[rehypeHighlight, rehypeRaw]}
                  >
                    {currentResponse}
                  </ReactMarkdown>
                </div>
                
                {/* Active Tool Calls */}
                {toolCalls.length > 0 && (
                  <div className="mt-4 space-y-2">
                    <div className="text-xs font-semibold text-muted-foreground">
                      Tool Calls:
                    </div>
                    {toolCalls.map((tool, idx) => (
                      <div key={idx} className="text-xs bg-background rounded p-2 flex items-center gap-2">
                        <Loader2 className="h-3 w-3 animate-spin" />
                        <span className="font-mono">{tool.tool_name}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </ScrollArea>

      {/* Input Area */}
      <div className="border-t p-4">
        <div className="flex gap-2">
          <Textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Type your message... (Shift+Enter for new line)"
            className="flex-1 min-h-[60px] max-h-[200px] resize-none"
          />
          {isStreaming ? (
            <Button onClick={handleStop} variant="destructive" size="icon">
              <Square className="h-4 w-4" />
            </Button>
          ) : (
            <Button onClick={handleSend} size="icon" disabled={!input.trim()}>
              <Send className="h-4 w-4" />
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}
