import { create } from 'zustand'
import { IdeasData, TranscriptData, Idea, Segment } from './types'

interface EditableSegment extends Segment {
  id: string
  ideaIndex: number
}

interface EditorState {
  // Data
  ideas: IdeasData | null
  transcript: TranscriptData | null
  videoId: string | null
  
  // Editable segments (derived from selected idea)
  editableSegments: EditableSegment[]
  
  // Current state
  selectedIdeaId: string | null
  selectedSegmentId: string | null
  currentTime: number
  isPlaying: boolean
  zoom: number
  showSubtitles: boolean
  
  // Actions
  setData: (ideas: IdeasData, transcript: TranscriptData, videoId: string) => void
  selectIdea: (ideaIndex: number | null) => void
  selectSegment: (segmentId: string | null) => void
  setCurrentTime: (time: number) => void
  setIsPlaying: (playing: boolean) => void
  setZoom: (zoom: number) => void
  toggleSubtitles: () => void
  
  // Editing actions
  updateSegment: (segmentId: string, changes: Partial<EditableSegment>) => void
  deleteSegment: (segmentId: string) => void
  applyEditsToIdea: () => void
}

export const useEditorStore = create<EditorState>((set, get) => ({
  // Initial state
  ideas: null,
  transcript: null,
  videoId: null,
  editableSegments: [],
  selectedIdeaId: null,
  selectedSegmentId: null,
  currentTime: 0,
  isPlaying: false,
  zoom: 1,
  showSubtitles: true,
  
  // Actions
  setData: (ideas, transcript, videoId) => 
    set({ ideas, transcript, videoId }),
  
  selectIdea: (ideaIndex) => {
    if (ideaIndex === null) {
      set({ 
        selectedIdeaId: null, 
        editableSegments: [],
        selectedSegmentId: null 
      })
      return
    }
    
    const state = get()
    if (!state.ideas) return
    
    const idea = state.ideas.ideas[ideaIndex]
    
    // Convert segments to editable format with IDs
    const editableSegments: EditableSegment[] = idea.segments.map((seg, idx) => ({
      ...seg,
      id: `${ideaIndex}-${idx}`,
      ideaIndex
    }))
    
    set({ 
      selectedIdeaId: String(ideaIndex),
      editableSegments,
      selectedSegmentId: null
    })
  },
  
  selectSegment: (segmentId) => 
    set({ selectedSegmentId: segmentId }),
  
  setCurrentTime: (time) => 
    set({ currentTime: time }),
  
  setIsPlaying: (playing) => 
    set({ isPlaying: playing }),
  
  setZoom: (zoom) => 
    set({ zoom }),
  
  toggleSubtitles: () =>
    set((state) => ({ showSubtitles: !state.showSubtitles })),
  
  // Editing actions
  updateSegment: (segmentId, changes) => {
    set((state) => ({
      editableSegments: state.editableSegments.map(seg =>
        seg.id === segmentId 
          ? { 
              ...seg, 
              ...changes,
              // Recalculate duration if start or end changed
              duration_seconds: (changes.end_seconds ?? seg.end_seconds) - 
                               (changes.start_seconds ?? seg.start_seconds)
            }
          : seg
      )
    }))
  },
  
  deleteSegment: (segmentId) => {
    set((state) => ({
      editableSegments: state.editableSegments.filter(seg => seg.id !== segmentId),
      selectedSegmentId: state.selectedSegmentId === segmentId ? null : state.selectedSegmentId
    }))
  },
  
  applyEditsToIdea: () => {
    const state = get()
    if (!state.ideas || state.selectedIdeaId === null) return
    
    const ideaIndex = parseInt(state.selectedIdeaId)
    const updatedIdeas = { ...state.ideas }
    
    // Update the idea with edited segments
    updatedIdeas.ideas[ideaIndex] = {
      ...updatedIdeas.ideas[ideaIndex],
      segments: state.editableSegments.map(({ id, ideaIndex, ...seg }) => seg),
      segment_count: state.editableSegments.length,
      total_duration_seconds: state.editableSegments.reduce(
        (sum, seg) => sum + seg.duration_seconds, 
        0
      )
    }
    
    set({ ideas: updatedIdeas })
  }
}))