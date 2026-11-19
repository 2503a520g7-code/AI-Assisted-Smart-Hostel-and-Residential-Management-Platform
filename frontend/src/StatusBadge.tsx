import React from 'react';
import { ItemStatus } from '../../types/item';
import { AlertCircle, CheckCircle2, PackageCheck } from 'lucide-react';

interface StatusBadgeProps {
  status: ItemStatus;
  size?: 'sm' | 'md' | 'lg';
  showIcon?: boolean;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ 
  status, 
  size = 'md',
  showIcon = true 
}) => {
  const sizeClasses = {
    sm: 'text-xs px-2 py-0.5 gap-1',
    md: 'text-xs px-2.5 py-1 gap-1.5 font-medium',
    lg: 'text-sm px-3.5 py-1.5 gap-2 font-medium',
  };

  const iconSizes = {
    sm: 12,
    md: 14,
    lg: 16,
  };

  switch (status) {
    case 'Lost':
      return (
        <span
          className={`inline-flex items-center rounded-full bg-rose-50 text-rose-700 border border-rose-200 shadow-sm ${sizeClasses[size]}`}
          title="Item has been reported missing"
        >
          {showIcon && <AlertCircle size={iconSizes[size]} className="text-rose-500" />}
          <span>Lost</span>
        </span>
      );
    case 'Found':
      return (
        <span
          className={`inline-flex items-center rounded-full bg-amber-50 text-amber-700 border border-amber-200 shadow-sm ${sizeClasses[size]}`}
          title="Item has been found and stored in Smart Box"
        >
          {showIcon && <PackageCheck size={iconSizes[size]} className="text-amber-600" />}
          <span>Found</span>
        </span>
      );
    case 'Returned':
      return (
        <span
          className={`inline-flex items-center rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 shadow-sm ${sizeClasses[size]}`}
          title="Item has been collected by its owner"
        >
          {showIcon && <CheckCircle2 size={iconSizes[size]} className="text-emerald-600" />}
          <span>Returned</span>
        </span>
      );
    default:
      return (
        <span className={`inline-flex items-center rounded-full bg-slate-100 text-slate-700 ${sizeClasses[size]}`}>
          {status}
        </span>
      );
  }
};
