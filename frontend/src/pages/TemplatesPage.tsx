/**
 * TemplatesPage — Starter Templates by Persona (BACKLOG-087).
 *
 * A gallery of persona templates that one-click scaffold a tasteful starting
 * structure (areas + projects with phases + starter next actions). Surfaced
 * from the empty states on Projects/Dashboard and the sidebar.
 */

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import {
  PenTool,
  Briefcase,
  Code,
  LayoutTemplate,
  Sparkles,
  ChevronDown,
  ChevronUp,
  Check,
  ArrowRight,
} from 'lucide-react';
import { useTemplates, useTemplate, useApplyTemplate } from '@/hooks/useTemplates';
import { telemetry } from '@/services/telemetry';
import { EmptyState } from '@/components/common/EmptyState';
import type { TemplateSummary } from '@/types';

const ICONS: Record<string, React.ComponentType<{ className?: string }>> = {
  'pen-tool': PenTool,
  briefcase: Briefcase,
  code: Code,
};

export function TemplatesPage() {
  const { data: templates, isLoading, isError, refetch } = useTemplates();
  const applyMutation = useApplyTemplate();
  const navigate = useNavigate();
  const [applyingId, setApplyingId] = useState<string | null>(null);

  const handleApply = async (id: string) => {
    setApplyingId(id);
    try {
      const result = await applyMutation.mutateAsync(id);
      toast.success(
        `Added ${result.projects_created} projects and ${result.tasks_created} actions to get you moving.`,
      );
      navigate(
        result.first_project_id ? `/projects/${result.first_project_id}` : '/projects',
      );
    } catch {
      toast.error('Could not apply that template. Please try again.');
    } finally {
      setApplyingId(null);
    }
  };

  return (
    <div className="p-4 md:p-8 max-w-5xl mx-auto">
      <div className="mb-6">
        <div className="flex items-center gap-2 mb-1">
          <Sparkles className="w-6 h-6 text-primary-600" />
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
            Start from a template
          </h1>
        </div>
        <p className="text-gray-600 dark:text-gray-400">
          Pick the setup closest to how you work. We'll scaffold the areas,
          projects, and first actions — you can change anything afterward.
        </p>
      </div>

      {isLoading && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {[0, 1, 2].map((i) => (
            <div key={i} className="card animate-pulse h-56" />
          ))}
        </div>
      )}

      {isError && (
        <EmptyState
          variant="generic"
          title="Couldn't load templates"
          description="Something went wrong fetching the starter templates."
          action={
            <button onClick={() => refetch()} className="btn btn-primary">
              Try again
            </button>
          }
        />
      )}

      {templates && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {templates.map((t) => (
            <TemplateCard
              key={t.id}
              template={t}
              applying={applyingId === t.id}
              disabled={applyingId !== null}
              onApply={() => handleApply(t.id)}
            />
          ))}
        </div>
      )}
    </div>
  );
}

interface TemplateCardProps {
  template: TemplateSummary;
  applying: boolean;
  disabled: boolean;
  onApply: () => void;
}

function TemplateCard({ template, applying, disabled, onApply }: TemplateCardProps) {
  const [expanded, setExpanded] = useState(false);
  const Icon = ICONS[template.icon] ?? LayoutTemplate;
  const { data: detail, isLoading: detailLoading } = useTemplate(
    expanded ? template.id : null,
  );

  const toggleExpand = () => {
    const next = !expanded;
    setExpanded(next);
    if (next) {
      telemetry.track('template_previewed', { template_id: template.id });
    }
  };

  return (
    <div className="card flex flex-col">
      <div className="flex items-start gap-3">
        <div className="inline-flex items-center justify-center w-11 h-11 rounded-lg bg-primary-100 dark:bg-primary-900/30 shrink-0">
          <Icon className="w-6 h-6 text-primary-600 dark:text-primary-400" />
        </div>
        <div className="min-w-0">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
            {template.name}
          </h2>
          <p className="text-sm text-gray-600 dark:text-gray-400">{template.tagline}</p>
        </div>
      </div>

      <p className="text-sm text-gray-500 dark:text-gray-400 mt-3">
        {template.description}
      </p>

      <div className="flex flex-wrap gap-1.5 mt-3">
        <span className="badge badge-blue">{template.area_count} areas</span>
        <span className="badge badge-purple">{template.project_count} projects</span>
        <span className="badge badge-gray">{template.task_count} actions</span>
      </div>

      <button
        type="button"
        onClick={toggleExpand}
        className="mt-3 inline-flex items-center gap-1 text-sm text-primary-600 dark:text-primary-400 hover:underline self-start"
        aria-expanded={expanded}
      >
        {expanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        {expanded ? 'Hide preview' : 'Preview what you get'}
      </button>

      {expanded && (
        <div className="mt-3 border-t border-gray-100 dark:border-gray-700 pt-3 space-y-3">
          {detailLoading && (
            <p className="text-sm text-gray-400">Loading preview…</p>
          )}
          {detail?.projects.map((p) => (
            <div key={p.title}>
              <p className="text-sm font-medium text-gray-800 dark:text-gray-200">
                {p.title}
                {p.area_title && (
                  <span className="text-xs font-normal text-gray-400"> · {p.area_title}</span>
                )}
              </p>
              {p.phases.length > 0 && (
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                  Phases: {p.phases.join(' → ')}
                </p>
              )}
              <ul className="mt-1 space-y-0.5">
                {p.tasks.map((task) => (
                  <li
                    key={task.title}
                    className="text-xs text-gray-500 dark:text-gray-400 flex items-center gap-1.5"
                  >
                    <span className="w-1 h-1 rounded-full bg-gray-300 dark:bg-gray-600" />
                    {task.title}
                    {task.is_next_action && (
                      <span className="badge badge-yellow ml-1">next action</span>
                    )}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      )}

      <button
        type="button"
        onClick={onApply}
        disabled={disabled}
        className="btn btn-primary w-full mt-4 inline-flex items-center justify-center gap-1.5 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {applying ? (
          <>
            <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
            Setting up…
          </>
        ) : (
          <>
            <Check className="w-4 h-4" />
            Use this template
            <ArrowRight className="w-4 h-4" />
          </>
        )}
      </button>
    </div>
  );
}
