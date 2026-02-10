import React, { useState } from 'react';
import toast from 'react-hot-toast';
import { Modal } from '@/components/common/Modal';
import { useCreateTask } from '@/hooks/useTasks';
import { useContexts } from '@/hooks/useContexts';
import { Loader2 } from 'lucide-react';

interface CreateTaskModalProps {
  isOpen: boolean;
  onClose: () => void;
  projectId: number;
}

export function CreateTaskModal({ isOpen, onClose, projectId }: CreateTaskModalProps) {
  const [formData, setFormData] = useState<{
    title: string;
    description: string;
    status: 'pending' | 'in_progress' | 'completed' | 'waiting' | 'cancelled';
    priority: number;
    is_next_action: boolean;
    is_two_minute_task: boolean;
    task_type: 'action' | 'waiting_for' | 'someday_maybe' | undefined;
    context: string;
    energy_level: '' | 'high' | 'medium' | 'low';
    estimated_minutes: string;
    due_date: string;
  }>({
    title: '',
    description: '',
    status: 'pending',
    priority: 5,
    is_next_action: false,
    is_two_minute_task: false,
    task_type: 'action',
    context: '',
    energy_level: '',
    estimated_minutes: '',
    due_date: '',
  });

  const createTask = useCreateTask();
  const { data: contexts } = useContexts();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    // Validation
    if (!formData.title.trim()) {
      toast.error('Task title is required');
      return;
    }

    createTask.mutate(
      {
        project_id: projectId,
        title: formData.title.trim(),
        description: formData.description.trim() || undefined,
        status: formData.status,
        priority: formData.priority,
        is_next_action: formData.is_next_action,
        is_two_minute_task: formData.is_two_minute_task,
        is_unstuck_task: false,
        task_type: formData.task_type || undefined,
        context: formData.context.trim() || undefined,
        energy_level: formData.energy_level || undefined,
        estimated_minutes: formData.estimated_minutes
          ? parseInt(formData.estimated_minutes, 10)
          : undefined,
        due_date: formData.due_date || undefined,
      },
      {
        onSuccess: () => {
          toast.success('Task created successfully!');
          // Reset form
          setFormData({
            title: '',
            description: '',
            status: 'pending',
            priority: 5,
            is_next_action: false,
            is_two_minute_task: false,
            task_type: 'action',
            context: '',
            energy_level: '',
            estimated_minutes: '',
            due_date: '',
          });
          onClose();
        },
        onError: (error) => {
          console.error('Failed to create task:', error);
          toast.error('Failed to create task. Please try again.');
        },
      }
    );
  };

  const handleClose = () => {
    if (!createTask.isPending) {
      onClose();
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={handleClose} title="Create New Task" size="lg">
      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Title */}
        <div>
          <label htmlFor="title" className="label">
            Task Title <span className="text-red-500">*</span>
          </label>
          <input
            id="title"
            type="text"
            className="input"
            value={formData.title}
            onChange={(e) => setFormData({ ...formData, title: e.target.value })}
            placeholder="Enter task title"
            disabled={createTask.isPending}
            required
          />
        </div>

        {/* Description */}
        <div>
          <label htmlFor="description" className="label">
            Description
          </label>
          <textarea
            id="description"
            className="input"
            rows={3}
            value={formData.description}
            onChange={(e) => setFormData({ ...formData, description: e.target.value })}
            placeholder="Enter task description (optional)"
            disabled={createTask.isPending}
          />
        </div>

        {/* Status, Priority, Task Type Row */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Status */}
          <div>
            <label htmlFor="status" className="label">
              Status
            </label>
            <select
              id="status"
              className="input"
              value={formData.status}
              onChange={(e) =>
                setFormData({
                  ...formData,
                  status: e.target.value as
                    | 'pending'
                    | 'in_progress'
                    | 'completed'
                    | 'waiting'
                    | 'cancelled',
                })
              }
              disabled={createTask.isPending}
            >
              <option value="pending">Pending</option>
              <option value="in_progress">In Progress</option>
              <option value="waiting">Waiting</option>
              <option value="completed">Completed</option>
              <option value="cancelled">Cancelled</option>
            </select>
          </div>

          {/* Priority */}
          <div>
            <label htmlFor="priority" className="label">
              Priority (1-10)
            </label>
            <input
              id="priority"
              type="number"
              min="1"
              max="10"
              className="input"
              value={formData.priority}
              onChange={(e) =>
                setFormData({ ...formData, priority: parseInt(e.target.value, 10) })
              }
              disabled={createTask.isPending}
            />
          </div>

          {/* Task Type */}
          <div>
            <label htmlFor="task_type" className="label">
              Task Type
            </label>
            <select
              id="task_type"
              className="input"
              value={formData.task_type}
              onChange={(e) =>
                setFormData({
                  ...formData,
                  task_type: e.target.value as 'action' | 'waiting_for' | 'someday_maybe',
                })
              }
              disabled={createTask.isPending}
            >
              <option value="action">Action</option>
              <option value="waiting_for">Waiting For</option>
              <option value="someday_maybe">Someday/Maybe</option>
            </select>
          </div>
        </div>

        {/* Context, Energy Level, Estimated Time Row */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Context */}
          <div>
            <label htmlFor="context" className="label">
              Context
            </label>
            <select
              id="context"
              className="input"
              value={formData.context}
              onChange={(e) => setFormData({ ...formData, context: e.target.value })}
              disabled={createTask.isPending}
            >
              <option value="">No Context</option>
              {contexts?.map(ctx => (
                <option key={ctx.id} value={ctx.name}>
                  {ctx.name.charAt(0).toUpperCase() + ctx.name.slice(1)}
                </option>
              ))}
            </select>
          </div>

          {/* Energy Level */}
          <div>
            <label htmlFor="energy_level" className="label">
              Energy Level
            </label>
            <select
              id="energy_level"
              className="input"
              value={formData.energy_level}
              onChange={(e) =>
                setFormData({
                  ...formData,
                  energy_level: e.target.value as '' | 'high' | 'medium' | 'low',
                })
              }
              disabled={createTask.isPending}
            >
              <option value="">Not specified</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
            </select>
          </div>

          {/* Estimated Minutes */}
          <div>
            <label htmlFor="estimated_minutes" className="label">
              Est. Time (min)
            </label>
            <input
              id="estimated_minutes"
              type="number"
              min="1"
              className="input"
              value={formData.estimated_minutes}
              onChange={(e) =>
                setFormData({ ...formData, estimated_minutes: e.target.value })
              }
              placeholder="e.g., 30"
              disabled={createTask.isPending}
            />
          </div>
        </div>

        {/* Due Date */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label htmlFor="due_date" className="label">
              Due Date
            </label>
            <input
              id="due_date"
              type="date"
              className="input"
              value={formData.due_date}
              onChange={(e) => setFormData({ ...formData, due_date: e.target.value })}
              disabled={createTask.isPending}
            />
          </div>
        </div>

        {/* Checkboxes */}
        <div className="space-y-2">
          <div className="flex items-center">
            <input
              id="is_next_action"
              type="checkbox"
              className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 dark:border-gray-600 rounded"
              checked={formData.is_next_action}
              onChange={(e) =>
                setFormData({ ...formData, is_next_action: e.target.checked })
              }
              disabled={createTask.isPending}
            />
            <label htmlFor="is_next_action" className="ml-2 text-sm text-gray-700 dark:text-gray-300">
              Mark as Next Action
            </label>
          </div>
          <div className="flex items-center">
            <input
              id="is_two_minute_task"
              type="checkbox"
              className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 dark:border-gray-600 rounded"
              checked={formData.is_two_minute_task}
              onChange={(e) =>
                setFormData({ ...formData, is_two_minute_task: e.target.checked })
              }
              disabled={createTask.isPending}
            />
            <label htmlFor="is_two_minute_task" className="ml-2 text-sm text-gray-700 dark:text-gray-300">
              2-Minute Task (Quick Win)
            </label>
          </div>
        </div>

        {/* Form Actions */}
        <div className="flex items-center justify-end gap-3 pt-4 border-t border-gray-200 dark:border-gray-700">
          <button
            type="button"
            onClick={handleClose}
            className="btn btn-secondary"
            disabled={createTask.isPending}
          >
            Cancel
          </button>
          <button
            type="submit"
            className="btn btn-primary"
            disabled={createTask.isPending || !formData.title.trim()}
          >
            {createTask.isPending ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin mr-2" />
                Creating...
              </>
            ) : (
              'Create Task'
            )}
          </button>
        </div>
      </form>
    </Modal>
  );
}
