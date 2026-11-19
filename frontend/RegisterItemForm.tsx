import React, { useState } from 'react';
import { 
  ItemCategory, 
  ItemStatus, 
  CreateItemInput 
} from '../../types/item';
import { useApp } from '../../context/AppContext';
import { 
  Radio, 
  Sparkles, 
  Send, 
  RotateCcw, 
  MapPin, 
  Calendar, 
  User, 
  Phone, 
  FileText, 
  Tag, 
  CheckCircle2, 
  AlertCircle,
  HelpCircle,
  Layers
} from 'lucide-react';
import { StatusBadge } from '../items/StatusBadge';

export const RegisterItemForm: React.FC = () => {
  const { createItem, isLoading, setActivePage, awsStatus } = useApp();

  const today = new Date().toISOString().slice(0, 10);

  const initialFormState: CreateItemInput = {
    itemName: '',
    category: 'Electronics',
    description: '',
    rfidTagId: '',
    locationFound: '',
    dateReported: today,
    reportedBy: '',
    contactInformation: '',
    status: 'Found',
  };

  const [formData, setFormData] = useState<CreateItemInput>(initialFormState);
  const [formErrors, setFormErrors] = useState<Record<string, string>>({});
  const [isScanningRfid, setIsScanningRfid] = useState(false);

  const categories: ItemCategory[] = [
    'ID Card',
    'Electronics',
    'Books',
    'Keys',
    'Bags',
    'Accessories',
    'Other',
  ];

  const statuses: { value: ItemStatus; label: string; desc: string }[] = [
    { value: 'Found', label: 'Found & Check-In', desc: 'Item is in possession and will be placed in Smart Box' },
    { value: 'Lost', label: 'Report Lost', desc: 'Item is missing and owner is seeking recovery' },
    { value: 'Returned', label: 'Returned to Owner', desc: 'Item was verified and handed back to rightful owner' },
  ];

  const campusLocations = [
    'Campus Main Library (2nd Fl)',
    'Engineering Hall B',
    'Student Cafeteria & Lounge',
    'Science Lab Complex #3',
    'Sports Arena & Gymnasium',
    'Administration Building Foyer',
    'North Parking Lot Zone C',
  ];

  // RFID Tag Generator / Simulation
  const handleSimulateRfidScan = () => {
    setIsScanningRfid(true);
    setTimeout(() => {
      const randomHex = Math.floor(100000 + Math.random() * 900000);
      setFormData((prev) => ({
        ...prev,
        rfidTagId: `RFID-${randomHex}`,
      }));
      setIsScanningRfid(false);
      setFormErrors((prev) => ({ ...prev, rfidTagId: '' }));
    }, 600);
  };

  const validate = (): boolean => {
    const errors: Record<string, string> = {};

    if (!formData.itemName.trim()) {
      errors.itemName = 'Item name is required.';
    } else if (formData.itemName.trim().length < 3) {
      errors.itemName = 'Item name must be at least 3 characters.';
    }

    if (!formData.category) {
      errors.category = 'Please select a category.';
    }

    if (!formData.dateReported) {
      errors.dateReported = 'Date is required.';
    }

    if (!formData.reportedBy.trim()) {
      errors.reportedBy = 'Reporter name is required.';
    }

    if (!formData.contactInformation.trim()) {
      errors.contactInformation = 'Contact email or phone is required.';
    }

    if (!formData.status) {
      errors.status = 'Initial status is required.';
    }

    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validate()) {
      return;
    }

    const created = await createItem(formData);
    if (created) {
      // Reset form on success
      setFormData(initialFormState);
      setFormErrors({});
      // Redirect to all-items
      setActivePage('all-items');
    }
  };

  const handleReset = () => {
    setFormData(initialFormState);
    setFormErrors({});
  };

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Intro Header */}
      <div className="bg-white rounded-2xl p-6 border border-slate-200/90 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-lg font-bold text-slate-800">
            Register Item into Smart Box System
          </h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Submit form to trigger AWS Lambda function and store record in Amazon DynamoDB.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs font-mono px-3 py-1 bg-slate-100 rounded-lg text-slate-700 border border-slate-200">
            Partition Key: itemId (Auto-generated)
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Main Form (8 cols on lg) */}
        <div className="lg:col-span-8 bg-white rounded-2xl p-6 sm:p-8 border border-slate-200/90 shadow-sm">
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Status Selection */}
            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
                Initial Item Status <span className="text-rose-500">*</span>
              </label>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                {statuses.map((st) => {
                  const isSelected = formData.status === st.value;
                  return (
                    <button
                      type="button"
                      key={st.value}
                      onClick={() => setFormData({ ...formData, status: st.value })}
                      className={`text-left p-3.5 rounded-xl border-2 transition-all flex flex-col justify-between ${
                        isSelected
                          ? 'border-blue-600 bg-blue-50/50 shadow-xs'
                          : 'border-slate-200 hover:border-slate-300 bg-white'
                      }`}
                    >
                      <div className="flex items-center justify-between mb-1">
                        <StatusBadge status={st.value} size="sm" />
                        {isSelected && (
                          <CheckCircle2 size={16} className="text-blue-600" />
                        )}
                      </div>
                      <p className="text-[11px] text-slate-500 mt-1 leading-snug">
                        {st.desc}
                      </p>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Item Name & Category */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1.5">
                  Item Name <span className="text-rose-500">*</span>
                </label>
                <div className="relative">
                  <Tag size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
                  <input
                    type="text"
                    placeholder="e.g., Apple AirPods Pro, Student ID Card"
                    value={formData.itemName}
                    onChange={(e) => {
                      setFormData({ ...formData, itemName: e.target.value });
                      if (formErrors.itemName) setFormErrors({ ...formErrors, itemName: '' });
                    }}
                    className={`w-full pl-10 pr-3.5 py-2 text-sm bg-slate-50 border rounded-xl focus:bg-white focus:outline-none transition ${
                      formErrors.itemName
                        ? 'border-rose-400 focus:border-rose-500'
                        : 'border-slate-200 focus:border-blue-500'
                    }`}
                  />
                </div>
                {formErrors.itemName && (
                  <p className="text-xs text-rose-500 mt-1 flex items-center gap-1">
                    <AlertCircle size={12} />
                    {formErrors.itemName}
                  </p>
                )}
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1.5">
                  Category <span className="text-rose-500">*</span>
                </label>
                <div className="relative">
                  <Layers size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
                  <select
                    value={formData.category}
                    onChange={(e) => {
                      setFormData({ ...formData, category: e.target.value as ItemCategory });
                      if (formErrors.category) setFormErrors({ ...formErrors, category: '' });
                    }}
                    className="w-full pl-10 pr-3.5 py-2 text-sm bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:border-blue-500 focus:outline-none transition appearance-none"
                  >
                    {categories.map((cat) => (
                      <option key={cat} value={cat}>
                        {cat}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
            </div>

            {/* RFID Tag ID & Scanner Button */}
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1.5">
                Smart Box RFID Tag ID (Optional / Auto-generated)
              </label>
              <div className="flex gap-2">
                <div className="relative flex-1">
                  <Radio size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
                  <input
                    type="text"
                    placeholder="e.g., RFID-981244"
                    value={formData.rfidTagId}
                    onChange={(e) => setFormData({ ...formData, rfidTagId: e.target.value.toUpperCase() })}
                    className="w-full pl-10 pr-3.5 py-2 text-sm font-mono bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:border-blue-500 focus:outline-none transition uppercase"
                  />
                </div>
                <button
                  type="button"
                  onClick={handleSimulateRfidScan}
                  disabled={isScanningRfid}
                  className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-semibold flex items-center gap-1.5 transition shrink-0"
                >
                  <Sparkles size={14} className={isScanningRfid ? 'animate-spin text-blue-600' : 'text-blue-500'} />
                  <span>{isScanningRfid ? 'Scanning...' : 'Scan RFID'}</span>
                </button>
              </div>
              <p className="text-[11px] text-slate-400 mt-1">
                Attach an RFID tag sticker when placing item inside the Smart Box compartment.
              </p>
            </div>

            {/* Description */}
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1.5">
                Item Description &amp; Distinct Marks
              </label>
              <div className="relative">
                <FileText size={16} className="absolute left-3.5 top-3 text-slate-400" />
                <textarea
                  rows={3}
                  placeholder="Color, brand, identifying stickers, contents, scratches, unique features..."
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  className="w-full pl-10 pr-3.5 py-2.5 text-sm bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:border-blue-500 focus:outline-none transition"
                />
              </div>
            </div>

            {/* Location & Date */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1.5">
                  Location Found / Lost
                </label>
                <div className="relative">
                  <MapPin size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
                  <input
                    type="text"
                    list="campus-locations"
                    placeholder="e.g., Main Library 2nd Floor"
                    value={formData.locationFound}
                    onChange={(e) => setFormData({ ...formData, locationFound: e.target.value })}
                    className="w-full pl-10 pr-3.5 py-2 text-sm bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:border-blue-500 focus:outline-none transition"
                  />
                  <datalist id="campus-locations">
                    {campusLocations.map((loc) => (
                      <option key={loc} value={loc} />
                    ))}
                  </datalist>
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1.5">
                  Date Reported <span className="text-rose-500">*</span>
                </label>
                <div className="relative">
                  <Calendar size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
                  <input
                    type="date"
                    value={formData.dateReported}
                    onChange={(e) => setFormData({ ...formData, dateReported: e.target.value })}
                    className="w-full pl-10 pr-3.5 py-2 text-sm bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:border-blue-500 focus:outline-none transition"
                  />
                </div>
              </div>
            </div>

            {/* Reporter Information */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2 border-t border-slate-100">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1.5">
                  Reported By (Name / Staff ID) <span className="text-rose-500">*</span>
                </label>
                <div className="relative">
                  <User size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
                  <input
                    type="text"
                    placeholder="e.g., Harshitha M. / Officer Roy"
                    value={formData.reportedBy}
                    onChange={(e) => {
                      setFormData({ ...formData, reportedBy: e.target.value });
                      if (formErrors.reportedBy) setFormErrors({ ...formErrors, reportedBy: '' });
                    }}
                    className={`w-full pl-10 pr-3.5 py-2 text-sm bg-slate-50 border rounded-xl focus:bg-white focus:outline-none transition ${
                      formErrors.reportedBy
                        ? 'border-rose-400 focus:border-rose-500'
                        : 'border-slate-200 focus:border-blue-500'
                    }`}
                  />
                </div>
                {formErrors.reportedBy && (
                  <p className="text-xs text-rose-500 mt-1 flex items-center gap-1">
                    <AlertCircle size={12} />
                    {formErrors.reportedBy}
                  </p>
                )}
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1.5">
                  Contact Information (Email / Phone) <span className="text-rose-500">*</span>
                </label>
                <div className="relative">
                  <Phone size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
                  <input
                    type="text"
                    placeholder="e.g., student@campus.edu or Ext 4022"
                    value={formData.contactInformation}
                    onChange={(e) => {
                      setFormData({ ...formData, contactInformation: e.target.value });
                      if (formErrors.contactInformation) setFormErrors({ ...formErrors, contactInformation: '' });
                    }}
                    className={`w-full pl-10 pr-3.5 py-2 text-sm bg-slate-50 border rounded-xl focus:bg-white focus:outline-none transition ${
                      formErrors.contactInformation
                        ? 'border-rose-400 focus:border-rose-500'
                        : 'border-slate-200 focus:border-blue-500'
                    }`}
                  />
                </div>
                {formErrors.contactInformation && (
                  <p className="text-xs text-rose-500 mt-1 flex items-center gap-1">
                    <AlertCircle size={12} />
                    {formErrors.contactInformation}
                  </p>
                )}
              </div>
            </div>

            {/* Buttons */}
            <div className="pt-4 border-t border-slate-100 flex items-center justify-between gap-3">
              <button
                type="button"
                onClick={handleReset}
                className="inline-flex items-center gap-1.5 px-4 py-2 text-xs font-semibold text-slate-600 hover:text-slate-900 bg-slate-100 hover:bg-slate-200 rounded-xl transition"
              >
                <RotateCcw size={14} />
                <span>Reset Form</span>
              </button>

              <button
                type="submit"
                disabled={isLoading}
                className="inline-flex items-center gap-2 px-6 py-2.5 bg-blue-600 hover:bg-blue-700 active:bg-blue-800 text-white rounded-xl text-sm font-semibold shadow-md shadow-blue-600/25 transition disabled:opacity-50"
              >
                <Send size={16} />
                <span>{isLoading ? 'Saving to DynamoDB...' : 'Register Item into DynamoDB'}</span>
              </button>
            </div>
          </form>
        </div>

        {/* Live Preview Card (4 cols on lg) */}
        <div className="lg:col-span-4 space-y-6">
          <div className="bg-slate-900 text-white rounded-2xl p-6 shadow-md border border-slate-800">
            <div className="flex items-center justify-between mb-4">
              <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                Live Record Preview
              </span>
              <StatusBadge status={formData.status} size="sm" />
            </div>

            <div className="space-y-4">
              <div>
                <h3 className="text-base font-bold text-white truncate">
                  {formData.itemName || 'Untitled Item'}
                </h3>
                <span className="text-xs text-blue-400 font-medium">
                  {formData.category}
                </span>
              </div>

              <div className="p-3 rounded-xl bg-slate-800/80 border border-slate-700/60 space-y-2 text-xs">
                <div className="flex items-center justify-between">
                  <span className="text-slate-400">RFID Tag:</span>
                  <span className="font-mono text-emerald-400">
                    {formData.rfidTagId || 'None assigned'}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-slate-400">Location:</span>
                  <span className="text-slate-200 truncate max-w-[150px]">
                    {formData.locationFound || 'Not specified'}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-slate-400">Reported On:</span>
                  <span className="text-slate-200">{formData.dateReported}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-slate-400">Reporter:</span>
                  <span className="text-slate-200 truncate max-w-[150px]">
                    {formData.reportedBy || 'Unknown'}
                  </span>
                </div>
              </div>

              <p className="text-xs text-slate-300 italic line-clamp-3">
                {formData.description ? `"${formData.description}"` : 'No description provided yet.'}
              </p>

              <div className="pt-3 border-t border-slate-800 text-[11px] text-slate-400 flex items-center justify-between">
                <span>DynamoDB Target:</span>
                <span className="font-mono text-slate-300">CampusLostAndFoundItems</span>
              </div>
            </div>
          </div>

          {/* Quick Smart Box Tip */}
          <div className="bg-blue-50 rounded-2xl p-5 border border-blue-200 text-xs text-blue-900 space-y-2">
            <h4 className="font-bold flex items-center gap-1.5 text-blue-800">
              <HelpCircle size={15} />
              Smart Box IoT Flow
            </h4>
            <p className="text-blue-700 leading-relaxed text-[11px]">
              When items are marked as <strong>Found</strong>, the system generates a check-in timestamp and prepares a Smart Box locker compartment for physical storage. When collected, the check-out timestamp is stamped and status becomes <strong>Returned</strong>.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
