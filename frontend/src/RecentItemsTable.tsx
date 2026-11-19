import React from 'react';
import { LostAndFoundItem } from '../../types/item';
import { StatusBadge } from '../items/StatusBadge';
import { ArrowRight, Eye, LogIn, LogOut, Radio } from 'lucide-react';
import { useApp } from '../../context/AppContext';

interface RecentItemsTableProps {
  items: LostAndFoundItem[];
}

export const RecentItemsTable: React.FC<RecentItemsTableProps> = ({ items }) => {
  const { 
    setActivePage, 
    setSelectedDetailItem, 
    setSelectedSmartBoxItem 
  } = useApp();

  const recentItems = items.slice(0, 5);

  return (
    <div className="bg-white rounded-2xl border border-slate-200/90 shadow-sm overflow-hidden">
      <div className="p-6 border-b border-slate-100 flex items-center justify-between">
        <div>
          <h3 className="text-base font-bold text-slate-800">
            Recently Logged Items
          </h3>
          <p className="text-xs text-slate-500">Latest records retrieved directly from Amazon DynamoDB</p>
        </div>
        <button
          onClick={() => setActivePage('all-items')}
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-blue-600 hover:text-blue-700 bg-blue-50 hover:bg-blue-100 px-3 py-1.5 rounded-lg transition"
        >
          <span>View All Records</span>
          <ArrowRight size={14} />
        </button>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-slate-50/70 border-b border-slate-100 text-[11px] font-semibold text-slate-500 uppercase tracking-wider">
              <th className="py-3 px-6">Item ID</th>
              <th className="py-3 px-6">Item Name</th>
              <th className="py-3 px-6">Category</th>
              <th className="py-3 px-6">Location</th>
              <th className="py-3 px-6">Date</th>
              <th className="py-3 px-6">Status</th>
              <th className="py-3 px-6 text-right">Quick Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 text-xs">
            {recentItems.length === 0 ? (
              <tr>
                <td colSpan={7} className="py-10 text-center text-slate-400">
                  No items found in DynamoDB. Click "Register Item" to add your first record.
                </td>
              </tr>
            ) : (
              recentItems.map((item) => (
                <tr
                  key={item.itemId}
                  className="hover:bg-slate-50/80 transition-colors group"
                >
                  <td className="py-3.5 px-6 font-mono text-[11px] font-medium text-slate-600">
                    <span className="px-2 py-0.5 rounded bg-slate-100 border border-slate-200">
                      {item.itemId}
                    </span>
                  </td>
                  <td className="py-3.5 px-6 font-semibold text-slate-800 max-w-[200px] truncate">
                    <button
                      onClick={() => setSelectedDetailItem(item)}
                      className="hover:text-blue-600 text-left truncate block w-full"
                    >
                      {item.itemName}
                    </button>
                    {item.rfidTagId && (
                      <span className="flex items-center gap-1 text-[10px] text-slate-400 font-mono mt-0.5">
                        <Radio size={10} className="text-blue-500" />
                        {item.rfidTagId}
                      </span>
                    )}
                  </td>
                  <td className="py-3.5 px-6 text-slate-600">
                    <span className="px-2 py-0.5 rounded-full bg-slate-100 text-slate-700 text-[11px]">
                      {item.category}
                    </span>
                  </td>
                  <td className="py-3.5 px-6 text-slate-600 max-w-[150px] truncate">
                    {item.locationFound || '—'}
                  </td>
                  <td className="py-3.5 px-6 text-slate-500 whitespace-nowrap">
                    {item.dateReported || '—'}
                  </td>
                  <td className="py-3.5 px-6">
                    <StatusBadge status={item.status} size="sm" />
                  </td>
                  <td className="py-3.5 px-6 text-right">
                    <div className="flex items-center justify-end gap-1.5">
                      <button
                        onClick={() => setSelectedDetailItem(item)}
                        className="p-1.5 rounded-lg text-slate-500 hover:text-blue-600 hover:bg-blue-50 transition"
                        title="View Full Details"
                      >
                        <Eye size={15} />
                      </button>

                      {item.status !== 'Found' && item.status !== 'Returned' && (
                        <button
                          onClick={() => setSelectedSmartBoxItem(item)}
                          className="p-1.5 rounded-lg text-slate-500 hover:text-amber-600 hover:bg-amber-50 transition"
                          title="Smart Box Check In"
                        >
                          <LogIn size={15} />
                        </button>
                      )}

                      {item.status === 'Found' && (
                        <button
                          onClick={() => setSelectedSmartBoxItem(item)}
                          className="p-1.5 rounded-lg text-slate-500 hover:text-emerald-600 hover:bg-emerald-50 transition"
                          title="Check Out / Return to Owner"
                        >
                          <LogOut size={15} />
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};
