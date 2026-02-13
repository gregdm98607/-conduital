import { useState, useMemo, useEffect } from 'react';
import { Plus, Filter, ArrowUpDown, LayoutGrid, List, Archive, AlertTriangle } from 'lucide-react';
import toast from 'react-hot-toast';
import { useAreas, useDeleteArea, useMarkAreaReviewed, useArchiveArea, useUnarchiveArea } from '../hooks/useAreas';
import { Error } from '../components/common/Error';
import { AreaCard } from '../components/areas/AreaCard';
import { AreaListView } from '../components/areas/AreaListView';
import { AreaModal } from '../components/areas/AreaModal';
import { Modal } from '../components/common/Modal';
import { CreateProjectModal } from '../components/projects/CreateProjectModal';
import { AreaCardSkeleton, TableRowSkeleton } from '@/components/common/Skeleton';
import { SearchInput } from '@/components/common/SearchInput';
import { Area } from '@/types';

type ViewMode = 'grid' | 'list';

const VIEW_MODE_STORAGE_KEY = 'pt-areasViewMode';

type SortOption =
  | 'frequency_urgency'
  | 'projects_desc'
  | 'projects_asc'
  | 'title_asc'
  | 'title_desc'
  | 'created_desc'
  | 'created_asc';

const sortOptions: { value: SortOption; label: string }[] = [
  { value: 'frequency_urgency', label: 'Review Frequency (Urgent First)' },
  { value: 'projects_desc', label: 'Active Projects (Most)' },
  { value: 'projects_asc', label: 'Active Projects (Least)' },
  { value: 'title_asc', label: 'Title (A-Z)' },
  { value: 'title_desc', label: 'Title (Z-A)' },
  { value: 'created_desc', label: 'Created (Newest)' },
  { value: 'created_asc', label: 'Created (Oldest)' },
];

// Map review frequency to urgency level (lower = more urgent)
const frequencyUrgency: Record<string, number> = {
  daily: 1,
  weekly: 2,
  monthly: 3,
};

export function Areas() {
  const [searchQuery, setSearchQuery] = useState('');
  const [reviewFrequencyFilter, setReviewFrequencyFilter] = useState<string>('all');
  const [sortBy, setSortBy] = useState<SortOption>('frequency_urgency');
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingArea, setEditingArea] = useState<Area | null>(null);
  const [viewMode, setViewMode] = useState<ViewMode>(() => {
    const saved = localStorage.getItem(VIEW_MODE_STORAGE_KEY);
    return (saved === 'list' || saved === 'grid') ? saved : 'grid';
  });

  const [showArchived, setShowArchived] = useState(false);

  // State for creating a project from area quick action
  const [isCreateProjectModalOpen, setIsCreateProjectModalOpen] = useState(false);
  const [createProjectAreaId, setCreateProjectAreaId] = useState<number | undefined>();

  // State for archive confirmation dialog
  const [archiveConfirm, setArchiveConfirm] = useState<{
    areaId: number;
    areaTitle: string;
    activeProjectCount: number;
  } | null>(null);

  const { data: areas, isLoading, error } = useAreas(showArchived);
  const deleteArea = useDeleteArea();
  const markAreaReviewed = useMarkAreaReviewed();
  const archiveArea = useArchiveArea();
  const unarchiveArea = useUnarchiveArea();

  // Persist view mode preference
  useEffect(() => {
    localStorage.setItem(VIEW_MODE_STORAGE_KEY, viewMode);
  }, [viewMode]);

  if (error) return <Error message="Failed to load areas" fullPage />;

  const allAreas = areas || [];

  // Client-side filtering and sorting for instant results
  const filteredAreas = useMemo(() => {
    // First, filter
    const filtered = allAreas.filter((area) => {
      // Search filter
      if (searchQuery) {
        const query = searchQuery.toLowerCase();
        const matchesTitle = area.title.toLowerCase().includes(query);
        const matchesDescription = area.description?.toLowerCase().includes(query);
        const matchesPath = area.folder_path?.toLowerCase().includes(query);
        if (!matchesTitle && !matchesDescription && !matchesPath) {
          return false;
        }
      }

      // Review frequency filter
      if (reviewFrequencyFilter && reviewFrequencyFilter !== 'all') {
        if (area.review_frequency !== reviewFrequencyFilter) {
          return false;
        }
      }

      return true;
    });

    // Then, sort
    const sortFunctions: Record<SortOption, (a: Area, b: Area) => number> = {
      frequency_urgency: (a, b) => {
        const aUrgency = frequencyUrgency[a.review_frequency] || 99;
        const bUrgency = frequencyUrgency[b.review_frequency] || 99;
        if (aUrgency !== bUrgency) return aUrgency - bUrgency;
        // Secondary sort by active projects (desc) for same frequency
        return (b.active_project_count || 0) - (a.active_project_count || 0);
      },
      projects_desc: (a, b) => (b.active_project_count || 0) - (a.active_project_count || 0),
      projects_asc: (a, b) => (a.active_project_count || 0) - (b.active_project_count || 0),
      title_asc: (a, b) => a.title.localeCompare(b.title),
      title_desc: (a, b) => b.title.localeCompare(a.title),
      created_desc: (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime(),
      created_asc: (a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime(),
    };

    return [...filtered].sort(sortFunctions[sortBy]);
  }, [allAreas, searchQuery, reviewFrequencyFilter, sortBy]);

  const handleCreate = () => {
    setEditingArea(null);
    setIsModalOpen(true);
  };

  const handleEdit = (area: Area) => {
    setEditingArea(area);
    setIsModalOpen(true);
  };

  const handleDelete = (id: number) => {
    deleteArea.mutate(id, {
      onSuccess: () => {
        toast.success('Area deleted successfully');
      },
      onError: (error) => {
        console.error('Failed to delete area:', error);
        toast.error('Failed to delete area. Please try again.', { id: 'area-delete-error' });
      },
    });
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
    setEditingArea(null);
  };

  const handleMarkReviewed = (id: number) => {
    markAreaReviewed.mutate(id, {
      onSuccess: () => {
        toast.success('Area marked as reviewed');
      },
      onError: (error) => {
        console.error('Failed to mark area as reviewed:', error);
        toast.error('Failed to mark area as reviewed', { id: 'area-review-error' });
      },
    });
  };

  const handleAddProject = (areaId: number) => {
    setCreateProjectAreaId(areaId);
    setIsCreateProjectModalOpen(true);
  };

  const handleArchive = (id: number) => {
    const area = allAreas.find((a) => a.id === id);
    const activeCount = area?.active_project_count ?? 0;

    if (activeCount > 0) {
      // Show confirmation dialog with cascade warning
      setArchiveConfirm({
        areaId: id,
        areaTitle: area?.title ?? 'this area',
        activeProjectCount: activeCount,
      });
    } else {
      // No active projects — archive directly with simple confirmation
      archiveArea.mutate({ id }, {
        onSuccess: () => toast.success('Area archived'),
        onError: () => toast.error('Failed to archive area', { id: 'area-archive-error' }),
      });
    }
  };

  const handleForceArchive = () => {
    if (!archiveConfirm) return;
    archiveArea.mutate({ id: archiveConfirm.areaId, force: true }, {
      onSuccess: () => {
        toast.success('Area archived — active projects moved to On Hold');
        setArchiveConfirm(null);
      },
      onError: () => {
        toast.error('Failed to archive area', { id: 'area-archive-error' });
        setArchiveConfirm(null);
      },
    });
  };

  const handleUnarchive = (id: number) => {
    unarchiveArea.mutate(id, {
      onSuccess: () => toast.success('Area unarchived'),
      onError: () => toast.error('Failed to unarchive area', { id: 'area-archive-error' }),
    });
  };

  return (
    <div className="p-8">
      {/* Header */}
      <header className="mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">Areas</h1>
            <p className="text-gray-600 dark:text-gray-400 mt-1">Organize your projects by areas of responsibility</p>
          </div>
          <button
            onClick={handleCreate}
            className="btn btn-primary flex items-center gap-2"
          >
            <Plus className="w-4 h-4" />
            New Area
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
            placeholder="Search areas by title, description, or folder path..."
            className="flex-1"
          />
          <div className="flex items-center gap-2">
            <ArrowUpDown className="w-4 h-4 text-gray-500 dark:text-gray-400" />
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as SortOption)}
              className="input py-2 pr-8 min-w-[220px]"
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
        </div>

        {/* Review Frequency Filters */}
        <div className="card">
          <div className="flex items-center gap-4">
            <Filter className="w-5 h-5 text-gray-500 dark:text-gray-400" />
            <div className="flex gap-2 flex-wrap">
              <button
                onClick={() => setReviewFrequencyFilter('all')}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  reviewFrequencyFilter === 'all'
                    ? 'bg-primary-100 text-primary-700'
                    : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-600'
                }`}
              >
                All
              </button>
              <button
                onClick={() => setReviewFrequencyFilter('daily')}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  reviewFrequencyFilter === 'daily'
                    ? 'bg-primary-100 text-primary-700'
                    : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-600'
                }`}
              >
                Daily
              </button>
              <button
                onClick={() => setReviewFrequencyFilter('weekly')}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  reviewFrequencyFilter === 'weekly'
                    ? 'bg-primary-100 text-primary-700'
                    : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-600'
                }`}
              >
                Weekly
              </button>
              <button
                onClick={() => setReviewFrequencyFilter('monthly')}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  reviewFrequencyFilter === 'monthly'
                    ? 'bg-primary-100 text-primary-700'
                    : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-600'
                }`}
              >
                Monthly
              </button>
            </div>
            <div className="ml-auto flex items-center gap-2">
              <label className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400 cursor-pointer">
                <input
                  type="checkbox"
                  checked={showArchived}
                  onChange={(e) => setShowArchived(e.target.checked)}
                  className="rounded border-gray-300 dark:border-gray-600 text-primary-600 focus:ring-primary-500"
                />
                <Archive className="w-4 h-4" />
                Show Archived
              </label>
            </div>
          </div>
        </div>

        {/* Results count */}
        {!isLoading && (
          <div className="text-sm text-gray-600 dark:text-gray-400">
            {filteredAreas.length} {filteredAreas.length === 1 ? 'area' : 'areas'}
            {searchQuery || reviewFrequencyFilter !== 'all' ? ' (filtered)' : ''}
          </div>
        )}
      </div>

      {/* Areas Grid/List */}
      {isLoading ? (
        viewMode === 'grid' ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {Array.from({ length: 6 }).map((_, i) => (
              <AreaCardSkeleton key={i} />
            ))}
          </div>
        ) : (
          <div className="card overflow-hidden">
            <table className="w-full">
              <thead className="bg-gray-50 dark:bg-gray-800 border-b dark:border-gray-700">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Title</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Review Frequency</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Projects</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Standard of Excellence</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Actions</th>
                </tr>
              </thead>
              <tbody>
                {Array.from({ length: 6 }).map((_, i) => (
                  <TableRowSkeleton key={i} columns={5} />
                ))}
              </tbody>
            </table>
          </div>
        )
      ) : filteredAreas.length > 0 ? (
        viewMode === 'grid' ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredAreas.map((area) => (
              <AreaCard
                key={area.id}
                area={area}
                onEdit={handleEdit}
                onDelete={handleDelete}
                onMarkReviewed={handleMarkReviewed}
                isMarkingReviewed={markAreaReviewed.isPending}
                onAddProject={handleAddProject}
                onArchive={handleArchive}
                onUnarchive={handleUnarchive}
              />
            ))}
          </div>
        ) : (
          <AreaListView
            areas={filteredAreas}
            onEdit={handleEdit}
            onDelete={handleDelete}
            onMarkReviewed={handleMarkReviewed}
            isMarkingReviewed={markAreaReviewed.isPending}
          />
        )
      ) : allAreas.length === 0 ? (
        <div className="card text-center py-12">
          <h3 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-2">No areas found</h3>
          <p className="text-gray-600 dark:text-gray-400 mb-6">
            Create your first area to organize your projects by responsibility
          </p>
          <button
            onClick={handleCreate}
            className="btn btn-primary inline-flex items-center gap-2"
          >
            <Plus className="w-4 h-4" />
            Create Your First Area
          </button>
        </div>
      ) : (
        <div className="card text-center py-12">
          <h3 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-2">No areas match your filters</h3>
          <p className="text-gray-600 dark:text-gray-400 mb-6">
            Try adjusting your search or filter criteria
          </p>
          <button
            onClick={() => {
              setSearchQuery('');
              setReviewFrequencyFilter('all');
              setSortBy('frequency_urgency');
            }}
            className="btn btn-secondary"
          >
            Clear Filters
          </button>
        </div>
      )}

      {/* Create/Edit Area Modal */}
      <AreaModal
        isOpen={isModalOpen}
        onClose={handleCloseModal}
        area={editingArea}
      />

      {/* Create Project Modal (from quick action) */}
      <CreateProjectModal
        isOpen={isCreateProjectModalOpen}
        onClose={() => {
          setIsCreateProjectModalOpen(false);
          setCreateProjectAreaId(undefined);
        }}
        defaultAreaId={createProjectAreaId}
      />

      {/* Archive Confirmation Dialog */}
      <Modal
        isOpen={!!archiveConfirm}
        onClose={() => setArchiveConfirm(null)}
        title="Archive Area"
        size="sm"
      >
        {archiveConfirm && (
          <div className="space-y-4">
            <div className="flex items-start gap-3 p-3 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg">
              <AlertTriangle className="w-5 h-5 text-amber-500 shrink-0 mt-0.5" />
              <div>
                <p className="font-medium text-amber-800 dark:text-amber-300">
                  "{archiveConfirm.areaTitle}" has {archiveConfirm.activeProjectCount} active project{archiveConfirm.activeProjectCount !== 1 ? 's' : ''}
                </p>
                <p className="text-sm text-amber-700 dark:text-amber-400 mt-1">
                  Archiving will move all active projects to <strong>On Hold</strong> status. You can unarchive the area later to restore it.
                </p>
              </div>
            </div>

            <div className="flex justify-end gap-3">
              <button
                onClick={() => setArchiveConfirm(null)}
                className="btn btn-secondary"
              >
                Cancel
              </button>
              <button
                onClick={handleForceArchive}
                disabled={archiveArea.isPending}
                className="btn bg-amber-600 hover:bg-amber-700 text-white"
              >
                {archiveArea.isPending ? 'Archiving...' : 'Archive Anyway'}
              </button>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
}
