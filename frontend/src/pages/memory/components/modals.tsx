import { useState, useEffect } from 'react';
import toast from 'react-hot-toast';
import { Tag, AlertTriangle } from 'lucide-react';
import { Modal } from '@/components/common/Modal';
import {
  useMemoryObject,
  useCreateMemoryObject,
  useUpdateMemoryObject,
  useCreateNamespace,
  useUpdateNamespace,
  useDeleteNamespace,
  type MemoryObjectCreate,
  type MemoryObjectUpdate,
  type MemoryNamespace,
} from '@/hooks/useMemory';
import { getPriorityColor } from './shared';

// ========== View Modal ==========

export function ViewObjectModal({ objectId, onClose }: { objectId: string; onClose: () => void }) {
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

export function EditObjectModal({ objectId, onClose }: { objectId: string; onClose: () => void }) {
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

export function CreateObjectModal({
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

export function CreateNamespaceModal({ onClose }: { onClose: () => void }) {
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

export function EditNamespaceModal({
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

export function DeleteNamespaceModal({
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
