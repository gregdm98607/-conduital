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
  BarChart2,
  ClipboardList,
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
  type MemoryObjectBrief,
  type MemoryObjectCreate,
  type MemoryObjectUpdate,
  type MemoryNamespace,
} from '@/hooks/useMemory';
import { getPriorityColor, getPriorityBg } from './memory/components/shared';
import { HealthView } from './memory/HealthView';
import { PrefetchRulesView, PrefetchRuleCreateButton } from './memory/PrefetchView';
import { SessionsView, SessionCaptureButton } from './memory/SessionsView';

/** Parse dot notation to determine indent depth (e.g. core.identity -> depth 1) */
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
          <TabButton active={activeTab === 'objects'} onClick={() => setActiveTab('objects')} icon={<Brain className="w-4 h-4" />} label="Objects" />
          <TabButton active={activeTab === 'prefetch'} onClick={() => setActiveTab('prefetch')} icon={<Zap className="w-4 h-4" />} label="Prefetch Rules" />
          <TabButton active={activeTab === 'health'} onClick={() => setActiveTab('health')} icon={<BarChart2 className="w-4 h-4" />} label="Health" />
          <TabButton active={activeTab === 'sessions'} onClick={() => setActiveTab('sessions')} icon={<ClipboardList className="w-4 h-4" />} label="Sessions" />
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
            if (selectedNamespace === deletingNamespace.name) {
              setSelectedNamespace(undefined);
            }
          }}
        />
      )}
    </div>
  );
}

// ========== Tab Button ==========

function TabButton({ active, onClick, icon, label }: { active: boolean; onClick: () => void; icon: React.ReactNode; label: string }) {
  return (
    <button
      onClick={onClick}
      className={`flex items-center gap-2 px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
        active
          ? 'border-primary-600 text-primary-600 dark:border-primary-400 dark:text-primary-400'
          : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
      }`}
    >
      {icon}
      {label}
    </button>
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
