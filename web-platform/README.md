# Fivoria AI Web Platform

Complete web application for the Fivoria AI Platform, providing a production-grade AI workspace.

## Architecture

The web platform consists of:

- **Frontend**: Next.js 14+ with TypeScript, Tailwind CSS, and shadcn/ui
- **API Gateway**: FastAPI-based gateway for routing and authentication
- **Web API Service**: Handles projects, files, conversations, and documents
- **Agent API Service**: Handles AI agent interactions and task management
- **Project Service**: Manages workspaces, file operations, and Git integration
- **Model Gateway**: Connects to the Fivoria inference gateway
- **Preview Service**: Manages isolated preview containers
- **Background Workers**: Celery-based workers for long-running tasks

## Getting Started

### Prerequisites

- Node.js 18+
- Python 3.11+
- MySQL
- Redis
- Docker (for preview service)

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

The frontend will be available at `http://localhost:3000`

### Backend Services

#### Web API Service

```bash
cd services/web-api
pip install -r requirements.txt
python main.py
```

Available at `http://localhost:8001`

#### Agent API Service

```bash
cd services/agent-api
pip install -r requirements.txt
python main.py
```

Available at `http://localhost:8002`

#### Project Service

```bash
cd services/project-service
pip install -r requirements.txt
python main.py
```

Available at `http://localhost:8003`

#### Model Gateway

```bash
cd services/model-gateway
pip install -r requirements.txt
python main.py
```

Available at `http://localhost:8004`

### Environment Variables

Create a `.env.local` file in the frontend directory:

```env
NEXT_PUBLIC_API_URL=http://localhost:8001
NEXT_PUBLIC_WS_URL=http://localhost:8002
NEXT_PUBLIC_MODEL_GATEWAY_URL=http://localhost:8004
```

## Features

### Implemented

- ✅ Next.js frontend with TypeScript and Tailwind CSS
- ✅ AI chat interface with streaming responses
- ✅ Project workspace and session management
- ✅ File explorer with Monaco code editor
- ✅ Web API service structure
- ✅ Agent API service structure

### Pending

- ⏳ AI coding agent with file operations
- ⏳ Terminal system with sandbox security
- ⏳ Live website preview system
- ⏳ Web search and research tools
- ⏳ RAG/knowledge engine integration with document upload
- ⏳ Memory system integration
- ⏳ Tool registry and execution framework
- ⏳ Agent orchestration and task management
- ⏳ Verification and testing agent
- ⏳ Git integration and diff viewer
- ⏳ Background workers and task queue
- ⏳ Model gateway and Fivoria model integration
- ⏳ Authentication and authorization system
- ⏳ Multi-user isolation and security
- ⏳ Observability and monitoring

## API Documentation

### Web API Endpoints

- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/auth/refresh` - Token refresh
- `GET /api/v1/user/profile` - Get user profile
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
- `GET /api/v1/conversations` - List conversations
- `POST /api/v1/conversations` - Create conversation
- `GET /api/v1/conversations/{id}` - Get conversation
- `DELETE /api/v1/conversations/{id}` - Delete conversation
- `POST /api/v1/documents/upload` - Upload document
- `GET /api/v1/knowledge/search` - Search knowledge base

### Agent API Endpoints

- `POST /api/v1/agent/chat` - Chat with agent (streaming)
- `POST /api/v1/agent/task` - Create agent task
- `GET /api/v1/agent/task/{id}` - Get task status
- `POST /api/v1/agent/task/{id}/cancel` - Cancel task
- `GET /api/v1/agent/task/{id}/events` - Stream task events (SSE)
- `POST /api/v1/agent/approval` - Handle approval request

## Development

### Adding New Components

1. Create component in `frontend/src/components/`
2. Add types to `frontend/src/types/index.ts`
3. Add API client methods to `frontend/src/lib/api-client.ts`
4. Add WebSocket events to `frontend/src/lib/websocket-client.ts`
5. Update state store in `frontend/src/lib/state/store.ts`

### Testing

```bash
cd frontend
npm test
```

## Deployment

### Docker

```bash
docker-compose up -d
```

### Kubernetes

```bash
kubectl apply -f kubernetes/
```

## Security

- JWT-based authentication
- Role-based access control (RBAC)
- API key authentication for service-to-service
- Rate limiting
- Input validation and sanitization
- SQL injection prevention
- XSS protection
- CSRF protection

## License

Proprietary - Fivoria AI Platform
