'use client';

import { useState } from 'react';
import { Upload, BookOpen, Sparkles, Zap, Type, Settings, Wand2, Download, Share2, Scissors, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { IdeaCard } from './idea-card';
import { VideoUpload } from './video-upload';
import { ProcessingProgress } from './processing-progress';
import { Idea } from '@/lib/api/client';

interface LeftSidebarProps {
  selectedIdea: string | null;
  onSelectIdea: (id: string) => void;
  projectId?: string | null;
  // Video processing state from parent (single source of truth)
  videoId: string | null;
  videoStreamUrl: string | null;
  status: string | null;
  progress: number;
  currentStage: string | null;
  message: string | null;
  ideas: Idea[];
  isLoading: boolean;
  isProcessing: boolean;
  isComplete: boolean;
  error: string | null;
  submitVideo: (url: string, mode?: string) => Promise<void>;
  reset: () => void;
}

const OTHER_TOPICS = [
  'Product Features',
  'Customer Testimonial',
  'Methodology Overview',
  'Results Summary',
];

export function LeftSidebar({
  selectedIdea,
  onSelectIdea,
  projectId,
  // Video processing state from parent
  videoId,
  videoStreamUrl,
  status,
  progress,
  currentStage,
  message,
  ideas,
  isLoading,
  isProcessing,
  isComplete,
  error,
  submitVideo,
  reset,
}: LeftSidebarProps) {
  const [activeTab, setActiveTab] = useState<'upload' | 'ideas' | 'edit' | 'transitions' | 'subtitles' | 'export'>('upload');
  const [isGistExpanded, setIsGistExpanded] = useState(true);
  const [isOtherExpanded, setIsOtherExpanded] = useState(true);
  const [subtitlesEnabled, setSubtitlesEnabled] = useState(true);

  // Handle YouTube URL submission
  const handleVideoSubmit = async (url: string) => {
    await submitVideo(url, 'groq');  // Using Gemini while Groq credits are exhausted
  };

  // Handle reset/new upload
  const handleReset = () => {
    reset();
    setActiveTab('upload');
  };

  const tabs = [
    { id: 'upload', label: 'Upload', icon: Upload },
    { id: 'ideas', label: 'Generated Ideas', icon: Sparkles },
    { id: 'edit', label: 'Trim & Edit', icon: Scissors },
    { id: 'transitions', label: 'Transitions', icon: Wand2 },
    { id: 'subtitles', label: 'Subtitles', icon: Type },
    { id: 'export', label: 'Export', icon: Download },
  ];

  return (
    <div className="flex w-96 flex-col border-r border-border bg-background">
      {/* Tab Navigation */}
      <div className="border-b border-border bg-background/50 backdrop-blur-sm">
        <div className="flex flex-col gap-1 p-2">
          {tabs.map((tab) => {
            const IconComponent = tab.icon;
            return (
              <Button
                key={tab.id}
                variant={activeTab === tab.id ? 'default' : 'ghost'}
                className={`justify-start gap-3 px-3 py-2 h-auto font-medium transition-all ${
                  activeTab === tab.id
                    ? 'bg-primary text-primary-foreground shadow-sm'
                    : 'text-muted-foreground hover:text-foreground hover:bg-secondary/50'
                }`}
                onClick={() => setActiveTab(tab.id as any)}
              >
                <IconComponent className="h-4 w-4 flex-shrink-0" />
                <span className="text-sm">{tab.label}</span>
              </Button>
            );
          })}
        </div>
      </div>

      {/* Content Area */}
      <ScrollArea className="flex-1 overflow-scroll">
        <div className="p-4">
          {activeTab === 'upload' && (
            <div className="space-y-4">
              {/* CRITICAL: Show loading state while fetching initial data */}
              {isLoading && (
                <div className="rounded-lg border border-border bg-secondary/30 p-8">
                  <div className="flex flex-col items-center justify-center gap-3">
                    <Loader2 className="h-8 w-8 animate-spin text-primary" />
                    <p className="text-sm text-muted-foreground">Loading project data...</p>
                  </div>
                </div>
              )}

              {/* Show upload form ONLY after loading completes AND no video exists */}
              {!isLoading && !videoId && !isProcessing && (
                <VideoUpload onVideoSubmit={handleVideoSubmit} />
              )}

              {/* Show processing progress */}
              {isProcessing && (
                <ProcessingProgress
                  currentStage={currentStage}
                  progress={progress}
                  message={message}
                  error={error}
                />
              )}

              {/* Show completion state with reset option */}
              {isComplete && (
                <div className="space-y-4">
                  <div className="rounded-lg border border-border bg-secondary/30 p-5">
                    <div className="flex items-start gap-3 mb-4">
                      <div className="rounded-full bg-primary/20 p-2">
                        <Sparkles className="h-5 w-5 text-primary" />
                      </div>
                      <div className="flex-1">
                        <h3 className="text-sm font-semibold text-foreground">Processing Complete!</h3>
                        <p className="text-xs text-muted-foreground mt-1">
                          {ideas.length} ideas generated from your video
                        </p>
                      </div>
                    </div>
                    <div className="flex gap-2">
                      <Button
                        size="sm"
                        variant="default"
                        className="flex-1"
                        onClick={() => setActiveTab('ideas')}
                      >
                        <Sparkles className="h-4 w-4 mr-2" />
                        View Ideas
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={handleReset}
                      >
                        <Upload className="h-4 w-4 mr-2" />
                        New Video
                      </Button>
                    </div>
                  </div>
                </div>
              )}

              {/* Show error state with retry option */}
              {error && status === 'failed' && (
                <div className="rounded-lg border border-destructive/20 bg-destructive/10 p-5">
                  <div className="flex items-start gap-3 mb-4">
                    <div className="rounded-full bg-destructive/20 p-2">
                      <Upload className="h-5 w-5 text-destructive" />
                      </div>
                    <div className="flex-1">
                      <h3 className="text-sm font-semibold text-destructive">Processing Failed</h3>
                      <p className="text-xs text-destructive/80 mt-1">{error}</p>
                    </div>
                  </div>
                  <Button
                    size="sm"
                    variant="outline"
                    className="w-full"
                    onClick={handleReset}
                  >
                    <Upload className="h-4 w-4 mr-2" />
                    Try Another Video
                  </Button>
                </div>
              )}
            </div>
          )}

          {activeTab === 'ideas' && (
            <div className="space-y-5">
              {/* Best Short-Video Ideas Section */}
              <div>
                <button
                  onClick={() => setIsGistExpanded(!isGistExpanded)}
                  className="mb-4 flex items-center gap-2 text-xs font-bold text-muted-foreground hover:text-foreground uppercase tracking-wider transition-colors"
                >
                  <span className={`transition-transform duration-200 ${isGistExpanded ? 'rotate-90' : ''}`}>▸</span>
                  <span>Best Short-Video Ideas</span>
                  <span className="ml-auto inline-flex items-center justify-center h-5 w-5 rounded-full bg-primary text-xs font-bold text-primary-foreground">
                    {ideas.length}
                  </span>
                </button>

                {isGistExpanded && (
                  <div className="space-y-3">
                    {ideas.length > 0 ? (
                      ideas.map((idea) => (
                        <IdeaCard
                          key={idea.id}
                          title={idea.title}
                          reason={idea.reason}
                          rank={idea.rank}
                          isSelected={selectedIdea === idea.id}
                          onClick={() => onSelectIdea(idea.id)}
                          strength={idea.strength}
                          highlights={idea.highlights}
                          viralPotential={idea.viral_potential || ''}
                        />
                      ))
                    ) : (
                      <div className="rounded-lg border border-dashed border-border bg-secondary/30 p-6 text-center">
                        <Sparkles className="mx-auto h-8 w-8 text-muted-foreground/50 mb-2" />
                        <p className="text-sm font-medium text-muted-foreground">No ideas yet</p>
                        <p className="text-xs text-muted-foreground/60 mt-1">Upload a video to generate ideas</p>
                      </div>
                    )}
                  </div>
                )}
              </div>

              {/* Other Topics Section */}
              <div className="border-t border-border/50 pt-5">
                <button
                  onClick={() => setIsOtherExpanded(!isOtherExpanded)}
                  className="mb-4 flex items-center gap-2 text-xs font-bold text-muted-foreground hover:text-foreground uppercase tracking-wider transition-colors"
                >
                  <span className={`transition-transform duration-200 ${isOtherExpanded ? 'rotate-90' : ''}`}>▸</span>
                  <span>Other Topics Discussed</span>
                </button>

                {isOtherExpanded && (
                  <div className="space-y-2">
                    {OTHER_TOPICS.map((topic) => (
                      <div
                        key={topic}
                        className="rounded-md px-3 py-2 text-xs font-medium text-muted-foreground hover:bg-secondary/50 hover:text-foreground transition-colors cursor-pointer"
                      >
                        {topic}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}

          {activeTab === 'edit' && (
            <div className="space-y-4">
              <div className="rounded-lg border border-border bg-secondary/30 p-5">
                <h3 className="flex items-center gap-3 text-sm font-semibold text-foreground mb-4">
                  <div className="rounded-lg bg-primary/10 p-2">
                    <Scissors className="h-4 w-4 text-primary" />
                  </div>
                  Trim & Edit Clip
                </h3>
                {selectedIdea ? (
                  <div className="space-y-4">
                    <p className="text-xs text-muted-foreground">
                      Use the timeline below to trim your clip by dragging the edges of segments.
                    </p>
                    <div className="space-y-3">
                      <div>
                        <label className="text-xs font-semibold text-muted-foreground block mb-2 uppercase tracking-wider">Start Time</label>
                        <input
                          type="text"
                          placeholder="0:00"
                          className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary/50 transition-all"
                        />
                      </div>
                      <div>
                        <label className="text-xs font-semibold text-muted-foreground block mb-2 uppercase tracking-wider">End Time</label>
                        <input
                          type="text"
                          placeholder="0:12"
                          className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary/50 transition-all"
                        />
                      </div>
                    </div>
                  </div>
                ) : (
                  <p className="text-xs text-muted-foreground text-center py-4">Select an idea to edit</p>
                )}
              </div>
            </div>
          )}

          {activeTab === 'transitions' && (
            <div className="space-y-4">
              <div className="rounded-lg border border-border bg-secondary/30 p-5">
                <h3 className="flex items-center gap-3 text-sm font-semibold text-foreground mb-4">
                  <div className="rounded-lg bg-primary/10 p-2">
                    <Wand2 className="h-4 w-4 text-primary" />
                  </div>
                  Transition Effects
                </h3>
                <div className="space-y-5">
                  {/* Transition Presets */}
                  <div className="grid grid-cols-2 gap-2">
                    {['Fade', 'Dissolve', 'Wipe', 'Zoom'].map((transition) => (
                      <button
                        key={transition}
                        className="rounded-md border border-border bg-background p-3 text-xs font-medium text-foreground hover:border-primary hover:bg-primary/5 transition-all"
                      >
                        {transition}
                      </button>
                    ))}
                  </div>

                  {/* Duration Control */}
                  <div>
                    <label className="text-xs font-medium text-muted-foreground block mb-2">
                      Duration: <span className="text-foreground">1.0s</span>
                    </label>
                    <input
                      type="range"
                      min="0.5"
                      max="2"
                      step="0.1"
                      defaultValue="1"
                      className="w-full h-1.5 cursor-pointer accent-primary"
                    />
                    <div className="flex justify-between text-xs text-muted-foreground mt-1">
                      <span>0.5s</span>
                      <span>2.0s</span>
                    </div>
                  </div>

                  {/* Intensity Control */}
                  <div>
                    <label className="text-xs font-medium text-muted-foreground block mb-2">
                      Intensity: <span className="text-foreground">50%</span>
                    </label>
                    <input
                      type="range"
                      min="0"
                      max="100"
                      defaultValue="50"
                      className="w-full h-1.5 cursor-pointer accent-primary"
                    />
                    <div className="flex justify-between text-xs text-muted-foreground mt-1">
                      <span>Subtle</span>
                      <span>Strong</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'subtitles' && (
            <div className="space-y-4">
              <div className="rounded-lg border border-border bg-secondary/30 p-5">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="flex items-center gap-3 text-sm font-semibold text-foreground">
                    <div className="rounded-lg bg-primary/10 p-2">
                      <Type className="h-4 w-4 text-primary" />
                    </div>
                    Subtitle Styling
                  </h3>
                  <button
                    onClick={() => setSubtitlesEnabled(!subtitlesEnabled)}
                    className={`text-xs font-medium px-2 py-1 rounded ${
                      subtitlesEnabled
                        ? 'bg-primary text-primary-foreground'
                        : 'bg-secondary text-muted-foreground'
                    }`}
                  >
                    {subtitlesEnabled ? 'ON' : 'OFF'}
                  </button>
                </div>

                {subtitlesEnabled && (
                  <div className="space-y-3">
                    {/* Style Presets */}
                    <div>
                      <label className="text-xs font-medium text-muted-foreground block mb-2">Style Preset</label>
                      <div className="grid grid-cols-2 gap-2">
                        {['Bold', 'Minimal', 'Highlighted', 'Outlined'].map((preset) => (
                          <button
                            key={preset}
                            className="rounded-md border border-border bg-background px-3 py-2 text-xs font-medium text-foreground hover:border-primary hover:bg-primary/5 transition-all"
                          >
                            {preset}
                          </button>
                        ))}
                      </div>
                    </div>

                    {/* Font Controls */}
                    <div className="grid grid-cols-2 gap-2">
                      <div>
                        <label className="text-xs font-medium text-muted-foreground block mb-1">Font</label>
                        <select className="w-full rounded-md border border-border bg-background px-2 py-1.5 text-xs text-foreground focus:border-primary focus:outline-none">
                          <option>Sans Serif</option>
                          <option>Serif</option>
                          <option>Monospace</option>
                        </select>
                      </div>
                      <div>
                        <label className="text-xs font-medium text-muted-foreground block mb-1">Size</label>
                        <select className="w-full rounded-md border border-border bg-background px-2 py-1.5 text-xs text-foreground focus:border-primary focus:outline-none">
                          <option>16px</option>
                          <option>20px</option>
                          <option>24px</option>
                          <option>32px</option>
                        </select>
                      </div>
                    </div>

                    {/* Color Controls */}
                    <div className="grid grid-cols-2 gap-2">
                      <div>
                        <label className="text-xs font-medium text-muted-foreground block mb-1">Text Color</label>
                        <input
                          type="color"
                          defaultValue="#ffffff"
                          className="w-full h-8 rounded-md border border-border cursor-pointer"
                        />
                      </div>
                      <div>
                        <label className="text-xs font-medium text-muted-foreground block mb-1">Background</label>
                        <input
                          type="color"
                          defaultValue="#000000"
                          className="w-full h-8 rounded-md border border-border cursor-pointer"
                        />
                      </div>
                    </div>

                    {/* Effects */}
                    <div>
                      <label className="text-xs font-medium text-muted-foreground block mb-2">Effects</label>
                      <select className="w-full rounded-md border border-border bg-background px-3 py-2 text-xs text-foreground focus:border-primary focus:outline-none">
                        <option>None</option>
                        <option>Fade In</option>
                        <option>Typewriter</option>
                        <option>Bounce</option>
                      </select>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {activeTab === 'export' && (
            <div className="space-y-4">
              <div className="rounded-lg border border-border bg-secondary/30 p-5">
                <h3 className="flex items-center gap-3 text-sm font-semibold text-foreground mb-4">
                  <div className="rounded-lg bg-primary/10 p-2">
                    <Download className="h-4 w-4 text-primary" />
                  </div>
                  Export Settings
                </h3>
                <div className="space-y-3">
                  {/* Platform Presets */}
                  <div>
                    <label className="text-xs font-medium text-muted-foreground block mb-2">Platform</label>
                    <div className="flex flex-col gap-2">
                      <Button variant="secondary" size="sm" className="w-full justify-start text-xs h-9 font-medium">
                        <Share2 className="h-3 w-3 mr-2" />
                        YouTube Shorts (9:16)
                      </Button>
                      <Button variant="outline" size="sm" className="w-full justify-start text-xs h-9 bg-transparent">
                        Instagram Reels (9:16)
                      </Button>
                      <Button variant="outline" size="sm" className="w-full justify-start text-xs h-9 bg-transparent">
                        TikTok (9:16)
                      </Button>
                      <Button variant="outline" size="sm" className="w-full justify-start text-xs h-9 bg-transparent">
                        Custom (16:9)
                      </Button>
                    </div>
                  </div>

                  {/* Quality Settings */}
                  <div>
                    <label className="text-xs font-medium text-muted-foreground block mb-2">Quality</label>
                    <select className="w-full rounded-md border border-border bg-background px-3 py-2 text-xs text-foreground focus:border-primary focus:outline-none">
                      <option>1080p (High)</option>
                      <option>720p (Medium)</option>
                      <option>480p (Low)</option>
                    </select>
                  </div>

                  {/* Export Button */}
                  <div className="pt-2">
                    <Button className="w-full gap-2" disabled={!selectedIdea}>
                      <Download className="h-4 w-4" />
                      Export Video
                    </Button>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </ScrollArea>
    </div>
  );
}
