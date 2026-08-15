import type { 
  ApiResponse, 
  PaginatedResponse, 
  User, 
  Project, 
  Conversation, 
  AgentTask, 
  File,
  ChatRequest 
} from '@/types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';

class ApiClient {
  private baseUrl: string;
  private token: string | null = null;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  setToken(token: string) {
    this.token = token;
  }

  clearToken() {
    this.token = null;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    const url = `${this.baseUrl}${endpoint}`;
    
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(options.headers as Record<string, string> || {}),
    };

    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }

    try {
      const response = await fetch(url, {
        ...options,
        headers,
      });

      const data = await response.json();

      if (!response.ok) {
        return {
          success: false,
          error: data.error || data.message || 'Request failed',
        };
      }

      return {
        success: true,
        data: data.data || data,
      };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Network error',
      };
    }
  }

  // Auth endpoints
  async login(email: string, password: string): Promise<ApiResponse<{ access_token: string; refresh_token: string; user: User }>> {
    return this.request('/api/v1/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
  }

  async register(username: string, email: string, password: string): Promise<ApiResponse<{ access_token: string; refresh_token: string; user: User }>> {
    return this.request('/api/v1/auth/register', {
      method: 'POST',
      body: JSON.stringify({ username, email, password }),
    });
  }

  async refreshToken(refreshToken: string): Promise<ApiResponse<{ access_token: string }>> {
    return this.request('/api/v1/auth/refresh', {
      method: 'POST',
      body: JSON.stringify({ refresh_token: refreshToken }),
    });
  }

  // User endpoints
  async getProfile(): Promise<ApiResponse<User>> {
    return this.request('/api/v1/user/profile');
  }

  async updateProfile(data: Partial<User>): Promise<ApiResponse<User>> {
    return this.request('/api/v1/user/profile', {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  // Project endpoints
  async getProjects(): Promise<ApiResponse<Project[]>> {
    return this.request('/api/v1/projects');
  }

  async createProject(data: Omit<Project, 'project_id' | 'user_id' | 'created_at' | 'updated_at'>): Promise<ApiResponse<Project>> {
    return this.request('/api/v1/projects', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async getProject(projectId: string): Promise<ApiResponse<Project>> {
    return this.request(`/api/v1/projects/${projectId}`);
  }

  async updateProject(projectId: string, data: Partial<Project>): Promise<ApiResponse<Project>> {
    return this.request(`/api/v1/projects/${projectId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async deleteProject(projectId: string): Promise<ApiResponse<void>> {
    return this.request(`/api/v1/projects/${projectId}`, {
      method: 'DELETE',
    });
  }

  // File endpoints
  async getFiles(projectId: string, path?: string): Promise<ApiResponse<File[]>> {
    const query = path ? `?path=${encodeURIComponent(path)}` : '';
    return this.request(`/api/v1/projects/${projectId}/files${query}`);
  }

  async createFile(projectId: string, path: string, content: string): Promise<ApiResponse<File>> {
    return this.request(`/api/v1/projects/${projectId}/files`, {
      method: 'POST',
      body: JSON.stringify({ path, content }),
    });
  }

  async getFile(projectId: string, path: string): Promise<ApiResponse<File>> {
    return this.request(`/api/v1/projects/${projectId}/files/${encodeURIComponent(path)}`);
  }

  async updateFile(projectId: string, path: string, content: string): Promise<ApiResponse<File>> {
    return this.request(`/api/v1/projects/${projectId}/files/${encodeURIComponent(path)}`, {
      method: 'PUT',
      body: JSON.stringify({ content }),
    });
  }

  async deleteFile(projectId: string, path: string): Promise<ApiResponse<void>> {
    return this.request(`/api/v1/projects/${projectId}/files/${encodeURIComponent(path)}`, {
      method: 'DELETE',
    });
  }

  // Conversation endpoints
  async getConversations(): Promise<ApiResponse<Conversation[]>> {
    return this.request('/api/v1/conversations');
  }

  async createConversation(data: Omit<Conversation, 'conversation_id' | 'messages' | 'created_at' | 'updated_at'>): Promise<ApiResponse<Conversation>> {
    return this.request('/api/v1/conversations', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async getConversation(conversationId: string): Promise<ApiResponse<Conversation>> {
    return this.request(`/api/v1/conversations/${conversationId}`);
  }

  async deleteConversation(conversationId: string): Promise<ApiResponse<void>> {
    return this.request(`/api/v1/conversations/${conversationId}`, {
      method: 'DELETE',
    });
  }

  // Task endpoints
  async createTask(data: Omit<AgentTask, 'task_id' | 'created_at' | 'started_at' | 'completed_at'>): Promise<ApiResponse<AgentTask>> {
    return this.request('/api/v1/agent/task', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async getTask(taskId: string): Promise<ApiResponse<AgentTask>> {
    return this.request(`/api/v1/agent/task/${taskId}`);
  }

  async cancelTask(taskId: string): Promise<ApiResponse<void>> {
    return this.request(`/api/v1/agent/task/${taskId}/cancel`, {
      method: 'POST',
    });
  }

  // Document endpoints
  async uploadDocument(file: globalThis.File, projectId?: string): Promise<ApiResponse<{ document_id: string }>> {
    const formData = new FormData();
    formData.append('file', file as any);
    if (projectId) {
      formData.append('project_id', projectId);
    }

    const headers: Record<string, string> = {};
    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }

    try {
      const response = await fetch(`${this.baseUrl}/api/v1/documents/upload`, {
        method: 'POST',
        headers,
        body: formData,
      });

      const data = await response.json();

      if (!response.ok) {
        return {
          success: false,
          error: data.error || 'Upload failed',
        };
      }

      return {
        success: true,
        data,
      };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Network error',
      };
    }
  }

  // Knowledge endpoints
  async searchKnowledge(query: string, projectId?: string): Promise<ApiResponse<any[]>> {
    const queryParams = new URLSearchParams({ query });
    if (projectId) {
      queryParams.append('project_id', projectId);
    }
    return this.request(`/api/v1/knowledge/search?${queryParams.toString()}`);
  }

  // Git endpoints
  async getGitHistory(projectId: string, limit: number = 20): Promise<ApiResponse<{ commits: any[]; total: number }>> {
    return this.request(`/api/v1/projects/${projectId}/git/history?limit=${limit}`);
  }

  async getGitBranches(projectId: string): Promise<ApiResponse<{ branches: any[]; current: string | null }>> {
    return this.request(`/api/v1/projects/${projectId}/git/branches`);
  }

  async gitCheckout(projectId: string, branch: string): Promise<ApiResponse<any>> {
    return this.request(`/api/v1/projects/${projectId}/git/checkout`, {
      method: 'POST',
      body: JSON.stringify({ branch }),
    });
  }

  async gitOperation(projectId: string, operation: string, params?: Record<string, any>): Promise<ApiResponse<any>> {
    return this.request(`/api/v1/projects/${projectId}/git`, {
      method: 'POST',
      body: JSON.stringify({ operation, params }),
    });
  }

  async executeTerminalCommand(projectId: string, command: string, workingDir?: string): Promise<ApiResponse<any>> {
    return this.request(`/api/v1/projects/${projectId}/terminal/execute`, {
      method: 'POST',
      body: JSON.stringify({ command, working_dir: workingDir }),
    });
  }

  // Web search endpoint
  async webSearch(query: string, numResults: number = 10): Promise<ApiResponse<{ results: SearchResult[] }>> {
    return this.request(`/api/v1/tools/web_search`, {
      method: 'POST',
      body: JSON.stringify({ query, num_results: numResults }),
    });
  }
}

interface SearchResult {
  title: string;
  url: string;
  snippet: string;
  source: string;
}

export const apiClient = new ApiClient();
