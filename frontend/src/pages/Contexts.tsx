import { useState, useMemo, useEffect } from 'react';
import { Plus, Filter, ArrowUpDown, LayoutGrid, List, Pencil, Trash2, Tag } from 'lucide-react';
import toast from 'react-hot-toast';
import { useContexts, useDeleteContext } from '@/hooks/useContexts';
import { Error } from '@/components/common/Error';
import { ContextModal } from '@/components/contexts/ContextModal';
import { AreaCardSkeleton } from '@/components/common/Skeleton';
import { SearchInput } from '@/components/common/SearchInput';
import { Context, ContextType } from '@/types';

type ViewMode = 'grid' | 'list';

const VIEW_MODE_STORAGE_KEY = 'contextsViewMode';

type SortOption = 'name_asc' | 'name_desc' | 'type' | 'created_desc';

const sortOptions: { value: SortOption; label: string }[] = [
  { value: 'name_asc', label: 'Name (A-Z)' },
  { value: 'name_desc', label: 'Name (Z-A)' },
  { value: 'type', label: 'Type' },
  { value: 'created_desc', label: 'Created (Newest)' },
];

const typeConfig: Record<ContextType, { label: string; color: string }> = {
  location: { label: 'Location', color: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300' },
  energy: { label: 'Energy', color: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-300' },
  work_type: { label: 'Work Type', color: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300' },
  time: { label: 'Time', color: 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300' },
  tool: { label: 'Tool', color: 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-300' },
};

export function Contexts() {
  const [searchQuery, setSearchQuery] = useState('');
  const [typeFilter, setTypeFilter] = useState<string>('all');
  const [sortBy, setSortBy] = useState<SortOption>('name_asc');
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingContext, setEditingContext] = useState<Context | null>(null);
  const [viewMode, setViewMode] = useState<ViewMode>(() => {
    const saved = localStorage.getItem(VIEW_MODE_STORAGE_KEY);
    return (saved === 'list' || saved === 'grid') ? saved : 'grid';
  });

  const { data: contexts, isLoading, error } = useContexts();
  const deleteContext = useDeleteContext();

  useEffect(() => {
    localStorage.setItem(VIEW_MODE_STORAGE_KEY, viewMode);
  }, [viewMode]);

  if (error) return <Error message="Failed to load contexts" fullPage />;

  const allContexts = contexts || [];

  const filteredContexts = useMemo(() => {
    const filtered = allContexts.filter((ctx) => {
      if (searchQuery) {
        const query = searchQuery.toLowerCase();
        if (!ctx.name.toLowerCase().includes(query) &&
            !ctx.description?.toLowerCase().includes(query)) {
          return false;
        }
      }
      if (typeFilter !== 'all' && ctx.context_type !== typeFilter) return false;
      return true;
    });

    const sortFunctions: Record<SortOption, (a: Context, b: Context) => number> = {
      name_asc: (a, b) => a.name.localeCompare(b.name),
      name_desc: (a, b) => b.name.localeCompare(a.name),
      type: (a, b) => (a.context_type || '').localeCompare(b.context_type || ''),
      created_desc: (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime(),
    };

    return [...filtered].sort(sortFunctions[sortBy]);
  }, [allContexts, searchQuery, typeFilter, sortBy]);

  const handleCreate = () => {
    setEditingContext(null);
    setIsModalOpen(true);
  };

  const handleEdit = (ctx: Context) => {
    setEditingContext(ctx);
    setIsModalOpen(true);
  };

  const handleDelete = (id: number) => {
    if (confirm('Are you sure you want to delete this context?')) {
      deleteContext.mutate(id, {
        onSuccess: () => toast.success('Context deleted'),
        onError: () => toast.error('Failed to delete context'),
      });
    }
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
    setEditingContext(null);
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
            <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">Contexts</h1>
            <p className="text-gray-600 dark:text-gray-400 mt-1">Organize next actions by context</p>
          </div>
          <button onClick={handleCreate} className="btn btn-primary flex items-center gap-2">
            <Plus className="w-4 h-4" />
            New Context
          </button>
        </div>
      </header>

      <div className="mb-6 space-y-4">
        <div className="flex items-center gap-4">
          <SearchInput
            value={searchQuery}
            onChange={setSearchQuery}
            placeholder="Search contexts..."
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
              <FilterButton value="all" label="All Types" current={typeFilter} onClick={setTypeFilter} />
              <FilterButton value="location" label="Location" current={typeFilter} onClick={setTypeFilter} />
              <FilterButton value="energy" label="Energy" current={typeFilter} onClick={setTypeFilter} />
              <FilterButton value="work_type" label="Work Type" current={typeFilter} onClick={setTypeFilter} />
              <FilterButton value="time" label="Time" current={typeFilter} onClick={setTypeFilter} />
              <FilterButton value="tool" label="Tool" current={typeFilter} onClick={setTypeFilter} />
            </div>
          </div>
        </div>

        {!isLoading && (
          <div className="text-sm text-gray-600 dark:text-gray-400">
            {filteredContexts.length} {filteredContexts.length === 1 ? 'context' : 'contexts'}
            {searchQuery || typeFilter !== 'all' ? ' (filtered)' : ''}
          </div>
        )}
      </div>

      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {Array.from({ length: 6 }).map((_, i) => (
            <AreaCardSkeleton key={i} />
          ))}
        </div>
      ) : filteredContexts.length > 0 ? (
        viewMode === 'grid' ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredContexts.map((ctx) => (
              <div key={ctx.id} className="card hover:shadow-lg transition-all">
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center gap-2 min-w-0">
                    {ctx.icon ? (
                      <span className="text-lg flex-shrink-0">{ctx.icon}</span>
                    ) : (
                      <Tag className="w-5 h-5 text-gray-500 dark:text-gray-400 flex-shrink-0" />
                    )}
                    <h3 className="font-semibold text-gray-900 dark:text-gray-100 truncate">{ctx.name}</h3>
                  </div>
                  <div className="flex items-center gap-1 flex-shrink-0 ml-2">
                    <button
                      onClick={() => handleEdit(ctx)}
                      className="p-1.5 text-gray-400 hover:text-primary-600 dark:hover:text-primary-400 transition-colors"
                      title="Edit"
                    >
                      <Pencil className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => handleDelete(ctx.id)}
                      className="p-1.5 text-gray-400 hover:text-red-600 dark:hover:text-red-400 transition-colors"
                      title="Delete"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>

                {ctx.context_type && (
                  <div className="mb-3">
                    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${typeConfig[ctx.context_type].color}`}>
                      {typeConfig[ctx.context_type].label}
                    </span>
                  </div>
                )}

                {ctx.description && (
                  <p className="text-sm text-gray-600 dark:text-gray-400 line-clamp-2">
                    {ctx.description}
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
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Name</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Type</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Description</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                {filteredContexts.map((ctx) => (
                  <tr key={ctx.id} className="hover:bg-gray-50 dark:hover:bg-gray-800">
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        {ctx.icon && <span>{ctx.icon}</span>}
                        <span className="font-medium text-gray-900 dark:text-gray-100">{ctx.name}</span>
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      {ctx.context_type ? (
                        <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${typeConfig[ctx.context_type].color}`}>
                          {typeConfig[ctx.context_type].label}
                        </span>
                      ) : '-'}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-400 truncate max-w-md">
                      {ctx.description || '-'}
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-1">
                        <button onClick={() => handleEdit(ctx)} className="p-1.5 text-gray-400 hover:text-primary-600 transition-colors" title="Edit">
                          <Pencil className="w-4 h-4" />
                        </button>
                        <button onClick={() => handleDelete(ctx.id)} className="p-1.5 text-gray-400 hover:text-red-600 transition-colors" title="Delete">
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
      ) : allContexts.length === 0 ? (
        <div className="card text-center py-12">
          <Tag className="w-12 h-12 text-gray-400 dark:text-gray-500 mx-auto mb-4" />
          <h3 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-2">No contexts yet</h3>
          <p className="text-gray-600 dark:text-gray-400 mb-6">
            Create contexts like @home, @computer, @errands to organize your next actions
          </p>
          <button onClick={handleCreate} className="btn btn-primary inline-flex items-center gap-2">
            <Plus className="w-4 h-4" />
            Create Your First Context
          </button>
        </div>
      ) : (
        <div className="card text-center py-12">
          <h3 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-2">No contexts match your filters</h3>
          <p className="text-gray-600 dark:text-gray-400 mb-6">Try adjusting your search or filter criteria</p>
          <button
            onClick={() => { setSearchQuery(''); setTypeFilter('all'); }}
            className="btn btn-secondary"
          >
            Clear Filters
          </button>
        </div>
      )}

      <ContextModal isOpen={isModalOpen} onClose={handleCloseModal} context={editingContext} />
    </div>
  );
}
