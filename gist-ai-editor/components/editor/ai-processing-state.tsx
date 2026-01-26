'use client';

import { CheckCircle2 } from 'lucide-react';

interface ProcessingStep {
  id: string;
  label: string;
  status: 'pending' | 'active' | 'complete';
}

const PROCESSING_STEPS: ProcessingStep[] = [
  { id: '1', label: 'Transcribing video', status: 'complete' },
  { id: '2', label: 'Understanding topics and ideas', status: 'active' },
  { id: '3', label: 'Grouping related moments', status: 'pending' },
  { id: '4', label: 'Ranking short-form potential', status: 'pending' },
];

export function AIProcessingState() {
  const completedSteps = PROCESSING_STEPS.filter(s => s.status === 'complete').length;
  const totalSteps = PROCESSING_STEPS.length;
  const progress = (completedSteps / totalSteps) * 100;

  return (
    <div className="space-y-4 rounded-lg border border-border bg-secondary p-4">
      <div>
        <p className="text-sm font-medium text-foreground">Processing Your Video</p>
        <p className="mt-1 text-xs text-muted-foreground">AI is analyzing your video to find the best short-form content</p>
      </div>

      {/* Progress Bar */}
      <div className="space-y-2">
        <div className="flex justify-between text-xs text-muted-foreground">
          <span>Progress</span>
          <span>{completedSteps} of {totalSteps}</span>
        </div>
        <div className="h-1.5 overflow-hidden rounded-full bg-border">
          <div
            className="h-full bg-primary transition-all duration-500"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      {/* Processing Steps */}
      <div className="space-y-2">
        {PROCESSING_STEPS.map((step) => (
          <div key={step.id} className="flex items-center gap-2">
            <div
              className={`flex h-5 w-5 items-center justify-center rounded-full flex-shrink-0 ${
                step.status === 'complete'
                  ? 'bg-primary'
                  : step.status === 'active'
                    ? 'border-2 border-primary bg-background'
                    : 'border-2 border-border bg-background'
              }`}
            >
              {step.status === 'complete' && (
                <CheckCircle2 className="h-3 w-3 text-primary-foreground" />
              )}
              {step.status === 'active' && (
                <div className="h-2 w-2 rounded-full bg-primary animate-pulse" />
              )}
            </div>
            <span
              className={`text-xs ${
                step.status === 'complete'
                  ? 'text-foreground'
                  : 'text-muted-foreground'
              }`}
            >
              {step.label}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
