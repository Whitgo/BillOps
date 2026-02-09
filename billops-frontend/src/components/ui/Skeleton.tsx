/**
 * Reusable Skeleton component
 */

import clsx from 'clsx';

interface SkeletonProps {
  className?: string;
}

export const Skeleton = ({ className }: SkeletonProps) => {
  return (
    <div className={clsx('animate-pulse bg-gray-200 rounded-md', className)} />
  );
};
