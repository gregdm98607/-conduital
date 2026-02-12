import React, { useState, useEffect } from 'react';
import toast from 'react-hot-toast';
import { Modal } from '@/components/common/Modal';
import { useUpdateProject } from '@/hooks/useProjects';
import { api } from '@/services/api';
import { Area, Project } from '@/types';
import { Loader2, ChevronDown, ChevronRight } from 'lucide-react';
import { formatDateForApi } from '@/utils/date';

interface EditProjectModalProps {
  isOpen: boolean;
  onClose: () => void;
  project: Project;
}

export function EditProjectModal({ isOpen, onClose, project }: EditProjectModalProps) {
  const [formData, setFormData] = useState({
    title: project.title,
    description: project.description || '',
    outcome_statement: project.outcome_statement || '',
    purpose: project.purpose || '',
    vision_statement: project.vision_statement || '',
    brainstorm_notes: project.brainstorm_notes || '',
    organizing_notes: project.organizing_notes || '',
    status: project.status,
    priority: project.priority,
    area_id: project.area_id,
    target_completion_date: project.target_completion_date
      ? project.target_completion_date.split('T')[0]
      : '',
    review_frequency: project.review_frequency || 'weekly' as 'daily' | 'weekly' | 'monthly',
  });
  const [showNPM, setShowNPM] = useState(false);

  const [areas, setAreas] = useState<Area[]>([]);
  const [loadingAreas, setLoadingAreas] = useState(false);
  const updateProject = useUpdateProject();

  // Reset form data when project changes
  useEffect(() => {
    setFormData({
      title: project.title,
      description: project.description || '',
      outcome_statement: project.outcome_statement || '',
      purpose: project.purpose || '',
      vision_statement: project.vision_statement || '',
      brainstorm_notes: project.brainstorm_notes || '',
      organizing_notes: project.organizing_notes || '',
      status: project.status,
      priority: project.priority,
      area_id: project.area_id,
      target_completion_date: project.target_completion_date
        ? project.target_completion_date.split('T')[0]
        : '',
      review_frequency: project.review_frequency || 'weekly' as 'daily' | 'weekly' | 'monthly',
    });
    // Auto-expand NPM section if any field has content
    setShowNPM(!!(project.purpose || project.vision_statement || project.brainstorm_notes || project.organizing_notes));
  }, [project]);

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

    updateProject.mutate(
      {
        id: project.id,
        project: {
          title: formData.title.trim(),
          description: formData.description.trim() || undefined,
          outcome_statement: formData.outcome_statement.trim() || undefined,
          purpose: formData.purpose.trim() || undefined,
          vision_statement: formData.vision_statement.trim() || undefined,
          brainstorm_notes: formData.brainstorm_notes.trim() || undefined,
          organizing_notes: formData.organizing_notes.trim() || undefined,
          status: formData.status,
          priority: formData.priority,
          area_id: formData.area_id || undefined,
          target_completion_date: formatDateForApi(formData.target_completion_date),
          review_frequency: formData.review_frequency,
        },
      },
      {
        onSuccess: () => {
          toast.success('Project updated successfully!');
          onClose();
        },
        onError: (error) => {
          console.error('Failed to update project:', error);
          toast.error('Failed to update project. Please try again.');
        },
      }
    );
  };

  const handleClose = () => {
    if (!updateProject.isPending) {
      onClose();
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={handleClose} title="Edit Project" size="md">
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
            disabled={updateProject.isPending}
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
            disabled={updateProject.isPending}
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
            disabled={updateProject.isPending}
          />
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">Define what "done" looks like</p>
        </div>

        {/* Natural Planning Model (collapsible) */}
        <div className="border border-gray-200 dark:border-gray-700 rounded-lg">
          <button
            type="button"
            onClick={() => setShowNPM(!showNPM)}
            className="w-full flex items-center gap-2 p-3 text-left text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800 rounded-lg"
          >
            {showNPM ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
            Natural Planning Model
            <span className="text-xs text-gray-400 font-normal">(structured planning)</span>
          </button>
          {showNPM && (
            <div className="px-3 pb-3 space-y-3">
              <div>
                <label htmlFor="purpose" className="label">Purpose</label>
                <textarea
                  id="purpose"
                  className="input"
                  rows={2}
                  value={formData.purpose}
                  onChange={(e) => setFormData({ ...formData, purpose: e.target.value })}
                  placeholder="Why are we doing this project? What's the motivation?"
                  disabled={updateProject.isPending}
                />
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">Step 1: The "why" behind this project</p>
              </div>
              <div>
                <label htmlFor="vision_statement" className="label">Vision</label>
                <textarea
                  id="vision_statement"
                  className="input"
                  rows={2}
                  value={formData.vision_statement}
                  onChange={(e) => setFormData({ ...formData, vision_statement: e.target.value })}
                  placeholder="What does wild success look like? Paint the picture."
                  disabled={updateProject.isPending}
                />
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">Step 2: The end result you're envisioning</p>
              </div>
              <div>
                <label htmlFor="brainstorm_notes" className="label">Brainstorming</label>
                <textarea
                  id="brainstorm_notes"
                  className="input"
                  rows={3}
                  value={formData.brainstorm_notes}
                  onChange={(e) => setFormData({ ...formData, brainstorm_notes: e.target.value })}
                  placeholder="Dump all ideas here. No judging, just capture."
                  disabled={updateProject.isPending}
                />
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">Step 3: Raw ideas, no judgment</p>
              </div>
              <div>
                <label htmlFor="organizing_notes" className="label">Organizing</label>
                <textarea
                  id="organizing_notes"
                  className="input"
                  rows={3}
                  value={formData.organizing_notes}
                  onChange={(e) => setFormData({ ...formData, organizing_notes: e.target.value })}
                  placeholder="How do the pieces fit together? Key milestones, sequences, categories."
                  disabled={updateProject.isPending}
                />
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">Step 4: Structure and sequence</p>
              </div>
            </div>
          )}
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
              disabled={updateProject.isPending}
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
              disabled={updateProject.isPending}
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
              disabled={updateProject.isPending || loadingAreas}
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
              disabled={updateProject.isPending}
            />
          </div>
        </div>

        {/* Review Frequency */}
        <div>
          <label htmlFor="review_frequency" className="label">
            Review Frequency
          </label>
          <select
            id="review_frequency"
            className="input"
            value={formData.review_frequency}
            onChange={(e) =>
              setFormData({ ...formData, review_frequency: e.target.value as 'daily' | 'weekly' | 'monthly' })
            }
            disabled={updateProject.isPending}
          >
            <option value="daily">Daily</option>
            <option value="weekly">Weekly</option>
            <option value="monthly">Monthly</option>
          </select>
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">How often should this project be reviewed?</p>
        </div>

        {/* Form Actions */}
        <div className="flex items-center justify-end gap-3 pt-4 border-t border-gray-200 dark:border-gray-700">
          <button
            type="button"
            onClick={handleClose}
            className="btn btn-secondary"
            disabled={updateProject.isPending}
          >
            Cancel
          </button>
          <button
            type="submit"
            className="btn btn-primary"
            disabled={updateProject.isPending || !formData.title.trim()}
          >
            {updateProject.isPending ? (
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
