import { useState } from 'react';
import {
  Brain,
  Zap,
  BarChart2,
  ClipboardList,
} from 'lucide-react';
import { HealthView } from './memory/HealthView';
import { PrefetchRulesView, PrefetchRuleCreateButton } from './memory/PrefetchView';
import { SessionsView, SessionCaptureButton } from './memory/SessionsView';
import { ObjectsView, ObjectsHeaderActions } from './memory/ObjectsView';

type MemoryTab = 'objects' | 'prefetch' | 'health' | 'sessions';

export function MemoryPage() {
  const [activeTab, setActiveTab] = useState<MemoryTab>('objects');

  return (
    <div className="p-8">
      {/* Header */}
      <header className="mb-8">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Brain className="w-8 h-8 text-primary-600" />
            <div>
              <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">Memory</h1>
              <p className="text-gray-600 dark:text-gray-400 mt-1">
                Persistent context for AI assistants
              </p>
            </div>
          </div>
          {activeTab === 'objects' ? (
            <ObjectsHeaderActions />
          ) : activeTab === 'prefetch' ? (
            <PrefetchRuleCreateButton />
          ) : activeTab === 'sessions' ? (
            <SessionCaptureButton />
          ) : null}
        </div>

        {/* Tab switcher */}
        <div className="flex gap-1 mt-6 border-b border-gray-200 dark:border-gray-700">
          <TabButton active={activeTab === 'objects'} onClick={() => setActiveTab('objects')} icon={<Brain className="w-4 h-4" />} label="Objects" />
          <TabButton active={activeTab === 'prefetch'} onClick={() => setActiveTab('prefetch')} icon={<Zap className="w-4 h-4" />} label="Prefetch Rules" />
          <TabButton active={activeTab === 'health'} onClick={() => setActiveTab('health')} icon={<BarChart2 className="w-4 h-4" />} label="Health" />
          <TabButton active={activeTab === 'sessions'} onClick={() => setActiveTab('sessions')} icon={<ClipboardList className="w-4 h-4" />} label="Sessions" />
        </div>
      </header>

      {activeTab === 'objects' && <ObjectsView />}
      {activeTab === 'prefetch' && <PrefetchRulesView />}
      {activeTab === 'health' && <HealthView />}
      {activeTab === 'sessions' && <SessionsView />}
    </div>
  );
}

// ========== Tab Button ==========

function TabButton({ active, onClick, icon, label }: { active: boolean; onClick: () => void; icon: React.ReactNode; label: string }) {
  return (
    <button
      onClick={onClick}
      className={`flex items-center gap-2 px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
        active
          ? 'border-primary-600 text-primary-600 dark:border-primary-400 dark:text-primary-400'
          : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
      }`}
    >
      {icon}
      {label}
    </button>
  );
}
