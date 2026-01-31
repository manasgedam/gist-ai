'use client';

import { useState } from 'react';
import { Sparkles, Zap, TrendingUp, ChevronDown, ChevronUp, Clock, Film } from 'lucide-react';

interface TimeRange {
  start: number;
  end: number;
  confidence?: number;
}

interface IdeaCardProps {
  title: string;
  reason: string;
  description?: string;
  rank: number;
  isSelected: boolean;
  onClick: () => void;
  strength?: 'high' | 'medium' | 'low';
  highlights?: string[];
  viralPotential?: string;
  timeRanges?: TimeRange[];
}

export function IdeaCard({
  title,
  reason,
  description,
  rank,
  isSelected,
  onClick,
  strength = 'medium',
  highlights = [],
  viralPotential,
  timeRanges = [],
}: IdeaCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  // Strength indicator configuration
  const strengthConfig = {
    high: {
      label: 'High Impact',
      color: 'bg-emerald-500/20 text-emerald-600 dark:text-emerald-400',
      borderColor: 'border-emerald-500/30',
      icon: Zap,
    },
    medium: {
      label: 'Good Potential',
      color: 'bg-blue-500/20 text-blue-600 dark:text-blue-400',
      borderColor: 'border-blue-500/30',
      icon: TrendingUp,
    },
    low: {
      label: 'Moderate',
      color: 'bg-amber-500/20 text-amber-600 dark:text-amber-400',
      borderColor: 'border-amber-500/30',
      icon: Sparkles,
    },
  };

  const config = strengthConfig[strength];
  const StrengthIcon = config.icon;

  // Calculate total duration from time ranges
  const totalDuration = timeRanges.reduce((acc, range) => acc + (range.end - range.start), 0);
  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  // Highlight key phrases in title
  const renderHighlightedTitle = () => {
    if (highlights.length === 0) {
      return <span>{title}</span>;
    }

    let parts: { text: string; isHighlight: boolean }[] = [];
    let lastIndex = 0;

    highlights.forEach((highlight) => {
      const index = title.toLowerCase().indexOf(highlight.toLowerCase());
      if (index !== -1) {
        // Add text before highlight
        if (index > lastIndex) {
          parts.push({ text: title.slice(lastIndex, index), isHighlight: false });
        }
        // Add highlighted text
        parts.push({ text: title.slice(index, index + highlight.length), isHighlight: true });
        lastIndex = index + highlight.length;
      }
    });

    // Add remaining text
    if (lastIndex < title.length) {
      parts.push({ text: title.slice(lastIndex), isHighlight: false });
    }

    return (
      <>
        {parts.map((part, idx) => (
          part.isHighlight ? (
            <mark key={idx} className="bg-primary/20 text-primary font-semibold px-0.5 rounded">
              {part.text}
            </mark>
          ) : (
            <span key={idx}>{part.text}</span>
          )
        ))}
      </>
    );
  };

  // Handle keyboard interaction for card selection
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      onClick();
    }
  };

  return (
    <div
      role="button"
      tabIndex={0}
      onClick={onClick}
      onKeyDown={handleKeyDown}
      className={`group w-full rounded-lg border-2 transition-all duration-200 cursor-pointer ${
        isSelected
          ? 'border-primary bg-primary/5 shadow-md'
          : 'border-border bg-secondary hover:border-primary/30 hover:bg-secondary/80 hover:shadow-sm'
      }`}
    >
      <div className="p-3.5">
        <div className="flex items-start gap-3">
          {/* Rank Badge */}
          <div
            className={`flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-full font-bold text-sm shadow-sm ${
              isSelected
                ? 'bg-primary text-primary-foreground'
                : 'bg-gradient-to-br from-primary/30 to-primary/10 text-primary'
            }`}
          >
            {rank}
          </div>

          {/* Content */}
          <div className="flex-1 min-w-0 text-left space-y-2">
            {/* Title with Highlights - TRUNCATED TO 2 LINES */}
            <p className="text-sm font-medium text-foreground leading-snug line-clamp-2">
              {renderHighlightedTitle()}
            </p>

            {/* Metadata Row */}
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              <span className="font-medium">#{rank}</span>
              <span>•</span>
              <div className="flex items-center gap-1">
                <Film className="h-3 w-3" />
                <span>{timeRanges.length} segment{timeRanges.length !== 1 ? 's' : ''}</span>
              </div>
              {totalDuration > 0 && (
                <>
                  <span>•</span>
                  <div className="flex items-center gap-1">
                    <Clock className="h-3 w-3" />
                    <span>{formatDuration(totalDuration)}</span>
                  </div>
                </>
              )}
            </div>

            {/* Description - COLLAPSIBLE */}
            {description && (
              <div className="space-y-1">
                <p className={`text-xs text-muted-foreground leading-relaxed ${!isExpanded ? 'line-clamp-3' : ''}`}>
                  {description}
                </p>
                {description.length > 150 && (
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      setIsExpanded(!isExpanded);
                    }}
                    className="flex items-center gap-1 text-xs text-primary hover:underline font-medium"
                  >
                    {isExpanded ? (
                      <>
                        <ChevronUp className="h-3 w-3" />
                        Show less
                      </>
                    ) : (
                      <>
                        <ChevronDown className="h-3 w-3" />
                        Read more
                      </>
                    )}
                  </button>
                )}
              </div>
            )}


            {/* Viral Potential Indicator */}
            {viralPotential && (
              <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
                <TrendingUp className="h-3 w-3" />
                <span className="font-medium">Viral Potential: <span className="text-foreground">{viralPotential}</span></span>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
