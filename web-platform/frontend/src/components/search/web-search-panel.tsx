'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Search, ExternalLink, Clock, Globe } from 'lucide-react';
import { apiClient } from '@/lib/api-client';
import { cn } from '@/lib/utils';

interface SearchResult {
  title: string;
  url: string;
  snippet: string;
  source: string;
  published_at?: string;
}

export function WebSearchPanel() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchHistory, setSearchHistory] = useState<string[]>([]);

  const handleSearch = async () => {
    if (!query.trim()) return;

    setLoading(true);
    try {
      // Use web search tool via agent API
      const response = await apiClient.webSearch(query, 10);
      
      if (response.success && response.data) {
        setResults(response.data.results || []);
        
        // Add to history
        if (!searchHistory.includes(query)) {
          setSearchHistory(prev => [query, ...prev].slice(0, 10));
        }
      }
    } catch (error) {
      console.error('Search failed:', error);
    }
    setLoading(false);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleSearch();
    }
  };

  const handleHistoryClick = (historyQuery: string) => {
    setQuery(historyQuery);
    handleSearch();
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="h-10 border-b flex items-center px-4">
        <div className="flex items-center gap-2">
          <Globe className="h-4 w-4" />
          <span className="text-sm font-semibold">Web Search</span>
        </div>
      </div>

      {/* Search Input */}
      <div className="p-4 border-b">
        <div className="flex gap-2">
          <Input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Search the web..."
            disabled={loading}
          />
          <Button onClick={handleSearch} disabled={loading || !query.trim()}>
            <Search className="h-4 w-4" />
          </Button>
        </div>

        {/* Search History */}
        {searchHistory.length > 0 && (
          <div className="mt-3">
            <div className="text-xs text-muted-foreground mb-2 flex items-center gap-1">
              <Clock className="h-3 w-3" />
              Recent searches
            </div>
            <div className="flex flex-wrap gap-1">
              {searchHistory.map((historyQuery) => (
                <Button
                  key={historyQuery}
                  variant="ghost"
                  size="sm"
                  className="h-6 text-xs"
                  onClick={() => handleHistoryClick(historyQuery)}
                >
                  {historyQuery}
                </Button>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Results */}
      <ScrollArea className="flex-1">
        <div className="p-4">
          {loading ? (
            <div className="text-sm text-muted-foreground text-center py-8">
              Searching...
            </div>
          ) : results.length === 0 ? (
            <div className="text-sm text-muted-foreground text-center py-8">
              Enter a query to search the web
            </div>
          ) : (
            <div className="space-y-4">
              {results.map((result, idx) => (
                <div key={idx} className="p-3 rounded-lg border hover:bg-accent">
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1 min-w-0">
                      <a
                        href={result.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-sm font-medium text-blue-500 hover:underline block"
                      >
                        {result.title}
                      </a>
                      <p className="text-xs text-muted-foreground mt-1 line-clamp-2">
                        {result.snippet}
                      </p>
                      <div className="flex items-center gap-2 mt-2">
                        <span className="text-xs text-muted-foreground">{result.source}</span>
                        {result.published_at && (
                          <span className="text-xs text-muted-foreground">
                            • {new Date(result.published_at).toLocaleDateString()}
                          </span>
                        )}
                      </div>
                    </div>
                    <Button
                      size="icon"
                      variant="ghost"
                      className="h-7 w-7 flex-shrink-0"
                      onClick={() => window.open(result.url, '_blank')}
                    >
                      <ExternalLink className="h-3 w-3" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </ScrollArea>
    </div>
  );
}
