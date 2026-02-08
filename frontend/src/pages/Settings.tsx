import { useState, useEffect, useCallback } from 'react';
import { Settings as SettingsIcon, Database, RefreshCw, Brain, FolderTree, Plus, Trash2, Edit2, Check, X, Lightbulb, AlertTriangle, Sun, Moon, Monitor, Wifi, WifiOff, Eye, EyeOff, ChevronDown, ChevronRight, Download, HardDrive } from 'lucide-react';
import toast from 'react-hot-toast';
import { useAreaMappings, useUpdateAreaMappings, useAreaMappingSuggestions, useScanProjects } from '@/hooks/useDiscovery';
import { useTheme } from '@/context/ThemeContext';
import { api } from '@/services/api';

const SETTINGS_SECTIONS_KEY = 'pt-settings-sections';

type SectionId = 'appearance' | 'area-mappings' | 'database' | 'sync' | 'ai' | 'momentum' | 'export';

function loadCollapsedSections(): Set<SectionId> {
  try {
    const stored = localStorage.getItem(SETTINGS_SECTIONS_KEY);
    if (stored) {
      return new Set(JSON.parse(stored) as SectionId[]);
    }
  } catch {
    localStorage.removeItem(SETTINGS_SECTIONS_KEY);
  }
  return new Set<SectionId>(['appearance', 'area-mappings', 'database', 'sync', 'ai', 'momentum', 'export']);
}

export function Settings() {
  const [collapsedSections, setCollapsedSections] = useState<Set<SectionId>>(loadCollapsedSections);

  const toggleSection = useCallback((id: SectionId) => {
    setCollapsedSections(prev => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      localStorage.setItem(SETTINGS_SECTIONS_KEY, JSON.stringify([...next]));
      return next;
    });
  }, []);
  const [editingPrefix, setEditingPrefix] = useState<string | null>(null);
  const [editValue, setEditValue] = useState('');
  const [newPrefix, setNewPrefix] = useState('');
  const [newAreaName, setNewAreaName] = useState('');
  const [showAddForm, setShowAddForm] = useState(false);

  // AI Settings state
  const [aiProvider, setAiProvider] = useState('anthropic');
  const [aiEnabled, setAiEnabled] = useState(false);
  const [aiModel, setAiModel] = useState('');
  const [aiMaxTokens, setAiMaxTokens] = useState(2000);
  const [apiKeyConfigured, setApiKeyConfigured] = useState(false);
  const [apiKeyMasked, setApiKeyMasked] = useState<string | null>(null);
  const [openaiKeyConfigured, setOpenaiKeyConfigured] = useState(false);
  const [openaiKeyMasked, setOpenaiKeyMasked] = useState<string | null>(null);
  const [googleKeyConfigured, setGoogleKeyConfigured] = useState(false);
  const [googleKeyMasked, setGoogleKeyMasked] = useState<string | null>(null);
  const [newApiKey, setNewApiKey] = useState('');
  const [newOpenaiKey, setNewOpenaiKey] = useState('');
  const [newGoogleKey, setNewGoogleKey] = useState('');
  const [showApiKey, setShowApiKey] = useState(false);
  const [aiLoading, setAiLoading] = useState(true);
  const [aiSaving, setAiSaving] = useState(false);
  const [aiTestResult, setAiTestResult] = useState<{ success: boolean; message: string } | null>(null);
  const [providerModels, setProviderModels] = useState<Record<string, Array<{ id: string; name: string }>>>({});

  // Momentum Settings state
  const [stalledThreshold, setStalledThreshold] = useState(14);
  const [atRiskThreshold, setAtRiskThreshold] = useState(7);
  const [activityDecayDays, setActivityDecayDays] = useState(30);
  const [recalculateInterval, setRecalculateInterval] = useState(3600);
  const [momentumLoading, setMomentumLoading] = useState(true);
  const [momentumSaving, setMomentumSaving] = useState(false);

  // Export state
  const [exportPreview, setExportPreview] = useState<{
    entity_counts: Record<string, number>;
    estimated_size_display: string;
  } | null>(null);
  const [exportLoading, setExportLoading] = useState(false);
  const [downloadingJSON, setDownloadingJSON] = useState(false);
  const [downloadingBackup, setDownloadingBackup] = useState(false);

  const { theme, setTheme } = useTheme();

  // Load Momentum settings on mount
  useEffect(() => {
    api.getMomentumSettings()
      .then((data) => {
        setStalledThreshold(data.stalled_threshold_days);
        setAtRiskThreshold(data.at_risk_threshold_days);
        setActivityDecayDays(data.activity_decay_days);
        setRecalculateInterval(data.recalculate_interval);
        setMomentumLoading(false);
      })
      .catch(() => setMomentumLoading(false));
  }, []);

  // Load AI settings on mount
  useEffect(() => {
    api.getAISettings()
      .then((data) => {
        setAiProvider(data.ai_provider);
        setAiEnabled(data.ai_features_enabled);
        setAiModel(data.ai_model);
        setAiMaxTokens(data.ai_max_tokens);
        setApiKeyConfigured(data.api_key_configured);
        setApiKeyMasked(data.api_key_masked);
        setOpenaiKeyConfigured(data.openai_key_configured);
        setOpenaiKeyMasked(data.openai_key_masked);
        setGoogleKeyConfigured(data.google_key_configured);
        setGoogleKeyMasked(data.google_key_masked);
        setProviderModels(data.provider_models);
        setAiLoading(false);
      })
      .catch(() => {
        setAiLoading(false);
      });
  }, []);

  const handleSaveAISettings = async () => {
    setAiSaving(true);
    try {
      const update: Record<string, unknown> = {
        ai_provider: aiProvider,
        ai_features_enabled: aiEnabled,
        ai_model: aiModel,
        ai_max_tokens: aiMaxTokens,
      };
      if (newApiKey.trim()) {
        update.api_key = newApiKey.trim();
      }
      if (newOpenaiKey.trim()) {
        update.openai_api_key = newOpenaiKey.trim();
      }
      if (newGoogleKey.trim()) {
        update.google_api_key = newGoogleKey.trim();
      }
      const result = await api.updateAISettings(update);
      setApiKeyConfigured(result.api_key_configured);
      setApiKeyMasked(result.api_key_masked);
      setOpenaiKeyConfigured(result.openai_key_configured);
      setOpenaiKeyMasked(result.openai_key_masked);
      setGoogleKeyConfigured(result.google_key_configured);
      setGoogleKeyMasked(result.google_key_masked);
      setProviderModels(result.provider_models);
      setNewApiKey('');
      setNewOpenaiKey('');
      setNewGoogleKey('');
      toast.success('AI settings saved');
    } catch {
      toast.error('Failed to update AI settings');
    }
    setAiSaving(false);
  };

  const handleTestAI = async () => {
    setAiTestResult(null);
    try {
      const result = await api.testAIConnection();
      setAiTestResult(result);
      if (result.success) {
        toast.success(result.message);
      } else {
        toast.error(result.message);
      }
    } catch {
      setAiTestResult({ success: false, message: 'Connection test failed' });
      toast.error('Connection test failed');
    }
  };

  // Get models for current provider
  const currentModels = providerModels[aiProvider] || [];

  // Provider display info
  const providerLabels: Record<string, string> = {
    anthropic: 'Anthropic (Claude)',
    openai: 'OpenAI (GPT)',
    google: 'Google (Gemini)',
  };

  const providerKeyPlaceholders: Record<string, string> = {
    anthropic: 'Enter Anthropic API key (sk-ant-...)',
    openai: 'Enter OpenAI API key (sk-...)',
    google: 'Enter Google API key',
  };

  // Current provider's key state
  const currentKeyConfigured = aiProvider === 'anthropic' ? apiKeyConfigured : aiProvider === 'openai' ? openaiKeyConfigured : googleKeyConfigured;
  const currentKeyMasked = aiProvider === 'anthropic' ? apiKeyMasked : aiProvider === 'openai' ? openaiKeyMasked : googleKeyMasked;
  const currentNewKey = aiProvider === 'anthropic' ? newApiKey : aiProvider === 'openai' ? newOpenaiKey : newGoogleKey;
  const setCurrentNewKey = aiProvider === 'anthropic' ? setNewApiKey : aiProvider === 'openai' ? setNewOpenaiKey : setNewGoogleKey;

  const { data: mappings, isLoading: mappingsLoading } = useAreaMappings();
  const { data: suggestions } = useAreaMappingSuggestions();
  const updateMappings = useUpdateAreaMappings();
  const scanProjects = useScanProjects();

  const handleStartEdit = (prefix: string, currentValue: string) => {
    setEditingPrefix(prefix);
    setEditValue(currentValue);
  };

  const handleCancelEdit = () => {
    setEditingPrefix(null);
    setEditValue('');
  };

  const handleSaveEdit = (prefix: string) => {
    if (!editValue.trim()) {
      toast.error('Area name cannot be empty');
      return;
    }
    if (!mappings) return;

    const newMappings = { ...mappings, [prefix]: editValue.trim() };
    updateMappings.mutate(newMappings, {
      onSuccess: () => {
        toast.success('Mapping updated (runtime only)');
        setEditingPrefix(null);
        setEditValue('');
      },
      onError: () => {
        toast.error('Failed to update mapping');
      },
    });
  };

  const handleDeleteMapping = (prefix: string) => {
    if (!mappings) return;
    if (!confirm(`Delete mapping for prefix "${prefix}"?`)) return;

    const newMappings = { ...mappings };
    delete newMappings[prefix];
    updateMappings.mutate(newMappings, {
      onSuccess: () => {
        toast.success('Mapping deleted (runtime only)');
      },
      onError: () => {
        toast.error('Failed to delete mapping');
      },
    });
  };

  const handleAddMapping = () => {
    if (!newPrefix.trim() || !newAreaName.trim()) {
      toast.error('Both prefix and area name are required');
      return;
    }
    if (!/^\d{2}$/.test(newPrefix)) {
      toast.error('Prefix must be exactly 2 digits (e.g., "01", "10")');
      return;
    }
    if (mappings && mappings[newPrefix]) {
      toast.error(`Prefix "${newPrefix}" already exists`);
      return;
    }

    const newMappings = { ...mappings, [newPrefix]: newAreaName.trim() };
    updateMappings.mutate(newMappings, {
      onSuccess: () => {
        toast.success('Mapping added (runtime only)');
        setNewPrefix('');
        setNewAreaName('');
        setShowAddForm(false);
      },
      onError: () => {
        toast.error('Failed to add mapping');
      },
    });
  };

  const handleAddSuggestion = (prefix: string, suggestedName: string) => {
    const newMappings = { ...mappings, [prefix]: suggestedName };
    updateMappings.mutate(newMappings, {
      onSuccess: () => {
        toast.success(`Added mapping for prefix "${prefix}"`);
      },
      onError: () => {
        toast.error('Failed to add mapping');
      },
    });
  };

  const handleRescanProjects = () => {
    scanProjects.mutate(undefined, {
      onSuccess: (data) => {
        toast.success(`Scan complete: ${data.imported} imported, ${data.skipped} skipped`);
      },
      onError: () => {
        toast.error('Failed to scan projects');
      },
    });
  };

  const handleSaveMomentumSettings = async () => {
    setMomentumSaving(true);
    try {
      const result = await api.updateMomentumSettings({
        stalled_threshold_days: stalledThreshold,
        at_risk_threshold_days: atRiskThreshold,
        activity_decay_days: activityDecayDays,
        recalculate_interval: recalculateInterval,
      });
      setStalledThreshold(result.stalled_threshold_days);
      setAtRiskThreshold(result.at_risk_threshold_days);
      setActivityDecayDays(result.activity_decay_days);
      setRecalculateInterval(result.recalculate_interval);
      toast.success('Momentum settings saved');
    } catch {
      toast.error('Failed to save momentum settings');
    }
    setMomentumSaving(false);
  };

  const handleLoadExportPreview = async () => {
    setExportLoading(true);
    try {
      const preview = await api.getExportPreview();
      setExportPreview(preview);
    } catch {
      toast.error('Failed to load export preview');
    }
    setExportLoading(false);
  };

  const handleDownloadJSON = async () => {
    setDownloadingJSON(true);
    try {
      await api.downloadJSONExport();
      toast.success('JSON export downloaded');
    } catch {
      toast.error('Failed to download JSON export');
    }
    setDownloadingJSON(false);
  };

  const handleDownloadBackup = async () => {
    setDownloadingBackup(true);
    try {
      await api.downloadDatabaseBackup();
      toast.success('Database backup downloaded');
    } catch {
      toast.error('Failed to download database backup');
    }
    setDownloadingBackup(false);
  };

  const sortedMappings = mappings
    ? Object.entries(mappings).sort(([a], [b]) => a.localeCompare(b))
    : [];

  const unmappedPrefixes = suggestions?.unmapped_prefixes
    ? Object.entries(suggestions.unmapped_prefixes)
    : [];

  return (
    <div className="p-8">
      {/* Header */}
      <header className="mb-8">
        <div className="flex items-center gap-3 mb-2">
          <SettingsIcon className="w-8 h-8 text-primary-600" />
          <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">Settings</h1>
        </div>
        <p className="text-gray-600 dark:text-gray-400">Configure your Project Tracker</p>
      </header>

      {/* Settings Sections */}
      <div className="space-y-6">
        {/* Appearance Section */}
        <section className="card">
          <button
            onClick={() => toggleSection('appearance')}
            className="flex items-center gap-3 w-full text-left"
          >
            {collapsedSections.has('appearance') ? <ChevronRight className="w-5 h-5 text-gray-400" /> : <ChevronDown className="w-5 h-5 text-gray-400" />}
            <Sun className="w-6 h-6 text-primary-600" />
            <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100">Appearance</h2>
          </button>
          {!collapsedSections.has('appearance') && (
            <div className="mt-4">
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                Choose your preferred color theme.
              </p>
              <div className="flex gap-3">
                {([
                  { value: 'light' as const, label: 'Light', icon: Sun },
                  { value: 'dark' as const, label: 'Dark', icon: Moon },
                  { value: 'system' as const, label: 'System', icon: Monitor },
                ]).map(({ value, label, icon: Icon }) => (
                  <button
                    key={value}
                    onClick={() => setTheme(value)}
                    className={`flex items-center gap-2 px-4 py-2.5 rounded-lg border text-sm font-medium transition-colors ${
                      theme === value
                        ? 'border-primary-500 bg-primary-50 text-primary-700 dark:bg-primary-900/30 dark:text-primary-400 dark:border-primary-500'
                        : 'border-gray-200 text-gray-600 hover:bg-gray-50 dark:border-gray-600 dark:text-gray-400 dark:hover:bg-gray-700'
                    }`}
                  >
                    <Icon className="w-4 h-4" />
                    {label}
                  </button>
                ))}
              </div>
            </div>
          )}
        </section>

        {/* Area Mapping Section */}
        <section className="card">
          <div className="flex items-center justify-between">
            <button
              onClick={() => toggleSection('area-mappings')}
              className="flex items-center gap-3 text-left"
            >
              {collapsedSections.has('area-mappings') ? <ChevronRight className="w-5 h-5 text-gray-400" /> : <ChevronDown className="w-5 h-5 text-gray-400" />}
              <FolderTree className="w-6 h-6 text-primary-600" />
              <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100">Area Prefix Mappings</h2>
            </button>
            {!collapsedSections.has('area-mappings') && (
              <div className="flex items-center gap-2">
                <button
                  onClick={handleRescanProjects}
                  disabled={scanProjects.isPending}
                  className="btn btn-secondary btn-sm flex items-center gap-2"
                >
                  <RefreshCw className={`w-4 h-4 ${scanProjects.isPending ? 'animate-spin' : ''}`} />
                  Rescan
                </button>
                <button
                  onClick={() => setShowAddForm(true)}
                  className="btn btn-primary btn-sm flex items-center gap-2"
                >
                  <Plus className="w-4 h-4" />
                  Add Mapping
                </button>
              </div>
            )}
          </div>
          {!collapsedSections.has('area-mappings') && (
          <div className="mt-4">
          <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
            Map folder prefixes to area names. Projects in folders like <code className="bg-gray-100 dark:bg-gray-700 px-1 rounded">01.05 Project_Name</code> will be assigned to the area mapped to prefix "01".
          </p>

          {/* Runtime Warning */}
          <div className="bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg p-3 mb-4 flex items-start gap-2">
            <AlertTriangle className="w-5 h-5 text-amber-600 dark:text-amber-400 flex-shrink-0 mt-0.5" />
            <p className="text-sm text-amber-800 dark:text-amber-300">
              <strong>Note:</strong> Changes are applied at runtime only. To persist changes permanently, update <code className="bg-amber-100 dark:bg-amber-900/40 px-1 rounded">AREA_PREFIX_MAP</code> in the backend <code className="bg-amber-100 dark:bg-amber-900/40 px-1 rounded">.env</code> file.
            </p>
          </div>

          {/* Add New Mapping Form */}
          {showAddForm && (
            <div className="bg-gray-50 dark:bg-gray-700/50 border border-gray-200 dark:border-gray-600 rounded-lg p-4 mb-4">
              <h3 className="font-medium text-gray-900 dark:text-gray-100 mb-3">Add New Mapping</h3>
              <div className="flex items-end gap-3">
                <div>
                  <label className="label">Prefix</label>
                  <input
                    type="text"
                    className="input w-20"
                    placeholder="01"
                    maxLength={2}
                    value={newPrefix}
                    onChange={(e) => setNewPrefix(e.target.value.replace(/\D/g, '').slice(0, 2))}
                  />
                </div>
                <div className="flex-1">
                  <label className="label">Area Name</label>
                  <input
                    type="text"
                    className="input"
                    placeholder="Literary Projects"
                    value={newAreaName}
                    onChange={(e) => setNewAreaName(e.target.value)}
                  />
                </div>
                <button
                  onClick={handleAddMapping}
                  disabled={updateMappings.isPending}
                  className="btn btn-primary"
                >
                  Add
                </button>
                <button
                  onClick={() => {
                    setShowAddForm(false);
                    setNewPrefix('');
                    setNewAreaName('');
                  }}
                  className="btn btn-secondary"
                >
                  Cancel
                </button>
              </div>
            </div>
          )}

          {/* Mappings Table */}
          {mappingsLoading ? (
            <div className="text-center py-8 text-gray-500 dark:text-gray-400">Loading mappings...</div>
          ) : sortedMappings.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50 dark:bg-gray-700/50 border-b dark:border-gray-600">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase w-24">Prefix</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Area Name</th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase w-32">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                  {sortedMappings.map(([prefix, areaName]) => (
                    <tr key={prefix} className="hover:bg-gray-50 dark:hover:bg-gray-700/50">
                      <td className="px-4 py-3">
                        <span className="font-mono bg-gray-100 dark:bg-gray-700 px-2 py-1 rounded text-sm">{prefix}</span>
                      </td>
                      <td className="px-4 py-3">
                        {editingPrefix === prefix ? (
                          <input
                            type="text"
                            className="input py-1"
                            value={editValue}
                            onChange={(e) => setEditValue(e.target.value)}
                            autoFocus
                            onKeyDown={(e) => {
                              if (e.key === 'Enter') handleSaveEdit(prefix);
                              if (e.key === 'Escape') handleCancelEdit();
                            }}
                          />
                        ) : (
                          <span className="text-gray-900 dark:text-gray-100">{areaName}</span>
                        )}
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center justify-end gap-2">
                          {editingPrefix === prefix ? (
                            <>
                              <button
                                onClick={() => handleSaveEdit(prefix)}
                                className="p-1.5 text-green-600 hover:bg-green-50 dark:hover:bg-green-900/30 rounded transition-colors"
                                title="Save"
                              >
                                <Check className="w-4 h-4" />
                              </button>
                              <button
                                onClick={handleCancelEdit}
                                className="p-1.5 text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-600 rounded transition-colors"
                                title="Cancel"
                              >
                                <X className="w-4 h-4" />
                              </button>
                            </>
                          ) : (
                            <>
                              <button
                                onClick={() => handleStartEdit(prefix, areaName)}
                                className="p-1.5 text-gray-400 hover:text-primary-600 hover:bg-gray-100 dark:hover:bg-gray-600 rounded transition-colors"
                                title="Edit"
                              >
                                <Edit2 className="w-4 h-4" />
                              </button>
                              <button
                                onClick={() => handleDeleteMapping(prefix)}
                                className="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-900/30 rounded transition-colors"
                                title="Delete"
                              >
                                <Trash2 className="w-4 h-4" />
                              </button>
                            </>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500 dark:text-gray-400">
              No mappings configured. Add a mapping to start.
            </div>
          )}

          {/* Suggestions Section */}
          {unmappedPrefixes.length > 0 && (
            <div className="mt-6 pt-6 border-t border-gray-200 dark:border-gray-700">
              <div className="flex items-center gap-2 mb-3">
                <Lightbulb className="w-5 h-5 text-amber-500" />
                <h3 className="font-medium text-gray-900 dark:text-gray-100">Unmapped Prefixes Found</h3>
              </div>
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                The following folder prefixes don't have area mappings. Click "Add" to create a mapping.
              </p>
              <div className="space-y-2">
                {unmappedPrefixes.map(([prefix, data]) => (
                  <div
                    key={prefix}
                    className="flex items-center justify-between p-3 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg"
                  >
                    <div>
                      <span className="font-mono bg-amber-100 dark:bg-amber-900/40 px-2 py-1 rounded text-sm mr-3">{prefix}</span>
                      <span className="text-gray-700 dark:text-gray-300">
                        Suggested: <strong>{data.suggested_name}</strong>
                      </span>
                      <span className="text-gray-500 dark:text-gray-400 text-sm ml-2">
                        ({data.folders.length} folder{data.folders.length !== 1 ? 's' : ''})
                      </span>
                    </div>
                    <button
                      onClick={() => handleAddSuggestion(prefix, data.suggested_name)}
                      disabled={updateMappings.isPending}
                      className="btn btn-sm btn-primary"
                    >
                      Add
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}
          </div>
          )}
        </section>

        {/* Database Section */}
        <section className="card">
          <button
            onClick={() => toggleSection('database')}
            className="flex items-center gap-3 w-full text-left"
          >
            {collapsedSections.has('database') ? <ChevronRight className="w-5 h-5 text-gray-400" /> : <ChevronDown className="w-5 h-5 text-gray-400" />}
            <Database className="w-6 h-6 text-primary-600" />
            <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100">Database</h2>
          </button>
          {!collapsedSections.has('database') && (
            <div className="space-y-4 mt-4">
              <div>
                <label className="label">Database Location</label>
                <input
                  type="text"
                  className="input"
                  value="~/.project-tracker/tracker.db"
                  disabled
                />
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                  SQLite database location (read-only)
                </p>
              </div>
            </div>
          )}
        </section>

        {/* Sync Section */}
        <section className="card">
          <button
            onClick={() => toggleSection('sync')}
            className="flex items-center gap-3 w-full text-left"
          >
            {collapsedSections.has('sync') ? <ChevronRight className="w-5 h-5 text-gray-400" /> : <ChevronDown className="w-5 h-5 text-gray-400" />}
            <RefreshCw className="w-6 h-6 text-primary-600" />
            <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100">Second Brain Sync</h2>
          </button>
          {!collapsedSections.has('sync') && (
            <div className="space-y-4 mt-4">
              <div>
                <label className="label">Second Brain Root</label>
                <input
                  type="text"
                  className="input"
                  placeholder="/path/to/your/second-brain"
                  disabled
                />
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                  Configure this in backend .env file
                </p>
              </div>
              <div>
                <label className="label">Watch Directories</label>
                <input
                  type="text"
                  className="input"
                  value="10_Projects, 20_Areas"
                  disabled
                />
              </div>
            </div>
          )}
        </section>

        {/* AI Configuration Section */}
        <section className="card">
          <button
            onClick={() => toggleSection('ai')}
            className="flex items-center gap-3 w-full text-left"
          >
            {collapsedSections.has('ai') ? <ChevronRight className="w-5 h-5 text-gray-400" /> : <ChevronDown className="w-5 h-5 text-gray-400" />}
            <Brain className="w-6 h-6 text-primary-600" />
            <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100">AI Configuration</h2>
          </button>

          {!collapsedSections.has('ai') && (aiLoading ? (
            <div className="text-center py-8 text-gray-500 dark:text-gray-400">Loading AI settings...</div>
          ) : (
            <div className="space-y-5">
              {/* Enable/Disable Toggle */}
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium text-gray-900 dark:text-gray-100">AI Features Enabled</p>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Enable AI for task generation, project analysis, and suggestions</p>
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    className="sr-only peer"
                    checked={aiEnabled}
                    onChange={(e) => setAiEnabled(e.target.checked)}
                  />
                  <div className="w-11 h-6 bg-gray-200 dark:bg-gray-600 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 dark:after:border-gray-500 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-600"></div>
                </label>
              </div>

              {/* Provider Selection */}
              <div>
                <label className="label">AI Provider</label>
                <select
                  className="input"
                  value={aiProvider}
                  onChange={(e) => {
                    const newProvider = e.target.value;
                    setAiProvider(newProvider);
                    // Auto-select first model for the new provider
                    const models = providerModels[newProvider];
                    if (models?.length) {
                      setAiModel(models[0].id);
                    }
                  }}
                >
                  <option value="anthropic">Anthropic (Claude)</option>
                  <option value="openai">OpenAI (GPT)</option>
                  <option value="google">Google (Gemini)</option>
                </select>
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                  Choose your AI provider
                </p>
              </div>

              {/* API Key for Current Provider */}
              <div>
                <label className="label">{providerLabels[aiProvider]} API Key</label>
                <div className="flex items-center gap-2">
                  <div className="flex-1 relative">
                    <input
                      type={showApiKey ? 'text' : 'password'}
                      className="input pr-10"
                      placeholder={currentKeyConfigured ? `Configured (${currentKeyMasked})` : providerKeyPlaceholders[aiProvider]}
                      value={currentNewKey}
                      onChange={(e) => setCurrentNewKey(e.target.value)}
                    />
                    <button
                      type="button"
                      onClick={() => setShowApiKey(!showApiKey)}
                      className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                    >
                      {showApiKey ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                  </div>
                  <div className="flex items-center gap-1">
                    {currentKeyConfigured ? (
                      <span className="inline-flex items-center gap-1 px-2 py-1 rounded text-xs bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400">
                        <Wifi className="w-3 h-3" />
                        Configured
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 px-2 py-1 rounded text-xs bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400">
                        <WifiOff className="w-3 h-3" />
                        Not set
                      </span>
                    )}
                  </div>
                </div>
              </div>

              {/* Model Selection - Dynamic per provider */}
              <div>
                <label className="label">Model</label>
                <select
                  className="input"
                  value={aiModel}
                  onChange={(e) => setAiModel(e.target.value)}
                >
                  {currentModels.map((m) => (
                    <option key={m.id} value={m.id}>{m.name}</option>
                  ))}
                </select>
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                  Select the model for AI features
                </p>
              </div>

              {/* Max Tokens */}
              <div>
                <label className="label">Max Tokens</label>
                <div className="flex items-center gap-3">
                  <input
                    type="range"
                    min="100"
                    max="4000"
                    step="100"
                    value={aiMaxTokens}
                    onChange={(e) => setAiMaxTokens(Number(e.target.value))}
                    className="flex-1"
                  />
                  <span className="text-sm font-mono text-gray-700 dark:text-gray-300 w-16 text-right">
                    {aiMaxTokens}
                  </span>
                </div>
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                  Maximum tokens per AI response (100-4000)
                </p>
              </div>

              {/* Action Buttons */}
              <div className="flex items-center gap-3 pt-2">
                <button
                  onClick={handleSaveAISettings}
                  disabled={aiSaving}
                  className="btn btn-primary flex items-center gap-2"
                >
                  {aiSaving ? (
                    <RefreshCw className="w-4 h-4 animate-spin" />
                  ) : (
                    <Check className="w-4 h-4" />
                  )}
                  Save Settings
                </button>
                <button
                  onClick={handleTestAI}
                  className="btn btn-secondary flex items-center gap-2"
                >
                  <Wifi className="w-4 h-4" />
                  Test Connection
                </button>
                {aiTestResult && (
                  <span className={`text-sm ${aiTestResult.success ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>
                    {aiTestResult.message}
                  </span>
                )}
              </div>
            </div>
          ))}
        </section>

        {/* Momentum Section */}
        <section className="card">
          <button
            onClick={() => toggleSection('momentum')}
            className="flex items-center gap-3 w-full text-left"
          >
            {collapsedSections.has('momentum') ? <ChevronRight className="w-5 h-5 text-gray-400" /> : <ChevronDown className="w-5 h-5 text-gray-400" />}
            <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100">Momentum Thresholds</h2>
          </button>
          {!collapsedSections.has('momentum') && (momentumLoading ? (
            <div className="text-center py-8 text-gray-500 dark:text-gray-400">Loading momentum settings...</div>
          ) : (
            <div className="space-y-4 mt-4">
              <div>
                <label className="label">Stalled Threshold (days)</label>
                <input
                  type="number"
                  className="input w-32"
                  value={stalledThreshold}
                  min={1}
                  max={90}
                  onChange={(e) => setStalledThreshold(Number(e.target.value))}
                />
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                  Projects are marked stalled after this many days of inactivity
                </p>
              </div>
              <div>
                <label className="label">At Risk Threshold (days)</label>
                <input
                  type="number"
                  className="input w-32"
                  value={atRiskThreshold}
                  min={1}
                  max={90}
                  onChange={(e) => setAtRiskThreshold(Number(e.target.value))}
                />
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                  Projects are flagged at risk after this many days
                </p>
              </div>
              <div>
                <label className="label">Activity Decay (days)</label>
                <input
                  type="number"
                  className="input w-32"
                  value={activityDecayDays}
                  min={7}
                  max={365}
                  onChange={(e) => setActivityDecayDays(Number(e.target.value))}
                />
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                  Activity factor decays to 0 after this many days without activity
                </p>
              </div>
              <div className="pt-2">
                <button
                  onClick={handleSaveMomentumSettings}
                  disabled={momentumSaving}
                  className="btn btn-primary flex items-center gap-2"
                >
                  {momentumSaving ? (
                    <RefreshCw className="w-4 h-4 animate-spin" />
                  ) : (
                    <Check className="w-4 h-4" />
                  )}
                  Save Thresholds
                </button>
              </div>
            </div>
          ))}
        </section>

        {/* Data Export Section */}
        <section className="card">
          <button
            onClick={() => toggleSection('export')}
            className="flex items-center gap-3 w-full text-left"
          >
            {collapsedSections.has('export') ? <ChevronRight className="w-5 h-5 text-gray-400" /> : <ChevronDown className="w-5 h-5 text-gray-400" />}
            <Download className="w-6 h-6 text-primary-600" />
            <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100">Data Export</h2>
          </button>
          {!collapsedSections.has('export') && (
            <div className="space-y-4 mt-4">
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Export your data for backup or migration purposes.
              </p>

              {/* Preview */}
              {exportPreview ? (
                <div className="bg-gray-50 dark:bg-gray-700/50 border border-gray-200 dark:border-gray-600 rounded-lg p-4">
                  <h3 className="font-medium text-gray-900 dark:text-gray-100 mb-2">Export Summary</h3>
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-sm">
                    {Object.entries(exportPreview.entity_counts).map(([key, count]) => (
                      <div key={key} className="text-center">
                        <div className="text-lg font-bold text-gray-900 dark:text-gray-100">{count}</div>
                        <div className="text-gray-500 dark:text-gray-400 capitalize">{key.replace('_', ' ')}</div>
                      </div>
                    ))}
                  </div>
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-3">
                    Estimated size: {exportPreview.estimated_size_display}
                  </p>
                </div>
              ) : (
                <button
                  onClick={handleLoadExportPreview}
                  disabled={exportLoading}
                  className="btn btn-secondary btn-sm flex items-center gap-2"
                >
                  {exportLoading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Database className="w-4 h-4" />}
                  Preview Export Data
                </button>
              )}

              {/* Download Buttons */}
              <div className="flex flex-wrap gap-3">
                <button
                  onClick={handleDownloadJSON}
                  disabled={downloadingJSON}
                  className="btn btn-primary flex items-center gap-2"
                >
                  {downloadingJSON ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />}
                  Export as JSON
                </button>
                <button
                  onClick={handleDownloadBackup}
                  disabled={downloadingBackup}
                  className="btn btn-secondary flex items-center gap-2"
                >
                  {downloadingBackup ? <RefreshCw className="w-4 h-4 animate-spin" /> : <HardDrive className="w-4 h-4" />}
                  Download Database Backup
                </button>
              </div>

              <p className="text-xs text-gray-500 dark:text-gray-400">
                JSON export includes all projects, tasks, areas, goals, visions, and inbox items.
                Database backup is a raw SQLite copy.
              </p>
            </div>
          )}
        </section>

        {/* Info Section */}
        <section className="card bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800">
          <p className="text-sm text-blue-800 dark:text-blue-300">
            <strong>Note:</strong> Most settings are configured in the backend .env file.
            Restart the backend server after making changes to environment variables.
          </p>
        </section>
      </div>
    </div>
  );
}
