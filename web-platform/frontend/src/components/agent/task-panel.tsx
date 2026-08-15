'use client';

import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { 
  Bot, 
  Play, 
  Stop, 
  RefreshCw, 
  Check, 
  X, 
  Clock,
  AlertTriangle
} from 'lucide-react';
import { apiClient } from '@/lib/api-client';
import { cn } from '@/lib/utils';

interface AgentTask {
  task_id: string;
  task_type: string;
  status: 'queued' | 'planning' | 'running' | 'waiting_approval' | 'verifying' | 'completed' | 'failed' | 'cancelled';
  current_step?: string;
  progress?: number;
  result?: string;
  error?: string;
  created_at: string;
}

export function TaskPanel() {
  const [tasks, setTasks] = useState<AgentTask[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadTasks();
    const interval = setInterval(loadTasks, 5000);
    return () => clearInterval(interval);
  }, []);

  const loadTasks = async () => {
    setLoading(true);
    try {
      // TODO: Call tasks API
      setTasks([]);
    } catch (error) {
      console.error('Failed to load tasks:', error);
    }
    setLoading(false);
  };

  const handleCancelTask = async (taskId: string) => {
    await apiClient.cancelTask(taskId);
    loadTasks();
  };

  const getStatusIcon = (status: string) => {
    const icons = {
      queued: <Clock className="h-4 w-4 text-muted-foreground" />,
      planning: <Bot className="h-4 w-4 text-blue-500" />,
      running: <Play className="h-4 w-4 text-green-500" />,
      waiting_approval: <AlertTriangle className="h-4 w-4 text-yellow-500" />,
      verifying: <RefreshCw className="h-4 w-4 text-purple-500 animate-spin" />,
      completed: <Check className="h-4 w-4 text-green-500" />,
      failed: <X className="h-4 w-4 text-red-500" />,
      cancelled: <X className="h-4 w-4 text-gray-500" />,
    };
    return icons[status as keyof typeof icons] || <Clock className="h-4 w-4" />;
  };

  const getStatusColor = (status: string) => {
    const colors = {
      queued: 'bg-gray-500',
      planning: 'bg-blue-500',
      running: 'bg-green-500',
      waiting_approval: 'bg-yellow-500',
      verifying: 'bg-purple-500',
      completed: 'bg-green-500',
      failed: 'bg-red-500',
      cancelled: 'bg-gray-500',
    };
    return colors[status as keyof typeof colors] || 'bg-gray-500';
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="h-10 border-b flex items-center justify-between px-4">
        <div className="flex items-center gap-2">
          <Bot className="h-4 w-4" />
          <span className="text-sm font-semibold">Agent Tasks</span>
        </div>
        <Button
          size="icon"
          variant="ghost"
          className="h-7 w-7"
          onClick={loadTasks}
          disabled={loading}
        >
          <RefreshCw className={cn("h-3 w-3", loading && "animate-spin")} />
        </Button>
      </div>

      {/* Tasks */}
      <ScrollArea className="flex-1">
        <div className="p-4">
          {tasks.length === 0 ? (
            <div className="text-center py-8">
              <Bot className="h-12 w-12 mx-auto mb-2 text-muted-foreground opacity-50" />
              <p className="text-sm text-muted-foreground">No active tasks</p>
              <p className="text-xs text-muted-foreground mt-1">
                Tasks are created when you ask the AI to perform actions
              </p>
            </div>
          ) : (
            <div className="space-y-2">
              {tasks.map((task) => (
                <div key={task.task_id} className="p-3 rounded-lg border bg-card">
                  <div className="flex items-start gap-3">
                    {getStatusIcon(task.status)}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between">
                        <p className="text-sm font-medium">{task.task_type}</p>
                        <div className="flex items-center gap-1">
                          {task.status === 'running' && (
                            <Button
                              size="icon"
                              variant="ghost"
                              className="h-6 w-6"
                              onClick={() => handleCancelTask(task.task_id)}
                              title="Cancel"
                            >
                              <Stop className="h-3 w-3" />
                            </Button>
                          )}
                        </div>
                      </div>
                      
                      {task.current_step && (
                        <p className="text-xs text-muted-foreground mt-1">{task.current_step}</p>
                      )}
                      
                      {task.progress !== undefined && (
                        <div className="mt-2">
                          <div className="h-1.5 bg-muted rounded-full overflow-hidden">
                            <div 
                              className="h-full bg-primary transition-all"
                              style={{ width: `${task.progress}%` }}
                            />
                          </div>
                        </div>
                      )}
                      
                      {task.error && (
                        <p className="text-xs text-red-500 mt-1">{task.error}</p>
                      )}
                      
                      {task.result && (
                        <p className="text-xs text-green-500 mt-1 line-clamp-2">{task.result}</p>
                      )}
                      
                      <div className="flex items-center gap-2 mt-2">
                        <div className={cn("w-2 h-2 rounded-full", getStatusColor(task.status))} />
                        <span className="text-xs text-muted-foreground capitalize">{task.status.replace('_', ' ')}</span>
                        <span className="text-xs text-muted-foreground">
                          {new Date(task.created_at).toLocaleTimeString()}
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
    </div>
  );
}
