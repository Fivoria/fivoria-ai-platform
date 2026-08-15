'use client';

import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { 
  File, 
  Folder, 
  FolderOpen, 
  ChevronRight, 
  ChevronDown,
  Plus,
  Trash2,
  Edit
} from 'lucide-react';
import { apiClient } from '@/lib/api-client';
import type { File as FileType } from '@/types';
import { cn } from '@/lib/utils';

interface FileExplorerProps {
  projectId: string;
  onFileSelect?: (file: FileType) => void;
}

interface FileNode {
  path: string;
  name: string;
  type: 'file' | 'folder';
  children?: FileNode[];
  expanded?: boolean;
}

export function FileExplorer({ projectId, onFileSelect }: FileExplorerProps) {
  const [files, setFiles] = useState<FileType[]>([]);
  const [tree, setTree] = useState<FileNode[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedPath, setSelectedPath] = useState<string | null>(null);

  useEffect(() => {
    loadFiles();
  }, [projectId]);

  const loadFiles = async () => {
    setLoading(true);
    const result = await apiClient.getFiles(projectId);
    if (result.success && result.data) {
      setFiles(result.data);
      setTree(buildFileTree(result.data));
    }
    setLoading(false);
  };

  const buildFileTree = (fileList: FileType[]): FileNode[] => {
    const nodeMap = new Map<string, FileNode>();
    const rootNodes: FileNode[] = [];

    // Create nodes for all files
    fileList.forEach((file) => {
      const parts = file.path.split('/');
      let currentPath = '';

      parts.forEach((part, index) => {
        const isLast = index === parts.length - 1;
        currentPath = currentPath ? `${currentPath}/${part}` : part;

        if (!nodeMap.has(currentPath)) {
          const node: FileNode = {
            path: currentPath,
            name: part,
            type: isLast ? 'file' : 'folder',
            children: isLast ? undefined : [],
            expanded: false,
          };
          nodeMap.set(currentPath, node);

          // Add to parent or root
          if (index === 0) {
            rootNodes.push(node);
          } else {
            const parentPath = parts.slice(0, index).join('/');
            const parent = nodeMap.get(parentPath);
            if (parent && parent.children) {
              parent.children.push(node);
            }
          }
        }
      });
    });

    return rootNodes;
  };

  const toggleExpand = (node: FileNode) => {
    const updateNode = (nodes: FileNode[]): FileNode[] => {
      return nodes.map((n) => {
        if (n.path === node.path) {
          return { ...n, expanded: !n.expanded };
        }
        if (n.children) {
          return { ...n, children: updateNode(n.children) };
        }
        return n;
      });
    };

    setTree(updateNode(tree));
  };

  const handleFileSelect = (node: FileNode) => {
    if (node.type === 'file') {
      setSelectedPath(node.path);
      const file = files.find((f) => f.path === node.path);
      if (file && onFileSelect) {
        onFileSelect(file);
      }
    } else {
      toggleExpand(node);
    }
  };

  const renderNode = (node: FileNode, level: number = 0): React.ReactNode => {
    const isSelected = selectedPath === node.path;
    const paddingLeft = level * 12;

    return (
      <div key={node.path}>
        <button
          onClick={() => handleFileSelect(node)}
          className={cn(
            "w-full flex items-center gap-1 px-2 py-1 rounded text-sm text-left hover:text-accent",
            isSelected && "text-white"
          )}
          style={{
            paddingLeft: `${paddingLeft + 8}px`,
            backgroundColor: isSelected ? 'var(--accent)' : 'transparent'
          }}
        >
          {node.type === 'folder' ? (
            <>
              {node.expanded ? (
                <ChevronDown className="h-3 w-3" />
              ) : (
                <ChevronRight className="h-3 w-3" />
              )}
              {node.expanded ? (
                <FolderOpen className="h-4 w-4" style={{ color: 'var(--accent)' }} />
              ) : (
                <Folder className="h-4 w-4" style={{ color: 'var(--accent)' }} />
              )}
            </>
          ) : (
            <>
              <span className="w-4" />
              <File className="h-4 w-4 text-gray-500" />
            </>
          )}
          <span className="truncate">{node.name}</span>
        </button>
        {node.expanded && node.children && (
          <div>{node.children.map((child) => renderNode(child, level + 1))}</div>
        )}
      </div>
    );
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="p-2 border-b flex items-center justify-between">
        <div className="text-sm font-semibold">Files</div>
        <Button size="icon" variant="ghost" className="h-6 w-6">
          <Plus className="h-3 w-3" />
        </Button>
      </div>

      {/* File Tree */}
      <ScrollArea className="flex-1">
        <div className="p-2">
          {loading ? (
            <div className="text-sm text-muted-foreground py-2">Loading...</div>
          ) : tree.length === 0 ? (
            <div className="text-sm text-muted-foreground py-2">No files yet</div>
          ) : (
            <div className="space-y-0.5">
              {tree.map((node) => renderNode(node))}
            </div>
          )}
        </div>
      </ScrollArea>
    </div>
  );
}
