import React from 'react';

interface SkeletonProps {
  className?: string;
  variant?: 'text' | 'circular' | 'rectangular';
  width?: string | number;
  height?: string | number;
  animation?: 'pulse' | 'wave' | 'none';
}

/**
 * Base skeleton component for loading states
 */
export function Skeleton({
  className = '',
  variant = 'text',
  width,
  height,
  animation = 'pulse',
}: SkeletonProps) {
  const baseClasses = 'bg-gray-200 dark:bg-gray-600';

  const animationClasses = {
    pulse: 'animate-pulse',
    wave: 'animate-shimmer',
    none: '',
  };

  const variantClasses = {
    text: 'rounded',
    circular: 'rounded-full',
    rectangular: 'rounded-lg',
  };

  const style: React.CSSProperties = {
    width: width || '100%',
    height: height || (variant === 'text' ? '1em' : undefined),
  };

  return (
    <div
      className={`${baseClasses} ${variantClasses[variant]} ${animationClasses[animation]} ${className}`}
      style={style}
    />
  );
}

/**
 * Skeleton for stats cards
 */
export function StatsSkeleton() {
  return (
    <div className="card">
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <Skeleton width="60%" height="1rem" className="mb-2" />
          <Skeleton width="40%" height="2rem" />
        </div>
        <Skeleton variant="circular" width="3rem" height="3rem" />
      </div>
    </div>
  );
}

/**
 * Skeleton for project cards
 */
export function ProjectCardSkeleton() {
  return (
    <div className="card">
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-2">
            <Skeleton width="4rem" height="1.25rem" className="rounded-full" />
            <Skeleton width="3rem" height="1.25rem" className="rounded-full" />
          </div>
          <Skeleton width="70%" height="1.5rem" className="mb-2" />
          <Skeleton width="50%" height="1rem" />
        </div>
        <Skeleton width="5rem" height="2rem" />
      </div>
      <Skeleton width="100%" height="3rem" className="mb-3" />
      <div className="flex items-center gap-4 text-sm">
        <Skeleton width="4rem" height="1rem" />
        <Skeleton width="5rem" height="1rem" />
        <Skeleton width="4rem" height="1rem" />
      </div>
    </div>
  );
}

/**
 * Skeleton for task items
 */
export function TaskItemSkeleton() {
  return (
    <div className="card">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-2">
            <Skeleton width="3rem" height="1rem" className="rounded-full" />
            <Skeleton width="4rem" height="1rem" className="rounded-full" />
          </div>
          <Skeleton width="80%" height="1.25rem" className="mb-2" />
          <Skeleton width="60%" height="0.875rem" />
        </div>
        <div className="flex gap-2">
          <Skeleton width="2rem" height="2rem" />
          <Skeleton width="2rem" height="2rem" />
        </div>
      </div>
    </div>
  );
}

/**
 * Skeleton for next action cards
 */
export function NextActionSkeleton() {
  return (
    <div className="card">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-3">
            <Skeleton width="4rem" height="1.25rem" className="rounded-full" />
            <Skeleton width="3rem" height="1.25rem" className="rounded-full" />
            <Skeleton width="3rem" height="1.25rem" className="rounded-full" />
          </div>
          <Skeleton width="75%" height="1.5rem" className="mb-2" />
          <Skeleton width="40%" height="1rem" className="mb-2" />
          <Skeleton width="90%" height="0.875rem" />
        </div>
        <div className="flex flex-col gap-2 ml-4">
          <Skeleton width="5rem" height="2rem" />
          <Skeleton width="5rem" height="2rem" />
        </div>
      </div>
    </div>
  );
}

/**
 * Skeleton for project header
 */
export function ProjectHeaderSkeleton() {
  return (
    <div className="mb-8">
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1">
          <Skeleton width="40%" height="2rem" className="mb-2" />
          <Skeleton width="60%" height="1rem" className="mb-4" />
          <div className="flex items-center gap-2">
            <Skeleton width="4rem" height="1.5rem" className="rounded-full" />
            <Skeleton width="5rem" height="1.5rem" className="rounded-full" />
          </div>
        </div>
        <div className="flex gap-2">
          <Skeleton width="6rem" height="2.5rem" />
          <Skeleton width="8rem" height="2.5rem" />
        </div>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatsSkeleton />
        <StatsSkeleton />
        <StatsSkeleton />
        <StatsSkeleton />
      </div>
    </div>
  );
}

/**
 * Skeleton for area cards
 */
export function AreaCardSkeleton() {
  return (
    <div className="card">
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1">
          <Skeleton width="70%" height="1.5rem" className="mb-2" />
          <Skeleton width="4rem" height="1.25rem" className="rounded-full" />
        </div>
      </div>
      <div className="mb-4">
        <Skeleton width="100%" height="1rem" className="mb-1" />
        <Skeleton width="90%" height="1rem" />
      </div>
      <Skeleton width="60%" height="0.875rem" className="mb-4" />
      <div className="flex gap-2">
        <Skeleton width="5rem" height="2rem" />
        <Skeleton width="5rem" height="2rem" />
      </div>
    </div>
  );
}

/**
 * Skeleton for table rows
 */
export function TableRowSkeleton({ columns = 4 }: { columns?: number }) {
  return (
    <tr className="border-b border-gray-200 dark:border-gray-700">
      {Array.from({ length: columns }).map((_, i) => (
        <td key={i} className="px-4 py-3">
          <Skeleton width="80%" height="1rem" />
        </td>
      ))}
    </tr>
  );
}
