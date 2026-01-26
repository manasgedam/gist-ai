import { Share2, Download, ChevronDown } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface TopAppBarProps {
  projectName: string;
  autoSave: string;
}

export function TopAppBar({ projectName, autoSave }: TopAppBarProps) {
  return (
    <header className="flex items-center justify-between border-b border-border bg-background px-6 py-3">
      <div className="flex items-center gap-4">
        <h1 className="text-lg font-semibold text-foreground">{projectName}</h1>
        <div className="flex items-center gap-1 rounded-full bg-secondary px-3 py-1 text-xs text-muted-foreground">
          <div className="h-1.5 w-1.5 rounded-full bg-primary" />
          <span>{autoSave}</span>
        </div>
      </div>

      <div className="flex items-center gap-3">
        <Button variant="outline" size="sm" className="gap-2 bg-transparent">
          <Share2 className="h-4 w-4" />
          Share
        </Button>
        <Button variant="default" size="sm" className="gap-2">
          <Download className="h-4 w-4" />
          Export
        </Button>
      </div>
    </header>
  );
}
