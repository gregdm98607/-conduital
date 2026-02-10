import React, { useState, useEffect } from 'react';
import toast from 'react-hot-toast';
import { Modal } from '@/components/common/Modal';
import { useCreateVision, useUpdateVision } from '@/hooks/useVisions';
import { Vision, VisionTimeframe } from '@/types';
import { Loader2 } from 'lucide-react';

interface VisionModalProps {
  isOpen: boolean;
  onClose: () => void;
  vision?: Vision | null;
}

export function VisionModal({ isOpen, onClose, vision }: VisionModalProps) {
  const isEditMode = !!vision;
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    timeframe: '' as VisionTimeframe | '',
  });

  const createVision = useCreateVision();
  const updateVision = useUpdateVision();

  useEffect(() => {
    if (isOpen) {
      if (vision) {
        setFormData({
          title: vision.title,
          description: vision.description || '',
          timeframe: vision.timeframe || '',
        });
      } else {
        setFormData({
          title: '',
          description: '',
          timeframe: '',
        });
      }
    }
  }, [isOpen, vision]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (!formData.title.trim()) {
      toast.error('Vision title is required');
      return;
    }

    const visionData: Partial<Vision> = {
      title: formData.title.trim(),
      description: formData.description.trim() || undefined,
      timeframe: (formData.timeframe || undefined) as VisionTimeframe | undefined,
    };

    if (isEditMode && vision) {
      updateVision.mutate(
        { id: vision.id, vision: visionData },
        {
          onSuccess: () => {
            toast.success('Vision updated');
            onClose();
          },
          onError: () => toast.error('Failed to update vision'),
        }
      );
    } else {
      createVision.mutate(visionData, {
        onSuccess: () => {
          toast.success('Vision created');
          onClose();
        },
        onError: () => toast.error('Failed to create vision'),
      });
    }
  };

  const handleClose = () => {
    if (!createVision.isPending && !updateVision.isPending) {
      onClose();
    }
  };

  const isPending = createVision.isPending || updateVision.isPending;

  return (
    <Modal
      isOpen={isOpen}
      onClose={handleClose}
      title={isEditMode ? 'Edit Vision' : 'Create New Vision'}
      size="md"
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="vision-title" className="label">
            Title <span className="text-red-500">*</span>
          </label>
          <input
            id="vision-title"
            type="text"
            className="input"
            value={formData.title}
            onChange={(e) => setFormData({ ...formData, title: e.target.value })}
            placeholder="What is your long-term vision?"
            disabled={isPending}
            required
            maxLength={500}
          />
        </div>

        <div>
          <label htmlFor="vision-description" className="label">
            Description
          </label>
          <textarea
            id="vision-description"
            className="input"
            value={formData.description}
            onChange={(e) => setFormData({ ...formData, description: e.target.value })}
            placeholder="Describe your vision in detail. What does the future look like?"
            disabled={isPending}
            rows={4}
          />
        </div>

        <div>
          <label htmlFor="vision-timeframe" className="label">
            Timeframe
          </label>
          <select
            id="vision-timeframe"
            className="input"
            value={formData.timeframe}
            onChange={(e) =>
              setFormData({ ...formData, timeframe: e.target.value as VisionTimeframe | '' })
            }
            disabled={isPending}
          >
            <option value="">Not specified</option>
            <option value="3_year">3 Year Vision</option>
            <option value="5_year">5 Year Vision</option>
            <option value="life_purpose">Life Purpose</option>
          </select>
        </div>

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
            {isEditMode ? 'Update Vision' : 'Create Vision'}
          </button>
        </div>
      </form>
    </Modal>
  );
}
