'use client';

import { Check, Loader2, Circle, AlertCircle } from 'lucide-react';

interface ProcessingProgressProps {
  currentStage: string | null;
  progress: number;
  message: string | null;
  error: string | null;
}

const STAGES = [
  { id: 'PENDING', label: 'Queued', description: 'Video queued for processing' },
  { id: 'INGESTING', label: 'Ingesting', description: 'Downloading video and extracting audio' },
  { id: 'TRANSCRIBING', label: 'Transcribing', description: 'Converting speech to text' },
  { id: 'UNDERSTANDING', label: 'Understanding', description: 'Analyzing semantic content' },
  { id: 'GROUPING', label: 'Grouping', description: 'Identifying idea segments' },
  { id: 'RANKING', label: 'Ranking', description: 'Scoring short-form potential' },
];

export function ProcessingProgress({
  currentStage,
  progress,
  message,
  error,
}: ProcessingProgressProps) {
  const getCurrentStageIndex = () => {
    if (!currentStage) return -1;
    return STAGES.findIndex((s) => s.id === currentStage);
  };

  const currentIndex = getCurrentStageIndex();

  const getStageStatus = (index: number) => {
    if (error) return 'error';
    if (index < currentIndex) return 'complete';
    if (index === currentIndex) return 'active';
    return 'pending';
  };

  return (
    <div className="space-y-4 rounded-lg border border-border bg-card p-6">
      <div>
        <p className="text-sm font-medium text-foreground">Processing Your Video</p>
        {error ? (
          <p className="mt-1 text-xs text-destructive">{error}</p>
        ) : (
          <p className="mt-1 text-xs text-muted-foreground">
            {message || 'Processing...'}
          </p>
        )}
      </div>

      {/* Progress Bar */}
      <div className="space-y-2">
        <div className="flex items-center justify-between text-xs">
          <span className="text-muted-foreground">
            {progress}%
          </span>
          {!error && progress < 100 && (
            <span className="flex items-center gap-1.5 text-primary">
              <Loader2 className="h-3 w-3 animate-spin" />
              Processing...
            </span>
          )}
          {progress === 100 && !error && (
            <span className="flex items-center gap-1.5 text-green-600">
              <Check className="h-3 w-3" />
              Complete!
            </span>
          )}
        </div>
        <div className="h-2 overflow-hidden rounded-full bg-secondary">
          <div
            className="h-full bg-primary transition-all duration-300"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      {/* Stage List */}
      <div className="space-y-3">
        {STAGES.map((stage, index) => {
          const status = getStageStatus(index);
          return (
            <div key={stage.id} className="flex items-start gap-3">
              {/* Icon - FIXED SIZE */}
              <div className="flex-shrink-0 mt-0.5">
                {status === 'complete' && (
                  <div className="rounded-full bg-primary p-1">
                    <Check className="h-3.5 w-3.5 text-primary-foreground" />
                  </div>
                )}
                {status === 'active' && (
                  <div className="rounded-full bg-primary/10 p-1">
                    <Loader2 className="h-3.5 w-3.5 text-primary animate-spin" />
                  </div>
                )}
                {status === 'pending' && (
                  <div className="rounded-full border-2 border-border p-1">
                    <Circle className="h-3.5 w-3.5 text-transparent" />
                  </div>
                )}
                {status === 'error' && (
                  <div className="rounded-full bg-destructive/10 p-1">
                    <AlertCircle className="h-3.5 w-3.5 text-destructive" />
                  </div>
                )}
              </div>

              {/* Content */}
              <div className="flex-1 min-w-0">
                <p
                  className={`text-sm font-medium ${
                    status === 'pending' ? 'text-muted-foreground' : 'text-foreground'
                  }`}
                >
                  {stage.label}
                </p>
                <p className="text-xs text-muted-foreground mt-0.5">
                  {status === 'complete'
                    ? 'Complete'
                    : status === 'active' && message
                      ? message
                      : stage.description}
                </p>
              </div>

              {/* Progress indicator for active stage */}
              {status === 'active' && (
                <div className="flex-shrink-0 text-xs font-medium text-primary">
                  {progress}%
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Error message */}
      {error && (
        <div className="rounded-md border border-destructive/50 bg-destructive/10 p-3">
          <p className="text-xs font-medium text-destructive mb-1">
            Processing Failed
          </p>
          <p className="text-xs text-destructive/80">{error}</p>
        </div>
      )}
    </div>
  );
}