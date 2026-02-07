import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Edit2, Trash2, FolderOpen, Star, ChevronDown, ChevronUp, CheckCircle, Clock, Plus, Heart, Archive, ArchiveRestore } from 'lucide-react';
import { Area } from '../../types';
import { getReviewStatus } from '../../utils/date';

interface AreaCardProps {
  area: Area;
  onEdit: (area: Area) => void;
  onDelete: (id: number) => void;
  onMarkReviewed?: (id: number) => void;
  isMarkingReviewed?: boolean;
  onAddProject?: (areaId: number) => void;
  onArchive?: (id: number) => void;
  onUnarchive?: (id: number) => void;
}

export function AreaCard({ area, onEdit, onDelete, onMarkReviewed, isMarkingReviewed, onAddProject, onArchive, onUnarchive }: AreaCardProps) {
  const [isStandardExpanded, setIsStandardExpanded] = useState(false);

  const handleDelete = () => {
    if (confirm(`Are you sure you want to delete "${area.title}"? This may affect associated projects.`)) {
      onDelete(area.id);
    }
  };

  const getReviewFrequencyBadge = (frequency: string) => {
    const badges = {
      daily: 'badge badge-red',
      weekly: 'badge badge-blue',
      monthly: 'badge badge-green',
    };
    return badges[frequency as keyof typeof badges] || 'badge badge-blue';
  };

  const getReviewFrequencyLabel = (frequency: string) => {
    return frequency.charAt(0).toUpperCase() + frequency.slice(1);
  };

  const reviewStatus = getReviewStatus(area.last_reviewed_at, area.review_frequency);

  const getReviewStatusBadge = () => {
    if (reviewStatus.status === 'overdue' || reviewStatus.status === 'never-reviewed') {
      return 'badge badge-red';
    } else if (reviewStatus.status === 'due-soon') {
      return 'badge badge-yellow';
    }
    return 'badge badge-green';
  };

  return (
    <div className={`card hover:shadow-lg transition-all ${area.is_archived ? 'opacity-60' : ''}`}>
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">
            <Link to={`/areas/${area.id}`} className="hover:text-primary-600">
              {area.title}
            </Link>
          </h3>
          <div className="flex flex-wrap gap-2 items-center">
            {area.is_archived && (
              <span className="badge badge-gray flex items-center gap-1">
                <Archive className="w-3 h-3" />
                Archived
              </span>
            )}
            <span className={getReviewFrequencyBadge(area.review_frequency)}>
              {getReviewFrequencyLabel(area.review_frequency)} Review
            </span>
            {area.project_count !== undefined && area.project_count > 0 && (
              <span className="badge badge-gray flex items-center gap-1">
                <FolderOpen className="w-3 h-3" />
                {area.active_project_count}/{area.project_count} projects
              </span>
            )}
          </div>
          {/* Review Status */}
          <div className="mt-2">
            <span className={`${getReviewStatusBadge()} flex items-center gap-1`}>
              <Clock className="w-3 h-3" />
              {reviewStatus.text}
            </span>
          </div>
        </div>
        <button
          onClick={() => onEdit(area)}
          className="text-gray-400 hover:text-primary-600 transition-colors p-1"
          title="Edit area"
        >
          <Edit2 className="w-5 h-5" />
        </button>
      </div>

      {area.description ? (
        <p className="text-sm text-gray-600 dark:text-gray-400 mb-4 line-clamp-2">
          {area.description}
        </p>
      ) : (
        <p className="text-sm text-gray-400 mb-4 italic">
          No description
        </p>
      )}

      {area.folder_path && (
        <p className="text-xs text-gray-500 dark:text-gray-400 mb-4 font-mono">
          {area.folder_path}
        </p>
      )}

      {/* Health Score Bar */}
      {area.health_score !== undefined && (
        <div className="mb-4">
          <div className="flex items-center gap-2 mb-1">
            <Heart className="w-3 h-3 text-gray-500 dark:text-gray-400" />
            <span className="text-xs text-gray-500 dark:text-gray-400">Health</span>
            <span className="text-xs font-medium text-gray-700 dark:text-gray-300 ml-auto">
              {Math.round(area.health_score * 100)}%
            </span>
          </div>
          <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-1.5">
            <div
              className={`h-1.5 rounded-full transition-all ${
                area.health_score >= 0.7 ? 'bg-green-500' :
                area.health_score >= 0.4 ? 'bg-yellow-500' :
                area.health_score > 0 ? 'bg-red-500' : 'bg-gray-300 dark:bg-gray-600'
              }`}
              style={{ width: `${Math.round(area.health_score * 100)}%` }}
            />
          </div>
        </div>
      )}

      {area.standard_of_excellence && (
        <div className="mb-4">
          <button
            onClick={() => setIsStandardExpanded(!isStandardExpanded)}
            className="flex items-center gap-1 text-sm text-amber-600 hover:text-amber-700 transition-colors w-full text-left"
          >
            <Star className="w-4 h-4 fill-amber-400" />
            <span className="font-medium">Standard of Excellence</span>
            {isStandardExpanded ? (
              <ChevronUp className="w-4 h-4 ml-auto" />
            ) : (
              <ChevronDown className="w-4 h-4 ml-auto" />
            )}
          </button>
          {isStandardExpanded && (
            <p className="mt-2 text-sm text-gray-600 dark:text-gray-400 pl-5 border-l-2 border-amber-200 dark:border-amber-800">
              {area.standard_of_excellence}
            </p>
          )}
        </div>
      )}

      <div className="flex gap-2 pt-4 border-t border-gray-200 dark:border-gray-700">
        <Link
          to={`/areas/${area.id}`}
          className="btn btn-sm btn-primary flex-1"
        >
          View Details
        </Link>
        {onAddProject && (
          <button
            onClick={() => onAddProject(area.id)}
            className="btn btn-sm btn-secondary flex items-center gap-1"
            title="Add project to this area"
          >
            <Plus className="w-4 h-4" />
            Project
          </button>
        )}
        {onMarkReviewed && (
          <button
            onClick={() => onMarkReviewed(area.id)}
            disabled={isMarkingReviewed}
            className="btn btn-sm btn-secondary flex items-center gap-1"
            title="Mark as reviewed"
          >
            <CheckCircle className="w-4 h-4" />
          </button>
        )}
        {area.is_archived ? (
          onUnarchive && (
            <button
              onClick={() => onUnarchive(area.id)}
              className="btn btn-sm flex items-center gap-1 text-green-600 hover:bg-green-50 dark:hover:bg-green-900/20"
              title="Unarchive area"
            >
              <ArchiveRestore className="w-4 h-4" />
            </button>
          )
        ) : (
          onArchive && (
            <button
              onClick={() => onArchive(area.id)}
              className="btn btn-sm flex items-center gap-1 text-gray-500 hover:bg-gray-50 dark:hover:bg-gray-800"
              title="Archive area"
            >
              <Archive className="w-4 h-4" />
            </button>
          )
        )}
        <button
          onClick={handleDelete}
          className="btn btn-sm flex items-center gap-1 text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20"
          title="Delete area"
        >
          <Trash2 className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}
