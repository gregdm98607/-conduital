import { Brain, Zap, Layers, Clock, BarChart2, RefreshCw } from 'lucide-react';
import { useMemoryStats } from '@/hooks/useMemory';
import { StatCard, MiniBar } from './components/shared';

export function HealthView() {
  const { data: stats, isLoading, isError, refetch, isFetching } = useMemoryStats();

  if (isLoading) {
    return <div className="text-center py-12 text-gray-500 dark:text-gray-400">Loading health data...</div>;
  }

  if (isError || !stats) {
    return (
      <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 flex items-center justify-between">
        <p className="text-red-800 dark:text-red-300 text-sm">
          Failed to load memory health stats. The memory layer module may not be enabled.
        </p>
        <button
          onClick={() => refetch()}
          disabled={isFetching}
          className="btn btn-secondary text-sm flex items-center gap-1.5 flex-shrink-0 ml-4"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isFetching ? 'animate-spin' : ''}`} />
          Retry
        </button>
      </div>
    );
  }

  const { totals, objects, namespaces_by_count, recent_activity } = stats;
  const maxNsCount = namespaces_by_count[0]?.count || 1;

  return (
    <div className="space-y-6">
      {/* System Overview */}
      <section>
        <h2 className="text-sm font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-3 flex items-center gap-2">
          <BarChart2 className="w-4 h-4" />
          System Overview
        </h2>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <StatCard label="Memory Objects" value={totals.objects} />
          <StatCard label="Namespaces" value={totals.namespaces} />
          <StatCard
            label="Quick Keys"
            value={totals.quick_keys}
            sub={totals.quick_keys === 0 ? 'none configured' : undefined}
          />
          <StatCard
            label="Prefetch Rules"
            value={totals.prefetch_rules}
            sub={`${totals.active_prefetch_rules} active`}
          />
        </div>
      </section>

      {/* Object Health + Priority Distribution */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Object Health */}
        <section className="card">
          <h2 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-4 flex items-center gap-2">
            <Brain className="w-4 h-4" />
            Object Health
          </h2>
          <div className="space-y-3">
            <MiniBar
              label="Active"
              count={objects.active}
              total={totals.objects}
              colorClass="bg-green-500"
            />
            <MiniBar
              label="Inactive"
              count={objects.inactive}
              total={totals.objects}
              colorClass="bg-gray-400"
            />
            <div className="border-t border-gray-100 dark:border-gray-700 pt-3 mt-1" />
            <MiniBar
              label="DB storage"
              count={objects.db_storage}
              total={totals.objects}
              colorClass="bg-blue-500"
            />
            <MiniBar
              label="File storage"
              count={objects.file_storage}
              total={totals.objects}
              colorClass="bg-purple-500"
            />
          </div>
          {totals.objects > 0 && (
            <p className="text-xs text-gray-400 dark:text-gray-500 mt-4">
              Avg priority: <span className="font-medium text-gray-700 dark:text-gray-300">{objects.avg_priority}</span>
            </p>
          )}
        </section>

        {/* Priority Distribution */}
        <section className="card">
          <h2 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-4 flex items-center gap-2">
            <Zap className="w-4 h-4" />
            Priority Distribution
          </h2>
          {totals.objects === 0 ? (
            <p className="text-sm text-gray-400 dark:text-gray-500 italic">No objects yet</p>
          ) : (
            <div className="space-y-3">
              <MiniBar
                label="High (≥ 80)"
                count={objects.high_priority}
                total={totals.objects}
                colorClass="bg-red-500"
              />
              <MiniBar
                label="Medium (40–79)"
                count={objects.medium_priority}
                total={totals.objects}
                colorClass="bg-orange-400"
              />
              <MiniBar
                label="Low (< 40)"
                count={objects.low_priority}
                total={totals.objects}
                colorClass="bg-blue-400"
              />
            </div>
          )}
        </section>
      </div>

      {/* Top Namespaces */}
      {namespaces_by_count.length > 0 && (
        <section className="card">
          <h2 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-4 flex items-center gap-2">
            <Layers className="w-4 h-4" />
            Top Namespaces by Object Count
          </h2>
          <div className="space-y-2.5">
            {namespaces_by_count.map(({ name, count }) => (
              <div key={name} className="flex items-center gap-3 text-sm">
                <span className="w-48 font-mono text-xs text-gray-700 dark:text-gray-300 truncate flex-shrink-0">
                  {name}
                </span>
                <div className="flex-1 bg-gray-100 dark:bg-gray-700 rounded-full h-2">
                  <div
                    className="h-2 rounded-full bg-primary-500 transition-all"
                    style={{ width: `${Math.round((count / maxNsCount) * 100)}%` }}
                  />
                </div>
                <span className="w-6 text-right text-gray-900 dark:text-gray-100 font-medium tabular-nums flex-shrink-0">
                  {count}
                </span>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Recent Activity */}
      <section className="card">
        <h2 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-4 flex items-center gap-2">
          <Clock className="w-4 h-4" />
          Recent Activity
        </h2>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-center">
          <div>
            <p className="text-xl font-bold text-gray-900 dark:text-gray-100">
              {recent_activity.created_last_7d}
            </p>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">Created (7d)</p>
          </div>
          <div>
            <p className="text-xl font-bold text-gray-900 dark:text-gray-100">
              {recent_activity.updated_last_7d}
            </p>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">Updated (7d)</p>
          </div>
          <div>
            <p className="text-xl font-bold text-gray-900 dark:text-gray-100">
              {recent_activity.created_last_30d}
            </p>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">Created (30d)</p>
          </div>
          <div>
            <p className="text-xl font-bold text-gray-900 dark:text-gray-100">
              {recent_activity.updated_last_30d}
            </p>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">Updated (30d)</p>
          </div>
        </div>
      </section>
    </div>
  );
}
