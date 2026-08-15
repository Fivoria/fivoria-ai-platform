'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { ChatInterface } from '@/components/chat/chat-interface';
import { ProjectSidebar } from '@/components/sidebar/project-sidebar';
import { FileExplorer } from '@/components/explorer/file-explorer';
import { CodeEditor } from '@/components/editor/code-editor';
import { useUIStore, useAuthStore } from '@/lib/state/store';
import type { File as FileType } from '@/types';

export default function Workspace() {
  const router = useRouter();
  const { isAuthenticated } = useAuthStore();
  const { explorerOpen, sidebarOpen } = useUIStore();
  const [selectedFile, setSelectedFile] = useState<FileType | null>(null);

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/auth/login');
    }
  }, [isAuthenticated, router]);

  if (!isAuthenticated) {
    return null;
  }

  const handleFileSelect = (file: FileType) => {
    setSelectedFile(file);
  };

  const handleFileSave = async (content: string) => {
    if (selectedFile) {
      // Save file via API
      console.log('Saving file:', selectedFile.path);
    }
  };

  return (
    <div className="flex h-screen" style={{ backgroundColor: 'var(--background)' }}>
      {/* Left Sidebar */}
      {sidebarOpen && (
        <aside className="w-64 border-r flex flex-col" style={{ backgroundColor: 'var(--card-bg)', borderColor: 'var(--border-color)' }}>
          <ProjectSidebar />
        </aside>
      )}

      {/* Main Content */}
      <main className="flex-1 flex flex-col">
        {/* Header */}
        <header className="h-14 border-b flex items-center px-4" style={{ borderColor: 'var(--border-color)' }}>
          <h2 className="text-lg font-semibold">Workspace</h2>
        </header>

        {/* Content Area */}
        <div className="flex-1 flex">
          {/* File Explorer */}
          {explorerOpen && (
            <aside className="w-64 border-r" style={{ backgroundColor: 'var(--card-bg)', borderColor: 'var(--border-color)' }}>
              <FileExplorer 
                projectId="demo-project"
                onFileSelect={handleFileSelect}
              />
            </aside>
          )}

          {/* Chat / Editor Area */}
          <div className="flex-1 flex flex-col">
            {selectedFile ? (
              <div className="flex-1">
                <CodeEditor 
                  file={selectedFile}
                  onSave={handleFileSave}
                />
              </div>
            ) : (
              <div className="flex-1">
                <ChatInterface 
                  conversationId="demo-conversation"
                  projectId="demo-project"
                />
              </div>
            )}
          </div>
        </div>
      </main>

      {/* Right Panel - Preview */}
      <aside className="w-96 border-l bg-card flex flex-col">
        <div className="p-4 border-b">
          <h3 className="text-sm font-semibold">Preview</h3>
        </div>
        <div className="flex-1 flex items-center justify-center text-muted-foreground">
          <p className="text-sm">No preview available</p>
        </div>
      </aside>

      {/* Bottom Panel - Terminal */}
      <div className="absolute bottom-0 left-64 right-96 h-48 border-t bg-card flex flex-col">
        <div className="p-2 border-b flex items-center justify-between">
          <h3 className="text-sm font-semibold">Terminal</h3>
        </div>
        <div className="flex-1 p-2 font-mono text-sm bg-muted overflow-auto">
          <p className="text-muted-foreground">Terminal ready</p>
        </div>
      </div>
    </div>
  );
}
