import React, { useState, useEffect } from 'react';
import toast from 'react-hot-toast';
import { Modal } from '@/components/common/Modal';
import { useCreateGoal, useUpdateGoal } from '@/hooks/useGoals';
import { Goal, GoalTimeframe, GoalStatus } from '@/types';
import { Loader2 } from 'lucide-react';
import { formatDateForApi } from '@/utils/date';

interface GoalModalProps {
  isOpen: boolean;
  onClose: () => void;
  goal?: Goal | null;
}

export function GoalModal({ isOpen, onClose, goal }: GoalModalProps) {
  const isEditMode = !!goal;
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    timeframe: '' as GoalTimeframe | '',
    target_date: '',
    status: 'active' as GoalStatus,
  });

  const createGoal = useCreateGoal();
  const updateGoal = useUpdateGoal();

  useEffect(() => {
    if (isOpen) {
      if (goal) {
        setFormData({
          title: goal.title,
          description: goal.description || '',
          timeframe: goal.timeframe || '',
          target_date: goal.target_date || '',
          status: goal.status,
        });
      } else {
        setFormData({
          title: '',
          description: '',
          timeframe: '',
          target_date: '',
          status: 'active',
        });
      }
    }
  }, [isOpen, goal]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (!formData.title.trim()) {
      toast.error('Goal title is required');
      return;
    }

    const goalData: Partial<Goal> = {
      title: formData.title.trim(),
      description: formData.description.trim() || undefined,
      timeframe: (formData.timeframe || undefined) as GoalTimeframe | undefined,
      target_date: formatDateForApi(formData.target_date),
      status: formData.status,
    };

    if (isEditMode && goal) {
      updateGoal.mutate(
        { id: goal.id, goal: goalData },
        {
          onSuccess: () => {
            toast.success('Goal updated');
            onClose();
          },
          onError: () => toast.error('Failed to update goal'),
        }
      );
    } else {
      createGoal.mutate(goalData, {
        onSuccess: () => {
          toast.success('Goal created');
          onClose();
        },
        onError: () => toast.error('Failed to create goal'),
      });
    }
  };

  const handleClose = () => {
    if (!createGoal.isPending && !updateGoal.isPending) {
      onClose();
    }
  };

  const isPending = createGoal.isPending || updateGoal.isPending;

  return (
    <Modal
      isOpen={isOpen}
      onClose={handleClose}
      title={isEditMode ? 'Edit Goal' : 'Create New Goal'}
      size="md"
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="goal-title" className="label">
            Title <span className="text-red-500">*</span>
          </label>
          <input
            id="goal-title"
            type="text"
            className="input"
            value={formData.title}
            onChange={(e) => setFormData({ ...formData, title: e.target.value })}
            placeholder="What do you want to achieve?"
            disabled={isPending}
            required
            maxLength={500}
          />
        </div>

        <div>
          <label htmlFor="goal-description" className="label">
            Description
          </label>
          <textarea
            id="goal-description"
            className="input"
            value={formData.description}
            onChange={(e) => setFormData({ ...formData, description: e.target.value })}
            placeholder="Why is this goal important? What does success look like?"
            disabled={isPending}
            rows={3}
          />
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label htmlFor="goal-timeframe" className="label">
              Timeframe
            </label>
            <select
              id="goal-timeframe"
              className="input"
              value={formData.timeframe}
              onChange={(e) =>
                setFormData({ ...formData, timeframe: e.target.value as GoalTimeframe | '' })
              }
              disabled={isPending}
            >
              <option value="">Not specified</option>
              <option value="1_year">1 Year</option>
              <option value="2_year">2 Year</option>
              <option value="3_year">3 Year</option>
            </select>
          </div>

          <div>
            <label htmlFor="goal-target-date" className="label">
              Target Date
            </label>
            <input
              id="goal-target-date"
              type="date"
              className="input"
              value={formData.target_date}
              onChange={(e) => setFormData({ ...formData, target_date: e.target.value })}
              disabled={isPending}
            />
          </div>
        </div>

        {isEditMode && (
          <div>
            <label htmlFor="goal-status" className="label">
              Status
            </label>
            <select
              id="goal-status"
              className="input"
              value={formData.status}
              onChange={(e) =>
                setFormData({ ...formData, status: e.target.value as GoalStatus })
              }
              disabled={isPending}
            >
              <option value="active">Active</option>
              <option value="achieved">Achieved</option>
              <option value="deferred">Deferred</option>
              <option value="abandoned">Abandoned</option>
            </select>
          </div>
        )}

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
            {isEditMode ? 'Update Goal' : 'Create Goal'}
          </button>
        </div>
      </form>
    </Modal>
  );
}
