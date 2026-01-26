'use client';

import { Check, Loader2, Circle, AlertCircle } from 'lucide-react';

interface ProcessingProgressProps {
  currentStage: string | null;
  progress: number;
  message: string | null;
  error: string | null;
}

const STAGES = [
  { id: 'PENDING', label: 'Queued', description: 'Waiting to start...' },
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
    <div className="rounded-lg border border-border bg-secondary/30 p-5">
      <div className="mb-4">
        <h3 className="text-sm font-semibold text-foreground mb-1">Processing Your Video</h3>
        {error ? (
          <p className="text-xs text-destructive">{error}</p>
        ) : (
          <p className="text-xs text-muted-foreground">{message || 'Processing...'}</p>
        )}
      </div>

      {/* Progress Bar */}
      <div className="mb-5">
        <div className="h-2 w-full rounded-full bg-secondary overflow-hidden">
          <div
            className={`h-full transition-all duration-500 ${
              error ? 'bg-destructive' : 'bg-primary'
            }`}
            style={{ width: `${progress}%` }}
          />
        </div>
        <div className="flex justify-between mt-1">
          <span className="text-xs text-muted-foreground">{progress}%</span>
          {!error && progress < 100 && (
            <span className="text-xs text-muted-foreground">Processing...</span>
          )}
          {progress === 100 && !error && (
            <span className="text-xs text-primary font-medium">Complete!</span>
          )}
        </div>
      </div>

      {/* Stage List */}
      <div className="space-y-3">
        {STAGES.map((stage, index) => {
          const status = getStageStatus(index);

          return (
            <div key={stage.id} className="flex items-start gap-3">
              {/* Icon */}
              <div className="flex-shrink-0 mt-0.5">
                {status === 'complete' && (
                  <div className="rounded-full bg-primary/20 p-1">
                    <Check className="h-3 w-3 text-primary" />
                  </div>
                )}
                {status === 'active' && (
                  <div className="rounded-full bg-primary/20 p-1">
                    <Loader2 className="h-3 w-3 text-primary animate-spin" />
                  </div>
                )}
                {status === 'pending' && (
                  <div className="rounded-full bg-muted p-1">
                    <Circle className="h-3 w-3 text-muted-foreground" />
                  </div>
                )}
                {status === 'error' && (
                  <div className="rounded-full bg-destructive/20 p-1">
                    <AlertCircle className="h-3 w-3 text-destructive" />
                  </div>
                )}
              </div>

              {/* Content */}
              <div className="flex-1 min-w-0">
                <p
                  className={`text-sm font-medium ${
                    status === 'active'
                      ? 'text-foreground'
                      : status === 'complete'
                      ? 'text-muted-foreground'
                      : status === 'error'
                      ? 'text-destructive'
                      : 'text-muted-foreground/60'
                  }`}
                >
                  {stage.label}
                </p>
                <p
                  className={`text-xs ${
                    status === 'active'
                      ? 'text-muted-foreground'
                      : 'text-muted-foreground/60'
                  }`}
                >
                  {status === 'active' && message ? message : stage.description}
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
        <div className="mt-4 rounded-md bg-destructive/10 border border-destructive/20 p-3">
          <div className="flex items-start gap-2">
            <AlertCircle className="h-4 w-4 text-destructive flex-shrink-0 mt-0.5" />
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-destructive">Processing Failed</p>
              <p className="text-xs text-destructive/80 mt-1">{error}</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
