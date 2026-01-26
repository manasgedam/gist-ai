interface VideoPreviewProps {
  aspectRatio: '16:9' | '9:16';
}

export function VideoPreview({ aspectRatio }: VideoPreviewProps) {
  const containerClass =
    aspectRatio === '16:9'
      ? 'aspect-video max-w-3xl'
      : 'h-80 w-48';

  return (
    <div className="flex flex-1 items-center justify-center overflow-hidden bg-gradient-to-br from-muted via-secondary to-muted">
      <div
        className={`${containerClass} relative flex flex-col items-center justify-center rounded-lg border border-border bg-black shadow-lg overflow-hidden`}
      >
        {/* Gradient Overlay */}
        <div className="absolute inset-0 bg-gradient-to-br from-primary/20 via-transparent to-accent/20" />

        {/* Content */}
        <div className="relative z-10 flex flex-col items-center justify-center text-center">
          <div className="text-4xl font-light text-white opacity-80">
            {aspectRatio === '16:9' ? '16:9' : '9:16'}
          </div>
          <p className="mt-3 text-sm text-white/60">Video Preview Canvas</p>
          <p className="mt-1 text-xs text-white/40">Clip will render here after editing</p>
        </div>

        {/* Corner Indicators */}
        <div className="absolute inset-0 pointer-events-none">
          <div className="absolute top-2 left-2 w-2 h-2 border-t-2 border-l-2 border-white/30" />
          <div className="absolute top-2 right-2 w-2 h-2 border-t-2 border-r-2 border-white/30" />
          <div className="absolute bottom-2 left-2 w-2 h-2 border-b-2 border-l-2 border-white/30" />
          <div className="absolute bottom-2 right-2 w-2 h-2 border-b-2 border-r-2 border-white/30" />
        </div>
      </div>
    </div>
  );
}
