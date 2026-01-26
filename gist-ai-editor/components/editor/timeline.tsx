interface TimelineProps {
  currentTime: number;
  duration: number;
}

export function Timeline({ currentTime, duration }: TimelineProps) {
  const segments = [
    { id: 1, start: 0, end: 15, color: 'bg-primary', label: 'Intro' },
    { id: 2, start: 15, end: 45, color: 'bg-primary/80', label: 'Main' },
    { id: 3, start: 45, end: 75, color: 'bg-primary/60', label: 'Details' },
    { id: 4, start: 75, end: 120, color: 'bg-primary/80', label: 'Conclusion' },
  ];

  const audioSegments = [
    { id: 1, start: 0, end: 120, color: 'bg-accent/50' },
  ];

  const getPositionPercent = (time: number) => (time / duration) * 100;

  return (
    <div className="flex h-36 flex-col gap-3 border-t border-border bg-background p-4">
      {/* Ruler / Timeline */}
      <div className="flex items-center gap-2">
        <p className="text-xs font-medium text-muted-foreground w-12">Track</p>
        <div className="relative flex-1 h-5 bg-secondary rounded-sm">
          {[...Array(7)].map((_, i) => (
            <div
              key={i}
              className="absolute top-0 h-full w-px bg-border/50"
              style={{ left: `${(i / 6) * 100}%` }}
            />
          ))}
          <div
            className="absolute top-0 h-full w-0.5 bg-destructive shadow-md z-10"
            style={{ left: `${getPositionPercent(currentTime)}%` }}
          />
        </div>
      </div>

      {/* Video Track */}
      <div className="flex items-center gap-2">
        <p className="text-xs font-medium text-muted-foreground w-12">Video</p>
        <div className="relative flex-1 h-10 rounded-sm bg-secondary border border-border/50 overflow-hidden">
          {segments.map((segment) => (
            <div
              key={segment.id}
              className={`group absolute h-full ${segment.color} flex items-center justify-center text-xs font-medium text-primary-foreground transition-all hover:brightness-110 cursor-pointer border-x-2 border-transparent hover:border-primary/50`}
              style={{
                left: `${getPositionPercent(segment.start)}%`,
                right: `${100 - getPositionPercent(segment.end)}%`,
              }}
              title={`${segment.label}: ${segment.start}s - ${segment.end}s (drag edges to trim)`}
            >
              {/* Left Resize Handle */}
              <div className="absolute left-0 top-0 h-full w-1.5 bg-primary/0 group-hover:bg-primary cursor-ew-resize transition-colors" title="Drag to adjust start time" />
              
              {/* Segment Label */}
              <span className="pointer-events-none">{segment.label}</span>
              
              {/* Right Resize Handle */}
              <div className="absolute right-0 top-0 h-full w-1.5 bg-primary/0 group-hover:bg-primary cursor-ew-resize transition-colors" title="Drag to adjust end time" />
            </div>
          ))}
          <div
            className="pointer-events-none absolute top-0 h-full w-0.5 bg-destructive shadow-lg z-10"
            style={{ left: `${getPositionPercent(currentTime)}%` }}
          />
        </div>
      </div>

      {/* Audio Track */}
      <div className="flex items-center gap-2">
        <p className="text-xs font-medium text-muted-foreground w-12">Audio</p>
        <div className="relative flex-1 h-8 rounded-sm bg-secondary border border-border/50">
          {audioSegments.map((segment) => (
            <div
              key={segment.id}
              className={`group absolute h-full ${segment.color} transition-all hover:brightness-110 cursor-pointer border-x-2 border-transparent hover:border-accent`}
              style={{
                left: `${getPositionPercent(segment.start)}%`,
                right: `${100 - getPositionPercent(segment.end)}%`,
              }}
              title="Audio track (drag edges to trim)"
            >
              {/* Left Resize Handle */}
              <div className="absolute left-0 top-0 h-full w-1.5 bg-accent/0 group-hover:bg-accent cursor-ew-resize transition-colors" />
              
              {/* Right Resize Handle */}
              <div className="absolute right-0 top-0 h-full w-1.5 bg-accent/0 group-hover:bg-accent cursor-ew-resize transition-colors" />
            </div>
          ))}
          <div
            className="pointer-events-none absolute top-0 h-full w-0.5 bg-destructive z-10"
            style={{ left: `${getPositionPercent(currentTime)}%` }}
          />
        </div>
      </div>

      {/* Subtitle Track */}
      <div className="flex items-center gap-2">
        <p className="text-xs font-medium text-muted-foreground w-12">Subs</p>
        <div className="relative flex-1 h-8 rounded-sm bg-secondary border border-border/50">
          <div
            className="group absolute h-full w-16 rounded-sm bg-muted hover:bg-muted/80 transition-all cursor-pointer border-x-2 border-transparent hover:border-muted-foreground/50"
            style={{
              left: `${getPositionPercent(10)}%`,
            }}
            title="Subtitle segment (drag edges to adjust)"
          >
            {/* Left Resize Handle */}
            <div className="absolute left-0 top-0 h-full w-1.5 bg-muted-foreground/0 group-hover:bg-muted-foreground cursor-ew-resize transition-colors" />
            
            {/* Right Resize Handle */}
            <div className="absolute right-0 top-0 h-full w-1.5 bg-muted-foreground/0 group-hover:bg-muted-foreground cursor-ew-resize transition-colors" />
          </div>
          <div
            className="group absolute h-full w-20 rounded-sm bg-muted hover:bg-muted/80 transition-all cursor-pointer border-x-2 border-transparent hover:border-muted-foreground/50"
            style={{
              left: `${getPositionPercent(35)}%`,
            }}
            title="Subtitle segment (drag edges to adjust)"
          >
            {/* Left Resize Handle */}
            <div className="absolute left-0 top-0 h-full w-1.5 bg-muted-foreground/0 group-hover:bg-muted-foreground cursor-ew-resize transition-colors" />
            
            {/* Right Resize Handle */}
            <div className="absolute right-0 top-0 h-full w-1.5 bg-muted-foreground/0 group-hover:bg-muted-foreground cursor-ew-resize transition-colors" />
          </div>
          <div
            className="pointer-events-none absolute top-0 h-full w-0.5 bg-destructive z-10"
            style={{ left: `${getPositionPercent(currentTime)}%` }}
          />
        </div>
      </div>
    </div>
  );
}
