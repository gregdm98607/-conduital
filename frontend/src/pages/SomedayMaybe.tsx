import { useState, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { Lightbulb, Play, Archive, Clock, FolderKanban } from 'lucide-react';
import toast from 'react-hot-toast';
import { useProjects, useUpdateProject } from '../hooks/useProjects';
import { Error } from '../components/common/Error';
import { Loading } from '../components/common/Loading';
import { SearchInput } from '../components/common/SearchInput';
import type { Project } from '../types';

export function SomedayMaybe() {
  const [searchQuery, setSearchQuery] = useState('');
  const { data, isLoading, error } = useProjects({ status: 'someday_maybe' });
  const updateProject = useUpdateProject();

  const projects = data?.projects || [];

  const filteredProjects = useMemo(() => {
    if (!searchQuery) return projects;
    const query = searchQuery.toLowerCase();
    return projects.filter(
      (p) =>
        p.title.toLowerCase().includes(query) ||
        p.description?.toLowerCase().includes(query)
    );
  }, [projects, searchQuery]);

  const handleActivate = (project: Project) => {
    updateProject.mutate(
      { id: project.id, project: { status: 'active' } },
      {
        onSuccess: () => {
          toast.success(`"${project.title}" activated`);
        },
        onError: () => {
          toast.error('Failed to activate project');
        },
      }
    );
  };

  const handleArchive = (project: Project) => {
    updateProject.mutate(
      { id: project.id, project: { status: 'archived' } },
      {
        onSuccess: () => {
          toast.success(`"${project.title}" archived`);
        },
        onError: () => {
          toast.error('Failed to archive project');
        },
      }
    );
  };

  const formatDate = (dateString?: string) => {
    if (!dateString) return 'Unknown';
    return new Date(dateString).toLocaleDateString();
  };

  if (error) return <Error message="Failed to load Someday/Maybe projects" fullPage />;

  return (
    <div className="p-8">
      {/* Header */}
      <header className="mb-8">
        <div className="flex items-center gap-3 mb-2">
          <Lightbulb className="w-8 h-8 text-amber-500" />
          <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">Someday/Maybe</h1>
        </div>
        <p className="text-gray-600 dark:text-gray-400">
          Projects you might pursue someday. Review regularly during your Weekly Review.
        </p>
      </header>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        <div className="card bg-amber-50 dark:bg-amber-900/20 border-amber-200 dark:border-amber-800">
          <div className="flex items-center gap-3">
            <Lightbulb className="w-6 h-6 text-amber-600" />
            <div>
              <p className="text-2xl font-bold text-amber-900 dark:text-amber-200">{projects.length}</p>
              <p className="text-sm text-amber-700 dark:text-amber-300">Someday/Maybe Projects</p>
            </div>
          </div>
        </div>
        <div className="card bg-gray-50 dark:bg-gray-800 border-gray-200 dark:border-gray-700">
          <div className="flex items-center gap-3">
            <Clock className="w-6 h-6 text-gray-600 dark:text-gray-400" />
            <div>
              <p className="text-sm text-gray-700 dark:text-gray-300">
                Review these during your <Link to="/weekly-review" className="text-primary-600 hover:underline">Weekly Review</Link> to decide if any should become active.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Search */}
      {projects.length > 0 && (
        <div className="mb-6">
          <SearchInput
            value={searchQuery}
            onChange={setSearchQuery}
            placeholder="Search someday/maybe projects..."
          />
        </div>
      )}

      {/* Projects List */}
      {isLoading ? (
        <Loading />
      ) : filteredProjects.length > 0 ? (
        <div className="space-y-3">
          {filteredProjects.map((project) => (
            <div key={project.id} className="card hover:shadow-md transition-shadow">
              <div className="flex items-start gap-4">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <FolderKanban className="w-4 h-4 text-gray-400" />
                    <Link
                      to={`/projects/${project.id}`}
                      className="font-semibold text-gray-900 dark:text-gray-100 hover:text-primary-600 transition-colors"
                    >
                      {project.title}
                    </Link>
                  </div>
                  {project.description && (
                    <p className="text-sm text-gray-600 dark:text-gray-400 mt-1 line-clamp-2">
                      {project.description}
                    </p>
                  )}
                  {project.outcome_statement && (
                    <p className="text-sm text-gray-500 dark:text-gray-500 mt-1 italic">
                      Outcome: {project.outcome_statement}
                    </p>
                  )}
                  <div className="flex items-center gap-3 mt-2 text-xs text-gray-500 dark:text-gray-400">
                    <span>Added {formatDate(project.created_at)}</span>
                    {project.area && (
                      <span className="badge badge-gray">{project.area.title}</span>
                    )}
                  </div>
                </div>
                <div className="flex items-center gap-2 flex-shrink-0">
                  <button
                    onClick={() => handleActivate(project)}
                    disabled={updateProject.isPending}
                    className="btn btn-sm btn-primary flex items-center gap-1"
                    title="Activate this project"
                  >
                    <Play className="w-3 h-3" />
                    Activate
                  </button>
                  <button
                    onClick={() => handleArchive(project)}
                    disabled={updateProject.isPending}
                    className="btn btn-sm btn-secondary flex items-center gap-1"
                    title="Archive this project"
                  >
                    <Archive className="w-3 h-3" />
                    Archive
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="card text-center py-12">
          <Lightbulb className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-500 dark:text-gray-400 text-lg mb-2">
            {searchQuery ? 'No projects match your search' : 'No Someday/Maybe projects'}
          </p>
          <p className="text-gray-400 dark:text-gray-500 text-sm mb-4">
            {searchQuery
              ? 'Try adjusting your search query'
              : 'Move projects here that you might pursue in the future but not right now.'}
          </p>
        </div>
      )}
    </div>
  );
}
