/**
 * FeedbackWidget — F-001 In-App Feedback
 *
 * A persistent floating button in the sidebar footer that opens a compact
 * modal for sending bug reports, feature requests, or general feedback.
 * Feedback is stored locally in SQLite via POST /api/v1/feedback.
 *
 * UX decisions:
 * - Button lives in the sidebar footer (always accessible, no page disruption)
 * - Modal is sm size (compact — this is a quick capture, not a form)
 * - Category selector (Bug / Feature / General) + textarea
 * - Optional email field for users who want a reply
 * - Submit fires the API call, shows a toast, closes the modal
 * - No loading state shown > 500ms (local API is fast)
 */

import { useState, useRef } from 'react';
import { MessageSquarePlus, Bug, Lightbulb, MessageCircle, X } from 'lucide-react';
import toast from 'react-hot-toast';
import { api } from '@/services/api';

type Category = 'bug' | 'feature' | 'general';

interface CategoryOption {
  value: Category;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  description: string;
}

const CATEGORIES: CategoryOption[] = [
  {
    value: 'bug',
    label: 'Bug Report',
    icon: Bug,
    description: "Something isn't working",
  },
  {
    value: 'feature',
    label: 'Feature Request',
    icon: Lightbulb,
    description: 'An idea to make Conduital better',
  },
  {
    value: 'general',
    label: 'General',
    icon: MessageCircle,
    description: 'Anything else on your mind',
  },
];

export function FeedbackWidget() {
  const [open, setOpen] = useState(false);
  const [category, setCategory] = useState<Category>('general');
  const [message, setMessage] = useState('');
  const [email, setEmail] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const resetForm = () => {
    setCategory('general');
    setMessage('');
    setEmail('');
  };

  const handleOpen = () => {
    setOpen(true);
    // Focus textarea after render
    setTimeout(() => textareaRef.current?.focus(), 50);
  };

  const handleClose = () => {
    if (submitting) return;
    setOpen(false);
    resetForm();
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = message.trim();
    if (!trimmed) {
      toast.error('Please write a message before submitting.');
      textareaRef.current?.focus();
      return;
    }

    setSubmitting(true);
    try {
      await api.submitFeedback({
        category,
        message: trimmed,
        page: window.location.pathname,
        email: email.trim() || undefined,
      });
      toast.success('Thanks for your feedback!');
      setOpen(false);
      resetForm();
    } catch {
      toast.error('Could not submit feedback. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  const selectedCategory = CATEGORIES.find(c => c.value === category)!;
  const SelectedIcon = selectedCategory.icon;

  return (
    <>
      {/* Trigger button — sits in sidebar footer via Layout */}
      <button
        onClick={handleOpen}
        className="flex items-center gap-2 w-full px-3 py-2 rounded-lg text-gray-500 hover:text-gray-300 hover:bg-white/5 transition-all duration-150 text-sm"
        title="Send feedback"
        aria-label="Open feedback form"
      >
        <MessageSquarePlus className="w-[15px] h-[15px] shrink-0" />
        <span>Send Feedback</span>
      </button>

      {/* Modal */}
      {open && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center"
          role="presentation"
        >
          {/* Backdrop */}
          <div
            className="fixed inset-0 bg-black bg-opacity-60 transition-opacity"
            onClick={handleClose}
            aria-hidden="true"
          />

          {/* Dialog */}
          <div
            className="relative bg-gray-800 border border-gray-700 rounded-xl shadow-2xl w-full max-w-md mx-4"
            role="dialog"
            aria-modal="true"
            aria-labelledby="feedback-modal-title"
          >
            {/* Header */}
            <div className="flex items-center justify-between px-5 pt-5 pb-4 border-b border-gray-700">
              <div className="flex items-center gap-2.5">
                <div className="w-7 h-7 rounded-lg bg-primary-500/15 flex items-center justify-center">
                  <MessageSquarePlus className="w-4 h-4 text-primary-400" />
                </div>
                <h2
                  id="feedback-modal-title"
                  className="text-base font-semibold text-gray-100"
                >
                  Send Feedback
                </h2>
              </div>
              <button
                onClick={handleClose}
                disabled={submitting}
                className="p-1 rounded-md text-gray-500 hover:text-gray-300 hover:bg-white/5 transition-colors disabled:opacity-50"
                aria-label="Close feedback form"
              >
                <X className="w-4.5 h-4.5" />
              </button>
            </div>

            {/* Form */}
            <form onSubmit={handleSubmit} className="p-5 space-y-4">
              {/* Category selector */}
              <div>
                <label className="block text-xs font-medium text-gray-400 mb-2 uppercase tracking-wider">
                  Category
                </label>
                <div className="grid grid-cols-3 gap-2">
                  {CATEGORIES.map(cat => {
                    const Icon = cat.icon;
                    const active = category === cat.value;
                    return (
                      <button
                        key={cat.value}
                        type="button"
                        onClick={() => setCategory(cat.value)}
                        className={`flex flex-col items-center gap-1.5 py-2.5 px-2 rounded-lg border text-xs font-medium transition-all duration-150 ${
                          active
                            ? 'border-primary-500 bg-primary-500/10 text-primary-400'
                            : 'border-gray-700 bg-gray-900/50 text-gray-500 hover:border-gray-600 hover:text-gray-300'
                        }`}
                        aria-pressed={active}
                      >
                        <Icon className="w-4 h-4" />
                        <span>{cat.label.split(' ')[0]}</span>
                      </button>
                    );
                  })}
                </div>
                <p className="mt-1.5 text-[11px] text-gray-600 flex items-center gap-1">
                  <SelectedIcon className="w-3 h-3 shrink-0" />
                  {selectedCategory.description}
                </p>
              </div>

              {/* Message */}
              <div>
                <label
                  htmlFor="feedback-message"
                  className="block text-xs font-medium text-gray-400 mb-1.5 uppercase tracking-wider"
                >
                  Message <span className="text-red-500">*</span>
                </label>
                <textarea
                  id="feedback-message"
                  ref={textareaRef}
                  value={message}
                  onChange={e => setMessage(e.target.value)}
                  rows={4}
                  maxLength={2000}
                  placeholder={
                    category === 'bug'
                      ? 'Describe what happened and what you expected…'
                      : category === 'feature'
                        ? 'Describe the feature and the problem it would solve…'
                        : 'What's on your mind?'
                  }
                  className="w-full px-3 py-2.5 bg-gray-900 border border-gray-700 rounded-lg text-sm text-gray-200 placeholder-gray-600 resize-none focus:outline-none focus:ring-1 focus:ring-primary-500 focus:border-primary-500 transition-colors"
                  required
                  disabled={submitting}
                />
                <p className="mt-0.5 text-right text-[10px] text-gray-700">
                  {message.length}/2000
                </p>
              </div>

              {/* Optional email */}
              <div>
                <label
                  htmlFor="feedback-email"
                  className="block text-xs font-medium text-gray-400 mb-1.5 uppercase tracking-wider"
                >
                  Your email{' '}
                  <span className="normal-case font-normal text-gray-600">(optional — for replies)</span>
                </label>
                <input
                  id="feedback-email"
                  type="email"
                  value={email}
                  onChange={e => setEmail(e.target.value)}
                  placeholder="you@example.com"
                  maxLength={254}
                  className="w-full px-3 py-2 bg-gray-900 border border-gray-700 rounded-lg text-sm text-gray-200 placeholder-gray-600 focus:outline-none focus:ring-1 focus:ring-primary-500 focus:border-primary-500 transition-colors"
                  disabled={submitting}
                />
              </div>

              {/* Actions */}
              <div className="flex items-center justify-end gap-2 pt-1">
                <button
                  type="button"
                  onClick={handleClose}
                  disabled={submitting}
                  className="px-4 py-2 text-sm text-gray-400 hover:text-gray-200 transition-colors disabled:opacity-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting || !message.trim()}
                  className="px-5 py-2 bg-primary-600 hover:bg-primary-500 disabled:bg-gray-700 disabled:text-gray-500 text-white text-sm font-medium rounded-lg transition-colors disabled:cursor-not-allowed"
                >
                  {submitting ? 'Sending…' : 'Send Feedback'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </>
  );
}
