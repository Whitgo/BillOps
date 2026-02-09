/**
 * Reusable Loader component
 */

import clsx from 'clsx';

interface LoaderProps {
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

const sizeClasses: Record<NonNullable<LoaderProps['size']>, string> = {
  sm: 'h-4 w-4 border-2',
  md: 'h-8 w-8 border-3',
  lg: 'h-12 w-12 border-4',
};

export const Loader = ({ size = 'md', className }: LoaderProps) => {
  return (
    <div
      className={clsx(
        'animate-spin rounded-full border-gray-300 border-t-blue-600',
        sizeClasses[size],
        className
      )}
    />
  );
};
