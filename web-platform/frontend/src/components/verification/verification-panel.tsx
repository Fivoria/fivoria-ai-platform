'use client';

import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { CheckCircle, XCircle, AlertCircle, RefreshCw, Play } from 'lucide-react';
import { apiClient } from '@/lib/api-client';
import { cn } from '@/lib/utils';

interface TestResult {
  name: string;
  status: 'passed' | 'failed' | 'skipped' | 'running';
  duration?: number;
  error?: string;
}

export function VerificationPanel() {
  const [tests, setTests] = useState<TestResult[]>([]);
  const [running, setRunning] = useState(false);

  const handleRunTests = async () => {
    setRunning(true);
    setTests([
      { name: 'Unit Tests', status: 'running' },
      { name: 'Integration Tests', status: 'skipped' },
      { name: 'Linting', status: 'skipped' },
      { name: 'Type Checking', status: 'skipped' },
    ]);

    // Simulate test execution
    await new Promise(resolve => setTimeout(resolve, 1000));
    setTests(prev => prev.map(t => t.name === 'Unit Tests' ? { ...t, status: 'passed', duration: 1.2 } : t));

    await new Promise(resolve => setTimeout(resolve, 500));
    setTests(prev => prev.map(t => t.name === 'Integration Tests' ? { ...t, status: 'running' } : t));

    await new Promise(resolve => setTimeout(resolve, 1500));
    setTests(prev => prev.map(t => t.name === 'Integration Tests' ? { ...t, status: 'failed', duration: 2.3, error: 'Test failed: Expected 200 but got 500' } : t));

    await new Promise(resolve => setTimeout(resolve, 500));
    setTests(prev => prev.map(t => t.name === 'Linting' ? { ...t, status: 'running' } : t));

    await new Promise(resolve => setTimeout(resolve, 800));
    setTests(prev => prev.map(t => t.name === 'Linting' ? { ...t, status: 'passed', duration: 0.8 } : t));

    await new Promise(resolve => setTimeout(resolve, 500));
    setTests(prev => prev.map(t => t.name === 'Type Checking' ? { ...t, status: 'running' } : t));

    await new Promise(resolve => setTimeout(resolve, 600));
    setTests(prev => prev.map(t => t.name === 'Type Checking' ? { ...t, status: 'passed', duration: 0.6 } : t));

    setRunning(false);
  };

  const getStatusIcon = (status: string) => {
    const icons = {
      passed: <CheckCircle className="h-4 w-4 text-green-500" />,
      failed: <XCircle className="h-4 w-4 text-red-500" />,
      skipped: <AlertCircle className="h-4 w-4 text-yellow-500" />,
      running: <RefreshCw className="h-4 w-4 text-blue-500 animate-spin" />,
    };
    return icons[status as keyof typeof icons] || <AlertCircle className="h-4 w-4" />;
  };

  const passedCount = tests.filter(t => t.status === 'passed').length;
  const failedCount = tests.filter(t => t.status === 'failed').length;
  const totalCount = tests.length;

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="h-10 border-b flex items-center justify-between px-4">
        <div className="flex items-center gap-2">
          <CheckCircle className="h-4 w-4" />
          <span className="text-sm font-semibold">Verification</span>
        </div>
        <Button
          size="sm"
          onClick={handleRunTests}
          disabled={running}
        >
          <Play className="h-3 w-3 mr-1" />
          Run Tests
        </Button>
      </div>

      {/* Summary */}
      <div className="p-3 border-b bg-muted">
        <div className="flex items-center justify-between text-sm">
          <span>Tests: {totalCount}</span>
          <div className="flex items-center gap-3">
            <span className="text-green-500">{passedCount} passed</span>
            <span className="text-red-500">{failedCount} failed</span>
          </div>
        </div>
      </div>

      {/* Tests */}
      <ScrollArea className="flex-1">
        <div className="p-4">
          {tests.length === 0 ? (
            <div className="text-center py-8">
              <CheckCircle className="h-12 w-12 mx-auto mb-2 text-muted-foreground opacity-50" />
              <p className="text-sm text-muted-foreground">No tests run yet</p>
              <p className="text-xs text-muted-foreground mt-1">
                Click "Run Tests" to verify the project
              </p>
            </div>
          ) : (
            <div className="space-y-2">
              {tests.map((test, idx) => (
                <div key={idx} className="p-3 rounded-lg border bg-card">
                  <div className="flex items-start gap-3">
                    {getStatusIcon(test.status)}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between">
                        <p className="text-sm font-medium">{test.name}</p>
                        {test.duration && (
                          <span className="text-xs text-muted-foreground">{test.duration}s</span>
                        )}
                      </div>
                      {test.error && (
                        <p className="text-xs text-red-500 mt-1">{test.error}</p>
                      )}
                      <div className="flex items-center gap-2 mt-2">
                        <span className={cn(
                          "text-xs px-1.5 py-0.5 rounded",
                          test.status === 'passed' && "bg-green-500/20 text-green-500",
                          test.status === 'failed' && "bg-red-500/20 text-red-500",
                          test.status === 'skipped' && "bg-yellow-500/20 text-yellow-500",
                          test.status === 'running' && "bg-blue-500/20 text-blue-500"
                        )}>
                          {test.status.toUpperCase()}
                        </span>
                      </div>
                    </div>
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
