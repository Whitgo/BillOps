/**
 * Skeleton loader for page transitions
 */

import { Skeleton } from './Skeleton';

export const PageSkeleton = () => {
  return (
    <div className="container-main space-y-6">
      <Skeleton className="h-8 w-48" />
      <div className="grid-auto">
        <Skeleton className="h-32 w-full" />
        <Skeleton className="h-32 w-full" />
        <Skeleton className="h-32 w-full" />
      </div>
      <Skeleton className="h-64 w-full" />
    </div>
  );
};
