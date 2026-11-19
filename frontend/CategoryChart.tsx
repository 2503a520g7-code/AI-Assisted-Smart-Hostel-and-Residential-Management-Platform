import React from 'react';
import { ItemCategory } from '../../types/item';
import { CreditCard, Laptop, BookOpen, Key, Briefcase, Watch, HelpCircle, Layers } from 'lucide-react';

interface CategoryChartProps {
  categoryCounts?: Record<string, number>;
  totalItems: number;
  onSelectCategory?: (category: ItemCategory) => void;
}

const CATEGORY_META: Record<
  ItemCategory,
  { icon: React.ElementType; color: string; barColor: string }
> = {
  'ID Card': { icon: CreditCard, color: 'text-indigo-600 bg-indigo-50', barColor: 'bg-indigo-500' },
  'Electronics': { icon: Laptop, color: 'text-blue-600 bg-blue-50', barColor: 'bg-blue-500' },
  'Books': { icon: BookOpen, color: 'text-emerald-600 bg-emerald-50', barColor: 'bg-emerald-500' },
  'Keys': { icon: Key, color: 'text-amber-600 bg-amber-50', barColor: 'bg-amber-500' },
  'Bags': { icon: Briefcase, color: 'text-purple-600 bg-purple-50', barColor: 'bg-purple-500' },
  'Accessories': { icon: Watch, color: 'text-rose-600 bg-rose-50', barColor: 'bg-rose-500' },
  'Other': { icon: HelpCircle, color: 'text-slate-600 bg-slate-50', barColor: 'bg-slate-400' },
};

export const CategoryChart: React.FC<CategoryChartProps> = ({
  categoryCounts = {},
  totalItems,
  onSelectCategory,
}) => {
  const categories: ItemCategory[] = [
    'ID Card',
    'Electronics',
    'Books',
    'Keys',
    'Bags',
    'Accessories',
    'Other',
  ];

  return (
    <div className="bg-white rounded-2xl p-6 border border-slate-200/90 shadow-sm flex flex-col justify-between">
      <div>
        <div className="flex items-center justify-between mb-5">
          <div className="flex items-center gap-2">
            <div className="p-2 rounded-xl bg-slate-100 text-slate-700">
              <Layers size={18} />
            </div>
            <div>
              <h3 className="text-sm font-bold text-slate-800">
                Item Category Distribution
              </h3>
              <p className="text-xs text-slate-500">Live breakdown calculated from DynamoDB</p>
            </div>
          </div>
          <span className="text-xs font-semibold px-2.5 py-1 bg-slate-100 text-slate-700 rounded-full">
            {totalItems} total
          </span>
        </div>

        {totalItems === 0 ? (
          <div className="py-10 text-center text-slate-400 text-xs">
            No items registered in DynamoDB yet
          </div>
        ) : (
          <div className="space-y-3.5">
            {categories.map((cat) => {
              const count = categoryCounts[cat] || 0;
              const percentage = totalItems > 0 ? Math.round((count / totalItems) * 100) : 0;
              const meta = CATEGORY_META[cat];
              const Icon = meta.icon;

              return (
                <div
                  key={cat}
                  onClick={() => onSelectCategory && onSelectCategory(cat)}
                  className={`group ${
                    onSelectCategory ? 'cursor-pointer hover:bg-slate-50/80 p-1.5 -mx-1.5 rounded-lg transition' : ''
                  }`}
                >
                  <div className="flex items-center justify-between text-xs mb-1.5">
                    <div className="flex items-center gap-2">
                      <div className={`p-1 rounded-md ${meta.color}`}>
                        <Icon size={13} />
                      </div>
                      <span className="font-medium text-slate-700 group-hover:text-blue-600 transition">
                        {cat}
                      </span>
                    </div>
                    <div className="flex items-center gap-2 font-mono text-[11px]">
                      <span className="font-semibold text-slate-800">{count}</span>
                      <span className="text-slate-400">({percentage}%)</span>
                    </div>
                  </div>

                  <div className="w-full bg-slate-100 rounded-full h-2 overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all duration-500 ${meta.barColor}`}
                      style={{ width: `${percentage}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      <div className="mt-6 pt-4 border-t border-slate-100 text-[11px] text-slate-400 flex items-center justify-between">
        <span>Smart Box Storage Utilization</span>
        <span className="font-medium text-slate-600">Calculated live</span>
      </div>
    </div>
  );
};
