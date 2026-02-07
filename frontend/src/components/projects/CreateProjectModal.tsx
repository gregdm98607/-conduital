import React, { useState, useEffect } from 'react';
import toast from 'react-hot-toast';
import { Modal } from '@/components/common/Modal';
import { useCreateProject } from '@/hooks/useProjects';
import { api } from '@/services/api';
import { Area } from '@/types';
import { Loader2 } from 'lucide-react';

interface CreateProjectModalProps {
  isOpen: boolean;
  onClose: () => void;
  defaultAreaId?: number;
}

export function CreateProjectModal({ isOpen, onClose, defaultAreaId }: CreateProjectModalProps) {
  const [formData, setFormData] = useState<{
    title: string;
    description: string;
    outcome_statement: string;
    status: 'active' | 'completed' | 'on_hold' | 'archived' | 'someday_maybe';
    priority: number;
    area_id: number | undefined;
    target_completion_date: string;
    next_review_date: string;
  }>({
    title: '',
    description: '',
    outcome_statement: '',
    status: 'active',
    priority: 5,
    area_id: defaultAreaId,
    target_completion_date: '',
    next_review_date: '',
  });

  // Update area_id when defaultAreaId changes (e.g., opening from different area cards)
  useEffect(() => {
    if (isOpen && defaultAreaId !== undefined) {
      setFormData(prev => ({ ...prev, area_id: defaultAreaId }));
    }
  }, [isOpen, defaultAreaId]);

  const [areas, setAreas] = useState<Area[]>([]);
  const [loadingAreas, setLoadingAreas] = useState(false);
  const createProject = useCreateProject();

  // Load areas for dropdown
  useEffect(() => {
    if (isOpen) {
      setLoadingAreas(true);
      api
        .getAreas()
        .then(setAreas)
        .catch((err) => console.error('Failed to load areas:', err))
        .finally(() => setLoadingAreas(false));
    }
  }, [isOpen]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    // Validation
    if (!formData.title.trim()) {
      toast.error('Project title is required');
      return;
    }

    createProject.mutate(
      {
        ...formData,
        title: formData.title.trim(),
        description: formData.description.trim() || undefined,
        outcome_statement: formData.outcome_statement.trim() || undefined,
        target_completion_date: formData.target_completion_date || undefined,
        next_review_date: formData.next_review_date || undefined,
        area_id: formData.area_id || undefined,
      },
      {
        onSuccess: () => {
          toast.success('Project created successfully!');
          // Reset form
          setFormData({
            title: '',
            description: '',
            outcome_statement: '',
            status: 'active',
            priority: 5,
            area_id: undefined,
            target_completion_date: '',
            next_review_date: '',
          });
          onClose();
        },
        onError: (error) => {
          console.error('Failed to create project:', error);
          toast.error('Failed to create project. Please try again.');
        },
      }
    );
  };

  const handleClose = () => {
    if (!createProject.isPending) {
      onClose();
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={handleClose} title="Create New Project" size="md">
      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Title */}
        <div>
          <label htmlFor="title" className="label">
            Project Title <span className="text-red-500">*</span>
          </label>
          <input
            id="title"
            type="text"
            className="input"
            value={formData.title}
            onChange={(e) => setFormData({ ...formData, title: e.target.value })}
            placeholder="Enter project title"
            disabled={createProject.isPending}
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
            placeholder="Enter project description (optional)"
            disabled={createProject.isPending}
          />
        </div>

        {/* Outcome Statement */}
        <div>
          <label htmlFor="outcome_statement" className="label">
            Outcome Statement
          </label>
          <textarea
            id="outcome_statement"
            className="input"
            rows={2}
            value={formData.outcome_statement}
            onChange={(e) => setFormData({ ...formData, outcome_statement: e.target.value })}
            placeholder="What does successful completion look like? (e.g., 'Website live with all pages, mobile-first, under 2s load time')"
            disabled={createProject.isPending}
          />
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">GTD: Define what "done" looks like</p>
        </div>

        {/* Status and Priority Row */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
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
                  status: e.target.value as 'active' | 'completed' | 'on_hold' | 'archived' | 'someday_maybe',
                })
              }
              disabled={createProject.isPending}
            >
              <option value="active">Active</option>
              <option value="on_hold">On Hold</option>
              <option value="someday_maybe">Someday/Maybe</option>
              <option value="completed">Completed</option>
              <option value="archived">Archived</option>
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
              disabled={createProject.isPending}
            />
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">Higher numbers = higher priority</p>
          </div>
        </div>

        {/* Area and Target Date Row */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Area */}
          <div>
            <label htmlFor="area" className="label">
              Area
            </label>
            <select
              id="area"
              className="input"
              value={formData.area_id ?? ''}
              onChange={(e) =>
                setFormData({
                  ...formData,
                  area_id: e.target.value ? parseInt(e.target.value, 10) : undefined,
                })
              }
              disabled={createProject.isPending || loadingAreas}
            >
              <option value="">No Area</option>
              {areas.map((area) => (
                <option key={area.id} value={area.id}>
                  {area.title}
                </option>
              ))}
            </select>
            {loadingAreas && <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">Loading areas...</p>}
          </div>

          {/* Target Completion Date */}
          <div>
            <label htmlFor="target_date" className="label">
              Target Completion Date
            </label>
            <input
              id="target_date"
              type="date"
              className="input"
              value={formData.target_completion_date}
              onChange={(e) =>
                setFormData({ ...formData, target_completion_date: e.target.value })
              }
              disabled={createProject.isPending}
            />
          </div>
        </div>

        {/* Next Review Date */}
        <div>
          <label htmlFor="next_review_date" className="label">
            Next Review Date
          </label>
          <input
            id="next_review_date"
            type="date"
            className="input"
            value={formData.next_review_date}
            onChange={(e) =>
              setFormData({ ...formData, next_review_date: e.target.value })
            }
            disabled={createProject.isPending}
          />
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">GTD: When should this project be reviewed?</p>
        </div>

        {/* Form Actions */}
        <div className="flex items-center justify-end gap-3 pt-4 border-t border-gray-200 dark:border-gray-700">
          <button
            type="button"
            onClick={handleClose}
            className="btn btn-secondary"
            disabled={createProject.isPending}
          >
            Cancel
          </button>
          <button
            type="submit"
            className="btn btn-primary"
            disabled={createProject.isPending || !formData.title.trim()}
          >
            {createProject.isPending ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin mr-2" />
                Creating...
              </>
            ) : (
              'Create Project'
            )}
          </button>
        </div>
      </form>
    </Modal>
  );
}
