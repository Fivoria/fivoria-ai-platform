'use client';

import { useState, useRef } from 'react';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Upload, FileText, Trash2, Check } from 'lucide-react';
import { apiClient } from '@/lib/api-client';
import { cn } from '@/lib/utils';

interface DocumentUploadProps {
  projectId?: string;
}

interface UploadedDocument {
  id: string;
  name: string;
  size: number;
  status: 'uploading' | 'processing' | 'completed' | 'error';
  error?: string;
}

export function DocumentUpload({ projectId }: DocumentUploadProps) {
  const [documents, setDocuments] = useState<UploadedDocument[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    
    for (const file of files) {
      const docId = `doc-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
      
      setDocuments(prev => [...prev, {
        id: docId,
        name: file.name,
        size: file.size,
        status: 'uploading'
      }]);

      try {
        const result = await apiClient.uploadDocument(file, projectId);
        
        if (result.success) {
          setDocuments(prev => prev.map(doc => 
            doc.id === docId ? { ...doc, status: 'processing' } : doc
          ));

          // Simulate processing completion
          setTimeout(() => {
            setDocuments(prev => prev.map(doc => 
              doc.id === docId ? { ...doc, status: 'completed' } : doc
            ));
          }, 2000);
        }
      } catch (error) {
        setDocuments(prev => prev.map(doc => 
          doc.id === docId ? { ...doc, status: 'error', error: 'Upload failed' } : doc
        ));
      }
    }

    // Reset input
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleRemoveDocument = (docId: string) => {
    setDocuments(prev => prev.filter(doc => doc.id !== docId));
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="h-10 border-b flex items-center justify-between px-4">
        <div className="flex items-center gap-2">
          <FileText className="h-4 w-4" />
          <span className="text-sm font-semibold">Documents</span>
        </div>
        <Button
          size="sm"
          onClick={() => fileInputRef.current?.click()}
        >
          <Upload className="h-3 w-3 mr-1" />
          Upload
        </Button>
        <input
          ref={fileInputRef}
          type="file"
          multiple
          onChange={handleFileSelect}
          className="hidden"
          accept=".pdf,.doc,.docx,.txt,.md,.json,.csv"
        />
      </div>

      {/* Documents List */}
      <ScrollArea className="flex-1">
        <div className="p-4">
          {documents.length === 0 ? (
            <div className="text-center py-8">
              <FileText className="h-12 w-12 mx-auto mb-2 text-muted-foreground opacity-50" />
              <p className="text-sm text-muted-foreground">No documents uploaded</p>
              <p className="text-xs text-muted-foreground mt-1">
                Upload documents to add to knowledge base
              </p>
            </div>
          ) : (
            <div className="space-y-2">
              {documents.map((doc) => (
                <div
                  key={doc.id}
                  className="flex items-center gap-3 p-3 rounded-lg border bg-card"
                >
                  <FileText className="h-4 w-4 text-muted-foreground" />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate">{doc.name}</p>
                    <p className="text-xs text-muted-foreground">{formatFileSize(doc.size)}</p>
                  </div>
                  <div className="flex items-center gap-2">
                    {doc.status === 'uploading' && (
                      <span className="text-xs text-muted-foreground">Uploading...</span>
                    )}
                    {doc.status === 'processing' && (
                      <span className="text-xs text-blue-500">Processing...</span>
                    )}
                    {doc.status === 'completed' && (
                      <Check className="h-4 w-4 text-green-500" />
                    )}
                    {doc.status === 'error' && (
                      <span className="text-xs text-red-500" title={doc.error}>Error</span>
                    )}
                    <Button
                      size="icon"
                      variant="ghost"
                      className="h-6 w-6"
                      onClick={() => handleRemoveDocument(doc.id)}
                    >
                      <Trash2 className="h-3 w-3" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </ScrollArea>

      {/* Info */}
      <div className="p-3 border-t text-xs text-muted-foreground">
        Documents are processed for RAG/knowledge search
      </div>
    </div>
  );
}
