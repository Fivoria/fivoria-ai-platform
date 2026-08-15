import { io, Socket } from 'socket.io-client';
import type { WebSocketEvent } from '@/types';

class WebSocketClient {
  private socket: Socket | null = null;
  private token: string | null = null;
  private eventHandlers: Map<string, Set<(data: any) => void>> = new Map();

  connect(url: string, token: string) {
    this.token = token;
    
    this.socket = io(url, {
      auth: { token },
      transports: ['websocket'],
    });

    this.socket.on('connect', () => {
      console.log('WebSocket connected');
    });

    this.socket.on('disconnect', () => {
      console.log('WebSocket disconnected');
    });

    this.socket.on('error', (error) => {
      console.error('WebSocket error:', error);
    });

    // Register all event handlers
    this.eventHandlers.forEach((handlers, event) => {
      handlers.forEach(handler => {
        this.socket?.on(event, handler);
      });
    });
  }

  disconnect() {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
    }
    this.eventHandlers.clear();
  }

  on(event: string, handler: (data: any) => void) {
    if (!this.eventHandlers.has(event)) {
      this.eventHandlers.set(event, new Set());
    }
    this.eventHandlers.get(event)!.add(handler);
    
    if (this.socket) {
      this.socket.on(event, handler);
    }
  }

  off(event: string, handler: (data: any) => void) {
    const handlers = this.eventHandlers.get(event);
    if (handlers) {
      handlers.delete(handler);
      if (this.socket) {
        this.socket.off(event, handler);
      }
    }
  }

  emit(event: string, data: any) {
    if (this.socket) {
      this.socket.emit(event, data);
    }
  }

  // Convenience methods for specific events
  onChatToken(handler: (data: { token: string; conversation_id: string }) => void) {
    this.on('chat.token', handler);
  }

  onChatToolCall(handler: (data: { tool_call: any; conversation_id: string }) => void) {
    this.on('chat.tool_call', handler);
  }

  onChatDone(handler: (data: { response: any; conversation_id: string }) => void) {
    this.on('chat.done', handler);
  }

  onChatError(handler: (data: { error: string; conversation_id: string }) => void) {
    this.on('chat.error', handler);
  }

  onTaskStarted(handler: (data: { task_id: string; plan: any[] }) => void) {
    this.on('task.started', handler);
  }

  onTaskProgress(handler: (data: { task_id: string; step: string; progress: number }) => void) {
    this.on('task.progress', handler);
  }

  onTaskFileChange(handler: (data: { task_id: string; change: any }) => void) {
    this.on('task.file_change', handler);
  }

  onTaskCommand(handler: (data: { task_id: string; command: any }) => void) {
    this.on('task.command', handler);
  }

  onTaskApproval(handler: (data: { task_id: string; approval: any }) => void) {
    this.on('task.approval', handler);
  }

  onTaskCompleted(handler: (data: { task_id: string; result: string }) => void) {
    this.on('task.completed', handler);
  }

  onTaskError(handler: (data: { task_id: string; error: string }) => void) {
    this.on('task.error', handler);
  }

  onTerminalOutput(handler: (data: { project_id: string; output: string }) => void) {
    this.on('terminal.output', handler);
  }

  onTerminalError(handler: (data: { project_id: string; error: string }) => void) {
    this.on('terminal.error', handler);
  }

  // Send methods
  sendChatStart(data: any) {
    this.emit('chat.start', data);
  }

  sendChatStop(conversationId: string) {
    this.emit('chat.stop', { conversation_id: conversationId });
  }

  sendTaskCreate(data: any) {
    this.emit('task.create', data);
  }

  sendTaskCancel(taskId: string) {
    this.emit('task.cancel', { task_id: taskId });
  }

  sendTaskApprove(approvalId: string, approved: boolean) {
    this.emit('task.approve', { approval_id: approvalId, approved });
  }

  sendTerminalInput(projectId: string, input: string) {
    this.emit('terminal.input', { project_id: projectId, input });
  }

  sendTerminalResize(projectId: string, rows: number, cols: number) {
    this.emit('terminal.resize', { project_id: projectId, rows, cols });
  }

  isConnected(): boolean {
    return this.socket?.connected || false;
  }
}

export const wsClient = new WebSocketClient();
