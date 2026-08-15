// Core types for Fivoria AI Web Platform

export interface User {
  id: number;
  username: string;
  email: string;
  role: 'user' | 'developer' | 'admin' | 'system';
  permissions: Permission[];
  created_at: string;
  is_active: boolean;
}

export type Permission = 'read' | 'write' | 'admin' | 'super_admin';

export interface Project {
  project_id: string;
  user_id: number;
  name: string;
  description: string;
  workspace_path: string;
  git_url?: string;
  status: 'active' | 'archived' | 'deleted';
  created_at: string;
  updated_at: string;
}

export interface Conversation {
  conversation_id: string;
  project_id?: string;
  user_id: number;
  title: string;
  model_version_id?: number;
  messages: Message[];
  created_at: string;
  updated_at: string;
}

export interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  tool_calls?: ToolCall[];
  reasoning_steps?: ReasoningStep[];
  citations?: Citation[];
  files_changed?: FileChange[];
  timestamp: string;
}

export interface ToolCall {
  tool_name: string;
  inputs: Record<string, any>;
  output?: any;
  error?: string;
  execution_time_ms: number;
  status: 'pending' | 'running' | 'completed' | 'failed';
}

export interface ReasoningStep {
  step: number;
  description: string;
  result?: string;
}

export interface Citation {
  source: string;
  url?: string;
  title?: string;
  snippet?: string;
}

export interface FileChange {
  file_id: string;
  path: string;
  operation: 'create' | 'update' | 'delete' | 'move';
  content?: string;
  diff?: string;
}

export interface AgentTask {
  task_id: string;
  conversation_id: string;
  project_id?: string;
  user_id: number;
  task_type: string;
  status: 'queued' | 'planning' | 'running' | 'waiting_approval' | 'verifying' | 'completed' | 'failed' | 'cancelled';
  current_step?: string;
  plan?: PlanStep[];
  tool_calls?: ToolCall[];
  files_changed?: FileChange[];
  commands_executed?: CommandResult[];
  errors?: Error[];
  preview_url?: string;
  result?: string;
  created_at: string;
  started_at?: string;
  completed_at?: string;
}

export interface PlanStep {
  step: number;
  description: string;
  status: 'pending' | 'in_progress' | 'completed' | 'failed';
}

export interface CommandResult {
  command: string;
  exit_code: number;
  stdout: string;
  stderr: string;
  execution_time_ms: number;
}

export interface ApprovalRequest {
  approval_id: string;
  task_id: string;
  user_id: number;
  action_type: string;
  description: string;
  details: Record<string, any>;
  status: 'pending' | 'approved' | 'denied' | 'expired';
  created_at: string;
  expires_at?: string;
  decided_at?: string;
}

export interface File {
  file_id: string;
  project_id: string;
  path: string;
  content?: string;
  size_bytes: number;
  file_type: string;
  created_at: string;
  updated_at: string;
}

export interface ChatRequest {
  conversation_id: string;
  project_id?: string;
  message: string;
  model?: string;
  temperature?: number;
  max_tokens?: number;
  tools?: Tool[];
}

export interface Tool {
  name: string;
  description: string;
  schema: Record<string, any>;
  permission: 'public' | 'authenticated' | 'admin' | 'restricted';
}

// WebSocket event types
export type WebSocketEventType = 
  | 'chat.token'
  | 'chat.tool_call'
  | 'chat.done'
  | 'chat.error'
  | 'task.started'
  | 'task.progress'
  | 'task.file_change'
  | 'task.command'
  | 'task.approval'
  | 'task.completed'
  | 'task.error'
  | 'terminal.output'
  | 'terminal.error';

export interface WebSocketEvent {
  type: WebSocketEventType;
  data: any;
  conversation_id?: string;
  task_id?: string;
  project_id?: string;
}

// API response types
export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}
