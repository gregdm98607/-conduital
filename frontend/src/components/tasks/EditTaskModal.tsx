import React, { useState, useEffect } from 'react';
import toast from 'react-hot-toast';
import { Modal } from '@/components/common/Modal';
import { useUpdateTask } from '@/hooks/useTasks';
import { useContexts } from '@/hooks/useContexts';
import { Task, UrgencyZone } from '@/types';
import { Loader2 } from 'lucide-react';
import { formatDateForApi } from '@/utils/date';

interface EditTaskModalProps {
  isOpen: boolean;
  onClose: () => void;
  task: Task;
}

export function EditTaskModal({ isOpen, onClose, task }: EditTaskModalProps) {
  const [formData, setFormData] = useState({
    title: task.title,
    description: task.description || '',
    status: task.status,
    priority: task.priority,
    is_next_action: task.is_next_action,
    is_two_minute_task: task.is_two_minute_task,
    task_type: task.task_type || 'action',
    context: task.context || '',
    energy_level: task.energy_level || ('' as '' | 'high' | 'medium' | 'low'),
    urgency_zone: task.urgency_zone || ('opportunity_now' as UrgencyZone),
    estimated_minutes: task.estimated_minutes?.toString() || '',
    due_date: task.due_date ? task.due_date.split('T')[0] : '',
    defer_until: task.defer_until ? task.defer_until.split('T')[0] : '',
  });

  const updateTask = useUpdateTask();
  const { data: contexts } = useContexts();

  // Reset form data when task changes
  useEffect(() => {
    setFormData({
      title: task.title,
      description: task.description || '',
      status: task.status,
      priority: task.priority,
      is_next_action: task.is_next_action,
      is_two_minute_task: task.is_two_minute_task,
      task_type: task.task_type || 'action',
      context: task.context || '',
      energy_level: task.energy_level || '',
      urgency_zone: task.urgency_zone || 'opportunity_now',
      estimated_minutes: task.estimated_minutes?.toString() || '',
      due_date: task.due_date ? task.due_date.split('T')[0] : '',
      defer_until: task.defer_until ? task.defer_until.split('T')[0] : '',
    });
  }, [task]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    // Validation
    if (!formData.title.trim()) {
      toast.error('Task title is required');
      return;
    }

    updateTask.mutate(
      {
        id: task.id,
        task: {
          title: formData.title.trim(),
          description: formData.description.trim() || undefined,
          status: formData.status,
          priority: formData.priority,
          is_next_action: formData.is_next_action,
          is_two_minute_task: formData.is_two_minute_task,
          task_type: formData.task_type || undefined,
          urgency_zone: formData.urgency_zone || undefined,
          context: formData.context.trim() || undefined,
          energy_level: formData.energy_level || undefined,
          estimated_minutes: formData.estimated_minutes
            ? parseInt(formData.estimated_minutes, 10)
            : undefined,
          due_date: formatDateForApi(formData.due_date),
          defer_until: formatDateForApi(formData.defer_until),
        },
      },
      {
        onSuccess: () => {
          toast.success('Task updated successfully!');
          onClose();
        },
        onError: (error) => {
          console.error('Failed to update task:', error);
          toast.error('Failed to update task. Please try again.');
        },
      }
    );
  };

  const handleClose = () => {
    if (!updateTask.isPending) {
      onClose();
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={handleClose} title="Edit Task" size="lg">
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
            disabled={updateTask.isPending}
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
            disabled={updateTask.isPending}
          />
        </div>

        {/* Status, Priority, Task Type, Urgency Zone Row */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
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
              disabled={updateTask.isPending}
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
              disabled={updateTask.isPending}
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
              disabled={updateTask.isPending}
            >
              <option value="action">Action</option>
              <option value="waiting_for">Waiting For</option>
              <option value="someday_maybe">Someday/Maybe</option>
            </select>
          </div>

          {/* Urgency Zone (MYN) */}
          <div>
            <label htmlFor="urgency_zone" className="label">
              Urgency Zone
            </label>
            <select
              id="urgency_zone"
              className="input"
              value={formData.urgency_zone}
              onChange={(e) =>
                setFormData({
                  ...formData,
                  urgency_zone: e.target.value as UrgencyZone,
                })
              }
              disabled={updateTask.isPending}
            >
              <option value="critical_now">Critical Now</option>
              <option value="opportunity_now">Opportunity Now</option>
              <option value="over_the_horizon">Over the Horizon</option>
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
              disabled={updateTask.isPending}
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
              disabled={updateTask.isPending}
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
              disabled={updateTask.isPending}
            />
          </div>
        </div>

        {/* Due Date and Start Date (Defer Until) */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label htmlFor="defer_until" className="label">
              Start Date (Defer Until)
            </label>
            <input
              id="defer_until"
              type="date"
              className="input"
              value={formData.defer_until}
              onChange={(e) => {
                const newDeferUntil = e.target.value;
                // Auto-set to Over the Horizon if deferring to future
                const today = new Date().toISOString().split('T')[0];
                const shouldAutoSetZone = newDeferUntil && newDeferUntil > today;
                setFormData({
                  ...formData,
                  defer_until: newDeferUntil,
                  // Auto-assign Over the Horizon for future deferred tasks
                  urgency_zone: shouldAutoSetZone ? 'over_the_horizon' : formData.urgency_zone,
                });
              }}
              disabled={updateTask.isPending}
            />
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
              Task hidden from daily views until this date
            </p>
          </div>
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
              disabled={updateTask.isPending}
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
              disabled={updateTask.isPending}
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
              disabled={updateTask.isPending}
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
            disabled={updateTask.isPending}
          >
            Cancel
          </button>
          <button
            type="submit"
            className="btn btn-primary"
            disabled={updateTask.isPending || !formData.title.trim()}
          >
            {updateTask.isPending ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin mr-2" />
                Saving...
              </>
            ) : (
              'Save Changes'
            )}
          </button>
        </div>
      </form>
    </Modal>
  );
}
