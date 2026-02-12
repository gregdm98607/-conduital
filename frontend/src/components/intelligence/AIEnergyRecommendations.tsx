import { useState } from 'react';
import { Zap, Clock, Tag, ChevronRight, Battery, BatteryMedium, BatteryLow } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useEnergyRecommendations } from '../../hooks/useIntelligence';

const energyOptions = [
  { value: 'low', label: 'Low', icon: BatteryLow, color: 'text-green-600 dark:text-green-400', bg: 'bg-green-100 dark:bg-green-900/30' },
  { value: 'medium', label: 'Medium', icon: BatteryMedium, color: 'text-yellow-600 dark:text-yellow-400', bg: 'bg-yellow-100 dark:bg-yellow-900/30' },
  { value: 'high', label: 'High', icon: Battery, color: 'text-red-600 dark:text-red-400', bg: 'bg-red-100 dark:bg-red-900/30' },
];

export function AIEnergyRecommendations() {
  const [selectedEnergy, setSelectedEnergy] = useState('low');
  const [isExpanded, setIsExpanded] = useState(false);

  const { data, isLoading } = useEnergyRecommendations(selectedEnergy, 5, isExpanded);

  return (
    <div className="mb-8">
      <div className="card">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <Zap className="w-5 h-5 text-amber-500" />
            <h3 className="font-semibold text-gray-900 dark:text-gray-100">Energy Match</h3>
          </div>
          <div className="flex items-center gap-1">
            {energyOptions.map((opt) => {
              const Icon = opt.icon;
              return (
                <button
                  key={opt.value}
                  onClick={() => { setSelectedEnergy(opt.value); setIsExpanded(true); }}
                  className={`text-xs px-2.5 py-1 rounded-md flex items-center gap-1 transition-colors ${
                    selectedEnergy === opt.value && isExpanded
                      ? `${opt.bg} ${opt.color} font-medium`
                      : 'text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800'
                  }`}
                >
                  <Icon className="w-3.5 h-3.5" />
                  {opt.label}
                </button>
              );
            })}
          </div>
        </div>

        {!isExpanded && (
          <p className="text-sm text-gray-400 dark:text-gray-500 italic">
            Select your current energy level to see matching tasks.
          </p>
        )}

        {isExpanded && isLoading && (
          <div className="text-sm text-gray-500 flex items-center gap-2 py-3 justify-center">
            <div className="w-3.5 h-3.5 border-2 border-gray-400 border-t-transparent rounded-full animate-spin" />
            Finding tasks...
          </div>
        )}

        {isExpanded && data && data.tasks.length === 0 && (
          <p className="text-sm text-gray-500 dark:text-gray-400 py-2">
            No matching tasks found. Try a different energy level.
          </p>
        )}

        {isExpanded && data && data.tasks.length > 0 && (
          <div className="space-y-2">
            {data.tasks.map((task) => (
              <Link
                key={task.task_id}
                to={`/projects/${task.project_id}`}
                className="block p-2.5 bg-gray-50 dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 hover:border-amber-300 dark:hover:border-amber-700 transition-colors"
              >
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-gray-900 dark:text-gray-100">{task.task_title}</span>
                  <ChevronRight className="w-3 h-3 text-gray-400" />
                </div>
                <div className="flex items-center gap-3 mt-1">
                  <span className="text-xs text-gray-500 dark:text-gray-400">{task.project_title}</span>
                  {task.estimated_minutes && (
                    <span className="text-xs text-gray-500 dark:text-gray-400 flex items-center gap-0.5">
                      <Clock className="w-3 h-3" /> {task.estimated_minutes}m
                    </span>
                  )}
                  {task.context && (
                    <span className="text-xs text-gray-500 dark:text-gray-400 flex items-center gap-0.5">
                      <Tag className="w-3 h-3" /> {task.context.replace('_', ' ')}
                    </span>
                  )}
                </div>
              </Link>
            ))}
            <p className="text-xs text-gray-400 dark:text-gray-500 text-right">
              {data.total_available} next actions available
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
