import { useState, useMemo, useEffect } from 'react';
import { Plus, Filter, ArrowUpDown, LayoutGrid, List, Pencil, Trash2, Eye } from 'lucide-react';
import toast from 'react-hot-toast';
import { useVisions, useDeleteVision } from '@/hooks/useVisions';
import { Error } from '@/components/common/Error';
import { VisionModal } from '@/components/visions/VisionModal';
import { AreaCardSkeleton } from '@/components/common/Skeleton';
import { SearchInput } from '@/components/common/SearchInput';
import { Vision, VisionTimeframe } from '@/types';

type ViewMode = 'grid' | 'list';

const VIEW_MODE_STORAGE_KEY = 'visionsViewMode';

type SortOption = 'title_asc' | 'title_desc' | 'created_desc' | 'created_asc';

const sortOptions: { value: SortOption; label: string }[] = [
  { value: 'title_asc', label: 'Title (A-Z)' },
  { value: 'title_desc', label: 'Title (Z-A)' },
  { value: 'created_desc', label: 'Created (Newest)' },
  { value: 'created_asc', label: 'Created (Oldest)' },
];

const timeframeConfig: Record<VisionTimeframe, { label: string; color: string }> = {
  '3_year': { label: '3 Year', color: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300' },
  '5_year': { label: '5 Year', color: 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300' },
  'life_purpose': { label: 'Life Purpose', color: 'bg-indigo-100 text-indigo-700 dark:bg-indigo-900/30 dark:text-indigo-300' },
};

export function Visions() {
  const [searchQuery, setSearchQuery] = useState('');
  const [timeframeFilter, setTimeframeFilter] = useState<string>('all');
  const [sortBy, setSortBy] = useState<SortOption>('created_desc');
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingVision, setEditingVision] = useState<Vision | null>(null);
  const [viewMode, setViewMode] = useState<ViewMode>(() => {
    const saved = localStorage.getItem(VIEW_MODE_STORAGE_KEY);
    return (saved === 'list' || saved === 'grid') ? saved : 'grid';
  });

  const { data: visions, isLoading, error } = useVisions();
  const deleteVision = useDeleteVision();

  useEffect(() => {
    localStorage.setItem(VIEW_MODE_STORAGE_KEY, viewMode);
  }, [viewMode]);

  if (error) return <Error message="Failed to load visions" fullPage />;

  const allVisions = visions || [];

  const filteredVisions = useMemo(() => {
    const filtered = allVisions.filter((vision) => {
      if (searchQuery) {
        const query = searchQuery.toLowerCase();
        if (!vision.title.toLowerCase().includes(query) &&
            !vision.description?.toLowerCase().includes(query)) {
          return false;
        }
      }
      if (timeframeFilter !== 'all' && vision.timeframe !== timeframeFilter) return false;
      return true;
    });

    const sortFunctions: Record<SortOption, (a: Vision, b: Vision) => number> = {
      title_asc: (a, b) => a.title.localeCompare(b.title),
      title_desc: (a, b) => b.title.localeCompare(a.title),
      created_desc: (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime(),
      created_asc: (a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime(),
    };

    return [...filtered].sort(sortFunctions[sortBy]);
  }, [allVisions, searchQuery, timeframeFilter, sortBy]);

  const handleCreate = () => {
    setEditingVision(null);
    setIsModalOpen(true);
  };

  const handleEdit = (vision: Vision) => {
    setEditingVision(vision);
    setIsModalOpen(true);
  };

  const handleDelete = (id: number) => {
    if (confirm('Are you sure you want to delete this vision?')) {
      deleteVision.mutate(id, {
        onSuccess: () => toast.success('Vision deleted'),
        onError: () => toast.error('Failed to delete vision'),
      });
    }
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
    setEditingVision(null);
  };

  const FilterButton = ({ value, label, current, onClick }: { value: string; label: string; current: string; onClick: (v: string) => void }) => (
    <button
      onClick={() => onClick(value)}
      className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
        current === value
          ? 'bg-primary-100 text-primary-700'
          : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-600'
      }`}
    >
      {label}
    </button>
  );

  return (
    <div className="p-8">
      <header className="mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">Visions</h1>
            <p className="text-gray-600 dark:text-gray-400 mt-1">Long-term vision and life purpose</p>
          </div>
          <button onClick={handleCreate} className="btn btn-primary flex items-center gap-2">
            <Plus className="w-4 h-4" />
            New Vision
          </button>
        </div>
      </header>

      <div className="mb-6 space-y-4">
        <div className="flex items-center gap-4">
          <SearchInput
            value={searchQuery}
            onChange={setSearchQuery}
            placeholder="Search visions..."
            className="flex-1"
          />
          <div className="flex items-center gap-2">
            <ArrowUpDown className="w-4 h-4 text-gray-500 dark:text-gray-400" />
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as SortOption)}
              className="input py-2 pr-8 min-w-[200px]"
            >
              {sortOptions.map((option) => (
                <option key={option.value} value={option.value}>{option.label}</option>
              ))}
            </select>
          </div>
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

        <div className="card">
          <div className="flex items-center gap-4">
            <Filter className="w-5 h-5 text-gray-500 dark:text-gray-400" />
            <div className="flex gap-2 flex-wrap">
              <FilterButton value="all" label="All Timeframes" current={timeframeFilter} onClick={setTimeframeFilter} />
              <FilterButton value="3_year" label="3 Year" current={timeframeFilter} onClick={setTimeframeFilter} />
              <FilterButton value="5_year" label="5 Year" current={timeframeFilter} onClick={setTimeframeFilter} />
              <FilterButton value="life_purpose" label="Life Purpose" current={timeframeFilter} onClick={setTimeframeFilter} />
            </div>
          </div>
        </div>

        {!isLoading && (
          <div className="text-sm text-gray-600 dark:text-gray-400">
            {filteredVisions.length} {filteredVisions.length === 1 ? 'vision' : 'visions'}
            {searchQuery || timeframeFilter !== 'all' ? ' (filtered)' : ''}
          </div>
        )}
      </div>

      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {Array.from({ length: 6 }).map((_, i) => (
            <AreaCardSkeleton key={i} />
          ))}
        </div>
      ) : filteredVisions.length > 0 ? (
        viewMode === 'grid' ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredVisions.map((vision) => (
              <div key={vision.id} className="card hover:shadow-lg transition-all">
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center gap-2 min-w-0">
                    <Eye className="w-5 h-5 text-indigo-600 dark:text-indigo-400 flex-shrink-0" />
                    <h3 className="font-semibold text-gray-900 dark:text-gray-100 truncate">{vision.title}</h3>
                  </div>
                  <div className="flex items-center gap-1 flex-shrink-0 ml-2">
                    <button
                      onClick={() => handleEdit(vision)}
                      className="p-1.5 text-gray-400 hover:text-primary-600 dark:hover:text-primary-400 transition-colors"
                      title="Edit"
                    >
                      <Pencil className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => handleDelete(vision.id)}
                      className="p-1.5 text-gray-400 hover:text-red-600 dark:hover:text-red-400 transition-colors"
                      title="Delete"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>

                {vision.timeframe && (
                  <div className="mb-3">
                    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${timeframeConfig[vision.timeframe].color}`}>
                      {timeframeConfig[vision.timeframe].label}
                    </span>
                  </div>
                )}

                {vision.description && (
                  <p className="text-sm text-gray-600 dark:text-gray-400 line-clamp-3">
                    {vision.description}
                  </p>
                )}
              </div>
            ))}
          </div>
        ) : (
          <div className="card overflow-hidden">
            <table className="w-full">
              <thead className="bg-gray-50 dark:bg-gray-800 border-b dark:border-gray-700">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Title</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Timeframe</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Description</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                {filteredVisions.map((vision) => (
                  <tr key={vision.id} className="hover:bg-gray-50 dark:hover:bg-gray-800">
                    <td className="px-4 py-3 font-medium text-gray-900 dark:text-gray-100">{vision.title}</td>
                    <td className="px-4 py-3">
                      {vision.timeframe ? (
                        <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${timeframeConfig[vision.timeframe].color}`}>
                          {timeframeConfig[vision.timeframe].label}
                        </span>
                      ) : '-'}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-400 truncate max-w-md">
                      {vision.description || '-'}
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-1">
                        <button onClick={() => handleEdit(vision)} className="p-1.5 text-gray-400 hover:text-primary-600 transition-colors" title="Edit">
                          <Pencil className="w-4 h-4" />
                        </button>
                        <button onClick={() => handleDelete(vision.id)} className="p-1.5 text-gray-400 hover:text-red-600 transition-colors" title="Delete">
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )
      ) : allVisions.length === 0 ? (
        <div className="card text-center py-12">
          <Eye className="w-12 h-12 text-gray-400 dark:text-gray-500 mx-auto mb-4" />
          <h3 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-2">No visions yet</h3>
          <p className="text-gray-600 dark:text-gray-400 mb-6">
            Capture your long-term vision to guide your goals and projects
          </p>
          <button onClick={handleCreate} className="btn btn-primary inline-flex items-center gap-2">
            <Plus className="w-4 h-4" />
            Create Your First Vision
          </button>
        </div>
      ) : (
        <div className="card text-center py-12">
          <h3 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-2">No visions match your filters</h3>
          <p className="text-gray-600 dark:text-gray-400 mb-6">Try adjusting your search or filter criteria</p>
          <button
            onClick={() => { setSearchQuery(''); setTimeframeFilter('all'); }}
            className="btn btn-secondary"
          >
            Clear Filters
          </button>
        </div>
      )}

      <VisionModal isOpen={isModalOpen} onClose={handleCloseModal} vision={editingVision} />
    </div>
  );
}
