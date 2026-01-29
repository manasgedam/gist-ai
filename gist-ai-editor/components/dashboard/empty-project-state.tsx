'use client';

import { FilmIcon } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface EmptyProjectsStateProps {
  onCreateNew?: () => void;
}

export function EmptyProjectsState({ onCreateNew }: EmptyProjectsStateProps) {
  return (
    <div className="flex flex-col items-center justify-center min-h-[400px] px-4">
      <div className="rounded-full bg-secondary/50 p-6 mb-6">
        <FilmIcon className="h-12 w-12 text-muted-foreground" />
      </div>

      <h2 className="text-2xl font-semibold text-foreground mb-2 text-center">
        No projects yet
      </h2>

      <p className="text-muted-foreground text-center mb-8 max-w-sm">
        Get started by creating your first video project. Upload a video or paste a YouTube link to begin.
      </p>

      <Button onClick={onCreateNew} size="lg" className="gap-2">
        <FilmIcon className="h-5 w-5" />
        Create your first project
      </Button>
    </div>
  );
}
