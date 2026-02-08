import { useState, useMemo, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Plus, Filter, SlidersHorizontal, ArrowUpDown, LayoutGrid, List, AlertTriangle, Layers } from 'lucide-react';
import { useProjects } from '../hooks/useProjects';
import { Error } from '../components/common/Error';
import { ProjectCard } from '../components/projects/ProjectCard';
import { ProjectListView } from '../components/projects/ProjectListView';
import { CreateProjectModal } from '../components/projects/CreateProjectModal';
import { ProjectCardSkeleton, TableRowSkeleton } from '@/components/common/Skeleton';
import { SearchInput } from '@/components/common/SearchInput';
import { Project } from '../types';

type ViewMode = 'grid' | 'list';

const VIEW_MODE_STORAGE_KEY = 'projectsViewMode';

type SortOption =
  | 'title_asc'
  | 'title_desc'
  | 'priority_desc'
  | 'priority_asc'
  | 'momentum_desc'
  | 'momentum_asc'
  | 'activity_desc'
  | 'activity_asc'
  | 'created_desc'
  | 'created_asc'
  | 'target_asc'
  | 'target_desc';

const sortOptions: { value: SortOption; label: string }[] = [
  { value: 'priority_desc', label: 'Priority (High to Low)' },
  { value: 'priority_asc', label: 'Priority (Low to High)' },
  { value: 'momentum_desc', label: 'Momentum (High to Low)' },
  { value: 'momentum_asc', label: 'Momentum (Low to High)' },
  { value: 'title_asc', label: 'Title (A-Z)' },
  { value: 'title_desc', label: 'Title (Z-A)' },
  { value: 'activity_desc', label: 'Last Activity (Recent)' },
  { value: 'activity_asc', label: 'Last Activity (Oldest)' },
  { value: 'target_asc', label: 'Target Date (Soonest)' },
  { value: 'target_desc', label: 'Target Date (Latest)' },
  { value: 'created_desc', label: 'Created (Newest)' },
  { value: 'created_asc', label: 'Created (Oldest)' },
];

export function Projects() {
  const [status, setStatus] = useState<string>('active');
  const [searchQuery, setSearchQuery] = useState('');
  const [priorityFilter, setPriorityFilter] = useState<string>('');
  const [sortBy, setSortBy] = useState<SortOption>('priority_desc');
  const [showAdvancedFilters, setShowAdvancedFilters] = useState(false);
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [viewMode, setViewMode] = useState<ViewMode>(() => {
    const saved = localStorage.getItem(VIEW_MODE_STORAGE_KEY);
    return (saved === 'list' || saved === 'grid') ? saved : 'grid';
  });
  const { data, isLoading, error } = useProjects({ status });

  // Persist view mode preference
  useEffect(() => {
    localStorage.setItem(VIEW_MODE_STORAGE_KEY, viewMode);
  }, [viewMode]);

  const allProjects = data?.projects || [];

  // Compute orphan projects (active with no area assigned)
  const orphanProjects = useMemo(() => {
    return allProjects.filter(p => !p.area_id && p.status === 'active');
  }, [allProjects]);

  // Client-side filtering and sorting for instant results
  const filteredProjects = useMemo(() => {
    // First, filter
    const filtered = allProjects.filter((project) => {
      // Search filter
      if (searchQuery) {
        const query = searchQuery.toLowerCase();
        const matchesTitle = project.title.toLowerCase().includes(query);
        const matchesDescription = project.description?.toLowerCase().includes(query);
        const matchesArea = project.area?.title?.toLowerCase().includes(query);
        if (!matchesTitle && !matchesDescription && !matchesArea) {
          return false;
        }
      }

      // Priority filter
      if (priorityFilter) {
        if (priorityFilter === 'high' && project.priority < 7) return false;
        if (priorityFilter === 'medium' && (project.priority < 4 || project.priority > 6)) return false;
        if (priorityFilter === 'low' && project.priority > 3) return false;
      }

      return true;
    });

    // Then, sort
    const sortFunctions: Record<SortOption, (a: Project, b: Project) => number> = {
      title_asc: (a, b) => a.title.localeCompare(b.title),
      title_desc: (a, b) => b.title.localeCompare(a.title),
      priority_desc: (a, b) => b.priority - a.priority,
      priority_asc: (a, b) => a.priority - b.priority,
      momentum_desc: (a, b) => b.momentum_score - a.momentum_score,
      momentum_asc: (a, b) => a.momentum_score - b.momentum_score,
      activity_desc: (a, b) => {
        const aDate = a.last_activity_at ? new Date(a.last_activity_at).getTime() : 0;
        const bDate = b.last_activity_at ? new Date(b.last_activity_at).getTime() : 0;
        return bDate - aDate;
      },
      activity_asc: (a, b) => {
        const aDate = a.last_activity_at ? new Date(a.last_activity_at).getTime() : Infinity;
        const bDate = b.last_activity_at ? new Date(b.last_activity_at).getTime() : Infinity;
        return aDate - bDate;
      },
      created_desc: (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime(),
      created_asc: (a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime(),
      target_asc: (a, b) => {
        const aDate = a.target_completion_date ? new Date(a.target_completion_date).getTime() : Infinity;
        const bDate = b.target_completion_date ? new Date(b.target_completion_date).getTime() : Infinity;
        return aDate - bDate;
      },
      target_desc: (a, b) => {
        const aDate = a.target_completion_date ? new Date(a.target_completion_date).getTime() : 0;
        const bDate = b.target_completion_date ? new Date(b.target_completion_date).getTime() : 0;
        return bDate - aDate;
      },
    };

    return [...filtered].sort(sortFunctions[sortBy]);
  }, [allProjects, searchQuery, priorityFilter, sortBy]);

  if (error) return <Error message="Failed to load projects" fullPage />;

  return (
    <div className="p-8">
      {/* Header */}
      <header className="mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">Projects</h1>
            <p className="text-gray-600 dark:text-gray-400 mt-1">Manage your active projects and track momentum</p>
          </div>
          <button
            onClick={() => setIsCreateModalOpen(true)}
            className="btn btn-primary flex items-center gap-2"
          >
            <Plus className="w-4 h-4" />
            New Project
          </button>
        </div>
      </header>

      {/* Search and Filters */}
      <div className="mb-6 space-y-4">
        {/* Search Bar and Sort */}
        <div className="flex items-center gap-4">
          <SearchInput
            value={searchQuery}
            onChange={setSearchQuery}
            placeholder="Search projects by title, description, or area..."
            className="flex-1"
          />
          <div className="flex items-center gap-2">
            <ArrowUpDown className="w-4 h-4 text-gray-500 dark:text-gray-400" />
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as SortOption)}
              className="input py-2 pr-8 min-w-[180px]"
            >
              {sortOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>
          {/* View Toggle */}
          <div className="flex items-center border border-gray-300 dark:border-gray-600 rounded-lg overflow-hidden">
            <button
              onClick={() => setViewMode('grid')}
              className={`p-2 transition-colors ${
                viewMode === 'grid'
                  ? 'bg-primary-100 text-primary-700'
                  : 'bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-700'
              }`}
              title="Grid View"
            >
              <LayoutGrid className="w-4 h-4" />
            </button>
            <button
              onClick={() => setViewMode('list')}
              className={`p-2 transition-colors ${
                viewMode === 'list'
                  ? 'bg-primary-100 text-primary-700'
                  : 'bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-700'
              }`}
              title="List View"
            >
              <List className="w-4 h-4" />
            </button>
          </div>
          <button
            onClick={() => setShowAdvancedFilters(!showAdvancedFilters)}
            className={`btn btn-secondary flex items-center gap-2 ${
              showAdvancedFilters ? 'bg-primary-100 text-primary-700' : ''
            }`}
          >
            <SlidersHorizontal className="w-4 h-4" />
            Filters
          </button>
        </div>

        {/* Status Filters */}
        <div className="card">
          <div className="flex items-center gap-4">
            <Filter className="w-5 h-5 text-gray-500 dark:text-gray-400" />
            <div className="flex gap-2 flex-wrap">
              <button
                onClick={() => setStatus('active')}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  status === 'active'
                    ? 'bg-primary-100 text-primary-700'
                    : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-600'
                }`}
              >
                Active
              </button>
              <button
                onClick={() => setStatus('on_hold')}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  status === 'on_hold'
                    ? 'bg-primary-100 text-primary-700'
                    : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-600'
                }`}
              >
                On Hold
              </button>
              <button
                onClick={() => setStatus('someday_maybe')}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  status === 'someday_maybe'
                    ? 'bg-purple-100 text-purple-700'
                    : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-600'
                }`}
              >
                Someday/Maybe
              </button>
              <button
                onClick={() => setStatus('completed')}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  status === 'completed'
                    ? 'bg-primary-100 text-primary-700'
                    : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-600'
                }`}
              >
                Completed
              </button>
              <button
                onClick={() => setStatus('archived')}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  status === 'archived'
                    ? 'bg-primary-100 text-primary-700'
                    : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-600'
                }`}
              >
                Archived
              </button>
              <button
                onClick={() => setStatus('')}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  status === ''
                    ? 'bg-primary-100 text-primary-700'
                    : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-600'
                }`}
              >
                All
              </button>
            </div>
          </div>
        </div>

        {/* Advanced Filters */}
        {showAdvancedFilters && (
          <div className="card">
            <h3 className="font-semibold text-gray-900 dark:text-gray-100 mb-4">Advanced Filters</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="label">Priority Level</label>
                <select
                  value={priorityFilter}
                  onChange={(e) => setPriorityFilter(e.target.value)}
                  className="input"
                >
                  <option value="">All Priorities</option>
                  <option value="high">High Priority (7-10)</option>
                  <option value="medium">Medium Priority (4-6)</option>
                  <option value="low">Low Priority (1-3)</option>
                </select>
              </div>
              <div className="flex items-end">
                <button
                  onClick={() => {
                    setSearchQuery('');
                    setPriorityFilter('');
                    setSortBy('priority_desc');
                  }}
                  className="btn btn-secondary w-full"
                >
                  Reset Filters & Sort
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Results Count */}
        {(searchQuery || priorityFilter) && (
          <div className="text-sm text-gray-600 dark:text-gray-400">
            Showing {filteredProjects.length} of {allProjects.length} projects
          </div>
        )}
      </div>

      {/* Orphan Projects Warning */}
      {orphanProjects.length > 0 && (status === 'active' || status === '') && (
        <div className="mb-6 p-4 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg">
          <div className="flex items-start gap-3">
            <AlertTriangle className="w-5 h-5 text-amber-500 mt-0.5 flex-shrink-0" />
            <div className="flex-1">
              <h3 className="font-medium text-amber-800 dark:text-amber-300">
                {orphanProjects.length} project{orphanProjects.length !== 1 ? 's' : ''} without an area
              </h3>
              <p className="text-sm text-amber-700 dark:text-amber-400 mt-1">
                Best practice is to assign every project to an Area of Responsibility.
              </p>
              <div className="flex flex-wrap gap-2 mt-2">
                {orphanProjects.slice(0, 5).map((p) => (
                  <Link
                    key={p.id}
                    to={`/projects/${p.id}`}
                    className="inline-flex items-center gap-1 text-xs px-2 py-1 bg-amber-100 dark:bg-amber-800/40 text-amber-800 dark:text-amber-300 rounded hover:bg-amber-200 dark:hover:bg-amber-800/60 transition-colors"
                  >
                    <Layers className="w-3 h-3" />
                    {p.title}
                  </Link>
                ))}
                {orphanProjects.length > 5 && (
                  <span className="text-xs text-amber-600 dark:text-amber-400 px-2 py-1">
                    +{orphanProjects.length - 5} more
                  </span>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Projects Grid/List */}
      {isLoading ? (
        viewMode === 'grid' ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {Array.from({ length: 6 }).map((_, i) => (
              <ProjectCardSkeleton key={i} />
            ))}
          </div>
        ) : (
          <div className="card overflow-hidden">
            <table className="w-full">
              <thead className="bg-gray-50 dark:bg-gray-800 border-b dark:border-gray-700">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Title</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Area</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Status</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Priority</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Momentum</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Tasks</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Last Activity</th>
                </tr>
              </thead>
              <tbody>
                {Array.from({ length: 6 }).map((_, i) => (
                  <TableRowSkeleton key={i} columns={7} />
                ))}
              </tbody>
            </table>
          </div>
        )
      ) : filteredProjects.length > 0 ? (
        viewMode === 'grid' ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredProjects.map((project) => (
              <ProjectCard key={project.id} project={project} />
            ))}
          </div>
        ) : (
          <ProjectListView projects={filteredProjects} />
        )
      ) : allProjects.length === 0 ? (
        <div className="card text-center py-12">
          <p className="text-gray-500 dark:text-gray-400 text-lg">No {status} projects found</p>
          <button
            onClick={() => setIsCreateModalOpen(true)}
            className="btn btn-primary mt-4"
          >
            Create Your First Project
          </button>
        </div>
      ) : (
        <div className="card text-center py-12">
          <p className="text-gray-500 dark:text-gray-400 text-lg mb-2">No projects match your filters</p>
          <p className="text-gray-400 dark:text-gray-500 text-sm mb-4">
            Try adjusting your search or filter criteria
          </p>
          <button
            onClick={() => {
              setSearchQuery('');
              setPriorityFilter('');
              setSortBy('priority_desc');
            }}
            className="btn btn-secondary"
          >
            Clear Filters
          </button>
        </div>
      )}

      {/* Create Project Modal */}
      <CreateProjectModal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
      />
    </div>
  );
}
