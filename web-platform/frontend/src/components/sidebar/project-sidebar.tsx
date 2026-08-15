'use client';

import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Plus, FolderOpen, MessageSquare, Settings, LogOut } from 'lucide-react';
import { useProjectStore, useConversationStore } from '@/lib/state/store';
import { apiClient } from '@/lib/api-client';
import type { Project, Conversation } from '@/types';
import { cn } from '@/lib/utils';

interface ProjectSidebarProps {
  onProjectSelect?: (project: Project) => void;
  onConversationSelect?: (conversation: Conversation) => void;
}

export function ProjectSidebar({ onProjectSelect, onConversationSelect }: ProjectSidebarProps) {
  const { projects, currentProject, setProjects, setCurrentProject } = useProjectStore();
  const { conversations, setConversations, setCurrentConversation } = useConversationStore();
  const [showNewProject, setShowNewProject] = useState(false);
  const [newProjectName, setNewProjectName] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadProjects();
    loadConversations();
  }, []);

  const loadProjects = async () => {
    const result = await apiClient.getProjects();
    if (result.success && result.data) {
      setProjects(result.data);
    }
  };

  const loadConversations = async () => {
    const result = await apiClient.getConversations();
    if (result.success && result.data) {
      setConversations(result.data);
    }
  };

  const handleCreateProject = async () => {
    if (!newProjectName.trim()) return;

    setLoading(true);
    const result = await apiClient.createProject({
      name: newProjectName,
      description: '',
      workspace_path: '',
      status: 'active',
    });

    if (result.success && result.data) {
      setProjects([...projects, result.data]);
      setNewProjectName('');
      setShowNewProject(false);
    }

    setLoading(false);
  };

  const handleSelectProject = (project: Project) => {
    setCurrentProject(project);
    if (onProjectSelect) {
      onProjectSelect(project);
    }
  };

  const handleSelectConversation = (conversation: Conversation) => {
    setCurrentConversation(conversation);
    if (onConversationSelect) {
      onConversationSelect(conversation);
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="p-4 border-b">
        <h1 className="text-xl font-bold">Fivoria AI</h1>
      </div>

      {/* Projects */}
      <ScrollArea className="flex-1">
        <div className="p-4 space-y-4">
          {/* Projects Section */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <div className="text-sm font-semibold text-muted-foreground">Projects</div>
              <Button
                size="icon"
                variant="ghost"
                onClick={() => setShowNewProject(!showNewProject)}
              >
                <Plus className="h-4 w-4" />
              </Button>
            </div>

            {showNewProject && (
              <div className="flex gap-2 mb-2">
                <Input
                  placeholder="Project name"
                  value={newProjectName}
                  onChange={(e) => setNewProjectName(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleCreateProject()}
                  disabled={loading}
                />
                <Button
                  size="sm"
                  onClick={handleCreateProject}
                  disabled={loading || !newProjectName.trim()}
                >
                  {loading ? '...' : 'Add'}
                </Button>
              </div>
            )}

            <div className="space-y-1">
              {projects.length === 0 ? (
                <div className="text-sm text-gray-400 py-2">No projects yet</div>
              ) : (
                projects.map((project) => (
                  <button
                    key={project.project_id}
                    onClick={() => handleSelectProject(project)}
                    className={cn(
                      "w-full flex items-center gap-2 px-2 py-2 rounded-md text-sm text-left",
                      currentProject?.project_id === project.project_id ? "text-white" : "hover:text-accent"
                    )}
                    style={{
                      backgroundColor: currentProject?.project_id === project.project_id ? 'var(--accent)' : 'transparent'
                    }}
                  >
                    <FolderOpen className="h-4 w-4" />
                    <span className="truncate">{project.name}</span>
                  </button>
                ))
              )}
            </div>
          </div>

          {/* Conversations Section */}
          <div>
            <div className="text-sm font-semibold text-gray-400 mb-2">
              Conversations
            </div>
            <div className="space-y-1">
              {conversations.length === 0 ? (
                <div className="text-sm text-gray-400 py-2">No conversations yet</div>
              ) : (
                conversations.map((conversation) => (
                  <button
                    key={conversation.conversation_id}
                    onClick={() => handleSelectConversation(conversation)}
                    className={cn(
                      "w-full flex items-center gap-2 px-2 py-2 rounded-md text-sm text-left hover:text-accent",
                      "text-gray-400"
                    )}
                  >
                    <MessageSquare className="h-4 w-4" />
                    <span className="truncate">{conversation.title}</span>
                  </button>
                ))
              )}
            </div>
          </div>
        </div>
      </ScrollArea>

      {/* Footer */}
      <div className="p-4 border-t space-y-2">
        <Button variant="ghost" className="w-full justify-start" size="sm">
          <Settings className="h-4 w-4 mr-2" />
          Settings
        </Button>
        <Button variant="ghost" className="w-full justify-start" size="sm">
          <LogOut className="h-4 w-4 mr-2" />
          Sign Out
        </Button>
      </div>
    </div>
  );
}
