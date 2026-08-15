# Fivoria AI Web Platform Architecture

## Overview
Complete web application architecture for the Fivoria AI Platform, connecting the existing AI infrastructure to a production-grade user-facing workspace.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER BROWSER                              │
│                    (Next.js + TypeScript)                       │
└──────────────────────────────┬──────────────────────────────────┘
                               │ HTTPS/WSS
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                      API GATEWAY                                 │
│                    (FastAPI + Nginx)                            │
├─────────────────────────────────────────────────────────────────┤
│  Auth  │  Rate Limit  │  Routing  │  WebSocket  │  Static Files  │
└──────────────────────────────┬──────────────────────────────────┘
                               │
         ┌─────────────────────┼─────────────────────┐
         │                     │                     │
         ▼                     ▼                     ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│  WEB API        │  │  AGENT API      │  │  PROJECT API    │
│  (FastAPI)      │  │  (FastAPI)      │  │  (FastAPI)      │
└────────┬────────┘  └────────┬────────┘  └────────┬────────┘
         │                    │                    │
         └────────────────────┼────────────────────┘
                              │
         ┌────────────────────┼────────────────────┐
         │                    │                    │
         ▼                    ▼                    ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│ MODEL GATEWAY   │  │ AGENT SERVICE   │  │ PROJECT SERVICE │
│ (inference/)    │  │ (agents/)       │  │ (projects/)     │
└────────┬────────┘  └────────┬────────┘  └────────┬────────┘
         │                    │                    │
         │                    │                    │
         ▼                    ▼                    ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│ FIVORIA MODEL   │  │ AGENT ORCHEST.  │  │ FILE SYSTEM     │
│ (vLLM/Inf)      │  │ (knowledge/)    │  │ (Sandboxed)     │
└─────────────────┘  └────────┬────────┘  └────────┬────────┘
                              │                    │
         ┌────────────────────┼────────────────────┐
         │                    │                    │
         ▼                    ▼                    ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│ MEMORY SYSTEM   │  │ TOOL FRAMEWORK  │  │ RAG ENGINE      │
│ (memory/)       │  │ (tools/)        │  │ (rag/)          │
└─────────────────┘  └────────┬────────┘  └────────┬────────┘
                              │                    │
         ┌────────────────────┼────────────────────┐
         │                    │                    │
         ▼                    ▼                    ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│ MySQL           │  │ Redis           │  │ Vector DB       │
│ (Metadata)      │  │ (Cache/Queue)   │  │ (Embeddings)     │
└─────────────────┘  └─────────────────┘  └─────────────────┘
```

## Component Breakdown

### 1. Frontend (Next.js + TypeScript)

**Location**: `web-platform/frontend/`

**Tech Stack**:
- Next.js 14+ (App Router)
- TypeScript
- Tailwind CSS
- shadcn/ui components
- Monaco Editor (code editing)
- React Query (data fetching)
- Zustand (state management)
- Socket.io-client (real-time)
- React Markdown (markdown rendering)
- Syntax highlighting (Prism/Highlight.js)

**Key Components**:
- `app/` - Next.js app router
  - `page.tsx` - Main workspace
  - `auth/` - Authentication pages
  - `projects/` - Project management
  - `api/` - API routes (if needed)
- `components/` - React components
  - `chat/` - Chat interface
  - `editor/` - Monaco editor
  - `explorer/` - File explorer
  - `terminal/` - Terminal UI
  - `preview/` - Website preview
  - `sidebar/` - Sidebar navigation
- `lib/` - Utilities and clients
  - `api/` - API clients
  - `websocket/` - WebSocket client
  - `state/` - Zustand stores
- `hooks/` - Custom React hooks
- `types/` - TypeScript types

### 2. Backend Services

#### 2.1 API Gateway
**Location**: `web-platform/api-gateway/`

**Tech Stack**:
- FastAPI
- Nginx (reverse proxy)
- JWT authentication
- Rate limiting

**Responsibilities**:
- Request routing
- Authentication/authorization
- Rate limiting
- CORS handling
- WebSocket proxy
- Static file serving
- SSL termination

#### 2.2 Web API Service
**Location**: `web-platform/services/web-api/`

**Tech Stack**:
- FastAPI
- SQLAlchemy
- Pydantic

**Endpoints**:
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/auth/refresh` - Token refresh
- `GET /api/v1/user/profile` - User profile
- `PUT /api/v1/user/profile` - Update profile
- `GET /api/v1/projects` - List projects
- `POST /api/v1/projects` - Create project
- `GET /api/v1/projects/{id}` - Get project
- `PUT /api/v1/projects/{id}` - Update project
- `DELETE /api/v1/projects/{id}` - Delete project
- `GET /api/v1/projects/{id}/files` - List files
- `POST /api/v1/projects/{id}/files` - Create file
- `GET /api/v1/projects/{id}/files/{path}` - Read file
- `PUT /api/v1/projects/{id}/files/{path}` - Update file
- `DELETE /api/v1/projects/{id}/files/{path}` - Delete file
- `POST /api/v1/projects/{id}/terminal` - Execute terminal command
- `GET /api/v1/projects/{id}/preview` - Get preview URL
- `GET /api/v1/conversations` - List conversations
- `POST /api/v1/conversations` - Create conversation
- `GET /api/v1/conversations/{id}` - Get conversation
- `DELETE /api/v1/conversations/{id}` - Delete conversation
- `POST /api/v1/documents/upload` - Upload document
- `GET /api/v1/knowledge/search` - Search knowledge base

#### 2.3 Agent API Service
**Location**: `web-platform/services/agent-api/`

**Tech Stack**:
- FastAPI
- Connects to existing `knowledge-layer/agents/orchestrator.py`
- Connects to existing `knowledge-layer/complete_agent/complete_ai_agent.py`

**Endpoints**:
- `POST /api/v1/agent/chat` - Chat with agent (streaming)
- `POST /api/v1/agent/task` - Create agent task
- `GET /api/v1/agent/task/{id}` - Get task status
- `POST /api/v1/agent/task/{id}/cancel` - Cancel task
- `GET /api/v1/agent/task/{id}/events` - Stream task events (SSE)
- `POST /api/v1/agent/approval` - Handle approval request

#### 2.4 Project Service
**Location**: `web-platform/services/project-service/`

**Tech Stack**:
- FastAPI
- File system operations (sandboxed)
- Git integration

**Responsibilities**:
- Project workspace management
- File operations (CRUD)
- Terminal execution (sandboxed)
- Git operations
- Preview management
- Repository indexing

#### 2.5 Model Gateway Service
**Location**: `web-platform/services/model-gateway/`

**Tech Stack**:
- FastAPI
- Connects to existing `inference/gateway.py`
- vLLM client (for real model serving)

**Responsibilities**:
- Model routing
- Token counting
- Streaming responses
- Model health checks
- Fallback handling

### 3. Background Workers

**Location**: `web-platform/workers/`

**Tech Stack**:
- Celery + Redis
- Or BullMQ (Node.js alternative)

**Worker Tasks**:
- Document processing (chunking, embedding)
- Repository indexing
- Long-running agent tasks
- Preview server management
- Git operations
- Test execution
- Build processes

### 4. Preview Service

**Location**: `web-platform/services/preview-service/`

**Tech Stack**:
- Docker containers
- Port mapping
- Process management

**Responsibilities**:
- Spin up isolated preview containers
- Manage dev servers
- Proxy preview URLs
- Capture console errors
- Screenshot generation

### 5. Database Integration

**Existing**: `database/schema.sql`

**Additional Tables Needed**:
```sql
-- Web platform specific tables
CREATE TABLE web_projects (
    id INT AUTO_INCREMENT PRIMARY KEY,
    project_id VARCHAR(100) NOT NULL UNIQUE,
    user_id INT NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    workspace_path VARCHAR(500),
    git_url VARCHAR(500),
    status ENUM('active', 'archived', 'deleted') DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    INDEX idx_user_id (user_id)
);

CREATE TABLE web_conversations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    conversation_id VARCHAR(100) NOT NULL UNIQUE,
    project_id VARCHAR(100),
    user_id INT NOT NULL,
    title VARCHAR(255),
    model_version_id INT,
    messages JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (model_version_id) REFERENCES ai_model_versions(id),
    INDEX idx_user_id (user_id),
    INDEX idx_project_id (project_id)
);

CREATE TABLE web_files (
    id INT AUTO_INCREMENT PRIMARY KEY,
    file_id VARCHAR(100) NOT NULL UNIQUE,
    project_id VARCHAR(100) NOT NULL,
    path VARCHAR(500) NOT NULL,
    content TEXT,
    size_bytes BIGINT,
    file_type VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES web_projects(project_id),
    INDEX idx_project_id (project_id),
    INDEX idx_path (path)
);

CREATE TABLE web_agent_tasks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    task_id VARCHAR(100) NOT NULL UNIQUE,
    conversation_id VARCHAR(100),
    project_id VARCHAR(100),
    user_id INT NOT NULL,
    task_type VARCHAR(50),
    status ENUM('queued', 'planning', 'running', 'waiting_approval', 'verifying', 'completed', 'failed', 'cancelled') DEFAULT 'queued',
    current_step TEXT,
    plan JSON,
    tool_calls JSON,
    files_changed JSON,
    commands_executed JSON,
    errors JSON,
    preview_url VARCHAR(500),
    result TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP NULL,
    completed_at TIMESTAMP NULL,
    FOREIGN KEY (user_id) REFERENCES users(id),
    INDEX idx_user_id (user_id),
    INDEX idx_status (status)
);

CREATE TABLE web_approvals (
    id INT AUTO_INCREMENT PRIMARY KEY,
    approval_id VARCHAR(100) NOT NULL UNIQUE,
    task_id VARCHAR(100) NOT NULL,
    user_id INT NOT NULL,
    action_type VARCHAR(50),
    description TEXT,
    details JSON,
    status ENUM('pending', 'approved', 'denied', 'expired') DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NULL,
    decided_at TIMESTAMP NULL,
    FOREIGN KEY (task_id) REFERENCES web_agent_tasks(task_id),
    INDEX idx_task_id (task_id),
    INDEX idx_status (status)
);
```

## Integration Points

### 1. Existing Fivoria Components Integration

**Inference Gateway** (`inference/gateway.py`):
- Web API calls Model Gateway
- Model Gateway calls existing `inference/gateway.py`
- Streaming responses via SSE/WebSocket

**Agent Orchestrator** (`knowledge-layer/agents/orchestrator.py`):
- Agent API wraps existing orchestrator
- Task management via web API
- Event streaming to frontend

**Complete AI Agent** (`knowledge-layer/complete_agent/complete_ai_agent.py`):
- Used as primary agent for coding tasks
- Integrated with file operations
- Connected to memory system

**Memory System** (`knowledge-layer/memory/memory_system.py`):
- Web API calls memory system for context
- User preferences stored in long-term memory
- Conversation history in short-term memory

**Tool Framework** (`knowledge-layer/tools/tool_framework.py`):
- Agent API uses tool registry
- Additional web-specific tools (file operations, terminal)
- Permission checking via security layer

**Security/Auth** (`security/auth.py`):
- API Gateway uses existing auth system
- JWT tokens for web authentication
- RBAC for authorization

**Database** (`database/schema.sql`):
- Reuse existing tables
- Add web-specific tables
- Shared MySQL instance

### 2. New Components

**Project Service**:
- Manages isolated workspaces
- File operations with sandboxing
- Git integration
- Preview management

**Preview Service**:
- Docker-based preview containers
- Dev server management
- Error capture

**Background Workers**:
- Document processing
- Repository indexing
- Long-running tasks

## Data Flow

### Chat Flow
```
User Input (Frontend)
  ↓ WebSocket
Agent API
  ↓
Complete AI Agent
  ↓
Model Gateway
  ↓
Inference Gateway
  ↓
Fivoria Model
  ↓
Response (streaming)
  ↓
Agent API
  ↓ WebSocket
Frontend (display)
```

### Coding Task Flow
```
User Request (Frontend)
  ↓ API
Agent API
  ↓
Create Task
  ↓ Queue
Worker
  ↓
Agent Orchestrator
  ↓
Complete AI Agent
  ↓
Tool Execution (file operations)
  ↓
Project Service (sandboxed)
  ↓
File System
  ↓
Terminal (build/run)
  ↓
Preview Service
  ↓
Preview URL
  ↓ Events
Frontend (display preview)
```

### Document Upload Flow
```
User Upload (Frontend)
  ↓ API
Web API
  ↓ Queue
Worker
  ↓
Extract Content
  ↓
Chunk
  ↓
Embedding Model
  ↓
Vector DB
  ↓
RAG Engine
  ↓
Searchable
```

## Security Model

### 1. Authentication
- JWT tokens (access + refresh)
- API keys for service-to-service
- Session management

### 2. Authorization
- RBAC (from existing `security/auth.py`)
- Project-level permissions
- Resource-level access control

### 3. Isolation
- User workspace isolation
- Project sandboxing
- Containerized preview environments
- Network policies

### 4. Input Validation
- Sanitization (from existing `security/auth.py`)
- File type validation
- Command validation
- SQL injection prevention

### 5. Rate Limiting
- Per-user rate limits
- Per-endpoint limits
- API key quotas

## Deployment Architecture

### Development
```
Local Development:
- Next.js dev server (localhost:3000)
- FastAPI services (localhost:8000-8005)
- MySQL (localhost:3306)
- Redis (localhost:6379)
- Vector DB (localhost:19530)
```

### Production
```
Kubernetes Deployment:
- Ingress Controller (Nginx)
- Frontend Deployment (Next.js)
- API Gateway (FastAPI + Nginx)
- Web API Service (FastAPI)
- Agent API Service (FastAPI)
- Project Service (FastAPI)
- Model Gateway (FastAPI)
- Worker Pods (Celery)
- Preview Service (Docker-in-Docker)
- MySQL (StatefulSet)
- Redis (StatefulSet)
- Vector DB (StatefulSet)
- Prometheus + Grafana (Monitoring)
```

## Technology Stack Summary

### Frontend
- Next.js 14+ (App Router)
- TypeScript
- Tailwind CSS
- shadcn/ui
- Monaco Editor
- Socket.io-client
- React Query
- Zustand

### Backend
- FastAPI
- Python 3.11+
- SQLAlchemy
- Pydantic
- Celery
- Redis
- WebSocket

### Infrastructure
- Docker
- Kubernetes (production)
- Nginx
- MySQL
- Redis
- Vector DB (Milvus/Weaviate)
- vLLM (model serving)

### Monitoring
- Prometheus
- Grafana
- OpenTelemetry
- Structured logging

## Implementation Phases

### Phase 1: Foundation
- Set up Next.js project structure
- Implement authentication
- Create basic project management
- Set up API gateway

### Phase 2: Core Features
- Implement chat interface with streaming
- Implement file explorer
- Integrate Monaco editor
- Connect to existing AI agent

### Phase 3: Advanced Features
- Implement terminal with sandboxing
- Implement preview system
- Implement document upload
- Integrate RAG/knowledge engine

### Phase 4: Production
- Implement background workers
- Add Git integration
- Implement testing agent
- Add monitoring and observability

### Phase 5: Polish
- Performance optimization
- Security hardening
- Load testing
- Documentation

## API Contracts

### Chat API
```typescript
interface ChatRequest {
  conversation_id: string;
  project_id?: string;
  message: string;
  model?: string;
  temperature?: number;
  max_tokens?: number;
  tools?: Tool[];
}

interface ChatResponse {
  id: string;
  content: string;
  role: 'assistant';
  tool_calls?: ToolCall[];
  reasoning_steps?: ReasoningStep[];
  citations?: Citation[];
  files_changed?: FileChange[];
}

interface ChatEvent {
  type: 'token' | 'tool_call' | 'reasoning' | 'file_change' | 'error' | 'done';
  data: any;
}
```

### Project API
```typescript
interface Project {
  project_id: string;
  user_id: number;
  name: string;
  description: string;
  workspace_path: string;
  git_url?: string;
  status: 'active' | 'archived';
  created_at: string;
  updated_at: string;
}

interface File {
  file_id: string;
  project_id: string;
  path: string;
  content?: string;
  size_bytes: number;
  file_type: string;
  created_at: string;
  updated_at: string;
}
```

### Task API
```typescript
interface AgentTask {
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
```

## WebSocket Events

### Client → Server
```typescript
// Chat
{ type: 'chat.start', data: ChatRequest }
{ type: 'chat.stop', data: { conversation_id: string } }

// Task
{ type: 'task.create', data: TaskRequest }
{ type: 'task.cancel', data: { task_id: string } }
{ type: 'task.approve', data: { approval_id: string, approved: boolean } }

// Terminal
{ type: 'terminal.input', data: { project_id: string, input: string } }
{ type: 'terminal.resize', data: { project_id: string, rows: number, cols: number } }
```

### Server → Client
```typescript
// Chat
{ type: 'chat.token', data: { token: string, conversation_id: string } }
{ type: 'chat.tool_call', data: { tool_call: ToolCall, conversation_id: string } }
{ type: 'chat.done', data: { response: ChatResponse, conversation_id: string } }
{ type: 'chat.error', data: { error: string, conversation_id: string } }

// Task
{ type: 'task.started', data: { task_id: string, plan: PlanStep[] } }
{ type: 'task.progress', data: { task_id: string, step: string, progress: number } }
{ type: 'task.file_change', data: { task_id: string, change: FileChange } }
{ type: 'task.command', data: { task_id: string, command: CommandResult } }
{ type: 'task.approval', data: { task_id: string, approval: ApprovalRequest } }
{ type: 'task.completed', data: { task_id: string, result: string } }
{ type: 'task.error', data: { task_id: string, error: string } }

// Terminal
{ type: 'terminal.output', data: { project_id: string, output: string } }
{ type: 'terminal.error', data: { project_id: string, error: string } }
```

## File Structure

```
web-platform/
├── frontend/                    # Next.js frontend
│   ├── app/
│   ├── components/
│   ├── lib/
│   ├── hooks/
│   ├── types/
│   ├── package.json
│   ├── tsconfig.json
│   └── tailwind.config.ts
├── api-gateway/                 # API Gateway
│   ├── main.py
│   ├── routers/
│   ├── middleware/
│   └── requirements.txt
├── services/
│   ├── web-api/                 # Web API Service
│   ├── agent-api/               # Agent API Service
│   ├── project-service/         # Project Service
│   └── model-gateway/           # Model Gateway
├── workers/                     # Background Workers
│   ├── document_processor/
│   ├── repository_indexer/
│   └── task_worker/
├── preview-service/             # Preview Service
│   ├── main.py
│   ├── container_manager.py
│   └── requirements.txt
├── shared/                      # Shared code
│   ├── database/
│   ├── models/
│   └── utils/
├── docker/
│   ├── Dockerfile.frontend
│   ├── Dockerfile.api
│   └── docker-compose.yml
├── kubernetes/                  # K8s manifests
│   ├── deployments/
│   ├── services/
│   └── ingress/
└── WEB_ARCHITECTURE.md          # This file
```

## Next Steps

1. Create Next.js frontend structure
2. Set up API Gateway with FastAPI
3. Implement Web API service with authentication
4. Integrate existing AI agent backend
5. Implement chat interface with streaming
6. Implement project workspace management
7. Implement file explorer and Monaco editor
8. Implement terminal with sandboxing
9. Implement preview service
10. Integrate RAG and document upload
11. Add background workers
12. Implement Git integration
13. Add monitoring and observability
14. Deploy and test end-to-end
