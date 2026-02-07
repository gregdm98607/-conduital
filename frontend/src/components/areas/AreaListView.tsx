import { Link } from 'react-router-dom';
import { Edit2, Trash2, FolderOpen, Star, CheckCircle, Clock } from 'lucide-react';
import { Area } from '../../types';
import { getReviewStatus } from '../../utils/date';

interface AreaListViewProps {
  areas: Area[];
  onEdit: (area: Area) => void;
  onDelete: (id: number) => void;
  onMarkReviewed?: (id: number) => void;
  isMarkingReviewed?: boolean;
}

// Get badge class based on review frequency
function getReviewFrequencyBadgeClass(frequency: string): string {
  switch (frequency) {
    case 'daily':
      return 'badge-red';
    case 'weekly':
      return 'badge-blue';
    case 'monthly':
      return 'badge-green';
    default:
      return 'badge-gray';
  }
}

// Format review frequency for display
function formatReviewFrequency(frequency: string): string {
  return frequency.charAt(0).toUpperCase() + frequency.slice(1);
}

export function AreaListView({ areas, onEdit, onDelete, onMarkReviewed, isMarkingReviewed }: AreaListViewProps) {
  const handleDelete = (area: Area) => {
    if (confirm(`Are you sure you want to delete "${area.title}"? This may affect associated projects.`)) {
      onDelete(area.id);
    }
  };

  return (
    <div className="card overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-50 dark:bg-gray-800 border-b">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Title
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Review Frequency
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Projects
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Standard of Excellence
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Last Reviewed
              </th>
              <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
            {areas.map((area) => (
              <tr
                key={area.id}
                className="hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
              >
                {/* Title */}
                <td className="px-4 py-4">
                  <div className="flex flex-col">
                    <Link
                      to={`/areas/${area.id}`}
                      className="font-medium text-gray-900 dark:text-gray-100 hover:text-primary-600 transition-colors"
                    >
                      {area.title}
                    </Link>
                    {area.description && (
                      <span className="text-sm text-gray-500 dark:text-gray-400 line-clamp-1 mt-0.5">
                        {area.description}
                      </span>
                    )}
                  </div>
                </td>

                {/* Review Frequency */}
                <td className="px-4 py-4">
                  <span className={`badge ${getReviewFrequencyBadgeClass(area.review_frequency)} text-xs`}>
                    {formatReviewFrequency(area.review_frequency)}
                  </span>
                </td>

                {/* Projects */}
                <td className="px-4 py-4">
                  {area.project_count !== undefined && area.project_count > 0 ? (
                    <span className="inline-flex items-center gap-1 text-sm text-gray-600 dark:text-gray-400">
                      <FolderOpen className="w-4 h-4 text-gray-400" />
                      <span className="font-medium">{area.active_project_count}</span>
                      <span className="text-gray-400">/</span>
                      <span>{area.project_count}</span>
                    </span>
                  ) : (
                    <span className="text-gray-400 text-sm">-</span>
                  )}
                </td>

                {/* Standard of Excellence */}
                <td className="px-4 py-4 max-w-xs">
                  {area.standard_of_excellence ? (
                    <div className="flex items-start gap-1">
                      <Star className="w-4 h-4 text-amber-400 fill-amber-400 flex-shrink-0 mt-0.5" />
                      <span className="text-sm text-gray-600 dark:text-gray-400 line-clamp-2">
                        {area.standard_of_excellence}
                      </span>
                    </div>
                  ) : (
                    <span className="text-gray-400 text-sm">-</span>
                  )}
                </td>

                {/* Last Reviewed */}
                <td className="px-4 py-4">
                  {(() => {
                    const reviewStatus = getReviewStatus(area.last_reviewed_at, area.review_frequency);
                    const statusClasses = {
                      'overdue': 'text-red-600',
                      'never-reviewed': 'text-red-600',
                      'due-soon': 'text-yellow-600',
                      'current': 'text-green-600',
                    };
                    return (
                      <span className={`inline-flex items-center gap-1 text-xs font-medium ${statusClasses[reviewStatus.status]}`}>
                        <Clock className="w-3 h-3" />
                        {reviewStatus.text}
                      </span>
                    );
                  })()}
                </td>

                {/* Actions */}
                <td className="px-4 py-4">
                  <div className="flex items-center justify-end gap-2">
                    <Link
                      to={`/areas/${area.id}`}
                      className="btn btn-sm btn-primary"
                    >
                      View
                    </Link>
                    {onMarkReviewed && (
                      <button
                        onClick={() => onMarkReviewed(area.id)}
                        disabled={isMarkingReviewed}
                        className="p-1.5 text-gray-400 hover:text-green-600 hover:bg-green-50 dark:hover:bg-green-900/20 rounded transition-colors"
                        title="Mark as reviewed"
                      >
                        <CheckCircle className="w-4 h-4" />
                      </button>
                    )}
                    <button
                      onClick={() => onEdit(area)}
                      className="p-1.5 text-gray-400 hover:text-primary-600 hover:bg-gray-100 dark:hover:bg-gray-700 rounded transition-colors"
                      title="Edit area"
                    >
                      <Edit2 className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => handleDelete(area)}
                      className="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded transition-colors"
                      title="Delete area"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
