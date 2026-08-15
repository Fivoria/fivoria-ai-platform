import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { User, Project, Conversation } from '@/types';

interface AuthState {
  user: User | null;
  token: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  setUser: (user: User) => void;
  setTokens: (token: string, refreshToken: string) => void;
  logout: () => void;
}

interface ProjectState {
  projects: Project[];
  currentProject: Project | null;
  setProjects: (projects: Project[]) => void;
  setCurrentProject: (project: Project | null) => void;
  addProject: (project: Project) => void;
  updateProject: (projectId: string, data: Partial<Project>) => void;
  removeProject: (projectId: string) => void;
}

interface ConversationState {
  conversations: Conversation[];
  currentConversation: Conversation | null;
  setConversations: (conversations: Conversation[]) => void;
  setCurrentConversation: (conversation: Conversation | null) => void;
  addConversation: (conversation: Conversation) => void;
  updateConversation: (conversationId: string, data: Partial<Conversation>) => void;
  removeConversation: (conversationId: string) => void;
}

interface UIState {
  sidebarOpen: boolean;
  terminalOpen: boolean;
  previewOpen: boolean;
  explorerOpen: boolean;
  toggleSidebar: () => void;
  toggleTerminal: () => void;
  togglePreview: () => void;
  toggleExplorer: () => void;
  setSidebarOpen: (open: boolean) => void;
  setTerminalOpen: (open: boolean) => void;
  setPreviewOpen: (open: boolean) => void;
  setExplorerOpen: (open: boolean) => void;
}

// Auth store
export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      refreshToken: null,
      isAuthenticated: false,
      setUser: (user) => set({ user, isAuthenticated: true }),
      setTokens: (token, refreshToken) => set({ token, refreshToken }),
      logout: () => set({ user: null, token: null, refreshToken: null, isAuthenticated: false }),
    }),
    {
      name: 'auth-storage',
    }
  )
);

// Project store
export const useProjectStore = create<ProjectState>((set) => ({
  projects: [],
  currentProject: null,
  setProjects: (projects) => set({ projects }),
  setCurrentProject: (project) => set({ currentProject: project }),
  addProject: (project) => set((state) => ({ projects: [...state.projects, project] })),
  updateProject: (projectId, data) =>
    set((state) => ({
      projects: state.projects.map((p) =>
        p.project_id === projectId ? { ...p, ...data } : p
      ),
      currentProject:
        state.currentProject?.project_id === projectId
          ? { ...state.currentProject, ...data }
          : state.currentProject,
    })),
  removeProject: (projectId) =>
    set((state) => ({
      projects: state.projects.filter((p) => p.project_id !== projectId),
      currentProject:
        state.currentProject?.project_id === projectId
          ? null
          : state.currentProject,
    })),
}));

// Conversation store
export const useConversationStore = create<ConversationState>((set) => ({
  conversations: [],
  currentConversation: null,
  setConversations: (conversations) => set({ conversations }),
  setCurrentConversation: (conversation) => set({ currentConversation: conversation }),
  addConversation: (conversation) =>
    set((state) => ({ conversations: [...state.conversations, conversation] })),
  updateConversation: (conversationId, data) =>
    set((state) => ({
      conversations: state.conversations.map((c) =>
        c.conversation_id === conversationId ? { ...c, ...data } : c
      ),
      currentConversation:
        state.currentConversation?.conversation_id === conversationId
          ? { ...state.currentConversation, ...data }
          : state.currentConversation,
    })),
  removeConversation: (conversationId) =>
    set((state) => ({
      conversations: state.conversations.filter((c) => c.conversation_id !== conversationId),
      currentConversation:
        state.currentConversation?.conversation_id === conversationId
          ? null
          : state.currentConversation,
    })),
}));

// UI store
export const useUIStore = create<UIState>((set) => ({
  sidebarOpen: true,
  terminalOpen: false,
  previewOpen: false,
  explorerOpen: true,
  toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
  toggleTerminal: () => set((state) => ({ terminalOpen: !state.terminalOpen })),
  togglePreview: () => set((state) => ({ previewOpen: !state.previewOpen })),
  toggleExplorer: () => set((state) => ({ explorerOpen: !state.explorerOpen })),
  setSidebarOpen: (open) => set({ sidebarOpen: open }),
  setTerminalOpen: (open) => set({ terminalOpen: open }),
  setPreviewOpen: (open) => set({ previewOpen: open }),
  setExplorerOpen: (open) => set({ explorerOpen: open }),
}));
