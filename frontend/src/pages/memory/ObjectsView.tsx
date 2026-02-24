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
  Layers,
  MoreVertical,
} from 'lucide-react';
import { SearchInput } from '@/components/common/SearchInput';
import {
  useMemoryObjects,
  useMemoryNamespaces,
  useSearchMemoryObjects,
  useDeleteMemoryObject,
  type MemoryObjectBrief,
  type MemoryNamespace,
} from '@/hooks/useMemory';
import { getPriorityColor, getPriorityBg } from './components/shared';
import {
  ViewObjectModal,
  EditObjectModal,
  CreateObjectModal,
  CreateNamespaceModal,
  EditNamespaceModal,
  DeleteNamespaceModal,
} from './components/modals';

/** Parse dot notation to determine indent depth (e.g. core.identity -> depth 1) */
function getNamespaceDepth(name: string): number {
  return name.split('.').length - 1;
}

/** Build a sorted tree for display: parents before children, alphabetically */
function buildNamespaceTree(namespaces: MemoryNamespace[]): MemoryNamespace[] {
  return [...namespaces].sort((a, b) => a.name.localeCompare(b.name));
}

export function ObjectsHeaderActions() {
  const [isCreateNsOpen, setIsCreateNsOpen] = useState(false);
  const [isCreateObjOpen, setIsCreateObjOpen] = useState(false);
  const { data: namespaces } = useMemoryNamespaces();

  return (
    <>
      <div className="flex gap-2">
        <button
          onClick={() => setIsCreateNsOpen(true)}
          className="btn btn-secondary flex items-center gap-2"
        >
          <Layers className="w-4 h-4" />
          New Namespace
        </button>
        <button
          onClick={() => setIsCreateObjOpen(true)}
          className="btn btn-primary flex items-center gap-2"
        >
          <Plus className="w-4 h-4" />
          New Object
        </button>
      </div>
      {isCreateNsOpen && (
        <CreateNamespaceModal onClose={() => setIsCreateNsOpen(false)} />
      )}
      {isCreateObjOpen && (
        <CreateObjectModal
          namespaces={namespaces || []}
          onClose={() => setIsCreateObjOpen(false)}
        />
      )}
    </>
  );
}

export function ObjectsView() {
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
    <>
      <div className="flex gap-6">
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
      </div>

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
    </>
  );
}
