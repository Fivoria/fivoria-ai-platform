'use client';

import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { 
  GitBranch, 
  GitCommit, 
  GitMerge, 
  RefreshCw, 
  Plus,
  History,
  FileDiff
} from 'lucide-react';
import { apiClient } from '@/lib/api-client';
import { cn } from '@/lib/utils';

interface GitPanelProps {
  projectId: string;
}

interface Commit {
  hash: string;
  author: string;
  email: string;
  message: string;
  date: string;
}

interface Branch {
  name: string;
  current: boolean;
}

export function GitPanel({ projectId }: GitPanelProps) {
  const [commits, setCommits] = useState<Commit[]>([]);
  const [branches, setBranches] = useState<Branch[]>([]);
  const [currentBranch, setCurrentBranch] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<'commits' | 'branches'>('commits');

  useEffect(() => {
    loadGitData();
  }, [projectId]);

  const loadGitData = async () => {
    setLoading(true);
    try {
      const [commitsResult, branchesResult] = await Promise.all([
        apiClient.getGitHistory(projectId),
        apiClient.getGitBranches(projectId)
      ]);

      if (commitsResult.success && commitsResult.data) {
        setCommits(commitsResult.data.commits || []);
      }

      if (branchesResult.success && branchesResult.data) {
        setBranches(branchesResult.data.branches || []);
        setCurrentBranch(branchesResult.data.current || null);
      }
    } catch (error) {
      console.error('Failed to load Git data:', error);
    }
    setLoading(false);
  };

  const handleCommit = async () => {
    // TODO: Implement commit dialog
    console.log('Commit');
  };

  const handlePush = async () => {
    // TODO: Implement push
    console.log('Push');
  };

  const handlePull = async () => {
    // TODO: Implement pull
    console.log('Pull');
  };

  const handleCheckout = async (branch: string) => {
    await apiClient.gitCheckout(projectId, branch);
    loadGitData();
  };

  const handleCreateBranch = async () => {
    // TODO: Implement create branch dialog
    console.log('Create branch');
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="h-10 border-b flex items-center justify-between px-4">
        <div className="flex items-center gap-2">
          <GitBranch className="h-4 w-4" />
          <span className="text-sm font-semibold">Git</span>
          {currentBranch && (
            <span className="text-xs text-muted-foreground">{currentBranch}</span>
          )}
        </div>
        <Button
          size="icon"
          variant="ghost"
          className="h-7 w-7"
          onClick={loadGitData}
          disabled={loading}
        >
          <RefreshCw className={cn("h-3 w-3", loading && "animate-spin")} />
        </Button>
      </div>

      {/* Tabs */}
      <div className="h-8 border-b flex items-center px-2 gap-1">
        <Button
          size="sm"
          variant={activeTab === 'commits' ? 'default' : 'ghost'}
          className="h-6 text-xs"
          onClick={() => setActiveTab('commits')}
        >
          <History className="h-3 w-3 mr-1" />
          Commits
        </Button>
        <Button
          size="sm"
          variant={activeTab === 'branches' ? 'default' : 'ghost'}
          className="h-6 text-xs"
          onClick={() => setActiveTab('branches')}
        >
          <GitBranch className="h-3 w-3 mr-1" />
          Branches
        </Button>
      </div>

      {/* Content */}
      <ScrollArea className="flex-1">
        {activeTab === 'commits' ? (
          <div className="p-2 space-y-2">
            {commits.length === 0 ? (
              <p className="text-sm text-muted-foreground">No commits yet</p>
            ) : (
              commits.map((commit) => (
                <div key={commit.hash} className="p-2 rounded hover:bg-accent">
                  <div className="flex items-start gap-2">
                    <GitCommit className="h-4 w-4 mt-0.5 text-muted-foreground" />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium truncate">{commit.message}</p>
                      <p className="text-xs text-muted-foreground">
                        {commit.author} • {new Date(commit.date).toLocaleDateString()}
                      </p>
                      <p className="text-xs text-muted-foreground font-mono">
                        {commit.hash.slice(0, 7)}
                      </p>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        ) : (
          <div className="p-2 space-y-1">
            {branches.length === 0 ? (
              <p className="text-sm text-muted-foreground">No branches yet</p>
            ) : (
              branches.map((branch) => (
                <button
                  key={branch.name}
                  onClick={() => handleCheckout(branch.name)}
                  className={cn(
                    "w-full flex items-center gap-2 px-2 py-1.5 rounded text-sm text-left hover:bg-accent",
                    branch.current && "bg-accent"
                  )}
                >
                  <GitBranch className="h-3 w-3" />
                  <span className="flex-1 truncate">{branch.name}</span>
                  {branch.current && (
                    <span className="text-xs text-muted-foreground">current</span>
                  )}
                </button>
              ))
            )}
            <Button
              variant="ghost"
              size="sm"
              className="w-full justify-start mt-2"
              onClick={handleCreateBranch}
            >
              <Plus className="h-3 w-3 mr-2" />
              New Branch
            </Button>
          </div>
        )}
      </ScrollArea>

      {/* Actions */}
      <div className="h-10 border-t flex items-center justify-center gap-2 px-4">
        <Button size="sm" variant="outline" onClick={handleCommit}>
          <GitCommit className="h-3 w-3 mr-1" />
          Commit
        </Button>
        <Button size="sm" variant="outline" onClick={handlePull}>
          <GitMerge className="h-3 w-3 mr-1" />
          Pull
        </Button>
        <Button size="sm" variant="outline" onClick={handlePush}>
          <GitBranch className="h-3 w-3 mr-1" />
          Push
        </Button>
      </div>
    </div>
  );
}
