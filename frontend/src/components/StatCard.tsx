import type { LucideIcon } from 'lucide-react';

interface StatCardProps {
  label: string;
  value: string | number;
  subtitle?: string;
  accentColor?: 'emerald' | 'rose' | 'blue' | 'amber';
  icon?: LucideIcon;
}

/**
 * StatCard Component
 * Displays a single metric with label and value
 * Part of Phase 2: The "DNA" View
 */
export const StatCard = ({
  label,
  value,
  subtitle,
  accentColor = 'emerald',
  icon: Icon,
}: StatCardProps) => {
  const colorClasses = {
    emerald: 'text-emerald-500',
    rose: 'text-rose-500',
    blue: 'text-blue-500',
    amber: 'text-amber-500',
  };

  return (
    <div className="bg-slate-800 border border-slate-700 rounded-lg p-4 hover:border-slate-600 transition-colors">
      <div className="flex items-center justify-between mb-1">
        <div className="text-slate-400 text-sm font-medium">{label}</div>
        {Icon && <Icon className={`w-4 h-4 ${colorClasses[accentColor]}`} />}
      </div>
      <div className={`text-3xl font-bold ${colorClasses[accentColor]} font-mono`}>
        {value}
      </div>
      {subtitle && <div className="text-slate-500 text-xs mt-1">{subtitle}</div>}
    </div>
  );
};
