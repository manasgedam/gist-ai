'use client';

import React from "react"

import { useState, useRef } from 'react';
import { Upload, Link as LinkIcon, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';

interface VideoUploadProps {
  onVideoSelect?: (file: File | string) => void;
  onVideoSubmit?: (videoId: string) => void;
}

export function VideoUpload({ onVideoSelect, onVideoSubmit }: VideoUploadProps) {
  const [uploadMethod, setUploadMethod] = useState<'file' | 'youtube'>('youtube');
  const [youtubeUrl, setYoutubeUrl] = useState('');
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      const file = files[0];
      if (file.type.startsWith('video/')) {
        setUploadedFile(file);
        onVideoSelect?.(file);
      }
    }
  };

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.currentTarget.files;
    if (files && files.length > 0) {
      const file = files[0];
      if (file.type.startsWith('video/')) {
        setUploadedFile(file);
        onVideoSelect?.(file);
      }
    }
  };

  const handleYoutubeSubmit = async () => {
    if (youtubeUrl.trim() && onVideoSubmit) {
      setIsSubmitting(true);
      try {
        // Call the parent callback with the YouTube URL
        onVideoSubmit(youtubeUrl);
        setYoutubeUrl('');
      } catch (error) {
        console.error('Failed to submit YouTube URL:', error);
      } finally {
        setIsSubmitting(false);
      }
    }
  };

  const clearUpload = () => {
    setUploadedFile(null);
    setYoutubeUrl('');
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  return (
    <div className="space-y-4">
      {/* Upload Method Tabs */}
      <div className="flex gap-2 rounded-lg bg-secondary p-1">
        <button
          onClick={() => setUploadMethod('file')}
          className={`flex-1 rounded-md px-3 py-2 text-sm font-medium transition-all ${
            uploadMethod === 'file'
              ? 'bg-background text-foreground shadow-sm'
              : 'text-muted-foreground hover:text-foreground'
          }`}
        >
          <Upload className="inline-block h-4 w-4 mr-2" />
          Upload
        </button>
        <button
          onClick={() => setUploadMethod('youtube')}
          className={`flex-1 rounded-md px-3 py-2 text-sm font-medium transition-all ${
            uploadMethod === 'youtube'
              ? 'bg-background text-foreground shadow-sm'
              : 'text-muted-foreground hover:text-foreground'
          }`}
        >
          <LinkIcon className="inline-block h-4 w-4 mr-2" />
          YouTube
        </button>
      </div>

      {/* File Upload Section */}
      {uploadMethod === 'file' && (
        <div>
          {!uploadedFile ? (
            <div
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
              className={`rounded-lg border-2 border-dashed transition-all duration-200 cursor-pointer p-8 text-center ${
                isDragging
                  ? 'border-primary bg-primary/5'
                  : 'border-border bg-secondary/30 hover:border-border/80 hover:bg-secondary/50'
              }`}
            >
              <div className="flex flex-col items-center justify-center">
                <div className="rounded-full bg-primary/10 p-3 mb-3">
                  <Upload className="h-6 w-6 text-primary" />
                </div>
                <p className="text-sm font-semibold text-foreground">Drop your video here</p>
                <p className="mt-1 text-xs text-muted-foreground">or click to browse (MP4, WebM, etc.)</p>
                <p className="mt-2 text-xs text-muted-foreground/60">File upload coming soon - use YouTube for now</p>
              </div>
              <input
                ref={fileInputRef}
                type="file"
                accept="video/*"
                onChange={handleFileInput}
                className="hidden"
                disabled
              />
            </div>
          ) : (
            <div className="rounded-lg border border-border bg-secondary/50 p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="rounded-lg bg-primary/10 p-2">
                    <Upload className="h-5 w-5 text-primary" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-foreground truncate">{uploadedFile.name}</p>
                    <p className="text-xs text-muted-foreground">
                      {(uploadedFile.size / 1024 / 1024).toFixed(2)} MB
                    </p>
                  </div>
                </div>
                <button
                  onClick={clearUpload}
                  className="p-1 rounded-lg hover:bg-background transition-colors"
                >
                  <X className="h-4 w-4 text-muted-foreground hover:text-foreground" />
                </button>
              </div>
              <div className="mt-3 flex gap-2">
                <Button size="sm" className="flex-1" disabled>
                  Ready to Process
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={clearUpload}
                >
                  Change
                </Button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* YouTube Link Section */}
      {uploadMethod === 'youtube' && (
        <div className="space-y-3">
          <div>
            <label className="text-xs font-medium text-muted-foreground block mb-2">
              YouTube Video URL
            </label>
            <Input
              placeholder="https://www.youtube.com/watch?v=..."
              value={youtubeUrl}
              onChange={(e) => setYoutubeUrl(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && !isSubmitting && handleYoutubeSubmit()}
              className="text-sm"
              disabled={isSubmitting}
            />
            <p className="mt-1 text-xs text-muted-foreground">
              Paste a YouTube URL to analyze the video
            </p>
          </div>
          <Button
            onClick={handleYoutubeSubmit}
            disabled={!youtubeUrl.trim() || isSubmitting}
            className="w-full"
            size="sm"
          >
            {isSubmitting ? (
              <>Processing...</>
            ) : (
              <>
                <LinkIcon className="h-4 w-4 mr-2" />
                Import YouTube Video
              </>
            )}
          </Button>
        </div>
      )}   </div>
  );
}
