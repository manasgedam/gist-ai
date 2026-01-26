'use client';

import { Settings, Type, Share2, Download } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';

interface RightPanelProps {
  selectedIdea: string | null;
}

export function RightPanel({ selectedIdea }: RightPanelProps) {
  return (
    <div className="flex w-80 flex-col border-l border-border bg-background">
      {/* Panel Header */}
      <div className="border-b border-border px-4 py-3">
        <h2 className="text-sm font-semibold text-foreground">
          {selectedIdea ? 'Edit Clip' : 'Properties'}
        </h2>
        {selectedIdea && (
          <p className="mt-1 text-xs text-muted-foreground">
            Customizing short-form video clip
          </p>
        )}
      </div>

      {/* Panel Content */}
      <ScrollArea className="flex-1">
        <div className="space-y-6 p-4">
          {selectedIdea ? (
            <>
              {/* Trim Controls */}
              <div className="space-y-3 rounded-lg border border-border bg-secondary p-3">
                <h3 className="flex items-center gap-2 text-xs font-semibold text-foreground uppercase tracking-wide">
                  <Settings className="h-3.5 w-3.5" />
                  Trim Clip
                </h3>
                <div className="space-y-3">
                  <div>
                    <label className="text-xs font-medium text-muted-foreground block mb-1">Start Time</label>
                    <input
                      type="text"
                      placeholder="0:00"
                      className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:border-primary focus:outline-none"
                    />
                  </div>
                  <div>
                    <label className="text-xs font-medium text-muted-foreground block mb-1">End Time</label>
                    <input
                      type="text"
                      placeholder="0:12"
                      className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:border-primary focus:outline-none"
                    />
                  </div>
                </div>
              </div>

              {/* Subtitle Editing */}
              <div className="space-y-3 rounded-lg border border-border bg-secondary p-3">
                <h3 className="flex items-center gap-2 text-xs font-semibold text-foreground uppercase tracking-wide">
                  <Type className="h-3.5 w-3.5" />
                  Edit Subtitles
                </h3>
                <textarea
                  placeholder="Enter subtitle text..."
                  className="h-20 w-full rounded-md border border-border bg-background px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:border-primary focus:outline-none resize-none"
                />
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
              </div>

              {/* Format Settings */}
              <div className="space-y-3 rounded-lg border border-border bg-secondary p-3">
                <h3 className="text-xs font-semibold text-foreground uppercase tracking-wide">Export Format</h3>
                <div className="flex flex-col gap-2">
                  <Button variant="secondary" size="sm" className="w-full justify-start text-xs h-8 font-medium">
                    <Share2 className="h-3 w-3 mr-2" />
                    YouTube Shorts (9:16)
                  </Button>
                  <Button variant="outline" size="sm" className="w-full justify-start text-xs h-8 bg-transparent">
                    Instagram Reels (9:16)
                  </Button>
                  <Button variant="outline" size="sm" className="w-full justify-start text-xs h-8 bg-transparent">
                    TikTok (9:16)
                  </Button>
                  <Button variant="outline" size="sm" className="w-full justify-start text-xs h-8 bg-transparent">
                    Custom (16:9)
                  </Button>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex gap-2 border-t border-border pt-4 sticky bottom-0 bg-background">
                <Button variant="outline" size="sm" className="flex-1 text-xs bg-transparent">
                  Discard
                </Button>
                <Button size="sm" className="flex-1 gap-2 text-xs">
                  <Download className="h-3 w-3" />
                  Save Draft
                </Button>
              </div>
            </>
          ) : (
            <div className="flex h-full items-center justify-center">
              <div className="text-center">
                <div className="mx-auto mb-3 h-12 w-12 rounded-full bg-secondary flex items-center justify-center">
                  <Settings className="h-6 w-6 text-muted-foreground" />
                </div>
                <p className="text-sm font-medium text-foreground">
                  Select an idea to edit
                </p>
                <p className="mt-2 text-xs text-muted-foreground leading-relaxed">
                  Click on an AI-generated idea in the left panel to customize and export your short-form video
                </p>
              </div>
            </div>
          )}
        </div>
      </ScrollArea>
    </div>
  );
}
