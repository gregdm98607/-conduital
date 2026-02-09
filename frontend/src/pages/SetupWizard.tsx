import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Rocket,
  FolderSync,
  Brain,
  CheckCircle,
  ArrowRight,
  ArrowLeft,
  Check,
  AlertCircle,
  Loader2,
} from 'lucide-react';
import toast from 'react-hot-toast';
import { api } from '../services/api';

interface SetupConfig {
  sync_folder: string;
  anthropic_api_key: string;
  ai_features_enabled: boolean;
  migrate_legacy_data: boolean;
}

interface SetupStatusData {
  setup_complete: boolean;
  is_first_run: boolean;
  is_packaged: boolean;
  data_directory: string;
  config_path: string;
  legacy_migration: {
    needs_migration: boolean;
    legacy_path?: string;
    target_path?: string;
  };
  current_settings: {
    sync_folder_configured: boolean;
    sync_folder: string;
    ai_key_configured: boolean;
    ai_features_enabled: boolean;
    database_path: string;
  };
}

const STEPS = [
  { id: 'welcome', label: 'Welcome', icon: Rocket },
  { id: 'sync', label: 'File Sync', icon: FolderSync },
  { id: 'ai', label: 'AI Setup', icon: Brain },
  { id: 'ready', label: 'Ready', icon: CheckCircle },
];

export function SetupWizard() {
  const navigate = useNavigate();
  const [step, setStep] = useState(0);
  const [submitting, setSubmitting] = useState(false);
  const [status, setStatus] = useState<SetupStatusData | null>(null);
  const [loading, setLoading] = useState(true);

  const [config, setConfig] = useState<SetupConfig>({
    sync_folder: '',
    anthropic_api_key: '',
    ai_features_enabled: false,
    migrate_legacy_data: false,
  });

  // Path validation state
  const [pathValid, setPathValid] = useState<boolean | null>(null);
  const [pathValidating, setPathValidating] = useState(false);

  // AI test state
  const [aiTesting, setAiTesting] = useState(false);
  const [aiTestResult, setAiTestResult] = useState<{
    success: boolean;
    message: string;
  } | null>(null);

  useEffect(() => {
    loadStatus();
  }, []);

  const loadStatus = async () => {
    try {
      const data = await api.getSetupStatus();
      setStatus(data);

      // Pre-fill from existing settings if re-running setup
      if (data.current_settings.sync_folder) {
        setConfig((prev) => ({
          ...prev,
          sync_folder: data.current_settings.sync_folder,
        }));
      }
      if (data.current_settings.ai_features_enabled) {
        setConfig((prev) => ({
          ...prev,
          ai_features_enabled: data.current_settings.ai_features_enabled,
        }));
      }
    } catch {
      toast.error('Failed to load setup status');
    } finally {
      setLoading(false);
    }
  };

  const validatePath = async () => {
    if (!config.sync_folder.trim()) return;
    setPathValidating(true);
    setPathValid(null);
    try {
      const result = await api.validateSyncPath(config.sync_folder.trim());
      setPathValid(result.valid);
      if (result.valid) {
        setConfig((prev) => ({ ...prev, sync_folder: result.path }));
      }
    } catch {
      setPathValid(false);
    } finally {
      setPathValidating(false);
    }
  };

  const testAIConnection = async () => {
    setAiTesting(true);
    setAiTestResult(null);
    try {
      // First save the key temporarily via the AI settings endpoint
      if (config.anthropic_api_key.trim()) {
        await api.updateAISettings({
          api_key: config.anthropic_api_key.trim(),
          ai_features_enabled: true,
        });
      }
      const result = await api.testAIConnection();
      setAiTestResult(result);
    } catch {
      setAiTestResult({ success: false, message: 'Connection test failed' });
    } finally {
      setAiTesting(false);
    }
  };

  const handleSubmit = async () => {
    setSubmitting(true);
    try {
      const result = await api.completeSetup({
        sync_folder: config.sync_folder.trim() || undefined,
        anthropic_api_key: config.anthropic_api_key.trim() || undefined,
        ai_features_enabled: config.ai_features_enabled,
        migrate_legacy_data: config.migrate_legacy_data,
      });

      if (result.success) {
        toast.success('Setup complete! Redirecting to dashboard...');
        setTimeout(() => navigate('/'), 1000);
      } else {
        toast.error(result.message);
      }
    } catch {
      toast.error('Failed to complete setup. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <Loader2 className="w-8 h-8 animate-spin text-primary-600 mx-auto mb-4" />
          <p className="text-gray-600 dark:text-gray-400">Loading setup...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-8 max-w-2xl mx-auto min-h-screen flex flex-col justify-center">
      {/* Header */}
      <div className="text-center mb-8">
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-primary-100 dark:bg-primary-900/30 mb-4">
          <Rocket className="w-8 h-8 text-primary-600" />
        </div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-2">
          Set Up Conduital
        </h1>
        <p className="text-gray-600 dark:text-gray-400">
          Configure your intelligent momentum system in just a few steps.
        </p>
      </div>

      {/* Step Indicators */}
      <div className="flex items-center justify-center gap-2 mb-8">
        {STEPS.map((s, i) => {
          const Icon = s.icon;
          return (
            <div key={s.id} className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => (i <= step ? setStep(i) : undefined)}
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
                <div
                  className={`w-8 h-0.5 ${
                    i < step
                      ? 'bg-green-400'
                      : 'bg-gray-200 dark:bg-gray-700'
                  }`}
                />
              )}
            </div>
          );
        })}
      </div>

      {/* Step Content */}
      <div className="card">
        {/* Step 0: Welcome */}
        {step === 0 && (
          <div className="space-y-4">
            <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100 mb-4">
              Welcome to Conduital
            </h2>
            <p className="text-gray-600 dark:text-gray-400">
              Conduital is an intelligent momentum-based productivity system. It helps you
              manage projects, track tasks, and maintain forward progress on what matters most.
            </p>
            <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-4 space-y-2">
              <p className="text-sm font-medium text-gray-700 dark:text-gray-300">
                This wizard will help you configure:
              </p>
              <ul className="text-sm text-gray-600 dark:text-gray-400 space-y-1 ml-4 list-disc">
                <li>
                  <strong>File sync</strong> (optional) &mdash; Connect a folder
                  of markdown notes for bidirectional sync
                </li>
                <li>
                  <strong>AI features</strong> (optional) &mdash; Add your
                  Anthropic API key for AI-powered analysis
                </li>
              </ul>
            </div>

            {status?.data_directory && status.data_directory !== 'development mode' && (
              <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4 text-sm">
                <p className="text-blue-700 dark:text-blue-400">
                  Your data will be stored in:{' '}
                  <code className="bg-blue-100 dark:bg-blue-900/40 px-1 rounded">
                    {status.data_directory}
                  </code>
                </p>
              </div>
            )}

            {status?.legacy_migration?.needs_migration && (
              <div className="bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg p-4">
                <div className="flex items-start gap-3">
                  <AlertCircle className="w-5 h-5 text-amber-600 mt-0.5 flex-shrink-0" />
                  <div>
                    <p className="text-sm font-medium text-amber-800 dark:text-amber-300">
                      Existing data found
                    </p>
                    <p className="text-sm text-amber-700 dark:text-amber-400 mt-1">
                      A database was found at{' '}
                      <code className="bg-amber-100 dark:bg-amber-900/40 px-1 rounded text-xs">
                        {status.legacy_migration.legacy_path}
                      </code>
                      . Would you like to migrate it?
                    </p>
                    <label className="flex items-center gap-2 mt-3 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={config.migrate_legacy_data}
                        onChange={(e) =>
                          setConfig((prev) => ({
                            ...prev,
                            migrate_legacy_data: e.target.checked,
                          }))
                        }
                        className="rounded border-amber-300"
                      />
                      <span className="text-sm text-amber-800 dark:text-amber-300">
                        Yes, migrate my existing data
                      </span>
                    </label>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Step 1: File Sync */}
        {step === 1 && (
          <div className="space-y-4">
            <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100 mb-4">
              File Sync (Optional)
            </h2>
            <p className="text-gray-600 dark:text-gray-400 text-sm">
              Connect a folder of markdown files for bidirectional sync.
              Conduital will discover projects and areas from your file
              structure and keep them in sync with the database.
            </p>
            <div>
              <label className="label">Sync Folder Path</label>
              <div className="flex gap-2">
                <input
                  type="text"
                  className="input flex-1"
                  placeholder="e.g. C:\Users\You\Documents\Notes"
                  value={config.sync_folder}
                  onChange={(e) => {
                    setConfig((prev) => ({
                      ...prev,
                      sync_folder: e.target.value,
                    }));
                    setPathValid(null);
                  }}
                />
                <button
                  type="button"
                  onClick={validatePath}
                  disabled={!config.sync_folder.trim() || pathValidating}
                  className="btn btn-secondary"
                >
                  {pathValidating ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    'Validate'
                  )}
                </button>
              </div>
              {pathValid === true && (
                <p className="text-sm text-green-600 dark:text-green-400 mt-1 flex items-center gap-1">
                  <Check className="w-4 h-4" /> Valid folder path
                </p>
              )}
              {pathValid === false && (
                <p className="text-sm text-red-600 dark:text-red-400 mt-1 flex items-center gap-1">
                  <AlertCircle className="w-4 h-4" /> Folder not found or not accessible
                </p>
              )}
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
                Leave empty to skip. You can configure this later in Settings.
              </p>
            </div>
          </div>
        )}

        {/* Step 2: AI Setup */}
        {step === 2 && (
          <div className="space-y-4">
            <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100 mb-4">
              AI Features (Optional)
            </h2>
            <p className="text-gray-600 dark:text-gray-400 text-sm">
              Add an Anthropic API key to enable AI-powered features like project
              analysis, task suggestions, and intelligent unstuck recommendations.
            </p>

            <div>
              <label className="label">Anthropic API Key</label>
              <input
                type="password"
                className="input"
                placeholder="sk-ant-..."
                value={config.anthropic_api_key}
                onChange={(e) => {
                  setConfig((prev) => ({
                    ...prev,
                    anthropic_api_key: e.target.value,
                  }));
                  setAiTestResult(null);
                }}
              />
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                Get your API key from{' '}
                <a
                  href="https://console.anthropic.com/"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-primary-600 hover:underline"
                >
                  console.anthropic.com
                </a>
                . Usage costs are between you and Anthropic.
              </p>
            </div>

            {config.anthropic_api_key.trim() && (
              <div className="flex items-center gap-3">
                <button
                  type="button"
                  onClick={testAIConnection}
                  disabled={aiTesting}
                  className="btn btn-secondary"
                >
                  {aiTesting ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin mr-2" />
                      Testing...
                    </>
                  ) : (
                    'Test Connection'
                  )}
                </button>
                {aiTestResult && (
                  <span
                    className={`text-sm ${
                      aiTestResult.success
                        ? 'text-green-600 dark:text-green-400'
                        : 'text-red-600 dark:text-red-400'
                    }`}
                  >
                    {aiTestResult.success ? (
                      <span className="flex items-center gap-1">
                        <Check className="w-4 h-4" /> Connected
                      </span>
                    ) : (
                      aiTestResult.message
                    )}
                  </span>
                )}
              </div>
            )}

            <label className="flex items-center gap-3 cursor-pointer">
              <input
                type="checkbox"
                checked={config.ai_features_enabled}
                onChange={(e) =>
                  setConfig((prev) => ({
                    ...prev,
                    ai_features_enabled: e.target.checked,
                  }))
                }
                className="rounded border-gray-300"
              />
              <span className="text-sm text-gray-700 dark:text-gray-300">
                Enable AI features
              </span>
            </label>

            <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-4 text-sm text-gray-600 dark:text-gray-400">
              Without an API key, all other features work normally. AI features
              can always be configured later in Settings.
            </div>
          </div>
        )}

        {/* Step 3: Ready */}
        {step === 3 && (
          <div className="space-y-4">
            <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100 mb-4">
              You're All Set!
            </h2>
            <p className="text-gray-600 dark:text-gray-400">
              Here's a summary of your configuration:
            </p>
            <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-4 space-y-3">
              <div className="flex items-center gap-3">
                <FolderSync className="w-5 h-5 text-gray-400" />
                <div>
                  <p className="text-sm font-medium text-gray-700 dark:text-gray-300">
                    File Sync
                  </p>
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    {config.sync_folder.trim()
                      ? config.sync_folder
                      : 'Not configured (can be set up later)'}
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <Brain className="w-5 h-5 text-gray-400" />
                <div>
                  <p className="text-sm font-medium text-gray-700 dark:text-gray-300">
                    AI Features
                  </p>
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    {config.anthropic_api_key.trim()
                      ? `Configured${config.ai_features_enabled ? ' and enabled' : ' (disabled)'}`
                      : 'Not configured (can be set up later)'}
                  </p>
                </div>
              </div>
              {config.migrate_legacy_data && (
                <div className="flex items-center gap-3">
                  <AlertCircle className="w-5 h-5 text-amber-500" />
                  <div>
                    <p className="text-sm font-medium text-gray-700 dark:text-gray-300">
                      Data Migration
                    </p>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      Existing database will be migrated
                    </p>
                  </div>
                </div>
              )}
            </div>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              All settings can be changed later from the Settings page.
            </p>
          </div>
        )}
      </div>

      {/* Navigation */}
      <div className="flex items-center justify-between mt-6">
        <button
          type="button"
          onClick={() => {
            if (step > 0) {
              setStep(step - 1);
            } else {
              // Skip setup entirely (mark complete with defaults)
              handleSubmit();
            }
          }}
          className="btn btn-secondary flex items-center gap-2"
        >
          <ArrowLeft className="w-4 h-4" />
          {step === 0 ? 'Skip Setup' : 'Back'}
        </button>

        {step < STEPS.length - 1 ? (
          <button
            type="button"
            onClick={() => setStep(step + 1)}
            className="btn btn-primary flex items-center gap-2"
          >
            Next
            <ArrowRight className="w-4 h-4" />
          </button>
        ) : (
          <button
            type="button"
            onClick={handleSubmit}
            disabled={submitting}
            className="btn btn-primary flex items-center gap-2"
          >
            {submitting ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Saving...
              </>
            ) : (
              <>
                <Check className="w-4 h-4" />
                Get Started
              </>
            )}
          </button>
        )}
      </div>
    </div>
  );
}
