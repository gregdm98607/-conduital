import { useState, useMemo, useEffect } from 'react';
import { Plus, Filter, ArrowUpDown, LayoutGrid, List, Pencil, Trash2, Crosshair } from 'lucide-react';
import toast from 'react-hot-toast';
import { useGoals, useDeleteGoal } from '@/hooks/useGoals';
import { Error } from '@/components/common/Error';
import { GoalModal } from '@/components/goals/GoalModal';
import { AreaCardSkeleton } from '@/components/common/Skeleton';
import { SearchInput } from '@/components/common/SearchInput';
import { formatDate } from '@/utils/date';
import { Goal, GoalStatus, GoalTimeframe } from '@/types';

type ViewMode = 'grid' | 'list';

const VIEW_MODE_STORAGE_KEY = 'goalsViewMode';

type SortOption = 'title_asc' | 'title_desc' | 'target_date' | 'created_desc' | 'created_asc';

const sortOptions: { value: SortOption; label: string }[] = [
  { value: 'target_date', label: 'Target Date (Soonest)' },
  { value: 'title_asc', label: 'Title (A-Z)' },
  { value: 'title_desc', label: 'Title (Z-A)' },
  { value: 'created_desc', label: 'Created (Newest)' },
  { value: 'created_asc', label: 'Created (Oldest)' },
];

const statusConfig: Record<GoalStatus, { label: string; color: string }> = {
  active: { label: 'Active', color: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300' },
  achieved: { label: 'Achieved', color: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300' },
  deferred: { label: 'Deferred', color: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-300' },
  abandoned: { label: 'Abandoned', color: 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400' },
};

const timeframeLabels: Record<GoalTimeframe, string> = {
  '1_year': '1 Year',
  '2_year': '2 Year',
  '3_year': '3 Year',
};

export function Goals() {
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [timeframeFilter, setTimeframeFilter] = useState<string>('all');
  const [sortBy, setSortBy] = useState<SortOption>('target_date');
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingGoal, setEditingGoal] = useState<Goal | null>(null);
  const [viewMode, setViewMode] = useState<ViewMode>(() => {
    const saved = localStorage.getItem(VIEW_MODE_STORAGE_KEY);
    return (saved === 'list' || saved === 'grid') ? saved : 'grid';
  });

  const { data: goals, isLoading, error } = useGoals();
  const deleteGoal = useDeleteGoal();

  useEffect(() => {
    localStorage.setItem(VIEW_MODE_STORAGE_KEY, viewMode);
  }, [viewMode]);

  if (error) return <Error message="Failed to load goals" fullPage />;

  const allGoals = goals || [];

  const filteredGoals = useMemo(() => {
    const filtered = allGoals.filter((goal) => {
      if (searchQuery) {
        const query = searchQuery.toLowerCase();
        if (!goal.title.toLowerCase().includes(query) &&
            !goal.description?.toLowerCase().includes(query)) {
          return false;
        }
      }
      if (statusFilter !== 'all' && goal.status !== statusFilter) return false;
      if (timeframeFilter !== 'all' && goal.timeframe !== timeframeFilter) return false;
      return true;
    });

    const sortFunctions: Record<SortOption, (a: Goal, b: Goal) => number> = {
      title_asc: (a, b) => a.title.localeCompare(b.title),
      title_desc: (a, b) => b.title.localeCompare(a.title),
      target_date: (a, b) => {
        if (!a.target_date && !b.target_date) return 0;
        if (!a.target_date) return 1;
        if (!b.target_date) return -1;
        return new Date(a.target_date).getTime() - new Date(b.target_date).getTime();
      },
      created_desc: (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime(),
      created_asc: (a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime(),
    };

    return [...filtered].sort(sortFunctions[sortBy]);
  }, [allGoals, searchQuery, statusFilter, timeframeFilter, sortBy]);

  const handleCreate = () => {
    setEditingGoal(null);
    setIsModalOpen(true);
  };

  const handleEdit = (goal: Goal) => {
    setEditingGoal(goal);
    setIsModalOpen(true);
  };

  const handleDelete = (id: number) => {
    if (confirm('Are you sure you want to delete this goal?')) {
      deleteGoal.mutate(id, {
        onSuccess: () => toast.success('Goal deleted'),
        onError: () => toast.error('Failed to delete goal'),
      });
    }
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
    setEditingGoal(null);
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
            <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">Goals</h1>
            <p className="text-gray-600 dark:text-gray-400 mt-1">1-3 year objectives and milestones</p>
          </div>
          <button onClick={handleCreate} className="btn btn-primary flex items-center gap-2">
            <Plus className="w-4 h-4" />
            New Goal
          </button>
        </div>
      </header>

      <div className="mb-6 space-y-4">
        <div className="flex items-center gap-4">
          <SearchInput
            value={searchQuery}
            onChange={setSearchQuery}
            placeholder="Search goals..."
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
          <div className="flex items-center gap-4 flex-wrap">
            <Filter className="w-5 h-5 text-gray-500 dark:text-gray-400" />
            <div className="flex gap-2 flex-wrap">
              <FilterButton value="all" label="All" current={statusFilter} onClick={setStatusFilter} />
              <FilterButton value="active" label="Active" current={statusFilter} onClick={setStatusFilter} />
              <FilterButton value="achieved" label="Achieved" current={statusFilter} onClick={setStatusFilter} />
              <FilterButton value="deferred" label="Deferred" current={statusFilter} onClick={setStatusFilter} />
              <FilterButton value="abandoned" label="Abandoned" current={statusFilter} onClick={setStatusFilter} />
            </div>
            <div className="w-px h-6 bg-gray-300 dark:bg-gray-600" />
            <div className="flex gap-2 flex-wrap">
              <FilterButton value="all" label="All Timeframes" current={timeframeFilter} onClick={setTimeframeFilter} />
              <FilterButton value="1_year" label="1 Year" current={timeframeFilter} onClick={setTimeframeFilter} />
              <FilterButton value="2_year" label="2 Year" current={timeframeFilter} onClick={setTimeframeFilter} />
              <FilterButton value="3_year" label="3 Year" current={timeframeFilter} onClick={setTimeframeFilter} />
            </div>
          </div>
        </div>

        {!isLoading && (
          <div className="text-sm text-gray-600 dark:text-gray-400">
            {filteredGoals.length} {filteredGoals.length === 1 ? 'goal' : 'goals'}
            {searchQuery || statusFilter !== 'all' || timeframeFilter !== 'all' ? ' (filtered)' : ''}
          </div>
        )}
      </div>

      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {Array.from({ length: 6 }).map((_, i) => (
            <AreaCardSkeleton key={i} />
          ))}
        </div>
      ) : filteredGoals.length > 0 ? (
        viewMode === 'grid' ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredGoals.map((goal) => (
              <div
                key={goal.id}
                className={`card hover:shadow-lg transition-all ${goal.status === 'abandoned' ? 'opacity-60' : ''}`}
              >
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center gap-2 min-w-0">
                    <Crosshair className="w-5 h-5 text-primary-600 dark:text-primary-400 flex-shrink-0" />
                    <h3 className="font-semibold text-gray-900 dark:text-gray-100 truncate">{goal.title}</h3>
                  </div>
                  <div className="flex items-center gap-1 flex-shrink-0 ml-2">
                    <button
                      onClick={() => handleEdit(goal)}
                      className="p-1.5 text-gray-400 hover:text-primary-600 dark:hover:text-primary-400 transition-colors"
                      title="Edit"
                    >
                      <Pencil className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => handleDelete(goal.id)}
                      className="p-1.5 text-gray-400 hover:text-red-600 dark:hover:text-red-400 transition-colors"
                      title="Delete"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>

                <div className="flex gap-2 mb-3 flex-wrap">
                  <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${statusConfig[goal.status].color}`}>
                    {statusConfig[goal.status].label}
                  </span>
                  {goal.timeframe && (
                    <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300">
                      {timeframeLabels[goal.timeframe]}
                    </span>
                  )}
                </div>

                {goal.description && (
                  <p className="text-sm text-gray-600 dark:text-gray-400 line-clamp-2 mb-3">
                    {goal.description}
                  </p>
                )}

                {goal.target_date && (
                  <div className="text-xs text-gray-500 dark:text-gray-400">
                    Target: {formatDate(goal.target_date)}
                  </div>
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
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Status</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Timeframe</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Target Date</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                {filteredGoals.map((goal) => (
                  <tr key={goal.id} className={`hover:bg-gray-50 dark:hover:bg-gray-800 ${goal.status === 'abandoned' ? 'opacity-60' : ''}`}>
                    <td className="px-4 py-3">
                      <div className="font-medium text-gray-900 dark:text-gray-100">{goal.title}</div>
                      {goal.description && (
                        <div className="text-sm text-gray-500 dark:text-gray-400 truncate max-w-md">{goal.description}</div>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${statusConfig[goal.status].color}`}>
                        {statusConfig[goal.status].label}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-400">
                      {goal.timeframe ? timeframeLabels[goal.timeframe] : '-'}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-400">
                      {goal.target_date ? formatDate(goal.target_date) : '-'}
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-1">
                        <button onClick={() => handleEdit(goal)} className="p-1.5 text-gray-400 hover:text-primary-600 transition-colors" title="Edit">
                          <Pencil className="w-4 h-4" />
                        </button>
                        <button onClick={() => handleDelete(goal.id)} className="p-1.5 text-gray-400 hover:text-red-600 transition-colors" title="Delete">
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
      ) : allGoals.length === 0 ? (
        <div className="card text-center py-12">
          <Crosshair className="w-12 h-12 text-gray-400 dark:text-gray-500 mx-auto mb-4" />
          <h3 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-2">No goals yet</h3>
          <p className="text-gray-600 dark:text-gray-400 mb-6">
            Define your 1-3 year objectives to guide your projects
          </p>
          <button onClick={handleCreate} className="btn btn-primary inline-flex items-center gap-2">
            <Plus className="w-4 h-4" />
            Create Your First Goal
          </button>
        </div>
      ) : (
        <div className="card text-center py-12">
          <h3 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-2">No goals match your filters</h3>
          <p className="text-gray-600 dark:text-gray-400 mb-6">Try adjusting your search or filter criteria</p>
          <button
            onClick={() => { setSearchQuery(''); setStatusFilter('all'); setTimeframeFilter('all'); }}
            className="btn btn-secondary"
          >
            Clear Filters
          </button>
        </div>
      )}

      <GoalModal isOpen={isModalOpen} onClose={handleCloseModal} goal={editingGoal} />
    </div>
  );
}
