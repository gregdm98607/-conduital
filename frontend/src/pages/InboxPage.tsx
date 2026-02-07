import { useState, useMemo, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Inbox, Plus, Trash2, FolderKanban, CheckSquare, Archive, Clock, ExternalLink, Edit2, Check, X } from 'lucide-react';
import toast from 'react-hot-toast';
import { useInboxItems, useCreateInboxItem, useUpdateInboxItem, useProcessInboxItem, useDeleteInboxItem } from '../hooks/useInbox';
import { useProjects } from '../hooks/useProjects';
import { useCreateTask } from '../hooks/useTasks';
import { Error } from '../components/common/Error';
import { Loading } from '../components/common/Loading';
import { SearchInput } from '../components/common/SearchInput';
import { Modal } from '../components/common/Modal';
import type { InboxItem, InboxResultType, Project } from '../types';

export function InboxPage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [showProcessed, setShowProcessed] = useState(false);
  const [isQuickCaptureOpen, setIsQuickCaptureOpen] = useState(false);
  const [quickCaptureText, setQuickCaptureText] = useState('');
  const [processingItem, setProcessingItem] = useState<InboxItem | null>(null);
  const [selectedResultType, setSelectedResultType] = useState<InboxResultType>('task');
  const [selectedProjectId, setSelectedProjectId] = useState<number | undefined>();
  const [editTitle, setEditTitle] = useState('');
  const [editDescription, setEditDescription] = useState('');
  const [editingItemId, setEditingItemId] = useState<number | null>(null);
  const [editingContent, setEditingContent] = useState('');
  const [quickCaptureProjectId, setQuickCaptureProjectId] = useState<number | undefined>();

  const { data: items, isLoading, error } = useInboxItems(showProcessed);
  const { data: projectsData } = useProjects({ status: 'active' });
  const createInboxItem = useCreateInboxItem();
  const createTask = useCreateTask();
  const updateInboxItem = useUpdateInboxItem();
  const processInboxItem = useProcessInboxItem();
  const deleteInboxItem = useDeleteInboxItem();

  const projects = projectsData?.projects || [];

  // Pre-fill title when processing item changes
  useEffect(() => {
    if (processingItem) {
      setEditTitle(processingItem.content.slice(0, 500));
      setEditDescription('');
    }
  }, [processingItem]);

  // Client-side search filtering
  const filteredItems = useMemo(() => {
    if (!searchQuery || !items) return items;
    const query = searchQuery.toLowerCase();
    return items.filter((item) => item.content.toLowerCase().includes(query));
  }, [items, searchQuery]);

  const handleQuickCapture = (keepOpen: boolean = false) => {
    if (!quickCaptureText.trim()) return;

    if (quickCaptureProjectId) {
      // Create task directly on the project
      createTask.mutate(
        {
          title: quickCaptureText.trim(),
          project_id: quickCaptureProjectId,
          status: 'pending',
          is_next_action: true,
          priority: 5,
        } as any,
        {
          onSuccess: () => {
            const project = projects.find((p: Project) => p.id === quickCaptureProjectId);
            toast.success(`Task added to ${project?.title || 'project'}`);
            setQuickCaptureText('');
            if (!keepOpen) {
              setIsQuickCaptureOpen(false);
              setQuickCaptureProjectId(undefined);
            }
          },
          onError: () => {
            toast.error('Failed to create task');
          },
        }
      );
    } else {
      // Create inbox item (standard capture)
      createInboxItem.mutate(
        { content: quickCaptureText.trim() },
        {
          onSuccess: () => {
            toast.success('Captured to inbox');
            setQuickCaptureText('');
            if (!keepOpen) {
              setIsQuickCaptureOpen(false);
            }
          },
          onError: () => {
            toast.error('Failed to capture item');
          },
        }
      );
    }
  };

  const handleProcess = () => {
    if (!processingItem) return;

    processInboxItem.mutate(
      {
        id: processingItem.id,
        processing: {
          result_type: selectedResultType,
          result_id: selectedResultType === 'task' ? selectedProjectId : undefined,
          title: (selectedResultType === 'task' || selectedResultType === 'project') ? editTitle.trim() || undefined : undefined,
          description: (selectedResultType === 'task' || selectedResultType === 'project') ? editDescription.trim() || undefined : undefined,
        },
      },
      {
        onSuccess: () => {
          const messages: Record<InboxResultType, string> = {
            task: 'Created as task',
            project: 'Created as project',
            reference: 'Saved as reference',
            trash: 'Moved to trash',
          };
          toast.success(messages[selectedResultType]);
          setProcessingItem(null);
          setSelectedResultType('task');
          setSelectedProjectId(undefined);
          setEditTitle('');
          setEditDescription('');
        },
        onError: () => {
          toast.error('Failed to process item');
        },
      }
    );
  };

  const handleDelete = (id: number) => {
    deleteInboxItem.mutate(id, {
      onSuccess: () => {
        toast.success('Item deleted');
      },
      onError: () => {
        toast.error('Failed to delete item');
      },
    });
  };

  const startEditing = (item: InboxItem) => {
    setEditingItemId(item.id);
    setEditingContent(item.content);
  };

  const cancelEditing = () => {
    setEditingItemId(null);
    setEditingContent('');
  };

  const saveEdit = () => {
    if (editingItemId === null || !editingContent.trim()) return;

    updateInboxItem.mutate(
      { id: editingItemId, content: editingContent.trim() },
      {
        onSuccess: () => {
          toast.success('Item updated');
          setEditingItemId(null);
          setEditingContent('');
        },
        onError: () => {
          toast.error('Failed to update item');
        },
      }
    );
  };

  const getResultLink = (item: InboxItem): string | null => {
    if (!item.result_id || !item.result_type) return null;
    if (item.result_type === 'project') return `/projects/${item.result_id}`;
    if (item.result_type === 'task' && item.result_project_id) return `/projects/${item.result_project_id}`;
    return null;
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffMins < 1) return 'just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString();
  };

  if (error) return <Error message="Failed to load inbox" fullPage />;

  return (
    <div className="p-8">
      {/* Header */}
      <header className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100 flex items-center gap-3">
            <Inbox className="w-8 h-8 text-primary-600" />
            Inbox
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Capture everything, process later (GTD Capture + Clarify)
          </p>
        </div>
        <button
          onClick={() => setIsQuickCaptureOpen(true)}
          className="btn btn-primary flex items-center gap-2"
        >
          <Plus className="w-5 h-5" />
          Quick Capture
        </button>
      </header>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div className="card bg-primary-50 border-primary-200">
          <div className="flex items-center gap-3">
            <Inbox className="w-6 h-6 text-primary-600" />
            <div>
              <p className="text-2xl font-bold text-primary-900">{items?.filter(i => !i.processed_at).length || 0}</p>
              <p className="text-sm text-primary-700">Unprocessed Items</p>
            </div>
          </div>
        </div>
        <div className="card bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800">
          <div className="flex items-center gap-3">
            <CheckSquare className="w-6 h-6 text-green-600" />
            <div>
              <p className="text-2xl font-bold text-green-900 dark:text-green-200">{items?.filter(i => {
                if (!i.processed_at) return false;
                const processed = new Date(i.processed_at);
                const today = new Date();
                return processed.getFullYear() === today.getFullYear()
                  && processed.getMonth() === today.getMonth()
                  && processed.getDate() === today.getDate();
              }).length || 0}</p>
              <p className="text-sm text-green-700 dark:text-green-300">Processed Today</p>
            </div>
          </div>
        </div>
        <div className="card bg-gray-50 dark:bg-gray-800 border-gray-200 dark:border-gray-700">
          <div className="flex items-center gap-3">
            <Clock className="w-6 h-6 text-gray-600 dark:text-gray-400" />
            <div>
              <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                {items?.length ? formatDate(items[0].captured_at) : 'N/A'}
              </p>
              <p className="text-sm text-gray-700 dark:text-gray-300">Last Capture</p>
            </div>
          </div>
        </div>
      </div>

      {/* Search and Filters */}
      <div className="mb-6 flex gap-4 items-center">
        <div className="flex-1">
          <SearchInput
            value={searchQuery}
            onChange={setSearchQuery}
            placeholder="Search inbox items..."
          />
        </div>
        <label className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
          <input
            type="checkbox"
            checked={showProcessed}
            onChange={(e) => setShowProcessed(e.target.checked)}
            className="rounded border-gray-300 dark:border-gray-600 text-primary-600 focus:ring-primary-500"
          />
          Show processed
        </label>
      </div>

      {/* Items List */}
      {isLoading ? (
        <Loading />
      ) : filteredItems && filteredItems.length > 0 ? (
        <div className="space-y-3">
          {filteredItems.map((item) => {
            const resultLink = getResultLink(item);
            return (
              <div
                key={item.id}
                className={`card hover:shadow-md transition-shadow ${
                  item.processed_at ? 'bg-gray-50 dark:bg-gray-800 opacity-75' : ''
                }`}
              >
                <div className="flex items-start gap-4">
                  <div className="flex-1">
                    {editingItemId === item.id ? (
                      <div className="space-y-2">
                        <textarea
                          value={editingContent}
                          onChange={(e) => setEditingContent(e.target.value)}
                          className="input w-full resize-none"
                          rows={3}
                          autoFocus
                          onKeyDown={(e) => {
                            if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
                              e.preventDefault();
                              saveEdit();
                            } else if (e.key === 'Escape') {
                              cancelEditing();
                            }
                          }}
                        />
                        <div className="flex items-center gap-2">
                          <button
                            onClick={saveEdit}
                            disabled={!editingContent.trim() || updateInboxItem.isPending}
                            className="btn btn-sm btn-primary flex items-center gap-1"
                          >
                            <Check className="w-3 h-3" />
                            {updateInboxItem.isPending ? 'Saving...' : 'Save'}
                          </button>
                          <button
                            onClick={cancelEditing}
                            className="btn btn-sm btn-secondary flex items-center gap-1"
                          >
                            <X className="w-3 h-3" />
                            Cancel
                          </button>
                          <span className="text-xs text-gray-400 dark:text-gray-500">Ctrl+Enter to save</span>
                        </div>
                      </div>
                    ) : (
                      <p className="text-gray-900 dark:text-gray-100 whitespace-pre-wrap">{item.content}</p>
                    )}
                    <div className="flex items-center gap-3 mt-2 text-sm text-gray-500 dark:text-gray-400 flex-wrap">
                      <span className="flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {formatDate(item.captured_at)}
                      </span>
                      <span className="badge badge-gray">{item.source}</span>
                      {item.processed_at && item.result_type && (
                        <>
                          {resultLink && item.result_title ? (
                            <Link
                              to={resultLink}
                              className="inline-flex items-center gap-1 badge badge-green hover:opacity-80 transition-opacity"
                            >
                              {item.result_type === 'task' ? (
                                <CheckSquare className="w-3 h-3" />
                              ) : item.result_type === 'project' ? (
                                <FolderKanban className="w-3 h-3" />
                              ) : null}
                              <span>{item.result_title}</span>
                              <ExternalLink className="w-3 h-3" />
                            </Link>
                          ) : (
                            <span className="badge badge-green">
                              Processed: {item.result_type}
                            </span>
                          )}
                        </>
                      )}
                    </div>
                  </div>
                  {!item.processed_at && editingItemId !== item.id && (
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => startEditing(item)}
                        className="btn btn-sm btn-secondary"
                        title="Edit content"
                      >
                        <Edit2 className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => setProcessingItem(item)}
                        className="btn btn-sm btn-primary"
                        title="Process this item"
                      >
                        Process
                      </button>
                      <button
                        onClick={() => handleDelete(item.id)}
                        className="btn btn-sm btn-secondary text-red-600 hover:bg-red-50"
                        title="Delete"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        <div className="card text-center py-12">
          <Inbox className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-500 dark:text-gray-400 text-lg mb-2">
            {searchQuery ? 'No items match your search' : 'Inbox is empty'}
          </p>
          <p className="text-gray-400 dark:text-gray-500 text-sm mb-4">
            {searchQuery
              ? 'Try adjusting your search query'
              : 'Capture ideas, tasks, and thoughts here to process later'}
          </p>
          {!searchQuery && (
            <button
              onClick={() => setIsQuickCaptureOpen(true)}
              className="btn btn-primary"
            >
              <Plus className="w-4 h-4 mr-2" />
              Capture Something
            </button>
          )}
        </div>
      )}

      {/* Quick Capture Modal */}
      <Modal
        isOpen={isQuickCaptureOpen}
        onClose={() => { setIsQuickCaptureOpen(false); setQuickCaptureProjectId(undefined); }}
        title="Quick Capture"
      >
        <div className="space-y-4">
          <p className="text-sm text-gray-600 dark:text-gray-400">
            {quickCaptureProjectId
              ? 'Add a task directly to a project.'
              : 'Capture anything on your mind. Don\'t worry about organizing - just get it out of your head.'}
          </p>
          <textarea
            value={quickCaptureText}
            onChange={(e) => setQuickCaptureText(e.target.value)}
            placeholder={quickCaptureProjectId ? 'Task title...' : "What's on your mind?"}
            rows={4}
            autoFocus
            className="input w-full resize-none"
            onKeyDown={(e) => {
              if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
                e.preventDefault();
                handleQuickCapture(true);
              }
            }}
          />
          <div>
            <label className="label text-sm">Add directly to project (optional)</label>
            <select
              value={quickCaptureProjectId || ''}
              onChange={(e) => setQuickCaptureProjectId(e.target.value ? Number(e.target.value) : undefined)}
              className="input w-full"
            >
              <option value="">Inbox (process later)</option>
              {projects.map((project: Project) => (
                <option key={project.id} value={project.id}>
                  {project.title}
                </option>
              ))}
            </select>
          </div>
          <div className="flex justify-end gap-3">
            <button
              onClick={() => { setIsQuickCaptureOpen(false); setQuickCaptureProjectId(undefined); }}
              className="btn btn-secondary"
            >
              Close
            </button>
            <button
              onClick={() => handleQuickCapture(true)}
              disabled={!quickCaptureText.trim() || createInboxItem.isPending || createTask.isPending}
              className="btn btn-primary"
            >
              {(createInboxItem.isPending || createTask.isPending)
                ? 'Capturing...'
                : quickCaptureProjectId ? 'Add Task & Next' : 'Capture & Next'}
            </button>
          </div>
          <p className="text-xs text-gray-400 dark:text-gray-500 text-center">
            Ctrl+Enter to capture and keep entering · Esc to close
          </p>
        </div>
      </Modal>

      {/* Process Item Modal */}
      <Modal
        isOpen={!!processingItem}
        onClose={() => setProcessingItem(null)}
        title="Process Inbox Item"
      >
        {processingItem && (
          <div className="space-y-4">
            <div className="bg-gray-50 dark:bg-gray-800 p-4 rounded-lg">
              <p className="text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">Original capture:</p>
              <p className="text-gray-900 dark:text-gray-100 whitespace-pre-wrap">{processingItem.content}</p>
            </div>

            <div>
              <label className="label">What is this?</label>
              <div className="grid grid-cols-2 gap-3">
                <button
                  onClick={() => setSelectedResultType('task')}
                  className={`p-4 rounded-lg border-2 flex flex-col items-center gap-2 transition-colors ${
                    selectedResultType === 'task'
                      ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20'
                      : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
                  }`}
                >
                  <CheckSquare className="w-6 h-6" />
                  <span className="font-medium">Task</span>
                  <span className="text-xs text-gray-500 dark:text-gray-400">Single action item</span>
                </button>
                <button
                  onClick={() => setSelectedResultType('project')}
                  className={`p-4 rounded-lg border-2 flex flex-col items-center gap-2 transition-colors ${
                    selectedResultType === 'project'
                      ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20'
                      : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
                  }`}
                >
                  <FolderKanban className="w-6 h-6" />
                  <span className="font-medium">Project</span>
                  <span className="text-xs text-gray-500 dark:text-gray-400">Multi-step outcome</span>
                </button>
                <button
                  onClick={() => setSelectedResultType('reference')}
                  className={`p-4 rounded-lg border-2 flex flex-col items-center gap-2 transition-colors ${
                    selectedResultType === 'reference'
                      ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20'
                      : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
                  }`}
                >
                  <Archive className="w-6 h-6" />
                  <span className="font-medium">Reference</span>
                  <span className="text-xs text-gray-500 dark:text-gray-400">Not actionable</span>
                </button>
                <button
                  onClick={() => setSelectedResultType('trash')}
                  className={`p-4 rounded-lg border-2 flex flex-col items-center gap-2 transition-colors ${
                    selectedResultType === 'trash'
                      ? 'border-red-500 bg-red-50 dark:bg-red-900/20'
                      : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
                  }`}
                >
                  <Trash2 className="w-6 h-6" />
                  <span className="font-medium">Trash</span>
                  <span className="text-xs text-gray-500 dark:text-gray-400">Not needed</span>
                </button>
              </div>
            </div>

            {/* Editable title and description for task/project */}
            {(selectedResultType === 'task' || selectedResultType === 'project') && (
              <div className="space-y-3">
                <div>
                  <label className="label">Title</label>
                  <input
                    type="text"
                    value={editTitle}
                    onChange={(e) => setEditTitle(e.target.value)}
                    className="input w-full"
                    placeholder={`${selectedResultType === 'task' ? 'Task' : 'Project'} title...`}
                    maxLength={500}
                  />
                </div>
                <div>
                  <label className="label">Description (optional)</label>
                  <textarea
                    value={editDescription}
                    onChange={(e) => setEditDescription(e.target.value)}
                    className="input w-full resize-none"
                    placeholder="Add more details..."
                    rows={3}
                    maxLength={5000}
                  />
                </div>
              </div>
            )}

            {selectedResultType === 'task' && (
              <div>
                <label className="label">Add to project</label>
                <select
                  value={selectedProjectId || ''}
                  onChange={(e) => setSelectedProjectId(e.target.value ? Number(e.target.value) : undefined)}
                  className="input w-full"
                >
                  <option value="">Select a project...</option>
                  {projects.map((project: Project) => (
                    <option key={project.id} value={project.id}>
                      {project.title}
                    </option>
                  ))}
                </select>
                {!selectedProjectId && (
                  <p className="text-xs text-amber-600 mt-1">A project is required for tasks</p>
                )}
              </div>
            )}

            <div className="flex justify-end gap-3 pt-4">
              <button
                onClick={() => setProcessingItem(null)}
                className="btn btn-secondary"
              >
                Cancel
              </button>
              <button
                onClick={handleProcess}
                disabled={processInboxItem.isPending || (selectedResultType === 'task' && !selectedProjectId)}
                className="btn btn-primary"
              >
                {processInboxItem.isPending ? 'Processing...' : 'Process'}
              </button>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
}
