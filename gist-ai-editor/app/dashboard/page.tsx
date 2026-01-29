'use client';

import { useState, useEffect, useMemo } from 'react';
import { useRouter } from 'next/navigation';
import { Plus } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { DashboardHeader } from '@/components/dashboard/dashboard-header';
import { ProjectCard } from '@/components/dashboard/project-card';
import { EmptyProjectsState } from '@/components/dashboard/empty-project-state';
import { CreateProjectDialog } from '@/components/dashboard/create-project-dialog';
import { projectsApi, Project, formatRelativeTime } from '@/lib/api/projects';

export default function DashboardPage() {
  const router = useRouter();
  const [searchQuery, setSearchQuery] = useState('');
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);

  // Fetch projects on mount
  useEffect(() => {
    fetchProjects();
  }, []);

const fetchProjects = async () => {
  console.log('Dashboard: Starting to fetch projects...');
  try {
    setLoading(true);
    setError(null);
    
    console.log('Dashboard: Calling projectsApi.list()...');
    const data = await projectsApi.list();
    
    console.log('Dashboard: Raw response:', data);
    console.log(`Dashboard: Successfully fetched ${data.length} projects`);
    
    setProjects(data);
  } catch (err) {
    console.error('Dashboard: Error caught:', err);
    console.error('Dashboard: Error details:', {
      message: err instanceof Error ? err.message : 'Unknown error',
      stack: err instanceof Error ? err.stack : undefined,
      raw: err
    });
    setError(err instanceof Error ? err.message : 'Failed to load projects');
  } finally {
    console.log('Dashboard: Finished fetching projects (finally block)');
    setLoading(false);
  }
};
  // Filter projects based on search query
  const filteredProjects = useMemo(() => {
    return projects.filter((project) =>
      project.title.toLowerCase().includes(searchQuery.toLowerCase())
    );
  }, [projects, searchQuery]);

  const handleCreateNew = () => {
    setCreateDialogOpen(true);
  };

  const handleProjectCreated = (project: Project) => {
    // Add new project to the list
    setProjects([project, ...projects]);
    // Navigate to editor with new project
    router.push(`/editor?project=${project.id}`);
  };

  const handleOpenProject = (id: string) => {
    // Navigate to editor with project ID
    router.push(`/editor?project=${id}`);
  };

  const handleDeleteProject = async (id: string) => {
    try {
      await projectsApi.delete(id);
      setProjects(projects.filter((p) => p.id !== id));
    } catch (err) {
      console.error('Failed to delete project:', err);
      // Optionally show error toast
    }
  };

  // Loading state
  if (loading) {
    return (
      <div className="min-h-screen bg-background">
        <DashboardHeader searchQuery={searchQuery} onSearch={setSearchQuery} />
        <main className="max-w-7xl mx-auto px-6 py-12">
          <div className="flex items-center justify-center min-h-[400px]">
            <div className="text-center">
              <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-current border-r-transparent align-[-0.125em] motion-reduce:animate-[spin_1.5s_linear_infinite]" />
              <p className="mt-4 text-sm text-muted-foreground">Loading projects...</p>
            </div>
          </div>
        </main>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="min-h-screen bg-background">
        <DashboardHeader searchQuery={searchQuery} onSearch={setSearchQuery} />
        <main className="max-w-7xl mx-auto px-6 py-12">
          <div className="flex flex-col items-center justify-center min-h-[400px]">
            <p className="text-destructive mb-4">{error}</p>
            <Button onClick={fetchProjects}>Try Again</Button>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <DashboardHeader searchQuery={searchQuery} onSearch={setSearchQuery} />

      <main className="max-w-7xl mx-auto px-6 py-12">
        {/* Header Section */}
        <div className="mb-12 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-6">
          <div>
            <h1 className="text-3xl font-semibold text-foreground mb-2 text-balance">
              Your Projects
            </h1>
            <p className="text-muted-foreground">
              {projects.length === 0
                ? 'Create your first project to get started'
                : 'Pick up where you left off or create something new'}
            </p>
          </div>

          <Button
            size="lg"
            onClick={handleCreateNew}
            className="gap-2 w-full sm:w-auto"
          >
            <Plus className="h-5 w-5" />
            New Project
          </Button>
        </div>

        {/* Projects Grid or Empty State */}
        {projects.length === 0 && searchQuery === '' ? (
          <EmptyProjectsState onCreateNew={handleCreateNew} />
        ) : filteredProjects.length === 0 ? (
          <div className="flex flex-col items-center justify-center min-h-[300px]">
            <p className="text-muted-foreground">
              No projects found matching "{searchQuery}"
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredProjects.map((project) => (
              <ProjectCard
                key={project.id}
                id={project.id}
                title={project.title}
                thumbnail={project.thumbnail_url}
                lastUpdated={formatRelativeTime(project.updated_at)}
                status={project.status}
                onOpen={() => handleOpenProject(project.id)}
                onDelete={() => handleDeleteProject(project.id)}
              />
            ))}
          </div>
        )}
      </main>

      {/* Create Project Dialog */}
      <CreateProjectDialog
        open={createDialogOpen}
        onOpenChange={setCreateDialogOpen}
        onCreated={handleProjectCreated}
      />
    </div>
  );
}
