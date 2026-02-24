import { useState } from 'react';
import toast from 'react-hot-toast';
import { Plus, Trash2, Edit2, Zap, ToggleLeft, ToggleRight } from 'lucide-react';
import { Modal } from '@/components/common/Modal';
import {
  usePrefetchRules,
  useCreatePrefetchRule,
  useUpdatePrefetchRule,
  useDeletePrefetchRule,
  type PrefetchRule,
  type PrefetchRuleCreate,
  type PrefetchRuleUpdate,
} from '@/hooks/useMemory';

export function PrefetchRuleCreateButton() {
  const [isOpen, setIsOpen] = useState(false);
  return (
    <>
      <button
        onClick={() => setIsOpen(true)}
        className="btn btn-primary flex items-center gap-2"
      >
        <Plus className="w-4 h-4" />
        New Rule
      </button>
      {isOpen && <CreatePrefetchRuleModal onClose={() => setIsOpen(false)} />}
    </>
  );
}

export function PrefetchRulesView() {
  const { data: rules, isLoading, isError } = usePrefetchRules();
  const updateRule = useUpdatePrefetchRule();
  const deleteRule = useDeletePrefetchRule();
  const [editingRule, setEditingRule] = useState<PrefetchRule | null>(null);

  const handleToggleActive = (rule: PrefetchRule) => {
    updateRule.mutate(
      { name: rule.name, data: { is_active: !rule.is_active } },
      {
        onSuccess: () => toast.success(rule.is_active ? 'Rule deactivated' : 'Rule activated'),
        onError: () => toast.error('Failed to update rule'),
      }
    );
  };

  const handleDelete = (rule: PrefetchRule) => {
    if (!confirm(`Delete prefetch rule "${rule.name}"? This cannot be undone.`)) return;
    deleteRule.mutate(rule.name, {
      onSuccess: () => toast.success('Prefetch rule deleted'),
      onError: () => toast.error('Failed to delete rule'),
    });
  };

  if (isError) {
    return (
      <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
        <p className="text-red-800 dark:text-red-300 text-sm">
          Failed to load prefetch rules. The memory layer module may not be enabled.
        </p>
      </div>
    );
  }

  if (isLoading) {
    return <div className="text-center py-12 text-gray-500 dark:text-gray-400">Loading prefetch rules...</div>;
  }

  if (!rules || rules.length === 0) {
    return (
      <div className="card text-center py-12">
        <Zap className="w-12 h-12 text-gray-400 mx-auto mb-4" />
        <h3 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-2">No prefetch rules</h3>
        <p className="text-gray-600 dark:text-gray-400 mb-6">
          Prefetch rules preload memory object bundles when a trigger condition fires.
        </p>
      </div>
    );
  }

  return (
    <>
      <div className="mb-3 text-sm text-gray-600 dark:text-gray-400">
        {rules.length} rule{rules.length !== 1 ? 's' : ''} — {rules.filter((r) => r.is_active).length} active
      </div>

      <div className="space-y-3">
        {rules.map((rule) => (
          <div
            key={rule.id}
            className={`card flex items-start gap-4 py-3 transition-opacity ${!rule.is_active ? 'opacity-60' : ''}`}
          >
            {/* Active toggle */}
            <button
              onClick={() => handleToggleActive(rule)}
              title={rule.is_active ? 'Click to deactivate' : 'Click to activate'}
              className={`mt-0.5 flex-shrink-0 transition-colors ${
                rule.is_active
                  ? 'text-green-600 dark:text-green-400 hover:text-green-800'
                  : 'text-gray-400 hover:text-gray-600 dark:hover:text-gray-300'
              }`}
            >
              {rule.is_active ? (
                <ToggleRight className="w-6 h-6" />
              ) : (
                <ToggleLeft className="w-6 h-6" />
              )}
            </button>

            {/* Rule details */}
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 flex-wrap">
                <span className="font-medium text-gray-900 dark:text-gray-100 font-mono text-sm">
                  {rule.name}
                </span>
                <span className="badge badge-blue text-xs flex items-center gap-1">
                  <Zap className="w-3 h-3" />
                  {rule.trigger}
                </span>
                {!rule.is_active && (
                  <span className="text-xs text-gray-400 dark:text-gray-500 italic">inactive</span>
                )}
              </div>
              <div className="flex flex-wrap gap-3 mt-1.5 text-xs text-gray-500 dark:text-gray-400">
                <span>
                  <strong>{rule.bundle.length}</strong> object{rule.bundle.length !== 1 ? 's' : ''} in bundle
                </span>
                <span>lookahead: <strong>{rule.lookahead_minutes}</strong> min</span>
                <span>decay: <strong>{rule.false_prefetch_decay_minutes}</strong> min</span>
              </div>
              {rule.bundle.length > 0 && (
                <div className="flex flex-wrap gap-1 mt-2">
                  {rule.bundle.map((objId) => (
                    <span
                      key={objId}
                      className="inline-block px-1.5 py-0.5 bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 rounded text-xs font-mono"
                    >
                      {objId}
                    </span>
                  ))}
                </div>
              )}
            </div>

            {/* Actions */}
            <div className="flex items-center gap-1 flex-shrink-0">
              <button
                onClick={() => setEditingRule(rule)}
                className="p-1.5 text-gray-400 hover:text-primary-600 rounded transition-colors"
                title="Edit"
              >
                <Edit2 className="w-4 h-4" />
              </button>
              <button
                onClick={() => handleDelete(rule)}
                className="p-1.5 text-gray-400 hover:text-red-600 rounded transition-colors"
                title="Delete"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
          </div>
        ))}
      </div>

      {editingRule && (
        <EditPrefetchRuleModal
          rule={editingRule}
          onClose={() => setEditingRule(null)}
        />
      )}
    </>
  );
}

function CreatePrefetchRuleModal({ onClose }: { onClose: () => void }) {
  const createRule = useCreatePrefetchRule();
  const [name, setName] = useState('');
  const [trigger, setTrigger] = useState('');
  const [bundleStr, setBundleStr] = useState('');
  const [lookahead, setLookahead] = useState(120);
  const [decay, setDecay] = useState(30);
  const [isActive, setIsActive] = useState(true);

  const handleCreate = () => {
    if (!name.trim()) { toast.error('Rule name is required'); return; }
    if (!trigger.trim()) { toast.error('Trigger is required'); return; }

    const bundle = bundleStr
      .split('\n')
      .map((s) => s.trim())
      .filter(Boolean);

    const data: PrefetchRuleCreate = {
      name: name.trim(),
      trigger: trigger.trim(),
      bundle,
      lookahead_minutes: lookahead,
      false_prefetch_decay_minutes: decay,
      is_active: isActive,
    };

    createRule.mutate(data, {
      onSuccess: () => {
        toast.success('Prefetch rule created');
        onClose();
      },
      onError: (err: any) => {
        toast.error(err?.response?.data?.detail || 'Failed to create rule');
      },
    });
  };

  return (
    <Modal isOpen onClose={onClose} title="Create Prefetch Rule">
      <div className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="label">Rule Name</label>
            <input
              type="text"
              className="input font-mono"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g., session_boot"
            />
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">Unique, immutable after creation</p>
          </div>
          <div>
            <label className="label">Trigger</label>
            <input
              type="text"
              className="input font-mono"
              value={trigger}
              onChange={(e) => setTrigger(e.target.value)}
              placeholder="e.g., session_start"
            />
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">Condition that fires this rule</p>
          </div>
        </div>

        <div>
          <label className="label">Bundle — Object IDs (one per line)</label>
          <textarea
            className="input font-mono text-sm"
            rows={5}
            value={bundleStr}
            onChange={(e) => setBundleStr(e.target.value)}
            placeholder={"user-profile-001\ninteraction-preferences-001\nwork-context-001"}
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="label">Lookahead (minutes)</label>
            <input
              type="number"
              className="input"
              min={1}
              value={lookahead}
              onChange={(e) => setLookahead(Math.max(1, Number(e.target.value) || 1))}
            />
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">Time window for look-ahead context</p>
          </div>
          <div>
            <label className="label">False-Prefetch Decay (minutes)</label>
            <input
              type="number"
              className="input"
              min={1}
              value={decay}
              onChange={(e) => setDecay(Math.max(1, Number(e.target.value) || 1))}
            />
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">Cache TTL for unused prefetches</p>
          </div>
        </div>

        <label className="flex items-center gap-3 cursor-pointer p-3 rounded-lg border border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors">
          <input
            type="checkbox"
            checked={isActive}
            onChange={(e) => setIsActive(e.target.checked)}
            className="w-4 h-4 rounded"
          />
          <div>
            <p className="text-sm font-medium text-gray-900 dark:text-gray-100">Active</p>
            <p className="text-xs text-gray-500 dark:text-gray-400">Rule will fire when trigger condition is met</p>
          </div>
        </label>

        <div className="flex justify-end gap-2">
          <button onClick={onClose} className="btn btn-secondary">Cancel</button>
          <button
            onClick={handleCreate}
            disabled={createRule.isPending}
            className="btn btn-primary"
          >
            {createRule.isPending ? 'Creating...' : 'Create Rule'}
          </button>
        </div>
      </div>
    </Modal>
  );
}

function EditPrefetchRuleModal({ rule, onClose }: { rule: PrefetchRule; onClose: () => void }) {
  const updateRule = useUpdatePrefetchRule();
  const [trigger, setTrigger] = useState(rule.trigger);
  const [bundleStr, setBundleStr] = useState(rule.bundle.join('\n'));
  const [lookahead, setLookahead] = useState(rule.lookahead_minutes);
  const [decay, setDecay] = useState(rule.false_prefetch_decay_minutes);
  const [isActive, setIsActive] = useState(rule.is_active);

  const handleSave = () => {
    const bundle = bundleStr
      .split('\n')
      .map((s) => s.trim())
      .filter(Boolean);

    const data: PrefetchRuleUpdate = {
      trigger: trigger.trim() || undefined,
      bundle,
      lookahead_minutes: lookahead,
      false_prefetch_decay_minutes: decay,
      is_active: isActive,
    };

    updateRule.mutate(
      { name: rule.name, data },
      {
        onSuccess: () => {
          toast.success('Prefetch rule updated');
          onClose();
        },
        onError: (err: any) => {
          toast.error(err?.response?.data?.detail || 'Failed to update rule');
        },
      }
    );
  };

  return (
    <Modal isOpen onClose={onClose} title={`Edit Rule: ${rule.name}`}>
      <div className="space-y-4">
        <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-3 text-sm">
          <p className="text-gray-500 dark:text-gray-400 text-xs mb-1">Rule name (immutable)</p>
          <p className="font-mono text-gray-900 dark:text-gray-100">{rule.name}</p>
        </div>

        <div>
          <label className="label">Trigger</label>
          <input
            type="text"
            className="input font-mono"
            value={trigger}
            onChange={(e) => setTrigger(e.target.value)}
          />
        </div>

        <div>
          <label className="label">Bundle — Object IDs (one per line)</label>
          <textarea
            className="input font-mono text-sm"
            rows={5}
            value={bundleStr}
            onChange={(e) => setBundleStr(e.target.value)}
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="label">Lookahead (minutes)</label>
            <input
              type="number"
              className="input"
              min={1}
              value={lookahead}
              onChange={(e) => setLookahead(Math.max(1, Number(e.target.value) || 1))}
            />
          </div>
          <div>
            <label className="label">False-Prefetch Decay (minutes)</label>
            <input
              type="number"
              className="input"
              min={1}
              value={decay}
              onChange={(e) => setDecay(Math.max(1, Number(e.target.value) || 1))}
            />
          </div>
        </div>

        <label className="flex items-center gap-3 cursor-pointer p-3 rounded-lg border border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors">
          <input
            type="checkbox"
            checked={isActive}
            onChange={(e) => setIsActive(e.target.checked)}
            className="w-4 h-4 rounded"
          />
          <div>
            <p className="text-sm font-medium text-gray-900 dark:text-gray-100">Active</p>
            <p className="text-xs text-gray-500 dark:text-gray-400">Rule will fire when trigger condition is met</p>
          </div>
        </label>

        <div className="flex justify-end gap-2">
          <button onClick={onClose} className="btn btn-secondary">Cancel</button>
          <button
            onClick={handleSave}
            disabled={updateRule.isPending}
            className="btn btn-primary"
          >
            {updateRule.isPending ? 'Saving...' : 'Save Changes'}
          </button>
        </div>
      </div>
    </Modal>
  );
}
