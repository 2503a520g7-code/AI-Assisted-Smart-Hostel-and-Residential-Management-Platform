import React from 'react';
import { useApp } from '../../context/AppContext';
import { StatusBadge } from './StatusBadge';
import { 
  X, 
  Radio, 
  MapPin, 
  Calendar, 
  User, 
  Phone, 
  Clock, 
  Layers, 
  FileText, 
  LogIn, 
  LogOut, 
  AlertCircle, 
  Edit3, 
  Trash2,
  Database,
  QrCode
} from 'lucide-react';

export const ItemDetailModal: React.FC = () => {
  const { 
    selectedDetailItem, 
    setSelectedDetailItem, 
    setSelectedEditItem, 
    setSelectedSmartBoxItem,
    updateStatus, 
    deleteItem,
    isLoading 
  } = useApp();

  if (!selectedDetailItem) return null;

  const item = selectedDetailItem;

  const formatDate = (isoString?: string | null) => {
    if (!isoString) return 'Not recorded';
    try {
      const d = new Date(isoString);
      return d.toLocaleString(undefined, {
        dateStyle: 'medium',
        timeStyle: 'short',
      });
    } catch {
      return isoString;
    }
  };

  const handleDelete = async () => {
    if (window.confirm(`Permanently remove item "${item.itemName}" (${item.itemId}) from DynamoDB?`)) {
      await deleteItem(item.itemId);
      setSelectedDetailItem(null);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-xs flex items-center justify-center p-4 overflow-y-auto">
      <div className="bg-white rounded-3xl max-w-2xl w-full shadow-2xl border border-slate-200 overflow-hidden animate-in fade-in zoom-in-95 duration-150 my-8">
        {/* Header */}
        <div className="bg-slate-900 text-white p-6 relative">
          <button
            onClick={() => setSelectedDetailItem(null)}
            className="absolute right-5 top-5 p-1.5 rounded-full text-slate-400 hover:text-white hover:bg-slate-800 transition"
          >
            <X size={20} />
          </button>

          <div className="flex items-center gap-2 mb-2">
            <span className="px-2.5 py-0.5 rounded-md bg-blue-500/20 text-blue-300 border border-blue-500/30 font-mono text-xs font-semibold">
              {item.itemId}
            </span>
            <StatusBadge status={item.status} size="sm" />
          </div>

          <h2 className="text-xl font-bold text-white tracking-tight">
            {item.itemName}
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Category: <strong className="text-slate-200">{item.category}</strong>
          </p>
        </div>

        {/* Content Body */}
        <div className="p-6 space-y-6">
          {/* RFID & Smart Box Hardware Card */}
          <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200/80 flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-3 w-full sm:w-auto">
              <div className="p-3 rounded-xl bg-blue-100 text-blue-700">
                <Radio size={22} className="animate-pulse" />
              </div>
              <div>
                <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">
                  Smart Box RFID Hardware Tag
                </span>
                <span className="text-sm font-mono font-bold text-slate-800">
                  {item.rfidTagId || 'No RFID Tag Assigned'}
                </span>
              </div>
            </div>

            <div className="flex items-center gap-3 text-xs border-t sm:border-t-0 sm:border-l border-slate-200 pt-3 sm:pt-0 sm:pl-4 w-full sm:w-auto justify-between sm:justify-start">
              <div>
                <span className="text-[11px] text-slate-400 block">Current Status</span>
                <span className="font-semibold text-slate-700">{item.status}</span>
              </div>
              <div className="p-1.5 rounded-lg bg-white border border-slate-200 text-slate-600">
                <QrCode size={24} />
              </div>
            </div>
          </div>

          {/* Description */}
          <div>
            <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-1.5 flex items-center gap-1.5">
              <FileText size={14} />
              Description &amp; Details
            </h4>
            <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-100 text-xs text-slate-700 leading-relaxed">
              {item.description || 'No detailed description provided.'}
            </div>
          </div>

          {/* Location & Reporter Info */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="p-3.5 rounded-xl border border-slate-200/80 space-y-1">
              <span className="text-[11px] font-semibold text-slate-400 uppercase flex items-center gap-1">
                <MapPin size={13} className="text-rose-500" />
                Location
              </span>
              <p className="text-xs font-semibold text-slate-800">
                {item.locationFound || 'Not specified'}
              </p>
            </div>

            <div className="p-3.5 rounded-xl border border-slate-200/80 space-y-1">
              <span className="text-[11px] font-semibold text-slate-400 uppercase flex items-center gap-1">
                <Calendar size={13} className="text-blue-500" />
                Date Reported
              </span>
              <p className="text-xs font-semibold text-slate-800">
                {item.dateReported || '—'}
              </p>
            </div>

            <div className="p-3.5 rounded-xl border border-slate-200/80 space-y-1">
              <span className="text-[11px] font-semibold text-slate-400 uppercase flex items-center gap-1">
                <User size={13} className="text-indigo-500" />
                Reported By
              </span>
              <p className="text-xs font-semibold text-slate-800">
                {item.reportedBy || 'Anonymous'}
              </p>
            </div>

            <div className="p-3.5 rounded-xl border border-slate-200/80 space-y-1">
              <span className="text-[11px] font-semibold text-slate-400 uppercase flex items-center gap-1">
                <Phone size={13} className="text-emerald-500" />
                Contact Info
              </span>
              <p className="text-xs font-semibold text-slate-800 truncate">
                {item.contactInformation || 'None provided'}
              </p>
            </div>
          </div>

          {/* DynamoDB Timestamps */}
          <div className="p-4 rounded-2xl bg-slate-50/70 border border-slate-200/80 space-y-2">
            <h4 className="text-[11px] font-bold text-slate-500 uppercase tracking-wider flex items-center gap-1.5">
              <Clock size={13} />
              Smart Box &amp; DynamoDB Audit Trail
            </h4>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
              <div className="flex justify-between py-1 border-b border-slate-100">
                <span className="text-slate-400">Check-In Time:</span>
                <span className="font-mono text-slate-700">{formatDate(item.checkInTime)}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-100">
                <span className="text-slate-400">Check-Out Time:</span>
                <span className="font-mono text-slate-700">{formatDate(item.checkOutTime)}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-100">
                <span className="text-slate-400">Created At:</span>
                <span className="font-mono text-slate-700">{formatDate(item.createdAt)}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-100">
                <span className="text-slate-400">Last Updated:</span>
                <span className="font-mono text-slate-700">{formatDate(item.updatedAt)}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Footer Actions */}
        <div className="p-5 bg-slate-50 border-t border-slate-200/80 flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <button
              onClick={() => {
                setSelectedEditItem(item);
                setSelectedDetailItem(null);
              }}
              className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-white border border-slate-200 text-slate-700 hover:bg-slate-100 text-xs font-semibold transition"
            >
              <Edit3 size={14} />
              <span>Edit Record</span>
            </button>

            <button
              onClick={handleDelete}
              disabled={isLoading}
              className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-white border border-rose-200 text-rose-600 hover:bg-rose-50 text-xs font-semibold transition disabled:opacity-50"
            >
              <Trash2 size={14} />
              <span>Delete</span>
            </button>
          </div>

          <div className="flex items-center gap-2">
            {item.status !== 'Found' && (
              <button
                onClick={() => {
                  setSelectedSmartBoxItem(item);
                  setSelectedDetailItem(null);
                }}
                className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-amber-600 hover:bg-amber-700 text-white text-xs font-semibold shadow-sm transition"
              >
                <LogIn size={15} />
                <span>Check In to Box</span>
              </button>
            )}

            {item.status === 'Found' && (
              <button
                onClick={() => {
                  setSelectedSmartBoxItem(item);
                  setSelectedDetailItem(null);
                }}
                className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold shadow-sm transition"
              >
                <LogOut size={15} />
                <span>Check Out / Return</span>
              </button>
            )}

            {item.status !== 'Lost' && (
              <button
                onClick={async () => {
                  await updateStatus(item.itemId, 'Lost');
                  setSelectedDetailItem(null);
                }}
                className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 hover:bg-rose-100 text-xs font-semibold transition"
              >
                <AlertCircle size={14} />
                <span>Mark Lost</span>
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
