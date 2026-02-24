import { useState, useMemo, useEffect } from 'react';
import toast from 'react-hot-toast';
import {
  Brain,
  Plus,
  Trash2,
  Edit2,
  Eye,
  ChevronDown,
  ChevronRight,
  Tag,
  Layers,
  MoreVertical,
  AlertTriangle,
  Zap,
  ToggleLeft,
  ToggleRight,
  BarChart2,
  Clock,
  ClipboardList,
  CheckCircle2,
} from 'lucide-react';
import { SearchInput } from '@/components/common/SearchInput';
import { Modal } from '@/components/common/Modal';
import {
  useMemoryObjects,
  useMemoryObject,
  useMemoryNamespaces,
  useSearchMemoryObjects,
  useCreateMemoryObject,
  useUpdateMemoryObject,
  useDeleteMemoryObject,
  useCreateNamespace,
  useUpdateNamespace,
  useDeleteNamespace,
  usePrefetchRules,
  useCreatePrefetchRule,
  useUpdatePrefetchRule,
  useDeletePrefetchRule,
  useMemoryStats,
  useSessionSummaries,
  useCaptureSession,
  type MemoryObjectBrief,
  type MemoryObjectCreate,
  type MemoryObjectUpdate,
  type MemoryNamespace,
  type PrefetchRule,
  type PrefetchRuleCreate,
  type PrefetchRuleUpdate,
  type SessionCapture,
} from '@/hooks/useMemory';

function getPriorityColor(priority: number): string {
  if (priority >= 80) return 'text-red-600 dark:text-red-400';
  if (priority >= 60) return 'text-orange-600 dark:text-orange-400';
  if (priority >= 40) return 'text-blue-600 dark:text-blue-400';
  return 'text-gray-500 dark:text-gray-400';
}

function getPriorityBg(priority: number): string {
  if (priority >= 80) return 'bg-red-100 dark:bg-red-900/30';
  if (priority >= 60) return 'bg-orange-100 dark:bg-orange-900/30';
  if (priority >= 40) return 'bg-blue-100 dark:bg-blue-900/30';
  return 'bg-gray-100 dark:bg-gray-800';
}

/** Parse dot notation to determine indent depth (e.g. core.identity → depth 1) */
function getNamespaceDepth(name: string): number {
  return name.split('.').length - 1;
}

/** Build a sorted tree for display: parents before children, alphabetically */
function buildNamespaceTree(namespaces: MemoryNamespace[]): MemoryNamespace[] {
  return [...namespaces].sort((a, b) => a.name.localeCompare(b.name));
}

type MemoryTab = 'objects' | 'prefetch' | 'health' | 'sessions';

export function MemoryPage() {
  const [activeTab, setActiveTab] = useState<MemoryTab>('objects');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedNamespace, setSelectedNamespace] = useState<string | undefined>();
  const [viewingObjectId, setViewingObjectId] = useState<string | null>(null);
  const [editingObjectId, setEditingObjectId] = useState<string | null>(null);
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [isCreateNsOpen, setIsCreateNsOpen] = useState(false);
  const [editingNamespace, setEditingNamespace] = useState<MemoryNamespace | null>(null);
  const [deletingNamespace, setDeletingNamespace] = useState<MemoryNamespace | null>(null);
  const [namespaceSidebarExpanded, setNamespaceSidebarExpanded] = useState(true);
  const [nsMenuOpen, setNsMenuOpen] = useState<string | null>(null);

  const { data: objects, isLoading, isError: isObjectsError } = useMemoryObjects(selectedNamespace);
  const { data: namespaces, isError: isNamespacesError } = useMemoryNamespaces();
  const { data: searchResults, isFetching: isSearching } = useSearchMemoryObjects(
    searchQuery,
    selectedNamespace
  );
  const deleteObject = useDeleteMemoryObject();

  // Close namespace menu on outside click
  useEffect(() => {
    if (!nsMenuOpen) return;
    const handler = () => setNsMenuOpen(null);
    document.addEventListener('click', handler);
    return () => document.removeEventListener('click', handler);
  }, [nsMenuOpen]);

  const filteredObjects = useMemo(() => {
    if (searchQuery.length >= 2 && searchResults) return searchResults;
    if (!objects) return [];
    if (!searchQuery) return objects;
    const q = searchQuery.toLowerCase();
    return objects.filter(
      (obj) =>
        obj.object_id.toLowerCase().includes(q) ||
        obj.namespace.toLowerCase().includes(q)
    );
  }, [objects, searchQuery, searchResults]);

  const grouped = useMemo(() => {
    const map: Record<string, MemoryObjectBrief[]> = {};
    for (const obj of filteredObjects) {
      if (!map[obj.namespace]) map[obj.namespace] = [];
      map[obj.namespace].push(obj);
    }
    return Object.entries(map).sort(([a], [b]) => a.localeCompare(b));
  }, [filteredObjects]);

  const orderedNamespaces = useMemo(
    () => buildNamespaceTree(namespaces || []),
    [namespaces]
  );

  const handleDelete = (objectId: string) => {
    if (!confirm(`Delete memory object "${objectId}"? This cannot be undone.`)) return;
    deleteObject.mutate(objectId, {
      onSuccess: () => toast.success('Memory object deleted'),
      onError: () => toast.error('Failed to delete'),
    });
  };

  return (
    <div className="p-8">
      {/* Header */}
      <header className="mb-8">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Brain className="w-8 h-8 text-primary-600" />
            <div>
              <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">Memory</h1>
              <p className="text-gray-600 dark:text-gray-400 mt-1">
                Persistent context for AI assistants
              </p>
            </div>
          </div>
          {activeTab === 'objects' ? (
            <div className="flex gap-2">
              <button
                onClick={() => setIsCreateNsOpen(true)}
                className="btn btn-secondary flex items-center gap-2"
              >
                <Layers className="w-4 h-4" />
                New Namespace
              </button>
              <button
                onClick={() => setIsCreateModalOpen(true)}
                className="btn btn-primary flex items-center gap-2"
              >
                <Plus className="w-4 h-4" />
                New Object
              </button>
            </div>
          ) : activeTab === 'prefetch' ? (
            <PrefetchRuleCreateButton />
          ) : activeTab === 'sessions' ? (
            <SessionCaptureButton />
          ) : null}
        </div>

        {/* Tab switcher */}
        <div className="flex gap-1 mt-6 border-b border-gray-200 dark:border-gray-700">
          <button
            onClick={() => setActiveTab('objects')}
            className={`flex items-center gap-2 px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
              activeTab === 'objects'
                ? 'border-primary-600 text-primary-600 dark:border-primary-400 dark:text-primary-400'
                : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
            }`}
          >
            <Brain className="w-4 h-4" />
            Objects
          </button>
          <button
            onClick={() => setActiveTab('prefetch')}
            className={`flex items-center gap-2 px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
              activeTab === 'prefetch'
                ? 'border-primary-600 text-primary-600 dark:border-primary-400 dark:text-primary-400'
                : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
            }`}
          >
            <Zap className="w-4 h-4" />
            Prefetch Rules
          </button>
          <button
            onClick={() => setActiveTab('health')}
            className={`flex items-center gap-2 px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
              activeTab === 'health'
                ? 'border-primary-600 text-primary-600 dark:border-primary-400 dark:text-primary-400'
                : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
            }`}
          >
            <BarChart2 className="w-4 h-4" />
            Health
          </button>
          <button
            onClick={() => setActiveTab('sessions')}
            className={`flex items-center gap-2 px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
              activeTab === 'sessions'
                ? 'border-primary-600 text-primary-600 dark:border-primary-400 dark:text-primary-400'
                : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
            }`}
          >
            <ClipboardList className="w-4 h-4" />
            Sessions
          </button>
        </div>
      </header>

      {activeTab === 'prefetch' && <PrefetchRulesView />}

      {activeTab === 'health' && <HealthView />}

      {activeTab === 'sessions' && <SessionsView />}

      {activeTab === 'objects' && <div className="flex gap-6">
        {/* Namespace Sidebar */}
        <div className="w-64 flex-shrink-0">
          <div className="card sticky top-4">
            <button
              onClick={() => setNamespaceSidebarExpanded(!namespaceSidebarExpanded)}
              className="flex items-center gap-2 w-full text-left font-semibold text-gray-900 dark:text-gray-100 mb-3"
            >
              {namespaceSidebarExpanded ? (
                <ChevronDown className="w-4 h-4" />
              ) : (
                <ChevronRight className="w-4 h-4" />
              )}
              Namespaces
            </button>
            {namespaceSidebarExpanded && (
              <div className="space-y-0.5">
                {/* All */}
                <button
                  onClick={() => setSelectedNamespace(undefined)}
                  className={`w-full text-left px-3 py-2 rounded text-sm transition-colors flex items-center justify-between group ${
                    !selectedNamespace
                      ? 'bg-primary-100 text-primary-700 dark:bg-primary-900/30 dark:text-primary-400'
                      : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700'
                  }`}
                >
                  <span>All</span>
                  <span className="text-xs tabular-nums opacity-60">{objects?.length ?? 0}</span>
                </button>

                {/* Namespace tree */}
                {orderedNamespaces.map((ns) => {
                  const depth = getNamespaceDepth(ns.name);
                  const isSelected = selectedNamespace === ns.name;
                  const isMenuOpen = nsMenuOpen === ns.name;

                  return (
                    <div
                      key={ns.name}
                      className="relative group"
                      style={{ paddingLeft: `${depth * 12}px` }}
                    >
                      <div
                        className={`flex items-center rounded transition-colors ${
                          isSelected
                            ? 'bg-primary-100 text-primary-700 dark:bg-primary-900/30 dark:text-primary-400'
                            : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700'
                        }`}
                      >
                        <button
                          onClick={() => setSelectedNamespace(ns.name)}
                          className="flex-1 text-left px-3 py-2 text-sm min-w-0"
                          title={ns.description || ns.name}
                        >
                          <div className="flex items-center justify-between gap-1">
                            <span className="font-mono text-xs truncate">
                              {depth > 0 ? ns.name.split('.').pop() : ns.name}
                            </span>
                            <span className={`text-xs tabular-nums flex-shrink-0 ${
                              ns.object_count > 0
                                ? 'opacity-60'
                                : 'opacity-30'
                            }`}>
                              {ns.object_count}
                            </span>
                          </div>
                          {ns.description && (
                            <p className="text-xs opacity-50 truncate mt-0.5">{ns.description}</p>
                          )}
                        </button>

                        {/* Namespace action menu */}
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            setNsMenuOpen(isMenuOpen ? null : ns.name);
                          }}
                          className="p-1.5 opacity-0 group-hover:opacity-100 transition-opacity rounded hover:bg-gray-200 dark:hover:bg-gray-600 mr-1 flex-shrink-0"
                          title="Namespace options"
                        >
                          <MoreVertical className="w-3 h-3" />
                        </button>
                      </div>

                      {/* Dropdown menu */}
                      {isMenuOpen && (
                        <div
                          className="absolute right-0 top-full z-20 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg py-1 min-w-[140px]"
                          onClick={(e) => e.stopPropagation()}
                        >
                          <button
                            onClick={() => {
                              setEditingNamespace(ns);
                              setNsMenuOpen(null);
                            }}
                            className="w-full text-left px-3 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 flex items-center gap-2"
                          >
                            <Edit2 className="w-3.5 h-3.5" />
                            Edit
                          </button>
                          <button
                            onClick={() => {
                              setDeletingNamespace(ns);
                              setNsMenuOpen(null);
                            }}
                            className="w-full text-left px-3 py-2 text-sm text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 flex items-center gap-2"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                            Delete
                          </button>
                        </div>
                      )}
                    </div>
                  );
                })}

                {(!namespaces || namespaces.length === 0) && (
                  <p className="text-xs text-gray-400 dark:text-gray-500 px-3 py-2 italic">
                    No namespaces yet
                  </p>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Main Content */}
        <div className="flex-1">
          <div className="mb-4">
            <SearchInput
              value={searchQuery}
              onChange={setSearchQuery}
              placeholder="Search across IDs, namespaces, tags, and content..."
            />
          </div>


          {!isLoading && (
            <div className="text-sm text-gray-600 dark:text-gray-400 mb-4">
              {filteredObjects.length} object{filteredObjects.length !== 1 ? 's' : ''}
              {selectedNamespace && ` in ${selectedNamespace}`}
              {searchQuery && (isSearching ? ' (searching...)' : ' (filtered)')}
            </div>
          )}

          {(isObjectsError || isNamespacesError) && (
            <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 mb-4">
              <p className="text-red-800 dark:text-red-300 text-sm">
                Failed to load memory data. The memory layer module may not be enabled or the server may be unavailable.
              </p>
            </div>
          )}

          {isLoading ? (
            <div className="text-center py-12 text-gray-500 dark:text-gray-400">
              Loading memory objects...
            </div>
          ) : filteredObjects.length === 0 ? (
            <div className="card text-center py-12">
              <Brain className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-2">
                {searchQuery ? 'No matching objects' : 'No memory objects'}
              </h3>
              <p className="text-gray-600 dark:text-gray-400 mb-6">
                {searchQuery
                  ? 'Try a different search term'
                  : 'Create your first memory object to provide AI context'}
              </p>
              {!searchQuery && (
                <button
                  onClick={() => setIsCreateModalOpen(true)}
                  className="btn btn-primary inline-flex items-center gap-2"
                >
                  <Plus className="w-4 h-4" />
                  Create Memory Object
                </button>
              )}
            </div>
          ) : (
            <div className="space-y-6">
              {grouped.map(([ns, objs]) => (
                <div key={ns}>
                  <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-2 font-mono flex items-center gap-2">
                    <Layers className="w-4 h-4" />
                    {ns}
                    <span className="text-xs">({objs.length})</span>
                  </h3>
                  <div className="space-y-2">
                    {objs.map((obj) => (
                      <div
                        key={obj.id}
                        className="card flex items-center gap-4 py-3 hover:shadow-md transition-shadow"
                      >
                        <span
                          className={`text-sm font-bold w-10 text-center py-1 rounded ${getPriorityBg(obj.priority)} ${getPriorityColor(obj.priority)}`}
                        >
                          {obj.priority}
                        </span>

                        <div className="flex-1 min-w-0">
                          <p className="font-medium text-gray-900 dark:text-gray-100 truncate font-mono text-sm">
                            {obj.object_id}
                          </p>
                          <div className="flex items-center gap-2 mt-1">
                            <span className="text-xs text-gray-500 dark:text-gray-400">
                              v{obj.version}
                            </span>
                            {!obj.is_active && (
                              <span className="text-xs text-red-500">Inactive</span>
                            )}
                          </div>
                        </div>

                        <div className="flex items-center gap-1">
                          <button
                            onClick={() => setViewingObjectId(obj.object_id)}
                            className="p-1.5 text-gray-400 hover:text-primary-600 rounded transition-colors"
                            title="View"
                          >
                            <Eye className="w-4 h-4" />
                          </button>
                          <button
                            onClick={() => setEditingObjectId(obj.object_id)}
                            className="p-1.5 text-gray-400 hover:text-primary-600 rounded transition-colors"
                            title="Edit"
                          >
                            <Edit2 className="w-4 h-4" />
                          </button>
                          <button
                            onClick={() => handleDelete(obj.object_id)}
                            className="p-1.5 text-gray-400 hover:text-red-600 rounded transition-colors"
                            title="Delete"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>}

      {/* View Modal */}
      {viewingObjectId && (
        <ViewObjectModal
          objectId={viewingObjectId}
          onClose={() => setViewingObjectId(null)}
        />
      )}

      {/* Edit Object Modal */}
      {editingObjectId && (
        <EditObjectModal
          objectId={editingObjectId}
          onClose={() => setEditingObjectId(null)}
        />
      )}

      {/* Create Object Modal */}
      {isCreateModalOpen && (
        <CreateObjectModal
          namespaces={namespaces || []}
          onClose={() => setIsCreateModalOpen(false)}
        />
      )}

      {/* Create Namespace Modal */}
      {isCreateNsOpen && (
        <CreateNamespaceModal onClose={() => setIsCreateNsOpen(false)} />
      )}

      {/* Edit Namespace Modal */}
      {editingNamespace && (
        <EditNamespaceModal
          namespace={editingNamespace}
          onClose={() => setEditingNamespace(null)}
        />
      )}

      {/* Delete Namespace Modal */}
      {deletingNamespace && (
        <DeleteNamespaceModal
          namespace={deletingNamespace}
          onClose={() => {
            setDeletingNamespace(null);
            // Deselect if we just deleted the selected namespace
            if (selectedNamespace === deletingNamespace.name) {
              setSelectedNamespace(undefined);
            }
          }}
        />
      )}
    </div>
  );
}

// ========== Health View ==========

function StatCard({
  label,
  value,
  sub,
}: {
  label: string;
  value: number | string;
  sub?: string;
}) {
  return (
    <div className="card text-center py-4">
      <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">{value}</p>
      <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">{label}</p>
      {sub && <p className="text-xs text-gray-400 dark:text-gray-500 mt-0.5">{sub}</p>}
    </div>
  );
}

function MiniBar({
  label,
  count,
  total,
  colorClass,
}: {
  label: string;
  count: number;
  total: number;
  colorClass: string;
}) {
  const pct = total > 0 ? Math.round((count / total) * 100) : 0;
  return (
    <div className="flex items-center gap-3 text-sm">
      <span className="w-32 text-gray-600 dark:text-gray-400 truncate flex-shrink-0">{label}</span>
      <div className="flex-1 bg-gray-100 dark:bg-gray-700 rounded-full h-2">
        <div
          className={`h-2 rounded-full ${colorClass} transition-all`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="w-8 text-right text-gray-900 dark:text-gray-100 font-medium tabular-nums flex-shrink-0">
        {count}
      </span>
      <span className="w-8 text-right text-gray-400 dark:text-gray-500 text-xs tabular-nums flex-shrink-0">
        {pct}%
      </span>
    </div>
  );
}

function HealthView() {
  const { data: stats, isLoading, isError } = useMemoryStats();

  if (isLoading) {
    return <div className="text-center py-12 text-gray-500 dark:text-gray-400">Loading health data...</div>;
  }

  if (isError || !stats) {
    return (
      <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
        <p className="text-red-800 dark:text-red-300 text-sm">
          Failed to load memory health stats. The memory layer module may not be enabled.
        </p>
      </div>
    );
  }

  const { totals, objects, namespaces_by_count, recent_activity } = stats;
  const maxNsCount = namespaces_by_count[0]?.count || 1;

  return (
    <div className="space-y-6">
      {/* System Overview */}
      <section>
        <h2 className="text-sm font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-3 flex items-center gap-2">
          <BarChart2 className="w-4 h-4" />
          System Overview
        </h2>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <StatCard label="Memory Objects" value={totals.objects} />
          <StatCard label="Namespaces" value={totals.namespaces} />
          <StatCard
            label="Quick Keys"
            value={totals.quick_keys}
            sub={totals.quick_keys === 0 ? 'none configured' : undefined}
          />
          <StatCard
            label="Prefetch Rules"
            value={totals.prefetch_rules}
            sub={`${totals.active_prefetch_rules} active`}
          />
        </div>
      </section>

      {/* Object Health + Priority Distribution */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Object Health */}
        <section className="card">
          <h2 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-4 flex items-center gap-2">
            <Brain className="w-4 h-4" />
            Object Health
          </h2>
          <div className="space-y-3">
            <MiniBar
              label="Active"
              count={objects.active}
              total={totals.objects}
              colorClass="bg-green-500"
            />
            <MiniBar
              label="Inactive"
              count={objects.inactive}
              total={totals.objects}
              colorClass="bg-gray-400"
            />
            <div className="border-t border-gray-100 dark:border-gray-700 pt-3 mt-1" />
            <MiniBar
              label="DB storage"
              count={objects.db_storage}
              total={totals.objects}
              colorClass="bg-blue-500"
            />
            <MiniBar
              label="File storage"
              count={objects.file_storage}
              total={totals.objects}
              colorClass="bg-purple-500"
            />
          </div>
          {totals.objects > 0 && (
            <p className="text-xs text-gray-400 dark:text-gray-500 mt-4">
              Avg priority: <span className="font-medium text-gray-700 dark:text-gray-300">{objects.avg_priority}</span>
            </p>
          )}
        </section>

        {/* Priority Distribution */}
        <section className="card">
          <h2 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-4 flex items-center gap-2">
            <Zap className="w-4 h-4" />
            Priority Distribution
          </h2>
          {totals.objects === 0 ? (
            <p className="text-sm text-gray-400 dark:text-gray-500 italic">No objects yet</p>
          ) : (
            <div className="space-y-3">
              <MiniBar
                label="High (≥ 80)"
                count={objects.high_priority}
                total={totals.objects}
                colorClass="bg-red-500"
              />
              <MiniBar
                label="Medium (40–79)"
                count={objects.medium_priority}
                total={totals.objects}
                colorClass="bg-orange-400"
              />
              <MiniBar
                label="Low (< 40)"
                count={objects.low_priority}
                total={totals.objects}
                colorClass="bg-blue-400"
              />
            </div>
          )}
        </section>
      </div>

      {/* Top Namespaces */}
      {namespaces_by_count.length > 0 && (
        <section className="card">
          <h2 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-4 flex items-center gap-2">
            <Layers className="w-4 h-4" />
            Top Namespaces by Object Count
          </h2>
          <div className="space-y-2.5">
            {namespaces_by_count.map(({ name, count }) => (
              <div key={name} className="flex items-center gap-3 text-sm">
                <span className="w-48 font-mono text-xs text-gray-700 dark:text-gray-300 truncate flex-shrink-0">
                  {name}
                </span>
                <div className="flex-1 bg-gray-100 dark:bg-gray-700 rounded-full h-2">
                  <div
                    className="h-2 rounded-full bg-primary-500 transition-all"
                    style={{ width: `${Math.round((count / maxNsCount) * 100)}%` }}
                  />
                </div>
                <span className="w-6 text-right text-gray-900 dark:text-gray-100 font-medium tabular-nums flex-shrink-0">
                  {count}
                </span>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Recent Activity */}
      <section className="card">
        <h2 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-4 flex items-center gap-2">
          <Clock className="w-4 h-4" />
          Recent Activity
        </h2>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-center">
          <div>
            <p className="text-xl font-bold text-gray-900 dark:text-gray-100">
              {recent_activity.created_last_7d}
            </p>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">Created (7d)</p>
          </div>
          <div>
            <p className="text-xl font-bold text-gray-900 dark:text-gray-100">
              {recent_activity.updated_last_7d}
            </p>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">Updated (7d)</p>
          </div>
          <div>
            <p className="text-xl font-bold text-gray-900 dark:text-gray-100">
              {recent_activity.created_last_30d}
            </p>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">Created (30d)</p>
          </div>
          <div>
            <p className="text-xl font-bold text-gray-900 dark:text-gray-100">
              {recent_activity.updated_last_30d}
            </p>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">Updated (30d)</p>
          </div>
        </div>
      </section>
    </div>
  );
}


// ========== View Modal ==========

function ViewObjectModal({ objectId, onClose }: { objectId: string; onClose: () => void }) {
  const { data: obj, isLoading } = useMemoryObject(objectId);

  return (
    <Modal isOpen onClose={onClose} title={`Memory: ${objectId}`}>
      {isLoading ? (
        <div className="py-8 text-center text-gray-500">Loading...</div>
      ) : obj ? (
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-gray-500 dark:text-gray-400">Namespace:</span>
              <p className="font-mono">{obj.namespace}</p>
            </div>
            <div>
              <span className="text-gray-500 dark:text-gray-400">Priority:</span>
              <p className={`font-bold ${getPriorityColor(obj.priority)}`}>{obj.priority}</p>
            </div>
            <div>
              <span className="text-gray-500 dark:text-gray-400">Version:</span>
              <p>{obj.version}</p>
            </div>
            <div>
              <span className="text-gray-500 dark:text-gray-400">Storage:</span>
              <p>{obj.storage_type}</p>
            </div>
            <div>
              <span className="text-gray-500 dark:text-gray-400">Effective From:</span>
              <p>{obj.effective_from}</p>
            </div>
            <div>
              <span className="text-gray-500 dark:text-gray-400">Effective To:</span>
              <p>{obj.effective_to || 'Current'}</p>
            </div>
          </div>
          {obj.tags && obj.tags.length > 0 && (
            <div>
              <span className="text-sm text-gray-500 dark:text-gray-400">Tags:</span>
              <div className="flex flex-wrap gap-1 mt-1">
                {obj.tags.map((tag) => (
                  <span key={tag} className="badge badge-blue text-xs flex items-center gap-1">
                    <Tag className="w-3 h-3" />
                    {tag}
                  </span>
                ))}
              </div>
            </div>
          )}
          <div>
            <span className="text-sm text-gray-500 dark:text-gray-400">Content:</span>
            <pre className="mt-1 p-3 bg-gray-50 dark:bg-gray-800 rounded-lg text-sm overflow-auto max-h-96 font-mono">
              {JSON.stringify(obj.content, null, 2)}
            </pre>
          </div>
        </div>
      ) : (
        <div className="py-8 text-center text-red-500">Object not found</div>
      )}
    </Modal>
  );
}

// ========== Edit Object Modal ==========

function EditObjectModal({ objectId, onClose }: { objectId: string; onClose: () => void }) {
  const { data: obj, isLoading } = useMemoryObject(objectId);
  const updateObject = useUpdateMemoryObject();
  const [priority, setPriority] = useState<number | null>(null);
  const [version, setVersion] = useState('');
  const [tags, setTags] = useState('');
  const [contentStr, setContentStr] = useState('');

  useEffect(() => {
    if (obj) {
      setPriority(obj.priority);
      setVersion(obj.version);
      setTags(obj.tags?.join(', ') || '');
      setContentStr(JSON.stringify(obj.content, null, 2));
    }
  }, [obj]);

  const handleSave = () => {
    let parsedContent: Record<string, unknown> | undefined;
    try {
      if (contentStr.trim()) {
        parsedContent = JSON.parse(contentStr);
      }
    } catch {
      toast.error('Invalid JSON content');
      return;
    }

    const data: MemoryObjectUpdate = {};
    if (priority !== null && priority !== obj?.priority) data.priority = priority;
    if (version && version !== obj?.version) data.version = version;
    if (tags !== (obj?.tags?.join(', ') || '')) {
      data.tags = tags
        .split(',')
        .map((t) => t.trim())
        .filter(Boolean);
    }
    if (parsedContent) data.content = parsedContent;

    updateObject.mutate(
      { objectId, data },
      {
        onSuccess: () => {
          toast.success('Memory object updated');
          onClose();
        },
        onError: () => toast.error('Failed to update'),
      }
    );
  };

  return (
    <Modal isOpen onClose={onClose} title={`Edit: ${objectId}`}>
      {isLoading ? (
        <div className="py-8 text-center text-gray-500">Loading...</div>
      ) : (
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label">Priority (0-100)</label>
              <input
                type="number"
                className="input"
                min={0}
                max={100}
                value={priority ?? 50}
                onChange={(e) => setPriority(Math.min(100, Math.max(0, Number(e.target.value) || 0)))}
              />
            </div>
            <div>
              <label className="label">Version</label>
              <input
                type="text"
                className="input"
                value={version}
                onChange={(e) => setVersion(e.target.value)}
              />
            </div>
          </div>
          <div>
            <label className="label">Tags (comma-separated)</label>
            <input
              type="text"
              className="input"
              value={tags}
              onChange={(e) => setTags(e.target.value)}
              placeholder="tag1, tag2, tag3"
            />
          </div>
          <div>
            <label className="label">Content (JSON)</label>
            <textarea
              className="input font-mono text-sm"
              rows={10}
              value={contentStr}
              onChange={(e) => setContentStr(e.target.value)}
            />
          </div>
          <div className="flex justify-end gap-2">
            <button onClick={onClose} className="btn btn-secondary">
              Cancel
            </button>
            <button
              onClick={handleSave}
              disabled={updateObject.isPending}
              className="btn btn-primary"
            >
              {updateObject.isPending ? 'Saving...' : 'Save Changes'}
            </button>
          </div>
        </div>
      )}
    </Modal>
  );
}

// ========== Create Object Modal ==========

function CreateObjectModal({
  namespaces,
  onClose,
}: {
  namespaces: Array<{ name: string }>;
  onClose: () => void;
}) {
  const createObject = useCreateMemoryObject();
  const [objectId, setObjectId] = useState('');
  const [namespace, setNamespace] = useState(namespaces[0]?.name || '');
  const [priority, setPriority] = useState(50);
  const [tags, setTags] = useState('');
  const [contentStr, setContentStr] = useState('{\n  \n}');

  const handleCreate = () => {
    if (!objectId.trim()) {
      toast.error('Object ID is required');
      return;
    }
    if (!namespace.trim()) {
      toast.error('Namespace is required');
      return;
    }

    let content: Record<string, unknown>;
    try {
      content = JSON.parse(contentStr);
    } catch {
      toast.error('Invalid JSON content');
      return;
    }

    const data: MemoryObjectCreate = {
      object_id: objectId.trim(),
      namespace: namespace.trim(),
      priority,
      effective_from: new Date().toISOString().split('T')[0],
      content,
      tags: tags
        ? tags
            .split(',')
            .map((t) => t.trim())
            .filter(Boolean)
        : undefined,
    };

    createObject.mutate(data, {
      onSuccess: () => {
        toast.success('Memory object created');
        onClose();
      },
      onError: (err: any) => {
        const msg = err?.response?.data?.detail || 'Failed to create';
        toast.error(msg);
      },
    });
  };

  return (
    <Modal isOpen onClose={onClose} title="Create Memory Object">
      <div className="space-y-4">
        <div>
          <label className="label">Object ID</label>
          <input
            type="text"
            className="input font-mono"
            value={objectId}
            onChange={(e) => setObjectId(e.target.value)}
            placeholder="e.g., user-preferences-001"
          />
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="label">Namespace</label>
            {namespaces.length > 0 ? (
              <select
                className="input"
                value={namespace}
                onChange={(e) => setNamespace(e.target.value)}
              >
                {namespaces.map((ns) => (
                  <option key={ns.name} value={ns.name}>
                    {ns.name}
                  </option>
                ))}
              </select>
            ) : (
              <input
                type="text"
                className="input font-mono"
                value={namespace}
                onChange={(e) => setNamespace(e.target.value)}
                placeholder="e.g., core.identity"
              />
            )}
          </div>
          <div>
            <label className="label">Priority (0-100)</label>
            <input
              type="number"
              className="input"
              min={0}
              max={100}
              value={priority}
              onChange={(e) => setPriority(Math.min(100, Math.max(0, Number(e.target.value) || 0)))}
            />
          </div>
        </div>
        <div>
          <label className="label">Tags (comma-separated)</label>
          <input
            type="text"
            className="input"
            value={tags}
            onChange={(e) => setTags(e.target.value)}
            placeholder="identity, preferences"
          />
        </div>
        <div>
          <label className="label">Content (JSON)</label>
          <textarea
            className="input font-mono text-sm"
            rows={8}
            value={contentStr}
            onChange={(e) => setContentStr(e.target.value)}
          />
        </div>
        <div className="flex justify-end gap-2">
          <button onClick={onClose} className="btn btn-secondary">
            Cancel
          </button>
          <button
            onClick={handleCreate}
            disabled={createObject.isPending}
            className="btn btn-primary"
          >
            {createObject.isPending ? 'Creating...' : 'Create Object'}
          </button>
        </div>
      </div>
    </Modal>
  );
}

// ========== Create Namespace Modal ==========

function CreateNamespaceModal({ onClose }: { onClose: () => void }) {
  const createNamespace = useCreateNamespace();
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [defaultPriority, setDefaultPriority] = useState(50);

  const handleCreate = () => {
    if (!name.trim()) {
      toast.error('Namespace name is required');
      return;
    }

    createNamespace.mutate(
      {
        name: name.trim(),
        description: description.trim() || undefined,
        default_priority: defaultPriority,
      },
      {
        onSuccess: () => {
          toast.success('Namespace created');
          onClose();
        },
        onError: (err: any) => {
          const msg = err?.response?.data?.detail || 'Failed to create namespace';
          toast.error(msg);
        },
      }
    );
  };

  return (
    <Modal isOpen onClose={onClose} title="Create Namespace">
      <div className="space-y-4">
        <div>
          <label className="label">Name</label>
          <input
            type="text"
            className="input font-mono"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="e.g., core.identity"
          />
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
            Use dot notation for hierarchy (e.g., core.identity, projects.active)
          </p>
        </div>
        <div>
          <label className="label">Description</label>
          <input
            type="text"
            className="input"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="What this namespace contains"
          />
        </div>
        <div>
          <label className="label">Default Priority (0-100)</label>
          <input
            type="number"
            className="input"
            min={0}
            max={100}
            value={defaultPriority}
            onChange={(e) => setDefaultPriority(Math.min(100, Math.max(0, Number(e.target.value) || 0)))}
          />
        </div>
        <div className="flex justify-end gap-2">
          <button onClick={onClose} className="btn btn-secondary">
            Cancel
          </button>
          <button
            onClick={handleCreate}
            disabled={createNamespace.isPending}
            className="btn btn-primary"
          >
            {createNamespace.isPending ? 'Creating...' : 'Create Namespace'}
          </button>
        </div>
      </div>
    </Modal>
  );
}

// ========== Edit Namespace Modal ==========

function EditNamespaceModal({
  namespace,
  onClose,
}: {
  namespace: MemoryNamespace;
  onClose: () => void;
}) {
  const updateNamespace = useUpdateNamespace();
  const [description, setDescription] = useState(namespace.description || '');
  const [defaultPriority, setDefaultPriority] = useState(namespace.default_priority);

  const handleSave = () => {
    const hasChanges =
      description !== (namespace.description || '') ||
      defaultPriority !== namespace.default_priority;

    if (!hasChanges) {
      onClose();
      return;
    }

    updateNamespace.mutate(
      {
        name: namespace.name,
        data: {
          description: description.trim() || undefined,
          default_priority: defaultPriority,
        },
      },
      {
        onSuccess: () => {
          toast.success('Namespace updated');
          onClose();
        },
        onError: (err: any) => {
          const msg = err?.response?.data?.detail || 'Failed to update namespace';
          toast.error(msg);
        },
      }
    );
  };

  return (
    <Modal isOpen onClose={onClose} title={`Edit Namespace: ${namespace.name}`}>
      <div className="space-y-4">
        <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-3 text-sm">
          <p className="text-gray-500 dark:text-gray-400 text-xs mb-1">Namespace name (immutable)</p>
          <p className="font-mono text-gray-900 dark:text-gray-100">{namespace.name}</p>
        </div>

        <div>
          <label className="label">Description</label>
          <input
            type="text"
            className="input"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="What this namespace contains"
          />
        </div>

        <div>
          <label className="label">Default Priority (0-100)</label>
          <input
            type="number"
            className="input"
            min={0}
            max={100}
            value={defaultPriority}
            onChange={(e) => setDefaultPriority(Math.min(100, Math.max(0, Number(e.target.value) || 0)))}
          />
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
            Applied to new objects created in this namespace. Existing objects are not affected.
          </p>
        </div>

        <div className="flex justify-end gap-2">
          <button onClick={onClose} className="btn btn-secondary">
            Cancel
          </button>
          <button
            onClick={handleSave}
            disabled={updateNamespace.isPending}
            className="btn btn-primary"
          >
            {updateNamespace.isPending ? 'Saving...' : 'Save Changes'}
          </button>
        </div>
      </div>
    </Modal>
  );
}

// ========== Prefetch Rules: Create Button (rendered in header) ==========

function PrefetchRuleCreateButton() {
  const [isOpen, setIsOpen] = useState(false);
  return (
    <>
      <button
        onClick={() => setIsOpen(true)}
        className="btn btn-primary flex items-center gap-2"
      >
        <Plus className="w-4 h-4" />
        New Rule
      </button>
      {isOpen && <CreatePrefetchRuleModal onClose={() => setIsOpen(false)} />}
    </>
  );
}

// ========== Prefetch Rules: Main View ==========

function PrefetchRulesView() {
  const { data: rules, isLoading, isError } = usePrefetchRules();
  const updateRule = useUpdatePrefetchRule();
  const deleteRule = useDeletePrefetchRule();
  const [editingRule, setEditingRule] = useState<PrefetchRule | null>(null);

  const handleToggleActive = (rule: PrefetchRule) => {
    updateRule.mutate(
      { name: rule.name, data: { is_active: !rule.is_active } },
      {
        onSuccess: () => toast.success(rule.is_active ? 'Rule deactivated' : 'Rule activated'),
        onError: () => toast.error('Failed to update rule'),
      }
    );
  };

  const handleDelete = (rule: PrefetchRule) => {
    if (!confirm(`Delete prefetch rule "${rule.name}"? This cannot be undone.`)) return;
    deleteRule.mutate(rule.name, {
      onSuccess: () => toast.success('Prefetch rule deleted'),
      onError: () => toast.error('Failed to delete rule'),
    });
  };

  if (isError) {
    return (
      <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
        <p className="text-red-800 dark:text-red-300 text-sm">
          Failed to load prefetch rules. The memory layer module may not be enabled.
        </p>
      </div>
    );
  }

  if (isLoading) {
    return <div className="text-center py-12 text-gray-500 dark:text-gray-400">Loading prefetch rules...</div>;
  }

  if (!rules || rules.length === 0) {
    return (
      <div className="card text-center py-12">
        <Zap className="w-12 h-12 text-gray-400 mx-auto mb-4" />
        <h3 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-2">No prefetch rules</h3>
        <p className="text-gray-600 dark:text-gray-400 mb-6">
          Prefetch rules preload memory object bundles when a trigger condition fires.
        </p>
      </div>
    );
  }

  return (
    <>
      <div className="mb-3 text-sm text-gray-600 dark:text-gray-400">
        {rules.length} rule{rules.length !== 1 ? 's' : ''} — {rules.filter((r) => r.is_active).length} active
      </div>

      <div className="space-y-3">
        {rules.map((rule) => (
          <div
            key={rule.id}
            className={`card flex items-start gap-4 py-3 transition-opacity ${!rule.is_active ? 'opacity-60' : ''}`}
          >
            {/* Active toggle */}
            <button
              onClick={() => handleToggleActive(rule)}
              title={rule.is_active ? 'Click to deactivate' : 'Click to activate'}
              className={`mt-0.5 flex-shrink-0 transition-colors ${
                rule.is_active
                  ? 'text-green-600 dark:text-green-400 hover:text-green-800'
                  : 'text-gray-400 hover:text-gray-600 dark:hover:text-gray-300'
              }`}
            >
              {rule.is_active ? (
                <ToggleRight className="w-6 h-6" />
              ) : (
                <ToggleLeft className="w-6 h-6" />
              )}
            </button>

            {/* Rule details */}
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 flex-wrap">
                <span className="font-medium text-gray-900 dark:text-gray-100 font-mono text-sm">
                  {rule.name}
                </span>
                <span className="badge badge-blue text-xs flex items-center gap-1">
                  <Zap className="w-3 h-3" />
                  {rule.trigger}
                </span>
                {!rule.is_active && (
                  <span className="text-xs text-gray-400 dark:text-gray-500 italic">inactive</span>
                )}
              </div>
              <div className="flex flex-wrap gap-3 mt-1.5 text-xs text-gray-500 dark:text-gray-400">
                <span>
                  <strong>{rule.bundle.length}</strong> object{rule.bundle.length !== 1 ? 's' : ''} in bundle
                </span>
                <span>lookahead: <strong>{rule.lookahead_minutes}</strong> min</span>
                <span>decay: <strong>{rule.false_prefetch_decay_minutes}</strong> min</span>
              </div>
              {rule.bundle.length > 0 && (
                <div className="flex flex-wrap gap-1 mt-2">
                  {rule.bundle.map((objId) => (
                    <span
                      key={objId}
                      className="inline-block px-1.5 py-0.5 bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 rounded text-xs font-mono"
                    >
                      {objId}
                    </span>
                  ))}
                </div>
              )}
            </div>

            {/* Actions */}
            <div className="flex items-center gap-1 flex-shrink-0">
              <button
                onClick={() => setEditingRule(rule)}
                className="p-1.5 text-gray-400 hover:text-primary-600 rounded transition-colors"
                title="Edit"
              >
                <Edit2 className="w-4 h-4" />
              </button>
              <button
                onClick={() => handleDelete(rule)}
                className="p-1.5 text-gray-400 hover:text-red-600 rounded transition-colors"
                title="Delete"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
          </div>
        ))}
      </div>

      {editingRule && (
        <EditPrefetchRuleModal
          rule={editingRule}
          onClose={() => setEditingRule(null)}
        />
      )}
    </>
  );
}

// ========== Prefetch Rules: Create Modal ==========

function CreatePrefetchRuleModal({ onClose }: { onClose: () => void }) {
  const createRule = useCreatePrefetchRule();
  const [name, setName] = useState('');
  const [trigger, setTrigger] = useState('');
  const [bundleStr, setBundleStr] = useState('');
  const [lookahead, setLookahead] = useState(120);
  const [decay, setDecay] = useState(30);
  const [isActive, setIsActive] = useState(true);

  const handleCreate = () => {
    if (!name.trim()) { toast.error('Rule name is required'); return; }
    if (!trigger.trim()) { toast.error('Trigger is required'); return; }

    const bundle = bundleStr
      .split('\n')
      .map((s) => s.trim())
      .filter(Boolean);

    const data: PrefetchRuleCreate = {
      name: name.trim(),
      trigger: trigger.trim(),
      bundle,
      lookahead_minutes: lookahead,
      false_prefetch_decay_minutes: decay,
      is_active: isActive,
    };

    createRule.mutate(data, {
      onSuccess: () => {
        toast.success('Prefetch rule created');
        onClose();
      },
      onError: (err: any) => {
        toast.error(err?.response?.data?.detail || 'Failed to create rule');
      },
    });
  };

  return (
    <Modal isOpen onClose={onClose} title="Create Prefetch Rule">
      <div className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="label">Rule Name</label>
            <input
              type="text"
              className="input font-mono"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g., session_boot"
            />
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">Unique, immutable after creation</p>
          </div>
          <div>
            <label className="label">Trigger</label>
            <input
              type="text"
              className="input font-mono"
              value={trigger}
              onChange={(e) => setTrigger(e.target.value)}
              placeholder="e.g., session_start"
            />
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">Condition that fires this rule</p>
          </div>
        </div>

        <div>
          <label className="label">Bundle — Object IDs (one per line)</label>
          <textarea
            className="input font-mono text-sm"
            rows={5}
            value={bundleStr}
            onChange={(e) => setBundleStr(e.target.value)}
            placeholder={"user-profile-001\ninteraction-preferences-001\nwork-context-001"}
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="label">Lookahead (minutes)</label>
            <input
              type="number"
              className="input"
              min={1}
              value={lookahead}
              onChange={(e) => setLookahead(Math.max(1, Number(e.target.value) || 1))}
            />
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">Time window for look-ahead context</p>
          </div>
          <div>
            <label className="label">False-Prefetch Decay (minutes)</label>
            <input
              type="number"
              className="input"
              min={1}
              value={decay}
              onChange={(e) => setDecay(Math.max(1, Number(e.target.value) || 1))}
            />
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">Cache TTL for unused prefetches</p>
          </div>
        </div>

        <label className="flex items-center gap-3 cursor-pointer p-3 rounded-lg border border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors">
          <input
            type="checkbox"
            checked={isActive}
            onChange={(e) => setIsActive(e.target.checked)}
            className="w-4 h-4 rounded"
          />
          <div>
            <p className="text-sm font-medium text-gray-900 dark:text-gray-100">Active</p>
            <p className="text-xs text-gray-500 dark:text-gray-400">Rule will fire when trigger condition is met</p>
          </div>
        </label>

        <div className="flex justify-end gap-2">
          <button onClick={onClose} className="btn btn-secondary">Cancel</button>
          <button
            onClick={handleCreate}
            disabled={createRule.isPending}
            className="btn btn-primary"
          >
            {createRule.isPending ? 'Creating...' : 'Create Rule'}
          </button>
        </div>
      </div>
    </Modal>
  );
}

// ========== Prefetch Rules: Edit Modal ==========

function EditPrefetchRuleModal({ rule, onClose }: { rule: PrefetchRule; onClose: () => void }) {
  const updateRule = useUpdatePrefetchRule();
  const [trigger, setTrigger] = useState(rule.trigger);
  const [bundleStr, setBundleStr] = useState(rule.bundle.join('\n'));
  const [lookahead, setLookahead] = useState(rule.lookahead_minutes);
  const [decay, setDecay] = useState(rule.false_prefetch_decay_minutes);
  const [isActive, setIsActive] = useState(rule.is_active);

  const handleSave = () => {
    const bundle = bundleStr
      .split('\n')
      .map((s) => s.trim())
      .filter(Boolean);

    const data: PrefetchRuleUpdate = {
      trigger: trigger.trim() || undefined,
      bundle,
      lookahead_minutes: lookahead,
      false_prefetch_decay_minutes: decay,
      is_active: isActive,
    };

    updateRule.mutate(
      { name: rule.name, data },
      {
        onSuccess: () => {
          toast.success('Prefetch rule updated');
          onClose();
        },
        onError: (err: any) => {
          toast.error(err?.response?.data?.detail || 'Failed to update rule');
        },
      }
    );
  };

  return (
    <Modal isOpen onClose={onClose} title={`Edit Rule: ${rule.name}`}>
      <div className="space-y-4">
        <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-3 text-sm">
          <p className="text-gray-500 dark:text-gray-400 text-xs mb-1">Rule name (immutable)</p>
          <p className="font-mono text-gray-900 dark:text-gray-100">{rule.name}</p>
        </div>

        <div>
          <label className="label">Trigger</label>
          <input
            type="text"
            className="input font-mono"
            value={trigger}
            onChange={(e) => setTrigger(e.target.value)}
          />
        </div>

        <div>
          <label className="label">Bundle — Object IDs (one per line)</label>
          <textarea
            className="input font-mono text-sm"
            rows={5}
            value={bundleStr}
            onChange={(e) => setBundleStr(e.target.value)}
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="label">Lookahead (minutes)</label>
            <input
              type="number"
              className="input"
              min={1}
              value={lookahead}
              onChange={(e) => setLookahead(Math.max(1, Number(e.target.value) || 1))}
            />
          </div>
          <div>
            <label className="label">False-Prefetch Decay (minutes)</label>
            <input
              type="number"
              className="input"
              min={1}
              value={decay}
              onChange={(e) => setDecay(Math.max(1, Number(e.target.value) || 1))}
            />
          </div>
        </div>

        <label className="flex items-center gap-3 cursor-pointer p-3 rounded-lg border border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors">
          <input
            type="checkbox"
            checked={isActive}
            onChange={(e) => setIsActive(e.target.checked)}
            className="w-4 h-4 rounded"
          />
          <div>
            <p className="text-sm font-medium text-gray-900 dark:text-gray-100">Active</p>
            <p className="text-xs text-gray-500 dark:text-gray-400">Rule will fire when trigger condition is met</p>
          </div>
        </label>

        <div className="flex justify-end gap-2">
          <button onClick={onClose} className="btn btn-secondary">Cancel</button>
          <button
            onClick={handleSave}
            disabled={updateRule.isPending}
            className="btn btn-primary"
          >
            {updateRule.isPending ? 'Saving...' : 'Save Changes'}
          </button>
        </div>
      </div>
    </Modal>
  );
}

// ========== Session Capture: Button (rendered in header) ==========

function SessionCaptureButton() {
  const [isOpen, setIsOpen] = useState(false);
  return (
    <>
      <button
        onClick={() => setIsOpen(true)}
        className="btn btn-primary flex items-center gap-2"
      >
        <Plus className="w-4 h-4" />
        Log Session
      </button>
      {isOpen && <CaptureSessionModal onClose={() => setIsOpen(false)} />}
    </>
  );
}

// ========== Sessions: Energy indicator ==========

function EnergyDots({ level }: { level: number }) {
  return (
    <span className="flex items-center gap-0.5" title={`Energy: ${level}/5`}>
      {[1, 2, 3, 4, 5].map((n) => (
        <span
          key={n}
          className={`w-2 h-2 rounded-full ${
            n <= level
              ? level >= 4
                ? 'bg-green-500'
                : level >= 2
                ? 'bg-yellow-500'
                : 'bg-red-400'
              : 'bg-gray-200 dark:bg-gray-600'
          }`}
        />
      ))}
    </span>
  );
}

// ========== Sessions: Main View ==========

function SessionsView() {
  const { data: sessions, isLoading, isError } = useSessionSummaries(50);
  const [expandedIds, setExpandedIds] = useState<Set<string>>(new Set());

  const toggleExpand = (objectId: string) => {
    setExpandedIds((prev) => {
      const next = new Set(prev);
      if (next.has(objectId)) next.delete(objectId);
      else next.add(objectId);
      return next;
    });
  };

  if (isError) {
    return (
      <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
        <p className="text-red-800 dark:text-red-300 text-sm">
          Failed to load sessions. The memory layer module may not be enabled.
        </p>
      </div>
    );
  }

  if (isLoading) {
    return <div className="text-center py-12 text-gray-500 dark:text-gray-400">Loading sessions...</div>;
  }

  if (!sessions || sessions.length === 0) {
    return (
      <div className="card text-center py-12">
        <ClipboardList className="w-12 h-12 text-gray-400 mx-auto mb-4" />
        <h3 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-2">No sessions captured</h3>
        <p className="text-gray-600 dark:text-gray-400 mb-6">
          Log your first session to start building a record of your work.
        </p>
        <SessionCaptureButton />
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <p className="text-sm text-gray-600 dark:text-gray-400">
        {sessions.length} session{sessions.length !== 1 ? 's' : ''} captured
      </p>

      {sessions.map((session) => {
        const content = session.content as {
          date?: string;
          accomplishments?: string[];
          blockers?: string[];
          next_focus?: string;
          energy_level?: number;
          duration_minutes?: number;
          notes?: string;
        } | null;

        const accomplishments = content?.accomplishments ?? [];
        const isExpanded = expandedIds.has(session.object_id);
        const sessionDate = content?.date ?? session.effective_from;
        const energy = content?.energy_level;

        return (
          <div key={session.id} className="card py-3">
            {/* Header row */}
            <button
              onClick={() => toggleExpand(session.object_id)}
              className="w-full text-left flex items-center gap-3 group"
            >
              <CheckCircle2 className="w-5 h-5 text-green-500 flex-shrink-0" />
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="font-medium text-gray-900 dark:text-gray-100 text-sm">
                    {sessionDate}
                  </span>
                  <span className="font-mono text-xs text-gray-400 dark:text-gray-500">
                    {session.object_id}
                  </span>
                </div>
                <div className="flex items-center gap-3 mt-1 flex-wrap">
                  <span className="text-xs text-gray-500 dark:text-gray-400">
                    {accomplishments.length} accomplishment{accomplishments.length !== 1 ? 's' : ''}
                  </span>
                  {energy !== undefined && energy !== null && (
                    <EnergyDots level={energy} />
                  )}
                  {content?.duration_minutes && (
                    <span className="text-xs text-gray-500 dark:text-gray-400 flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      {content.duration_minutes} min
                    </span>
                  )}
                  {accomplishments.length > 0 && !isExpanded && (
                    <span className="text-xs text-gray-400 dark:text-gray-500 truncate italic">
                      {accomplishments[0]}
                      {accomplishments.length > 1 ? ` +${accomplishments.length - 1} more` : ''}
                    </span>
                  )}
                </div>
              </div>
              <ChevronDown
                className={`w-4 h-4 text-gray-400 flex-shrink-0 transition-transform ${isExpanded ? 'rotate-180' : ''}`}
              />
            </button>

            {/* Expanded detail */}
            {isExpanded && (
              <div className="mt-4 pt-4 border-t border-gray-100 dark:border-gray-700 space-y-3 text-sm">
                {accomplishments.length > 0 && (
                  <div>
                    <p className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-1">
                      Accomplishments
                    </p>
                    <ul className="space-y-1">
                      {accomplishments.map((item, i) => (
                        <li key={i} className="flex items-start gap-2 text-gray-700 dark:text-gray-300">
                          <span className="text-green-500 mt-0.5 flex-shrink-0">•</span>
                          {item}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {content?.blockers && content.blockers.length > 0 && (
                  <div>
                    <p className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-1">
                      Blockers
                    </p>
                    <ul className="space-y-1">
                      {content.blockers.map((item, i) => (
                        <li key={i} className="flex items-start gap-2 text-gray-700 dark:text-gray-300">
                          <span className="text-orange-500 mt-0.5 flex-shrink-0">•</span>
                          {item}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {content?.next_focus && (
                  <div>
                    <p className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-1">
                      Next Focus
                    </p>
                    <p className="text-gray-700 dark:text-gray-300">{content.next_focus}</p>
                  </div>
                )}

                {content?.notes && (
                  <div>
                    <p className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-1">
                      Notes
                    </p>
                    <p className="text-gray-700 dark:text-gray-300 whitespace-pre-line">{content.notes}</p>
                  </div>
                )}

                {session.tags && session.tags.length > 0 && (
                  <div className="flex flex-wrap gap-1 pt-1">
                    {session.tags.map((tag) => (
                      <span key={tag} className="badge badge-blue text-xs flex items-center gap-1">
                        <Tag className="w-3 h-3" />
                        {tag}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

// ========== Capture Session Modal ==========

function CaptureSessionModal({ onClose }: { onClose: () => void }) {
  const captureSession = useCaptureSession();
  const today = new Date().toISOString().split('T')[0];

  const [sessionDate, setSessionDate] = useState(today);
  const [accomplishmentsStr, setAccomplishmentsStr] = useState('');
  const [blockersStr, setBlockersStr] = useState('');
  const [nextFocus, setNextFocus] = useState('');
  const [energyLevel, setEnergyLevel] = useState<number | null>(null);
  const [durationMinutes, setDurationMinutes] = useState('');
  const [notes, setNotes] = useState('');
  const [tags, setTags] = useState('');

  const handleCapture = () => {
    const accomplishments = accomplishmentsStr
      .split('\n')
      .map((s) => s.trim())
      .filter(Boolean);

    if (accomplishments.length === 0) {
      toast.error('Add at least one accomplishment');
      return;
    }

    const blockers = blockersStr
      .split('\n')
      .map((s) => s.trim())
      .filter(Boolean);

    const data: SessionCapture = {
      session_date: sessionDate || undefined,
      accomplishments,
      blockers: blockers.length > 0 ? blockers : undefined,
      next_focus: nextFocus.trim() || undefined,
      energy_level: energyLevel ?? undefined,
      duration_minutes: durationMinutes ? parseInt(durationMinutes, 10) || undefined : undefined,
      notes: notes.trim() || undefined,
      tags: tags
        ? tags.split(',').map((t) => t.trim()).filter(Boolean)
        : undefined,
    };

    captureSession.mutate(data, {
      onSuccess: () => {
        toast.success('Session captured');
        onClose();
      },
      onError: (err: any) => {
        toast.error(err?.response?.data?.detail || 'Failed to capture session');
      },
    });
  };

  return (
    <Modal isOpen onClose={onClose} title="Log Session Summary">
      <div className="space-y-4">
        {/* Date */}
        <div>
          <label className="label">Session Date</label>
          <input
            type="date"
            className="input"
            value={sessionDate}
            onChange={(e) => setSessionDate(e.target.value)}
          />
        </div>

        {/* Accomplishments */}
        <div>
          <label className="label">
            Accomplishments <span className="text-red-500">*</span>
          </label>
          <textarea
            className="input text-sm"
            rows={4}
            value={accomplishmentsStr}
            onChange={(e) => setAccomplishmentsStr(e.target.value)}
            placeholder={"Finished refactoring the auth module\nFixed DEBT-133 import error handling\nReviewed PR #42"}
          />
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">One item per line</p>
        </div>

        {/* Blockers */}
        <div>
          <label className="label">Blockers (optional)</label>
          <textarea
            className="input text-sm"
            rows={2}
            value={blockersStr}
            onChange={(e) => setBlockersStr(e.target.value)}
            placeholder={"Waiting for design review on feature X\nNeed access to staging DB"}
          />
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">One item per line</p>
        </div>

        {/* Next focus */}
        <div>
          <label className="label">Next Session Focus (optional)</label>
          <input
            type="text"
            className="input"
            value={nextFocus}
            onChange={(e) => setNextFocus(e.target.value)}
            placeholder="e.g., Pick up design review and complete BACKLOG-083"
          />
        </div>

        {/* Energy + Duration row */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="label">Energy Level (optional)</label>
            <div className="flex gap-2 mt-1">
              {[1, 2, 3, 4, 5].map((n) => (
                <button
                  key={n}
                  onClick={() => setEnergyLevel(energyLevel === n ? null : n)}
                  className={`w-9 h-9 rounded-full text-sm font-bold transition-colors border-2 ${
                    energyLevel === n
                      ? n >= 4
                        ? 'bg-green-500 border-green-500 text-white'
                        : n >= 2
                        ? 'bg-yellow-500 border-yellow-500 text-white'
                        : 'bg-red-400 border-red-400 text-white'
                      : 'border-gray-200 dark:border-gray-600 text-gray-600 dark:text-gray-400 hover:border-gray-400'
                  }`}
                >
                  {n}
                </button>
              ))}
            </div>
          </div>
          <div>
            <label className="label">Duration (minutes, optional)</label>
            <input
              type="number"
              className="input"
              min={1}
              value={durationMinutes}
              onChange={(e) => setDurationMinutes(e.target.value)}
              placeholder="e.g., 90"
            />
          </div>
        </div>

        {/* Notes */}
        <div>
          <label className="label">Notes (optional)</label>
          <textarea
            className="input text-sm"
            rows={2}
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="Any additional context or observations..."
          />
        </div>

        {/* Tags */}
        <div>
          <label className="label">Tags (optional, comma-separated)</label>
          <input
            type="text"
            className="input"
            value={tags}
            onChange={(e) => setTags(e.target.value)}
            placeholder="e.g., backend, deep-work, refactor"
          />
        </div>

        <div className="flex justify-end gap-2 pt-1">
          <button onClick={onClose} className="btn btn-secondary">
            Cancel
          </button>
          <button
            onClick={handleCapture}
            disabled={captureSession.isPending}
            className="btn btn-primary flex items-center gap-2"
          >
            <ClipboardList className="w-4 h-4" />
            {captureSession.isPending ? 'Saving...' : 'Save Session'}
          </button>
        </div>
      </div>
    </Modal>
  );
}

// ========== Delete Namespace Modal ==========

function DeleteNamespaceModal({
  namespace,
  onClose,
}: {
  namespace: MemoryNamespace;
  onClose: () => void;
}) {
  const deleteNamespace = useDeleteNamespace();
  const [forceDelete, setForceDelete] = useState(false);
  const hasObjects = namespace.object_count > 0;

  const handleDelete = () => {
    deleteNamespace.mutate(
      { name: namespace.name, force: forceDelete },
      {
        onSuccess: () => {
          toast.success(`Namespace "${namespace.name}" deleted`);
          onClose();
        },
        onError: (err: any) => {
          const msg = err?.response?.data?.detail || 'Failed to delete namespace';
          toast.error(msg);
        },
      }
    );
  };

  return (
    <Modal isOpen onClose={onClose} title="Delete Namespace">
      <div className="space-y-4">
        <div className="flex items-start gap-3 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
          <AlertTriangle className="w-5 h-5 text-red-600 dark:text-red-400 flex-shrink-0 mt-0.5" />
          <div className="text-sm">
            <p className="font-medium text-red-800 dark:text-red-300">
              Delete <span className="font-mono">{namespace.name}</span>?
            </p>
            {hasObjects ? (
              <p className="text-red-700 dark:text-red-400 mt-1">
                This namespace contains{' '}
                <strong>{namespace.object_count} object{namespace.object_count !== 1 ? 's' : ''}</strong>.
                You must delete the objects first, or enable force delete below.
              </p>
            ) : (
              <p className="text-red-700 dark:text-red-400 mt-1">
                This namespace is empty and can be safely deleted.
              </p>
            )}
          </div>
        </div>

        {hasObjects && (
          <label className="flex items-center gap-3 cursor-pointer p-3 rounded-lg border border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors">
            <input
              type="checkbox"
              checked={forceDelete}
              onChange={(e) => setForceDelete(e.target.checked)}
              className="w-4 h-4 rounded"
            />
            <div>
              <p className="text-sm font-medium text-gray-900 dark:text-gray-100">
                Force delete — also delete all {namespace.object_count} object{namespace.object_count !== 1 ? 's' : ''}
              </p>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                This cannot be undone
              </p>
            </div>
          </label>
        )}

        <div className="flex justify-end gap-2">
          <button onClick={onClose} className="btn btn-secondary">
            Cancel
          </button>
          <button
            onClick={handleDelete}
            disabled={deleteNamespace.isPending || (hasObjects && !forceDelete)}
            className="btn btn-danger"
          >
            {deleteNamespace.isPending ? 'Deleting...' : 'Delete Namespace'}
          </button>
        </div>
      </div>
    </Modal>
  );
}
