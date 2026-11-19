import React from 'react';
import { LostAndFoundItem } from '../../types/item';
import { PackageCheck, CheckCircle2, AlertCircle, ArrowUpRight, Clock } from 'lucide-react';

interface RecentActivityProps {
  items: LostAndFoundItem[];
  onSelectItem: (item: LostAndFoundItem) => void;
}

export const RecentActivity: React.FC<RecentActivityProps> = ({ items, onSelectItem }) => {
  // Build activity feed from items' checkInTime, checkOutTime, and createdAt
  const activities: {
    id: string;
    item: LostAndFoundItem;
    type: 'check_in' | 'check_out' | 'registered_lost';
    timestamp: string;
    title: string;
    description: string;
  }[] = [];

  items.forEach((item) => {
    if (item.checkOutTime) {
      activities.push({
        id: `${item.itemId}-out`,
        item,
        type: 'check_out',
        timestamp: item.checkOutTime,
        title: `Item Returned & Checked Out`,
        description: `"${item.itemName}" was collected from Smart Box`,
      });
    }
    if (item.checkInTime) {
      activities.push({
        id: `${item.itemId}-in`,
        item,
        type: 'check_in',
        timestamp: item.checkInTime,
        title: `Smart Box Check-In`,
        description: `"${item.itemName}" locked into Smart Box storage`,
      });
    }
    if (item.status === 'Lost') {
      activities.push({
        id: `${item.itemId}-lost`,
        item,
        type: 'registered_lost',
        timestamp: item.createdAt,
        title: `Missing Item Report`,
        description: `"${item.itemName}" reported lost near ${item.locationFound || 'campus'}`,
      });
    }
  });

  // Sort activities by timestamp descending
  activities.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());
  const recentActivities = activities.slice(0, 5);

  const formatTime = (isoString: string) => {
    try {
      const d = new Date(isoString);
      return d.toLocaleDateString(undefined, {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch {
      return isoString;
    }
  };

  return (
    <div className="bg-white rounded-2xl p-6 border border-slate-200/90 shadow-sm flex flex-col justify-between">
      <div>
        <div className="flex items-center justify-between mb-5">
          <div className="flex items-center gap-2">
            <div className="p-2 rounded-xl bg-slate-100 text-slate-700">
              <Clock size={18} />
            </div>
            <div>
              <h3 className="text-sm font-bold text-slate-800">
                Recent Smart Box Activity
              </h3>
              <p className="text-xs text-slate-500">Live hardware check-in &amp; return events</p>
            </div>
          </div>
          <span className="text-[11px] font-mono text-slate-400 bg-slate-50 px-2 py-0.5 rounded border border-slate-200">
            AUTO-SYNC
          </span>
        </div>

        {recentActivities.length === 0 ? (
          <div className="py-12 text-center text-slate-400 text-xs">
            No activity logged yet. Check in or register an item to begin.
          </div>
        ) : (
          <div className="relative pl-6 space-y-5 before:absolute before:left-2.5 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-200">
            {recentActivities.map((act) => {
              const Icon =
                act.type === 'check_in'
                  ? PackageCheck
                  : act.type === 'check_out'
                  ? CheckCircle2
                  : AlertCircle;

              const badgeColor =
                act.type === 'check_in'
                  ? 'bg-amber-100 text-amber-700 border-amber-300'
                  : act.type === 'check_out'
                  ? 'bg-emerald-100 text-emerald-700 border-emerald-300'
                  : 'bg-rose-100 text-rose-700 border-rose-300';

              return (
                <div key={act.id} className="relative group">
                  {/* Timeline dot */}
                  <div
                    className={`absolute -left-6 top-0.5 w-5 h-5 rounded-full border-2 border-white flex items-center justify-center shadow-xs ${badgeColor}`}
                  >
                    <Icon size={11} className="stroke-[2.5]" />
                  </div>

                  <div
                    onClick={() => onSelectItem(act.item)}
                    className="cursor-pointer p-2 -my-1 rounded-xl hover:bg-slate-50 transition"
                  >
                    <div className="flex items-center justify-between gap-2">
                      <h4 className="text-xs font-semibold text-slate-800 group-hover:text-blue-600 transition flex items-center gap-1">
                        <span>{act.title}</span>
                        <ArrowUpRight size={12} className="opacity-0 group-hover:opacity-100 transition" />
                      </h4>
                      <span className="text-[10px] text-slate-400 font-mono">
                        {formatTime(act.timestamp)}
                      </span>
                    </div>
                    <p className="text-xs text-slate-500 mt-0.5 line-clamp-1">
                      {act.description}
                    </p>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      <div className="mt-6 pt-4 border-t border-slate-100 text-[11px] text-slate-400 flex items-center justify-between">
        <span>DynamoDB Activity Stream</span>
        <span className="font-mono text-[10px] text-slate-500">Live Events</span>
      </div>
    </div>
  );
};
