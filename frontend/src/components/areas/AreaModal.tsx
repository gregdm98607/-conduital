import React, { useState, useEffect } from 'react';
import toast from 'react-hot-toast';
import { Modal } from '@/components/common/Modal';
import { useCreateArea, useUpdateArea } from '@/hooks/useAreas';
import { Area } from '@/types';
import { Loader2 } from 'lucide-react';

interface AreaModalProps {
  isOpen: boolean;
  onClose: () => void;
  area?: Area | null;
}

export function AreaModal({ isOpen, onClose, area }: AreaModalProps) {
  const isEditMode = !!area;
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    folder_path: '',
    standard_of_excellence: '',
    review_frequency: 'weekly' as 'daily' | 'weekly' | 'monthly',
  });

  const createArea = useCreateArea();
  const updateArea = useUpdateArea();

  // Reset form when modal opens or area changes
  useEffect(() => {
    if (isOpen) {
      if (area) {
        setFormData({
          title: area.title,
          description: area.description || '',
          folder_path: area.folder_path || '',
          standard_of_excellence: area.standard_of_excellence || '',
          review_frequency: area.review_frequency,
        });
      } else {
        setFormData({
          title: '',
          description: '',
          folder_path: '',
          standard_of_excellence: '',
          review_frequency: 'weekly',
        });
      }
    }
  }, [isOpen, area]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    // Validation
    if (!formData.title.trim()) {
      toast.error('Area title is required');
      return;
    }

    const areaData = {
      ...formData,
      title: formData.title.trim(),
      description: formData.description.trim() || undefined,
      folder_path: formData.folder_path.trim() || undefined,
      standard_of_excellence: formData.standard_of_excellence.trim() || undefined,
    };

    if (isEditMode && area) {
      updateArea.mutate(
        { id: area.id, area: areaData },
        {
          onSuccess: () => {
            toast.success('Area updated successfully!');
            onClose();
          },
          onError: (error) => {
            console.error('Failed to update area:', error);
            toast.error('Failed to update area. Please try again.');
          },
        }
      );
    } else {
      createArea.mutate(areaData, {
        onSuccess: () => {
          toast.success('Area created successfully!');
          onClose();
        },
        onError: (error) => {
          console.error('Failed to create area:', error);
          toast.error('Failed to create area. Please try again.');
        },
      });
    }
  };

  const handleClose = () => {
    if (!createArea.isPending && !updateArea.isPending) {
      onClose();
    }
  };

  const isPending = createArea.isPending || updateArea.isPending;

  return (
    <Modal
      isOpen={isOpen}
      onClose={handleClose}
      title={isEditMode ? 'Edit Area' : 'Create New Area'}
      size="md"
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Title */}
        <div>
          <label htmlFor="title" className="label">
            Title <span className="text-red-500">*</span>
          </label>
          <input
            id="title"
            type="text"
            className="input"
            value={formData.title}
            onChange={(e) => setFormData({ ...formData, title: e.target.value })}
            placeholder="Enter area title"
            disabled={isPending}
            required
            maxLength={200}
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
            value={formData.description}
            onChange={(e) => setFormData({ ...formData, description: e.target.value })}
            placeholder="Enter area description"
            disabled={isPending}
            rows={3}
          />
        </div>

        {/* Folder Path */}
        <div>
          <label htmlFor="folder_path" className="label">
            Folder Path
          </label>
          <input
            id="folder_path"
            type="text"
            className="input"
            value={formData.folder_path}
            onChange={(e) => setFormData({ ...formData, folder_path: e.target.value })}
            placeholder="20_Areas/20.05_AI_Systems"
            disabled={isPending}
          />
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
            Optional path to the area folder in your file system
          </p>
        </div>

        {/* Standard of Excellence */}
        <div>
          <label htmlFor="standard_of_excellence" className="label">
            Standard of Excellence
          </label>
          <textarea
            id="standard_of_excellence"
            className="input"
            value={formData.standard_of_excellence}
            onChange={(e) => setFormData({ ...formData, standard_of_excellence: e.target.value })}
            placeholder="What does 'good' look like for this area?"
            disabled={isPending}
            rows={3}
          />
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
            Define what success looks like for this area of responsibility
          </p>
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
              setFormData({
                ...formData,
                review_frequency: e.target.value as 'daily' | 'weekly' | 'monthly',
              })
            }
            disabled={isPending}
          >
            <option value="daily">Daily</option>
            <option value="weekly">Weekly</option>
            <option value="monthly">Monthly</option>
          </select>
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
            How often should this area be reviewed?
          </p>
        </div>

        {/* Actions */}
        <div className="flex justify-end gap-3 pt-4 border-t">
          <button
            type="button"
            onClick={handleClose}
            className="btn btn-secondary"
            disabled={isPending}
          >
            Cancel
          </button>
          <button
            type="submit"
            className="btn btn-primary flex items-center gap-2"
            disabled={isPending}
          >
            {isPending && <Loader2 className="w-4 h-4 animate-spin" />}
            {isEditMode ? 'Update Area' : 'Create Area'}
          </button>
        </div>
      </form>
    </Modal>
  );
}
