'use client';

import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Wrench, Play, Settings, RefreshCw } from 'lucide-react';
import { apiClient } from '@/lib/api-client';
import { cn } from '@/lib/utils';

interface Tool {
  name: string;
  description: string;
  permission: string;
  enabled: boolean;
}

export function ToolsPanel() {
  const [tools, setTools] = useState<Tool[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadTools();
  }, []);

  const loadTools = async () => {
    setLoading(true);
    try {
      // TODO: Call tools API
      setTools([
        { name: 'web_search', description: 'Search the web for information', permission: 'authenticated', enabled: true },
        { name: 'file_read', description: 'Read file contents', permission: 'authenticated', enabled: true },
        { name: 'file_write', description: 'Write to files', permission: 'authenticated', enabled: true },
        { name: 'terminal', description: 'Execute terminal commands', permission: 'authenticated', enabled: true },
        { name: 'git', description: 'Git operations', permission: 'authenticated', enabled: true },
        { name: 'database_query', description: 'Query database', permission: 'restricted', enabled: false },
      ]);
    } catch (error) {
      console.error('Failed to load tools:', error);
    }
    setLoading(false);
  };

  const handleToggleTool = async (toolName: string) => {
    setTools(prev => prev.map(tool => 
      tool.name === toolName ? { ...tool, enabled: !tool.enabled } : tool
    ));
    // TODO: Call API to update tool status
  };

  const handleExecuteTool = async (toolName: string) => {
    // TODO: Implement tool execution dialog
    console.log('Execute tool:', toolName);
  };

  const getPermissionColor = (permission: string) => {
    const colors = {
      public: 'bg-green-500',
      authenticated: 'bg-blue-500',
      admin: 'bg-purple-500',
      restricted: 'bg-red-500',
    };
    return colors[permission as keyof typeof colors] || 'bg-gray-500';
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="h-10 border-b flex items-center justify-between px-4">
        <div className="flex items-center gap-2">
          <Wrench className="h-4 w-4" />
          <span className="text-sm font-semibold">Tools</span>
        </div>
        <Button
          size="icon"
          variant="ghost"
          className="h-7 w-7"
          onClick={loadTools}
          disabled={loading}
        >
          <RefreshCw className={cn("h-3 w-3", loading && "animate-spin")} />
        </Button>
      </div>

      {/* Tools */}
      <ScrollArea className="flex-1">
        <div className="p-4">
          {tools.length === 0 ? (
            <div className="text-center py-8">
              <Wrench className="h-12 w-12 mx-auto mb-2 text-muted-foreground opacity-50" />
              <p className="text-sm text-muted-foreground">No tools available</p>
            </div>
          ) : (
            <div className="space-y-2">
              {tools.map((tool) => (
                <div key={tool.name} className="p-3 rounded-lg border bg-card">
                  <div className="flex items-start gap-3">
                    <div className={cn("w-2 h-2 rounded-full mt-1.5", getPermissionColor(tool.permission))} />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between">
                        <p className="text-sm font-medium">{tool.name}</p>
                        <div className="flex items-center gap-1">
                          <Button
                            size="icon"
                            variant="ghost"
                            className="h-6 w-6"
                            onClick={() => handleExecuteTool(tool.name)}
                            title="Execute"
                          >
                            <Play className="h-3 w-3" />
                          </Button>
                          <Button
                            size="icon"
                            variant="ghost"
                            className="h-6 w-6"
                            onClick={() => handleToggleTool(tool.name)}
                            title={tool.enabled ? 'Disable' : 'Enable'}
                          >
                            <Settings className="h-3 w-3" />
                          </Button>
                        </div>
                      </div>
                      <p className="text-xs text-muted-foreground mt-1">{tool.description}</p>
                      <div className="flex items-center gap-2 mt-2">
                        <span className="text-xs text-muted-foreground capitalize">{tool.permission}</span>
                        <span className={cn(
                          "text-xs px-1.5 py-0.5 rounded",
                          tool.enabled ? "bg-green-500/20 text-green-500" : "bg-gray-500/20 text-gray-500"
                        )}>
                          {tool.enabled ? 'Enabled' : 'Disabled'}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </ScrollArea>

      {/* Legend */}
      <div className="p-3 border-t">
        <div className="text-xs text-muted-foreground mb-2">Permission Levels:</div>
        <div className="flex flex-wrap gap-2">
          <div className="flex items-center gap-1">
            <div className="w-2 h-2 rounded-full bg-green-500" />
            <span className="text-xs">Public</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-2 h-2 rounded-full bg-blue-500" />
            <span className="text-xs">Authenticated</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-2 h-2 rounded-full bg-purple-500" />
            <span className="text-xs">Admin</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-2 h-2 rounded-full bg-red-500" />
            <span className="text-xs">Restricted</span>
          </div>
        </div>
      </div>
    </div>
  );
}
