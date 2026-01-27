'use client';

import { Loader, CheckCircle2 } from 'lucide-react';

export function AIProcessingState() {
  return (
    <div className="rounded-lg border border-border bg-secondary/50 p-4 space-y-4">
      <div className="space-y-3">
        {/* Step 1: Upload */}
        <div className="flex items-start gap-3">
          <div className="rounded-full bg-primary/10 p-1.5 mt-0.5">
            <CheckCircle2 className="h-4 w-4 text-primary" />
          </div>
          <div className="flex-1">
            <p className="text-sm font-medium text-foreground">Video uploaded</p>
            <p className="text-xs text-muted-foreground mt-0.5">Ready for processing</p>
          </div>
        </div>

        {/* Step 2: Analyzing */}
        <div className="flex items-start gap-3">
          <div className="rounded-full bg-primary/10 p-1.5 mt-0.5 animate-pulse">
            <Loader className="h-4 w-4 text-primary animate-spin" />
          </div>
          <div className="flex-1">
            <p className="text-sm font-medium text-foreground">Analyzing content</p>
            <p className="text-xs text-muted-foreground mt-0.5">Detecting key moments and topics</p>
          </div>
        </div>

        {/* Step 3: Generating Ideas */}
        <div className="flex items-start gap-3 opacity-50">
          <div className="rounded-full bg-secondary border border-border p-1.5 mt-0.5">
            <div className="h-4 w-4 border-2 border-border border-t-primary rounded-full" />
          </div>
          <div className="flex-1">
            <p className="text-sm font-medium text-foreground">Generating ideas</p>
            <p className="text-xs text-muted-foreground mt-0.5">Creating AI-powered suggestions</p>
          </div>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="pt-2">
        <div className="flex justify-between items-center mb-2">
          <span className="text-xs font-medium text-muted-foreground">Processing</span>
          <span className="text-xs font-medium text-primary">45%</span>
        </div>
        <div className="h-1.5 bg-secondary rounded-full overflow-hidden">
          <div
            className="h-full bg-primary transition-all duration-500"
            style={{ width: '45%' }}
          />
        </div>
      </div>
    </div>
  );
}
