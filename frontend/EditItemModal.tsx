import React, { useState, useEffect } from 'react';
import { useApp } from '../../context/AppContext';
import { ItemCategory, ItemStatus, UpdateItemInput } from '../../types/item';
import { X, Save, Layers, MapPin, Calendar, User, Phone, FileText, Tag, Radio } from 'lucide-react';

export const EditItemModal: React.FC = () => {
  const { selectedEditItem, setSelectedEditItem, updateItem, isLoading } = useApp();

  const [form, setForm] = useState<UpdateItemInput>({});
  const [error, setError] = useState<string>('');

  useEffect(() => {
    if (selectedEditItem) {
      setForm({
        itemName: selectedEditItem.itemName,
        category: selectedEditItem.category,
        description: selectedEditItem.description,
        rfidTagId: selectedEditItem.rfidTagId,
        locationFound: selectedEditItem.locationFound,
        dateReported: selectedEditItem.dateReported,
        reportedBy: selectedEditItem.reportedBy,
        contactInformation: selectedEditItem.contactInformation,
        status: selectedEditItem.status,
      });
      setError('');
    }
  }, [selectedEditItem]);

  if (!selectedEditItem) return null;

  const categories: ItemCategory[] = [
    'ID Card',
    'Electronics',
    'Books',
    'Keys',
    'Bags',
    'Accessories',
    'Other',
  ];

  const statuses: ItemStatus[] = ['Lost', 'Found', 'Returned'];

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.itemName?.trim()) {
      setError('Item name cannot be empty.');
      return;
    }

    const updated = await updateItem(selectedEditItem.itemId, form);
    if (updated) {
      setSelectedEditItem(null);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-xs flex items-center justify-center p-4 overflow-y-auto">
      <div className="bg-white rounded-3xl max-w-xl w-full shadow-2xl border border-slate-200 overflow-hidden animate-in fade-in zoom-in-95 duration-150 my-8">
        <div className="bg-slate-900 text-white p-6 flex items-center justify-between">
          <div>
            <span className="font-mono text-xs text-blue-300">
              Edit DynamoDB Record
            </span>
            <h3 className="text-base font-bold text-white mt-0.5">
              {selectedEditItem.itemId}
            </h3>
          </div>
          <button
            onClick={() => setSelectedEditItem(null)}
            className="p-1.5 rounded-full text-slate-400 hover:text-white hover:bg-slate-800 transition"
          >
            <X size={20} />
          </button>
        </div>

        <form onSubmit={handleSave} className="p-6 space-y-4">
          {error && (
            <div className="p-3 bg-rose-50 border border-rose-200 text-rose-700 rounded-xl text-xs">
              {error}
            </div>
          )}

          {/* Item Name */}
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Item Name
            </label>
            <div className="relative">
              <Tag size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
              <input
                type="text"
                value={form.itemName || ''}
                onChange={(e) => setForm({ ...form, itemName: e.target.value })}
                className="w-full pl-9 pr-3 py-2 text-xs bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:border-blue-500 focus:outline-none transition"
              />
            </div>
          </div>

          {/* Category & Status */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Category
              </label>
              <select
                value={form.category}
                onChange={(e) => setForm({ ...form, category: e.target.value as ItemCategory })}
                className="w-full px-3 py-2 text-xs bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:border-blue-500 focus:outline-none transition"
              >
                {categories.map((c) => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Status
              </label>
              <select
                value={form.status}
                onChange={(e) => setForm({ ...form, status: e.target.value as ItemStatus })}
                className="w-full px-3 py-2 text-xs bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:border-blue-500 focus:outline-none transition"
              >
                {statuses.map((s) => (
                  <option key={s} value={s}>{s}</option>
                ))}
              </select>
            </div>
          </div>

          {/* RFID Tag ID */}
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              RFID Tag ID
            </label>
            <div className="relative">
              <Radio size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
              <input
                type="text"
                value={form.rfidTagId || ''}
                onChange={(e) => setForm({ ...form, rfidTagId: e.target.value.toUpperCase() })}
                className="w-full pl-9 pr-3 py-2 text-xs font-mono bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:border-blue-500 focus:outline-none transition uppercase"
              />
            </div>
          </div>

          {/* Description */}
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Description
            </label>
            <textarea
              rows={2}
              value={form.description || ''}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
              className="w-full px-3 py-2 text-xs bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:border-blue-500 focus:outline-none transition"
            />
          </div>

          {/* Location & Date */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Location Found
              </label>
              <input
                type="text"
                value={form.locationFound || ''}
                onChange={(e) => setForm({ ...form, locationFound: e.target.value })}
                className="w-full px-3 py-2 text-xs bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:border-blue-500 focus:outline-none transition"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Date Reported
              </label>
              <input
                type="date"
                value={form.dateReported || ''}
                onChange={(e) => setForm({ ...form, dateReported: e.target.value })}
                className="w-full px-3 py-2 text-xs bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:border-blue-500 focus:outline-none transition"
              />
            </div>
          </div>

          {/* Reporter & Contact */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Reported By
              </label>
              <input
                type="text"
                value={form.reportedBy || ''}
                onChange={(e) => setForm({ ...form, reportedBy: e.target.value })}
                className="w-full px-3 py-2 text-xs bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:border-blue-500 focus:outline-none transition"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Contact Information
              </label>
              <input
                type="text"
                value={form.contactInformation || ''}
                onChange={(e) => setForm({ ...form, contactInformation: e.target.value })}
                className="w-full px-3 py-2 text-xs bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:border-blue-500 focus:outline-none transition"
              />
            </div>
          </div>

          {/* Footer */}
          <div className="pt-4 border-t border-slate-100 flex items-center justify-end gap-3">
            <button
              type="button"
              onClick={() => setSelectedEditItem(null)}
              className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-600 hover:bg-slate-100 transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isLoading}
              className="inline-flex items-center gap-1.5 px-5 py-2 rounded-xl text-xs font-semibold bg-blue-600 hover:bg-blue-700 text-white shadow-sm transition disabled:opacity-50"
            >
              <Save size={14} />
              <span>{isLoading ? 'Updating...' : 'Save Changes'}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
