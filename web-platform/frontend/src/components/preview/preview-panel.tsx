'use client';

import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Monitor, ExternalLink, RefreshCw, X, Maximize2, Minimize2, Smartphone, Tablet, Laptop } from 'lucide-react';
import { cn } from '@/lib/utils';

interface PreviewPanelProps {
  projectId: string;
  previewUrl?: string;
  onClose?: () => void;
}

type ViewportSize = 'mobile' | 'tablet' | 'desktop';

export function PreviewPanel({ projectId, previewUrl, onClose }: PreviewPanelProps) {
  const [url, setUrl] = useState(previewUrl || '');
  const [isLoading, setIsLoading] = useState(false);
  const [viewport, setViewport] = useState<ViewportSize>('desktop');
  const [isMaximized, setIsMaximized] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const viewportSizes = {
    mobile: 'w-[375px]',
    tablet: 'w-[768px]',
    desktop: 'w-full',
  };

  const handleRefresh = () => {
    setIsLoading(true);
    setError(null);
    // In production, this would trigger a preview refresh
    setTimeout(() => setIsLoading(false), 1000);
  };

  const handleOpenExternal = () => {
    if (url) {
      window.open(url, '_blank');
    }
  };

  const handleViewportChange = (size: ViewportSize) => {
    setViewport(size);
  };

  return (
    <div className={cn(
      "flex flex-col bg-card border-l",
      isMaximized ? "fixed inset-0 z-50" : "w-96"
    )}>
      {/* Header */}
      <div className="h-14 border-b flex items-center justify-between px-4">
        <div className="flex items-center gap-2">
          <Monitor className="h-4 w-4" />
          <span className="text-sm font-semibold">Preview</span>
        </div>
        <div className="flex items-center gap-1">
          <Button
            size="icon"
            variant="ghost"
            className="h-7 w-7"
            onClick={handleRefresh}
            disabled={isLoading}
            title="Refresh"
          >
            <RefreshCw className={cn("h-3 w-3", isLoading && "animate-spin")} />
          </Button>
          <Button
            size="icon"
            variant="ghost"
            className="h-7 w-7"
            onClick={handleOpenExternal}
            disabled={!url}
            title="Open in new tab"
          >
            <ExternalLink className="h-3 w-3" />
          </Button>
          <Button
            size="icon"
            variant="ghost"
            className="h-7 w-7"
            onClick={() => setIsMaximized(!isMaximized)}
          >
            {isMaximized ? (
              <Minimize2 className="h-3 w-3" />
            ) : (
              <Maximize2 className="h-3 w-3" />
            )}
          </Button>
          {onClose && (
            <Button
              size="icon"
              variant="ghost"
              className="h-7 w-7"
              onClick={onClose}
            >
              <X className="h-3 w-3" />
            </Button>
          )}
        </div>
      </div>

      {/* Viewport Controls */}
      <div className="h-10 border-b flex items-center justify-center gap-2 px-4 bg-muted">
        <Button
          size="icon"
          variant={viewport === 'mobile' ? 'default' : 'ghost'}
          className="h-7 w-7"
          onClick={() => handleViewportChange('mobile')}
          title="Mobile"
        >
          <Smartphone className="h-3 w-3" />
        </Button>
        <Button
          size="icon"
          variant={viewport === 'tablet' ? 'default' : 'ghost'}
          className="h-7 w-7"
          onClick={() => handleViewportChange('tablet')}
          title="Tablet"
        >
          <Tablet className="h-3 w-3" />
        </Button>
        <Button
          size="icon"
          variant={viewport === 'desktop' ? 'default' : 'ghost'}
          className="h-7 w-7"
          onClick={() => handleViewportChange('desktop')}
          title="Desktop"
        >
          <Laptop className="h-3 w-3" />
        </Button>
      </div>

      {/* Preview Area */}
      <ScrollArea className="flex-1 bg-muted">
        <div className="flex items-center justify-center min-h-full p-4">
          {url ? (
            <div className={cn(
              "bg-white rounded-lg shadow-lg overflow-hidden transition-all",
              viewportSizes[viewport],
              isMaximized && "h-full"
            )}>
              {isLoading ? (
                <div className="flex items-center justify-center h-48">
                  <RefreshCw className="h-6 w-6 animate-spin text-muted-foreground" />
                </div>
              ) : error ? (
                <div className="flex items-center justify-center h-48 text-red-500">
                  <p className="text-sm">{error}</p>
                </div>
              ) : (
                <iframe
                  src={url}
                  className="w-full h-full border-0"
                  title="Preview"
                  sandbox="allow-scripts allow-same-origin allow-forms"
                  onLoad={() => setIsLoading(false)}
                  onError={() => {
                    setIsLoading(false);
                    setError('Failed to load preview');
                  }}
                />
              )}
            </div>
          ) : (
            <div className="text-center text-muted-foreground">
              <Monitor className="h-12 w-12 mx-auto mb-2 opacity-50" />
              <p className="text-sm">No preview available</p>
              <p className="text-xs mt-1">Start a dev server to see the preview</p>
            </div>
          )}
        </div>
      </ScrollArea>

      {/* URL Bar */}
      {url && (
        <div className="h-8 border-t flex items-center px-4 bg-muted text-xs text-muted-foreground">
          <span className="truncate">{url}</span>
        </div>
      )}
    </div>
  );
}
