/**
 * FirstRunGuide — 4-step overlay introducing Conduital to a new user.
 *
 * Fires once after SetupWizard completes (or on first navigation if skipped).
 * Gated by localStorage flag `first_run_guide_v1_complete`. No close (×):
 * every path ends with the flag being set, so the guide never reappears.
 */

import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, ArrowRight } from 'lucide-react';
import { api } from '@/services/api';
import { telemetry } from '@/services/telemetry';

const COMPLETE_KEY = 'first_run_guide_v1_complete';
const METHODOLOGY_KEY = 'onboarding_methodology';

type Methodology = 'gtd' | 'myn' | 'hybrid' | 'default';

interface MethodologyOption {
  id: Methodology;
  title: string;
  description: string;
}

const METHODOLOGIES: MethodologyOption[] = [
  {
    id: 'gtd',
    title: 'Getting Things Done® (GTD)',
    description: 'Capture → Clarify → Organize → Review → Engage',
  },
  {
    id: 'myn',
    title: 'Mark Yurgent’s Next® (MYN)',
    description: 'Urgency Zones: Critical Now / Opportunity Now / Over-the-Horizon',
  },
  {
    id: 'hybrid',
    title: 'Both / Hybrid',
    description: 'Use GTD Inbox and MYN urgency zones together',
  },
  {
    id: 'default',
    title: 'Just get me started',
    description: "We’ll label things simply — you can customize later",
  },
];

const PROJECT_IDEAS = ['Work', 'Personal', 'Health', 'Side Project', 'Learning'];

export function FirstRunGuide() {
  const navigate = useNavigate();
  const [shouldShow, setShouldShow] = useState<boolean>(() => {
    return localStorage.getItem(COMPLETE_KEY) !== 'true';
  });

  const [step, setStep] = useState<1 | 2 | 3 | 4>(1);
  const [methodology, setMethodology] = useState<Methodology | null>(null);
  const [projectName, setProjectName] = useState('');
  const [taskName, setTaskName] = useState('');
  const [createdProjectId, setCreatedProjectId] = useState<number | null>(null);
  const [createdProjectName, setCreatedProjectName] = useState<string>('');
  const [createdTaskId, setCreatedTaskId] = useState<number | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (shouldShow) {
      telemetry.track('first_run_guide_started', { version: 'v1' });
    }
  }, [shouldShow]);

  if (!shouldShow) return null;

  const markComplete = () => {
    localStorage.setItem(COMPLETE_KEY, 'true');
    setShouldShow(false);
  };

  const handleSkipSetup = () => {
    markComplete();
  };

  const handleStep1Next = () => {
    const selected = methodology ?? 'default';
    localStorage.setItem(METHODOLOGY_KEY, selected);
    telemetry.track('methodology_selected', { methodology: selected });
    telemetry.track('first_run_guide_step_completed', { step: 1 });
    setStep(2);
  };

  const handleStep2Submit = async () => {
    const trimmed = projectName.trim();
    if (!trimmed || submitting) return;
    setError(null);
    setSubmitting(true);
    try {
      const project = await api.createProject({ title: trimmed });
      setCreatedProjectId(project.id);
      setCreatedProjectName(project.title);
      telemetry.track('first_project_created', { source: 'first_run_guide' });
      telemetry.track('first_run_guide_step_completed', { step: 2 });
      setStep(3);
    } catch (err) {
      console.error('FirstRunGuide: failed to create project', err);
      setError("We couldn’t create that project. Please try again.");
    } finally {
      setSubmitting(false);
    }
  };

  const handleStep3Submit = async () => {
    const trimmed = taskName.trim();
    if (!trimmed || submitting || createdProjectId === null) return;
    setError(null);
    setSubmitting(true);
    try {
      const task = await api.createTask({
        title: trimmed,
        project_id: createdProjectId,
        status: 'pending',
      });
      setCreatedTaskId(task.id);
      telemetry.track('first_task_created', {
        source: 'first_run_guide',
        project_id: createdProjectId,
      });
      telemetry.track('first_run_guide_step_completed', { step: 3 });
      setStep(4);
    } catch (err) {
      console.error('FirstRunGuide: failed to create task', err);
      setError("We couldn’t add that action. Please try again.");
    } finally {
      setSubmitting(false);
    }
  };

  const handleStep3Skip = () => {
    setError(null);
    telemetry.track('first_run_guide_step_completed', { step: 3 });
    setStep(4);
  };

  const finishAndNavigate = (path: string) => {
    telemetry.track('first_run_guide_step_completed', { step: 4 });
    telemetry.track('onboarding_completed', {
      steps_completed: 4,
      methodology: localStorage.getItem(METHODOLOGY_KEY) ?? 'default',
      project_created: createdProjectId !== null,
      task_created: createdTaskId !== null,
    });
    markComplete();
    navigate(path);
  };

  const goBack = () => {
    setError(null);
    setStep((s) => (s > 1 ? ((s - 1) as 1 | 2 | 3) : s));
  };

  return (
    <div className="fixed inset-0 z-[60] flex items-center justify-center bg-black/60 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-2xl max-w-lg w-full overflow-hidden">
        <div className="bg-gradient-to-br from-primary-500 to-primary-700 px-6 py-5 text-white">
          <p className="text-xs font-medium uppercase tracking-wider text-white/80">
            Step {step} of 4
          </p>
          <h2 className="text-xl font-bold mt-0.5">{titleForStep(step, createdProjectName)}</h2>
          <div className="flex items-center gap-2 mt-3" aria-hidden="true">
            {[1, 2, 3, 4].map((n) => (
              <span
                key={n}
                className={`h-2 w-2 rounded-full ${
                  n <= step ? 'bg-white' : 'bg-white/30'
                }`}
              />
            ))}
          </div>
        </div>

        <div className="px-6 py-5">
          {step === 1 && (
            <Step1
              methodology={methodology}
              onSelect={setMethodology}
            />
          )}
          {step === 2 && (
            <Step2
              value={projectName}
              onChange={setProjectName}
              onPickIdea={setProjectName}
              error={error}
              disabled={submitting}
            />
          )}
          {step === 3 && (
            <Step3
              projectName={createdProjectName}
              value={taskName}
              onChange={setTaskName}
              error={error}
              disabled={submitting}
            />
          )}
          {step === 4 && <Step4 projectName={createdProjectName} />}
        </div>

        <div className="px-6 py-4 bg-gray-50 dark:bg-gray-900/40 border-t border-gray-200 dark:border-gray-700 flex items-center justify-between gap-3">
          {step === 1 && (
            <>
              <button
                type="button"
                onClick={handleSkipSetup}
                className="text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200"
              >
                Skip setup
              </button>
              <button
                type="button"
                onClick={handleStep1Next}
                className="btn btn-primary inline-flex items-center gap-1.5"
              >
                Next
                <ArrowRight className="w-4 h-4" />
              </button>
            </>
          )}
          {step === 2 && (
            <>
              <button
                type="button"
                onClick={goBack}
                disabled={submitting}
                className="text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200 inline-flex items-center gap-1.5 disabled:opacity-50"
              >
                <ArrowLeft className="w-4 h-4" />
                Back
              </button>
              <button
                type="button"
                onClick={handleStep2Submit}
                disabled={!projectName.trim() || submitting}
                className="btn btn-primary inline-flex items-center gap-1.5 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {submitting ? 'Creating…' : 'Create project'}
                {!submitting && <ArrowRight className="w-4 h-4" />}
              </button>
            </>
          )}
          {step === 3 && (
            <>
              <button
                type="button"
                onClick={goBack}
                disabled={submitting}
                className="text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200 inline-flex items-center gap-1.5 disabled:opacity-50"
              >
                <ArrowLeft className="w-4 h-4" />
                Back
              </button>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={handleStep3Skip}
                  disabled={submitting}
                  className="text-sm px-3 py-1.5 rounded-md text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700 disabled:opacity-50"
                >
                  Skip this step
                </button>
                <button
                  type="button"
                  onClick={handleStep3Submit}
                  disabled={!taskName.trim() || submitting}
                  className="btn btn-primary inline-flex items-center gap-1.5 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {submitting ? 'Adding…' : 'Add to project'}
                  {!submitting && <ArrowRight className="w-4 h-4" />}
                </button>
              </div>
            </>
          )}
          {step === 4 && (
            <>
              <button
                type="button"
                onClick={goBack}
                className="text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200 inline-flex items-center gap-1.5"
              >
                <ArrowLeft className="w-4 h-4" />
                Back
              </button>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => finishAndNavigate('/')}
                  className="text-sm px-3 py-1.5 rounded-md text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700"
                >
                  Explore the dashboard
                </button>
                <button
                  type="button"
                  onClick={() =>
                    finishAndNavigate(
                      createdProjectId !== null ? `/projects/${createdProjectId}` : '/'
                    )
                  }
                  className="btn btn-primary inline-flex items-center gap-1.5"
                >
                  Go to my project
                  <ArrowRight className="w-4 h-4" />
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

function titleForStep(step: 1 | 2 | 3 | 4, projectName: string): string {
  switch (step) {
    case 1:
      return 'Welcome to Conduital';
    case 2:
      return 'Your first project';
    case 3:
      return `Your first action in ${projectName || 'your project'}`;
    case 4:
      return 'Your momentum score';
  }
}

interface Step1Props {
  methodology: Methodology | null;
  onSelect: (m: Methodology) => void;
}

function Step1({ methodology, onSelect }: Step1Props) {
  return (
    <div>
      <p className="text-sm text-gray-700 dark:text-gray-300">
        Conduital is built around one question: what keeps your work moving forward? To show you
        around right, tell us how you think about your work:
      </p>
      <div className="mt-4 space-y-2">
        {METHODOLOGIES.map((m) => {
          const selected = methodology === m.id;
          return (
            <button
              key={m.id}
              type="button"
              onClick={() => onSelect(m.id)}
              className={`w-full text-left px-4 py-3 rounded-lg border transition-colors ${
                selected
                  ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20 ring-1 ring-primary-500'
                  : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600 bg-white dark:bg-gray-800'
              }`}
            >
              <p
                className={`text-sm font-semibold ${
                  selected
                    ? 'text-primary-700 dark:text-primary-300'
                    : 'text-gray-900 dark:text-gray-100'
                }`}
              >
                {m.title}
              </p>
              <p className="text-xs text-gray-600 dark:text-gray-400 mt-0.5">{m.description}</p>
            </button>
          );
        })}
      </div>
    </div>
  );
}

interface Step2Props {
  value: string;
  onChange: (v: string) => void;
  onPickIdea: (v: string) => void;
  error: string | null;
  disabled: boolean;
}

function Step2({ value, onChange, onPickIdea, error, disabled }: Step2Props) {
  return (
    <div>
      <p className="text-sm text-gray-700 dark:text-gray-300">
        Projects are the work that moves forward together — a client, a launch, a goal, a life
        area.
      </p>
      <label
        htmlFor="frg-project-name"
        className="block text-xs font-medium text-gray-600 dark:text-gray-400 uppercase tracking-wide mt-4 mb-1"
      >
        Project name
      </label>
      <input
        id="frg-project-name"
        type="text"
        autoFocus
        maxLength={100}
        value={value}
        disabled={disabled}
        onChange={(e) => onChange(e.target.value)}
        className="input w-full"
        placeholder="What are you working on?"
      />
      <div className="mt-3 flex flex-wrap gap-2">
        {PROJECT_IDEAS.map((idea) => (
          <button
            key={idea}
            type="button"
            onClick={() => onPickIdea(idea)}
            disabled={disabled}
            className="text-xs px-2.5 py-1 rounded-full border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 disabled:opacity-50"
          >
            {idea}
          </button>
        ))}
      </div>
      {error && (
        <p className="mt-3 text-sm text-red-600 dark:text-red-400">{error}</p>
      )}
    </div>
  );
}

interface Step3Props {
  projectName: string;
  value: string;
  onChange: (v: string) => void;
  error: string | null;
  disabled: boolean;
}

function Step3({ value, onChange, error, disabled }: Step3Props) {
  return (
    <div>
      <p className="text-sm text-gray-700 dark:text-gray-300">
        In Conduital, tasks are physical actions — specific things you can do in one sitting.
      </p>
      <label
        htmlFor="frg-task-name"
        className="block text-xs font-medium text-gray-600 dark:text-gray-400 uppercase tracking-wide mt-4 mb-1"
      >
        What’s the next thing to do?
      </label>
      <input
        id="frg-task-name"
        type="text"
        autoFocus
        value={value}
        disabled={disabled}
        onChange={(e) => onChange(e.target.value)}
        className="input w-full"
        placeholder="e.g. Draft the kickoff email"
      />
      {error && (
        <p className="mt-3 text-sm text-red-600 dark:text-red-400">{error}</p>
      )}
    </div>
  );
}

function Step4({ projectName }: { projectName: string }) {
  return (
    <div>
      <p className="text-sm text-gray-700 dark:text-gray-300">
        Every project in Conduital has a Momentum Score — a live indicator of whether it’s
        moving forward or going stale.
      </p>
      <p className="text-sm text-gray-700 dark:text-gray-300 mt-2">
        Right now,{' '}
        <span className="font-semibold text-gray-900 dark:text-gray-100">
          {projectName || 'your project'}
        </span>{' '}
        is at 100% — you just created it and added an action. As days pass without movement,
        the score naturally drifts. Conduital notices, and can surface what needs attention.
      </p>
      <div className="mt-5 flex justify-center">
        <MomentumGauge percent={100} />
      </div>
      <p className="text-xs text-gray-500 dark:text-gray-400 mt-4 text-center">
        No email required. No notifications. Just visibility.
      </p>
    </div>
  );
}

function MomentumGauge({ percent }: { percent: number }) {
  const size = 120;
  const stroke = 10;
  const radius = (size - stroke) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference * (1 - percent / 100);
  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} aria-label={`Momentum ${percent}%`}>
      <circle
        cx={size / 2}
        cy={size / 2}
        r={radius}
        fill="none"
        className="stroke-gray-200 dark:stroke-gray-700"
        strokeWidth={stroke}
      />
      <circle
        cx={size / 2}
        cy={size / 2}
        r={radius}
        fill="none"
        className="stroke-primary-600 dark:stroke-primary-400"
        strokeWidth={stroke}
        strokeLinecap="round"
        strokeDasharray={circumference}
        strokeDashoffset={offset}
        transform={`rotate(-90 ${size / 2} ${size / 2})`}
      />
      <text
        x="50%"
        y="50%"
        textAnchor="middle"
        dominantBaseline="central"
        className="fill-primary-600 dark:fill-primary-400 font-bold"
        style={{ fontSize: '22px' }}
      >
        {percent}%
      </text>
    </svg>
  );
}
