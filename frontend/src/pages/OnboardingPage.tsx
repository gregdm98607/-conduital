import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { User, Settings, MapPin, BookOpen, ArrowRight, ArrowLeft, Check, Sparkles } from 'lucide-react';
import toast from 'react-hot-toast';
import axios from 'axios';

const memoryApi = axios.create({
  baseURL: (import.meta.env.VITE_API_BASE_URL || '/api/v1') + '/memory',
  headers: { 'Content-Type': 'application/json' },
});

interface OnboardingData {
  name: string;
  preferred_name: string;
  role: string;
  timezone: string;
  communication_style: string;
  work_methodology: string;
  planning_horizon: string;
  peak_hours: string[];
  primary_contexts: string[];
  locations: string[];
  primary_skills: string[];
  learning_goals: string[];
}

const STEPS = [
  { id: 'identity', label: 'Identity', icon: User },
  { id: 'preferences', label: 'Preferences', icon: Settings },
  { id: 'contexts', label: 'Contexts', icon: MapPin },
  { id: 'skills', label: 'Skills', icon: BookOpen },
];

const CONTEXT_OPTIONS = ['@computer', '@desk', '@phone', '@home', '@office', '@errands', '@anywhere'];
const METHODOLOGY_OPTIONS = [
  { value: 'gtd', label: 'GTD (Getting Things Done)' },
  { value: 'eisenhower', label: 'Eisenhower Matrix' },
  { value: 'timeblocking', label: 'Time Blocking' },
  { value: 'other', label: 'Other / None' },
];

export function OnboardingPage() {
  const navigate = useNavigate();
  const [step, setStep] = useState(0);
  const [submitting, setSubmitting] = useState(false);
  const [data, setData] = useState<OnboardingData>({
    name: '',
    preferred_name: '',
    role: '',
    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
    communication_style: 'balanced',
    work_methodology: 'gtd',
    planning_horizon: 'weekly',
    peak_hours: [],
    primary_contexts: ['@computer'],
    locations: [],
    primary_skills: [],
    learning_goals: [],
  });

  const [skillInput, setSkillInput] = useState('');
  const [goalInput, setGoalInput] = useState('');
  const [locationInput, setLocationInput] = useState('');

  const update = (field: keyof OnboardingData, value: unknown) => {
    setData(prev => ({ ...prev, [field]: value }));
  };

  const toggleContext = (ctx: string) => {
    setData(prev => ({
      ...prev,
      primary_contexts: prev.primary_contexts.includes(ctx)
        ? prev.primary_contexts.filter(c => c !== ctx)
        : [...prev.primary_contexts, ctx],
    }));
  };

  const addToList = (field: 'primary_skills' | 'learning_goals' | 'locations', value: string, clearFn: (v: string) => void) => {
    if (!value.trim()) return;
    setData(prev => ({
      ...prev,
      [field]: [...(prev[field] as string[]), value.trim()],
    }));
    clearFn('');
  };

  const removeFromList = (field: 'primary_skills' | 'learning_goals' | 'locations', index: number) => {
    setData(prev => ({
      ...prev,
      [field]: (prev[field] as string[]).filter((_, i) => i !== index),
    }));
  };

  const canProceed = step === 0 ? data.name.trim().length > 0 : true;

  const handleSubmit = async () => {
    setSubmitting(true);
    try {
      await memoryApi.post('/onboarding', {
        name: data.name,
        preferred_name: data.preferred_name || undefined,
        role: data.role || undefined,
        timezone: data.timezone || undefined,
        communication_style: data.communication_style || undefined,
        work_methodology: data.work_methodology || undefined,
        planning_horizon: data.planning_horizon || undefined,
        peak_hours: data.peak_hours.length ? data.peak_hours : undefined,
        primary_contexts: data.primary_contexts.length ? data.primary_contexts : undefined,
        locations: data.locations.length ? data.locations : undefined,
        primary_skills: data.primary_skills.length ? data.primary_skills : undefined,
        learning_goals: data.learning_goals.length ? data.learning_goals : undefined,
      });
      toast.success('Onboarding complete! Your AI memory has been initialized.');
      navigate('/memory');
    } catch (error) {
      toast.error('Failed to complete onboarding. Please try again.');
      console.error('Onboarding error:', error);
    }
    setSubmitting(false);
  };

  return (
    <div className="p-8 max-w-2xl mx-auto">
      {/* Header */}
      <div className="text-center mb-8">
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-primary-100 dark:bg-primary-900/30 mb-4">
          <Sparkles className="w-8 h-8 text-primary-600" />
        </div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-2">Welcome to Project Tracker</h1>
        <p className="text-gray-600 dark:text-gray-400">
          Let's set up your AI memory so the assistant can help you better.
        </p>
      </div>

      {/* Step Indicators */}
      <div className="flex items-center justify-center gap-2 mb-8">
        {STEPS.map((s, i) => {
          const Icon = s.icon;
          return (
            <div key={s.id} className="flex items-center gap-2">
              <button
                onClick={() => i <= step ? setStep(i) : undefined}
                className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                  i === step
                    ? 'bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-400'
                    : i < step
                    ? 'text-green-600 dark:text-green-400'
                    : 'text-gray-400 dark:text-gray-500'
                }`}
              >
                {i < step ? (
                  <Check className="w-4 h-4" />
                ) : (
                  <Icon className="w-4 h-4" />
                )}
                <span className="hidden sm:inline">{s.label}</span>
              </button>
              {i < STEPS.length - 1 && (
                <div className={`w-8 h-0.5 ${i < step ? 'bg-green-400' : 'bg-gray-200 dark:bg-gray-700'}`} />
              )}
            </div>
          );
        })}
      </div>

      {/* Step Content */}
      <div className="card">
        {step === 0 && (
          <div className="space-y-4">
            <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100 mb-4">Who are you?</h2>
            <div>
              <label className="label">Full Name *</label>
              <input
                type="text"
                className="input"
                placeholder="John Doe"
                value={data.name}
                onChange={(e) => update('name', e.target.value)}
                autoFocus
              />
            </div>
            <div>
              <label className="label">Preferred Name</label>
              <input
                type="text"
                className="input"
                placeholder="John"
                value={data.preferred_name}
                onChange={(e) => update('preferred_name', e.target.value)}
              />
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">How should the AI address you?</p>
            </div>
            <div>
              <label className="label">Role / Profession</label>
              <input
                type="text"
                className="input"
                placeholder="Software Engineer"
                value={data.role}
                onChange={(e) => update('role', e.target.value)}
              />
            </div>
            <div>
              <label className="label">Timezone</label>
              <input
                type="text"
                className="input"
                value={data.timezone}
                onChange={(e) => update('timezone', e.target.value)}
              />
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">Auto-detected from your browser</p>
            </div>
          </div>
        )}

        {step === 1 && (
          <div className="space-y-5">
            <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100 mb-4">Work Style</h2>
            <div>
              <label className="label">Communication Style</label>
              <div className="flex gap-3">
                {['concise', 'balanced', 'detailed'].map((style) => (
                  <button
                    key={style}
                    onClick={() => update('communication_style', style)}
                    className={`flex-1 px-4 py-2.5 rounded-lg border text-sm font-medium capitalize transition-colors ${
                      data.communication_style === style
                        ? 'border-primary-500 bg-primary-50 text-primary-700 dark:bg-primary-900/30 dark:text-primary-400 dark:border-primary-500'
                        : 'border-gray-200 text-gray-600 hover:bg-gray-50 dark:border-gray-600 dark:text-gray-400 dark:hover:bg-gray-700'
                    }`}
                  >
                    {style}
                  </button>
                ))}
              </div>
            </div>
            <div>
              <label className="label">Work Methodology</label>
              <select
                className="input"
                value={data.work_methodology}
                onChange={(e) => update('work_methodology', e.target.value)}
              >
                {METHODOLOGY_OPTIONS.map((opt) => (
                  <option key={opt.value} value={opt.value}>{opt.label}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="label">Planning Horizon</label>
              <div className="flex gap-3">
                {['daily', 'weekly', 'monthly'].map((h) => (
                  <button
                    key={h}
                    onClick={() => update('planning_horizon', h)}
                    className={`flex-1 px-4 py-2.5 rounded-lg border text-sm font-medium capitalize transition-colors ${
                      data.planning_horizon === h
                        ? 'border-primary-500 bg-primary-50 text-primary-700 dark:bg-primary-900/30 dark:text-primary-400 dark:border-primary-500'
                        : 'border-gray-200 text-gray-600 hover:bg-gray-50 dark:border-gray-600 dark:text-gray-400 dark:hover:bg-gray-700'
                    }`}
                  >
                    {h}
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}

        {step === 2 && (
          <div className="space-y-5">
            <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100 mb-4">Your Contexts</h2>
            <div>
              <label className="label">Available Contexts (GTD)</label>
              <p className="text-xs text-gray-500 dark:text-gray-400 mb-3">Select the contexts where you can work on tasks</p>
              <div className="flex flex-wrap gap-2">
                {CONTEXT_OPTIONS.map((ctx) => (
                  <button
                    key={ctx}
                    onClick={() => toggleContext(ctx)}
                    className={`px-3 py-1.5 rounded-full text-sm font-medium transition-colors ${
                      data.primary_contexts.includes(ctx)
                        ? 'bg-primary-100 text-primary-700 dark:bg-primary-900/30 dark:text-primary-400 border border-primary-300 dark:border-primary-600'
                        : 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400 border border-gray-200 dark:border-gray-600'
                    }`}
                  >
                    {ctx}
                  </button>
                ))}
              </div>
            </div>
            <div>
              <label className="label">Locations</label>
              <div className="flex gap-2">
                <input
                  type="text"
                  className="input flex-1"
                  placeholder="e.g. Home Office"
                  value={locationInput}
                  onChange={(e) => setLocationInput(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && addToList('locations', locationInput, setLocationInput)}
                />
                <button
                  onClick={() => addToList('locations', locationInput, setLocationInput)}
                  className="btn btn-secondary"
                >
                  Add
                </button>
              </div>
              {data.locations.length > 0 && (
                <div className="flex flex-wrap gap-2 mt-2">
                  {data.locations.map((loc, i) => (
                    <span key={i} className="badge badge-blue flex items-center gap-1">
                      {loc}
                      <button onClick={() => removeFromList('locations', i)} className="ml-1 hover:text-red-500">&times;</button>
                    </span>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {step === 3 && (
          <div className="space-y-5">
            <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100 mb-4">Skills & Goals (Optional)</h2>
            <div>
              <label className="label">Primary Skills</label>
              <div className="flex gap-2">
                <input
                  type="text"
                  className="input flex-1"
                  placeholder="e.g. Python, React, Writing"
                  value={skillInput}
                  onChange={(e) => setSkillInput(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && addToList('primary_skills', skillInput, setSkillInput)}
                />
                <button
                  onClick={() => addToList('primary_skills', skillInput, setSkillInput)}
                  className="btn btn-secondary"
                >
                  Add
                </button>
              </div>
              {data.primary_skills.length > 0 && (
                <div className="flex flex-wrap gap-2 mt-2">
                  {data.primary_skills.map((skill, i) => (
                    <span key={i} className="badge badge-green flex items-center gap-1">
                      {skill}
                      <button onClick={() => removeFromList('primary_skills', i)} className="ml-1 hover:text-red-500">&times;</button>
                    </span>
                  ))}
                </div>
              )}
            </div>
            <div>
              <label className="label">Learning Goals</label>
              <div className="flex gap-2">
                <input
                  type="text"
                  className="input flex-1"
                  placeholder="e.g. System Design, Machine Learning"
                  value={goalInput}
                  onChange={(e) => setGoalInput(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && addToList('learning_goals', goalInput, setGoalInput)}
                />
                <button
                  onClick={() => addToList('learning_goals', goalInput, setGoalInput)}
                  className="btn btn-secondary"
                >
                  Add
                </button>
              </div>
              {data.learning_goals.length > 0 && (
                <div className="flex flex-wrap gap-2 mt-2">
                  {data.learning_goals.map((goal, i) => (
                    <span key={i} className="badge badge-yellow flex items-center gap-1">
                      {goal}
                      <button onClick={() => removeFromList('learning_goals', i)} className="ml-1 hover:text-red-500">&times;</button>
                    </span>
                  ))}
                </div>
              )}
            </div>
            <p className="text-sm text-gray-500 dark:text-gray-400 italic">
              This step is optional. You can always update your skills and goals later in the Memory page.
            </p>
          </div>
        )}
      </div>

      {/* Navigation */}
      <div className="flex items-center justify-between mt-6">
        <button
          onClick={() => step > 0 ? setStep(step - 1) : navigate('/')}
          className="btn btn-secondary flex items-center gap-2"
        >
          <ArrowLeft className="w-4 h-4" />
          {step === 0 ? 'Skip' : 'Back'}
        </button>

        {step < STEPS.length - 1 ? (
          <button
            onClick={() => setStep(step + 1)}
            disabled={!canProceed}
            className="btn btn-primary flex items-center gap-2"
          >
            Next
            <ArrowRight className="w-4 h-4" />
          </button>
        ) : (
          <button
            onClick={handleSubmit}
            disabled={submitting || !data.name.trim()}
            className="btn btn-primary flex items-center gap-2"
          >
            {submitting ? (
              <>
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                Saving...
              </>
            ) : (
              <>
                <Check className="w-4 h-4" />
                Complete Setup
              </>
            )}
          </button>
        )}
      </div>
    </div>
  );
}
