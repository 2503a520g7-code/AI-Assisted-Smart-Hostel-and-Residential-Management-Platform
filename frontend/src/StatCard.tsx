import React from 'react';
import { LucideIcon } from 'lucide-react';

interface StatCardProps {
  title: string;
  count: number | undefined;
  icon: LucideIcon;
  variant: 'blue' | 'rose' | 'amber' | 'emerald';
  subtitle: string;
  isLoading?: boolean;
  onClick?: () => void;
}

export const StatCard: React.FC<StatCardProps> = ({
  title,
  count,
  icon: Icon,
  variant,
  subtitle,
  isLoading,
  onClick,
}) => {
  const styles = {
    blue: {
      bgIcon: 'bg-blue-50 text-blue-600',
      borderHover: 'hover:border-blue-300',
      pill: 'bg-blue-50 text-blue-700',
      countColor: 'text-blue-900',
    },
    rose: {
      bgIcon: 'bg-rose-50 text-rose-600',
      borderHover: 'hover:border-rose-300',
      pill: 'bg-rose-50 text-rose-700',
      countColor: 'text-rose-900',
    },
    amber: {
      bgIcon: 'bg-amber-50 text-amber-600',
      borderHover: 'hover:border-amber-300',
      pill: 'bg-amber-50 text-amber-700',
      countColor: 'text-amber-900',
    },
    emerald: {
      bgIcon: 'bg-emerald-50 text-emerald-600',
      borderHover: 'hover:border-emerald-300',
      pill: 'bg-emerald-50 text-emerald-700',
      countColor: 'text-emerald-900',
    },
  }[variant];

  return (
    <div
      onClick={onClick}
      className={`bg-white rounded-2xl p-5 border border-slate-200/90 shadow-sm transition-all duration-200 ${styles.borderHover} ${
        onClick ? 'cursor-pointer hover:shadow-md' : ''
      }`}
    >
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
          {title}
        </span>
        <div className={`p-2.5 rounded-xl ${styles.bgIcon}`}>
          <Icon size={20} />
        </div>
      </div>

      <div className="space-y-1">
        {isLoading ? (
          <div className="h-8 w-16 bg-slate-200 rounded animate-pulse my-1" />
        ) : (
          <div className={`text-3xl font-extrabold tracking-tight ${styles.countColor}`}>
            {count !== undefined ? count.toLocaleString() : '—'}
          </div>
        )}
        <div className="text-xs text-slate-500 flex items-center justify-between pt-1">
          <span>{subtitle}</span>
        </div>
      </div>
    </div>
  );
};
