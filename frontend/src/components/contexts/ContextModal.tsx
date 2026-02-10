import React, { useState, useEffect } from 'react';
import toast from 'react-hot-toast';
import { Modal } from '@/components/common/Modal';
import { useCreateContext, useUpdateContext } from '@/hooks/useContexts';
import { Context, ContextType } from '@/types';
import { Loader2 } from 'lucide-react';

interface ContextModalProps {
  isOpen: boolean;
  onClose: () => void;
  context?: Context | null;
}

export function ContextModal({ isOpen, onClose, context }: ContextModalProps) {
  const isEditMode = !!context;
  const [formData, setFormData] = useState({
    name: '',
    context_type: '' as ContextType | '',
    description: '',
    icon: '',
  });

  const createContext = useCreateContext();
  const updateContext = useUpdateContext();

  useEffect(() => {
    if (isOpen) {
      if (context) {
        setFormData({
          name: context.name,
          context_type: context.context_type || '',
          description: context.description || '',
          icon: context.icon || '',
        });
      } else {
        setFormData({
          name: '',
          context_type: '',
          description: '',
          icon: '',
        });
      }
    }
  }, [isOpen, context]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (!formData.name.trim()) {
      toast.error('Context name is required');
      return;
    }

    const ctxData: Partial<Context> = {
      name: formData.name.trim(),
      context_type: (formData.context_type || undefined) as ContextType | undefined,
      description: formData.description.trim() || undefined,
      icon: formData.icon.trim() || undefined,
    };

    if (isEditMode && context) {
      updateContext.mutate(
        { id: context.id, ctx: ctxData },
        {
          onSuccess: () => {
            toast.success('Context updated');
            onClose();
          },
          onError: () => toast.error('Failed to update context'),
        }
      );
    } else {
      createContext.mutate(ctxData, {
        onSuccess: () => {
          toast.success('Context created');
          onClose();
        },
        onError: () => toast.error('Failed to create context'),
      });
    }
  };

  const handleClose = () => {
    if (!createContext.isPending && !updateContext.isPending) {
      onClose();
    }
  };

  const isPending = createContext.isPending || updateContext.isPending;

  return (
    <Modal
      isOpen={isOpen}
      onClose={handleClose}
      title={isEditMode ? 'Edit Context' : 'Create New Context'}
      size="md"
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="sm:col-span-2">
            <label htmlFor="context-name" className="label">
              Name <span className="text-red-500">*</span>
            </label>
            <input
              id="context-name"
              type="text"
              className="input"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              placeholder="@home, @computer, @errands..."
              disabled={isPending}
              required
              maxLength={100}
            />
          </div>

          <div>
            <label htmlFor="context-icon" className="label">
              Icon
            </label>
            <input
              id="context-icon"
              type="text"
              className="input"
              value={formData.icon}
              onChange={(e) => setFormData({ ...formData, icon: e.target.value })}
              placeholder="e.g. emoji"
              disabled={isPending}
              maxLength={50}
            />
          </div>
        </div>

        <div>
          <label htmlFor="context-type" className="label">
            Type
          </label>
          <select
            id="context-type"
            className="input"
            value={formData.context_type}
            onChange={(e) =>
              setFormData({ ...formData, context_type: e.target.value as ContextType | '' })
            }
            disabled={isPending}
          >
            <option value="">Not specified</option>
            <option value="location">Location</option>
            <option value="energy">Energy Level</option>
            <option value="work_type">Work Type</option>
            <option value="time">Time of Day</option>
            <option value="tool">Tool Required</option>
          </select>
        </div>

        <div>
          <label htmlFor="context-description" className="label">
            Description
          </label>
          <textarea
            id="context-description"
            className="input"
            value={formData.description}
            onChange={(e) => setFormData({ ...formData, description: e.target.value })}
            placeholder="When should this context be used?"
            disabled={isPending}
            rows={2}
          />
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
            {isEditMode ? 'Update Context' : 'Create Context'}
          </button>
        </div>
      </form>
    </Modal>
  );
}
