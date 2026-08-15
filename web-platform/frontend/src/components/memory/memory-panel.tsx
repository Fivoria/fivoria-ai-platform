'use client';

import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Brain, Trash2, RefreshCw } from 'lucide-react';
import { apiClient } from '@/lib/api-client';
import { cn } from '@/lib/utils';

interface MemoryItem {
  id: string;
  content: string;
  type: 'short_term' | 'long_term' | 'semantic' | 'factual' | 'episodic';
  created_at: string;
  importance?: number;
}

export function MemoryPanel() {
  const [memories, setMemories] = useState<MemoryItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [filterType, setFilterType] = useState<string>('all');

  useEffect(() => {
    loadMemories();
  }, [filterType]);

  const loadMemories = async () => {
    setLoading(true);
    try {
      // TODO: Call memory API
      setMemories([]);
    } catch (error) {
      console.error('Failed to load memories:', error);
    }
    setLoading(false);
  };

  const handleClearMemory = async (memoryId: string) => {
    // TODO: Implement memory deletion
    setMemories(prev => prev.filter(m => m.id !== memoryId));
  };

  const handleClearAll = async () => {
    // TODO: Implement clear all memories
    setMemories([]);
  };

  const getTypeColor = (type: string) => {
    const colors = {
      short_term: 'bg-blue-500',
      long_term: 'bg-purple-500',
      semantic: 'bg-green-500',
      factual: 'bg-yellow-500',
      episodic: 'bg-orange-500',
    };
    return colors[type as keyof typeof colors] || 'bg-gray-500';
  };

  const filteredMemories = filterType === 'all' 
    ? memories 
    : memories.filter(m => m.type === filterType);

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="h-10 border-b flex items-center justify-between px-4">
        <div className="flex items-center gap-2">
          <Brain className="h-4 w-4" />
          <span className="text-sm font-semibold">Memory</span>
        </div>
        <Button
          size="icon"
          variant="ghost"
          className="h-7 w-7"
          onClick={loadMemories}
          disabled={loading}
        >
          <RefreshCw className={cn("h-3 w-3", loading && "animate-spin")} />
        </Button>
      </div>

      {/* Filter */}
      <div className="h-8 border-b flex items-center px-2 gap-1">
        <Button
          size="sm"
          variant={filterType === 'all' ? 'default' : 'ghost'}
          className="h-6 text-xs"
          onClick={() => setFilterType('all')}
        >
          All
        </Button>
        <Button
          size="sm"
          variant={filterType === 'short_term' ? 'default' : 'ghost'}
          className="h-6 text-xs"
          onClick={() => setFilterType('short_term')}
        >
          Short
        </Button>
        <Button
          size="sm"
          variant={filterType === 'semantic' ? 'default' : 'ghost'}
          className="h-6 text-xs"
          onClick={() => setFilterType('semantic')}
        >
          Semantic
        </Button>
        <Button
          size="sm"
          variant={filterType === 'episodic' ? 'default' : 'ghost'}
          className="h-6 text-xs"
          onClick={() => setFilterType('episodic')}
        >
          Episodic
        </Button>
      </div>

      {/* Memories */}
      <ScrollArea className="flex-1">
        <div className="p-4">
          {loading ? (
            <div className="text-sm text-muted-foreground text-center py-8">
              Loading memories...
            </div>
          ) : filteredMemories.length === 0 ? (
            <div className="text-center py-8">
              <Brain className="h-12 w-12 mx-auto mb-2 text-muted-foreground opacity-50" />
              <p className="text-sm text-muted-foreground">No memories yet</p>
              <p className="text-xs text-muted-foreground mt-1">
                Memories are created during conversations
              </p>
            </div>
          ) : (
            <div className="space-y-2">
              {filteredMemories.map((memory) => (
                <div key={memory.id} className="p-3 rounded-lg border bg-card">
                  <div className="flex items-start gap-2">
                    <div className={cn("w-2 h-2 rounded-full mt-1.5", getTypeColor(memory.type))} />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm line-clamp-3">{memory.content}</p>
                      <div className="flex items-center justify-between mt-2">
                        <span className="text-xs text-muted-foreground capitalize">{memory.type.replace('_', ' ')}</span>
                        <span className="text-xs text-muted-foreground">
                          {new Date(memory.created_at).toLocaleDateString()}
                        </span>
                      </div>
                    </div>
                    <Button
                      size="icon"
                      variant="ghost"
                      className="h-6 w-6"
                      onClick={() => handleClearMemory(memory.id)}
                    >
                      <Trash2 className="h-3 w-3" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </ScrollArea>

      {/* Actions */}
      <div className="h-10 border-t flex items-center justify-center px-4">
        <Button size="sm" variant="outline" onClick={handleClearAll}>
          Clear All
        </Button>
      </div>
    </div>
  );
}
