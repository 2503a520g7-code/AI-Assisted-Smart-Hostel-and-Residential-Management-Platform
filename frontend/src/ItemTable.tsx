import React, { useState, useMemo } from 'react';
import { 
  LostAndFoundItem, 
  ItemCategory, 
  ItemStatus 
} from '../../types/item';
import { StatusBadge } from './StatusBadge';
import { useApp } from '../../context/AppContext';
import { 
  Search, 
  Filter, 
  Calendar, 
  Eye, 
  Edit3, 
  LogIn, 
  LogOut, 
  Trash2, 
  AlertCircle, 
  ChevronLeft, 
  ChevronRight, 
  X, 
  Radio, 
  ArrowUpDown 
} from 'lucide-react';

interface ItemTableProps {
  initialStatusFilter?: ItemStatus | 'ALL';
  title?: string;
  subtitle?: string;
}

export const ItemTable: React.FC<ItemTableProps> = ({
  initialStatusFilter = 'ALL',
  title = 'Campus Lost & Found Records',
  subtitle = 'Full database stored in Amazon DynamoDB with live RFID Smart Box tracking'
}) => {
  const { 
    items, 
    isLoading, 
    updateStatus, 
    deleteItem, 
    setSelectedDetailItem, 
    setSelectedEditItem, 
    setSelectedSmartBoxItem,
    searchQuery: globalSearchQuery,
    setSearchQuery: setGlobalSearchQuery,
    setActivePage
  } = useApp();

  // Filters state
  const [localSearch, setLocalSearch] = useState<string>(globalSearchQuery || '');
  const [categoryFilter, setCategoryFilter] = useState<string>('ALL');
  const [statusFilter, setStatusFilter] = useState<string>(initialStatusFilter);
  const [dateFilter, setDateFilter] = useState<string>('');
  const [deleteConfirmItemId, setDeleteConfirmItemId] = useState<string | null>(null);

  // Sorting
  const [sortField, setSortField] = useState<keyof LostAndFoundItem>('createdAt');
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('desc');

  // Pagination
  const [currentPage, setCurrentPage] = useState<number>(1);
  const [pageSize, setPageSize] = useState<number>(10);

  const categories: ItemCategory[] = [
    'ID Card',
    'Electronics',
    'Books',
    'Keys',
    'Bags',
    'Accessories',
    'Other',
  ];

  // Filtering logic
  const filteredItems = useMemo(() => {
    return items.filter((item) => {
      // 1. Search by name, item ID, or RFID
      const search = localSearch.trim().toLowerCase();
      if (search) {
        const matchesName = item.itemName?.toLowerCase().includes(search);
        const matchesId = item.itemId?.toLowerCase().includes(search);
        const matchesRfid = item.rfidTagId?.toLowerCase().includes(search);
        const matchesLocation = item.locationFound?.toLowerCase().includes(search);
        if (!matchesName && !matchesId && !matchesRfid && !matchesLocation) {
          return false;
        }
      }

      // 2. Category filter
      if (categoryFilter !== 'ALL' && item.category !== categoryFilter) {
        return false;
      }

      // 3. Status filter
      if (statusFilter !== 'ALL' && item.status !== statusFilter) {
        return false;
      }

      // 4. Date filter
      if (dateFilter && item.dateReported !== dateFilter) {
        return false;
      }

      return true;
    });
  }, [items, localSearch, categoryFilter, statusFilter, dateFilter]);

  // Sorting logic
  const sortedItems = useMemo(() => {
    const list = [...filteredItems];
    list.sort((a, b) => {
      const valA = a[sortField] || '';
      const valB = b[sortField] || '';

      if (valA < valB) return sortDirection === 'asc' ? -1 : 1;
      if (valA > valB) return sortDirection === 'asc' ? 1 : -1;
      return 0;
    });
    return list;
  }, [filteredItems, sortField, sortDirection]);

  // Pagination calculation
  const totalItems = sortedItems.length;
  const totalPages = Math.max(1, Math.ceil(totalItems / pageSize));
  const paginatedItems = useMemo(() => {
    const start = (currentPage - 1) * pageSize;
    return sortedItems.slice(start, start + pageSize);
  }, [sortedItems, currentPage, pageSize]);

  const handleSort = (field: keyof LostAndFoundItem) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('desc');
    }
  };

  const handleClearFilters = () => {
    setLocalSearch('');
    setGlobalSearchQuery('');
    setCategoryFilter('ALL');
    setStatusFilter(initialStatusFilter);
    setDateFilter('');
    setCurrentPage(1);
  };

  const handleDelete = async (itemId: string) => {
    await deleteItem(itemId);
    setDeleteConfirmItemId(null);
  };

  return (
    <div className="space-y-5">
      {/* Page Title & Controls */}
      <div className="bg-white rounded-2xl p-6 border border-slate-200/90 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-lg font-bold text-slate-800">{title}</h2>
          <p className="text-xs text-slate-500 mt-0.5">{subtitle}</p>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold px-3 py-1.5 rounded-lg bg-blue-50 text-blue-700 border border-blue-200">
            {totalItems} item{totalItems === 1 ? '' : 's'} matching
          </span>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-white rounded-2xl p-4 sm:p-5 border border-slate-200/90 shadow-sm space-y-3">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-12 gap-3">
          {/* Search Box (5 cols on lg) */}
          <div className="lg:col-span-5 relative">
            <Search size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              placeholder="Search by Item Name, Item ID, or RFID..."
              value={localSearch}
              onChange={(e) => {
                setLocalSearch(e.target.value);
                setCurrentPage(1);
              }}
              className="w-full pl-10 pr-9 py-2 text-xs bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:border-blue-500 focus:outline-none transition"
            />
            {localSearch && (
              <button
                onClick={() => setLocalSearch('')}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
              >
                <X size={14} />
              </button>
            )}
          </div>

          {/* Category Filter (3 cols on lg) */}
          <div className="lg:col-span-3 relative">
            <Filter size={15} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
            <select
              value={categoryFilter}
              onChange={(e) => {
                setCategoryFilter(e.target.value);
                setCurrentPage(1);
              }}
              className="w-full pl-9 pr-3 py-2 text-xs bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:border-blue-500 focus:outline-none transition"
            >
              <option value="ALL">All Categories</option>
              {categories.map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>
          </div>

          {/* Status Filter (2 cols on lg) */}
          <div className="lg:col-span-2">
            <select
              value={statusFilter}
              onChange={(e) => {
                setStatusFilter(e.target.value);
                setCurrentPage(1);
              }}
              disabled={initialStatusFilter !== 'ALL'}
              className="w-full px-3 py-2 text-xs bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:border-blue-500 focus:outline-none transition disabled:opacity-60"
            >
              <option value="ALL">All Statuses</option>
              <option value="Lost">Lost</option>
              <option value="Found">Found</option>
              <option value="Returned">Returned</option>
            </select>
          </div>

          {/* Date Filter (2 cols on lg) */}
          <div className="lg:col-span-2 relative">
            <input
              type="date"
              value={dateFilter}
              onChange={(e) => {
                setDateFilter(e.target.value);
                setCurrentPage(1);
              }}
              className="w-full px-3 py-2 text-xs bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:border-blue-500 focus:outline-none transition"
              title="Filter by Reported Date"
            />
          </div>
        </div>

        {/* Filter Tags & Clear Filters */}
        {(localSearch || categoryFilter !== 'ALL' || (statusFilter !== 'ALL' && initialStatusFilter === 'ALL') || dateFilter) && (
          <div className="flex flex-wrap items-center gap-2 pt-2 border-t border-slate-100 text-xs">
            <span className="text-slate-400 text-[11px]">Active Filters:</span>
            {localSearch && (
              <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-blue-50 text-blue-700 text-[11px] font-medium border border-blue-200">
                Search: "{localSearch}"
                <button onClick={() => setLocalSearch('')}><X size={12} /></button>
              </span>
            )}
            {categoryFilter !== 'ALL' && (
              <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-purple-50 text-purple-700 text-[11px] font-medium border border-purple-200">
                Category: {categoryFilter}
                <button onClick={() => setCategoryFilter('ALL')}><X size={12} /></button>
              </span>
            )}
            {statusFilter !== 'ALL' && initialStatusFilter === 'ALL' && (
              <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-amber-50 text-amber-700 text-[11px] font-medium border border-amber-200">
                Status: {statusFilter}
                <button onClick={() => setStatusFilter('ALL')}><X size={12} /></button>
              </span>
            )}
            {dateFilter && (
              <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-slate-100 text-slate-700 text-[11px] font-medium border border-slate-200">
                Date: {dateFilter}
                <button onClick={() => setDateFilter('')}><X size={12} /></button>
              </span>
            )}
            <button
              onClick={handleClearFilters}
              className="text-[11px] text-rose-600 hover:text-rose-700 font-semibold ml-auto"
            >
              Reset Filters
            </button>
          </div>
        )}
      </div>

      {/* Main Table */}
      <div className="bg-white rounded-2xl border border-slate-200/90 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-50/80 border-b border-slate-200/80 text-[11px] font-semibold text-slate-500 uppercase tracking-wider">
                <th 
                  className="py-3.5 px-6 cursor-pointer hover:text-slate-800 transition select-none"
                  onClick={() => handleSort('itemId')}
                >
                  <div className="flex items-center gap-1.5">
                    <span>Item ID</span>
                    <ArrowUpDown size={12} />
                  </div>
                </th>
                <th 
                  className="py-3.5 px-6 cursor-pointer hover:text-slate-800 transition select-none"
                  onClick={() => handleSort('itemName')}
                >
                  <div className="flex items-center gap-1.5">
                    <span>Item Name</span>
                    <ArrowUpDown size={12} />
                  </div>
                </th>
                <th 
                  className="py-3.5 px-6 cursor-pointer hover:text-slate-800 transition select-none"
                  onClick={() => handleSort('category')}
                >
                  <div className="flex items-center gap-1.5">
                    <span>Category</span>
                    <ArrowUpDown size={12} />
                  </div>
                </th>
                <th className="py-3.5 px-6">RFID Tag ID</th>
                <th className="py-3.5 px-6">Location</th>
                <th 
                  className="py-3.5 px-6 cursor-pointer hover:text-slate-800 transition select-none"
                  onClick={() => handleSort('dateReported')}
                >
                  <div className="flex items-center gap-1.5">
                    <span>Date</span>
                    <ArrowUpDown size={12} />
                  </div>
                </th>
                <th className="py-3.5 px-6">Status</th>
                <th className="py-3.5 px-6 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-xs">
              {paginatedItems.length === 0 ? (
                <tr>
                  <td colSpan={8} className="py-16 text-center text-slate-400">
                    <div className="max-w-sm mx-auto space-y-3">
                      <div className="w-12 h-12 rounded-full bg-slate-100 mx-auto flex items-center justify-center text-slate-400">
                        <Search size={22} />
                      </div>
                      <p className="font-semibold text-slate-700">No items found</p>
                      <p className="text-xs text-slate-500">
                        {localSearch || categoryFilter !== 'ALL' || dateFilter
                          ? 'Try adjusting your filters or search keywords.'
                          : 'There are no records in DynamoDB yet.'}
                      </p>
                      {items.length === 0 ? (
                        <button
                          onClick={() => setActivePage('register')}
                          className="px-4 py-2 bg-blue-600 text-white rounded-xl text-xs font-semibold hover:bg-blue-700 transition"
                        >
                          Register First Item
                        </button>
                      ) : (
                        <button
                          onClick={handleClearFilters}
                          className="px-4 py-2 bg-slate-100 text-slate-700 rounded-xl text-xs font-semibold hover:bg-slate-200 transition"
                        >
                          Clear All Filters
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ) : (
                paginatedItems.map((item) => (
                  <tr
                    key={item.itemId}
                    className="hover:bg-slate-50/70 transition-colors group"
                  >
                    {/* Item ID */}
                    <td className="py-3.5 px-6 font-mono text-[11px] font-semibold text-slate-700 whitespace-nowrap">
                      <span className="px-2.5 py-1 rounded-md bg-slate-100 border border-slate-200/80 text-slate-800">
                        {item.itemId}
                      </span>
                    </td>

                    {/* Item Name */}
                    <td className="py-3.5 px-6 font-semibold text-slate-900 max-w-[200px]">
                      <button
                        onClick={() => setSelectedDetailItem(item)}
                        className="hover:text-blue-600 text-left truncate block w-full transition"
                      >
                        {item.itemName}
                      </button>
                      {item.description && (
                        <span className="text-[11px] text-slate-400 truncate block font-normal">
                          {item.description}
                        </span>
                      )}
                    </td>

                    {/* Category */}
                    <td className="py-3.5 px-6 whitespace-nowrap">
                      <span className="px-2.5 py-0.5 rounded-full bg-slate-100 text-slate-700 font-medium text-[11px]">
                        {item.category}
                      </span>
                    </td>

                    {/* RFID Tag ID */}
                    <td className="py-3.5 px-6 font-mono text-[11px] text-slate-600 whitespace-nowrap">
                      {item.rfidTagId ? (
                        <span className="inline-flex items-center gap-1 text-slate-700">
                          <Radio size={12} className="text-blue-500" />
                          {item.rfidTagId}
                        </span>
                      ) : (
                        <span className="text-slate-300 italic text-[11px]">Unassigned</span>
                      )}
                    </td>

                    {/* Location */}
                    <td className="py-3.5 px-6 text-slate-600 max-w-[150px] truncate">
                      {item.locationFound || '—'}
                    </td>

                    {/* Date */}
                    <td className="py-3.5 px-6 text-slate-500 whitespace-nowrap">
                      {item.dateReported || '—'}
                    </td>

                    {/* Status */}
                    <td className="py-3.5 px-6 whitespace-nowrap">
                      <StatusBadge status={item.status} size="sm" />
                    </td>

                    {/* Actions */}
                    <td className="py-3.5 px-6 text-right whitespace-nowrap">
                      <div className="flex items-center justify-end gap-1">
                        {/* View Details */}
                        <button
                          onClick={() => setSelectedDetailItem(item)}
                          className="p-1.5 rounded-lg text-slate-500 hover:text-blue-600 hover:bg-blue-50 transition"
                          title="View Details"
                        >
                          <Eye size={16} />
                        </button>

                        {/* Edit Item */}
                        <button
                          onClick={() => setSelectedEditItem(item)}
                          className="p-1.5 rounded-lg text-slate-500 hover:text-indigo-600 hover:bg-indigo-50 transition"
                          title="Edit Item"
                        >
                          <Edit3 size={16} />
                        </button>

                        {/* Check In / Mark as Found (if not already Found) */}
                        {item.status !== 'Found' && (
                          <button
                            onClick={() => setSelectedSmartBoxItem(item)}
                            className="p-1.5 rounded-lg text-slate-500 hover:text-amber-600 hover:bg-amber-50 transition"
                            title="Check In to Smart Box"
                          >
                            <LogIn size={16} />
                          </button>
                        )}

                        {/* Check Out / Mark as Returned (if Found) */}
                        {item.status === 'Found' && (
                          <button
                            onClick={() => setSelectedSmartBoxItem(item)}
                            className="p-1.5 rounded-lg text-slate-500 hover:text-emerald-600 hover:bg-emerald-50 transition"
                            title="Check Out / Return to Owner"
                          >
                            <LogOut size={16} />
                          </button>
                        )}

                        {/* Mark as Lost (if Found or Returned) */}
                        {item.status !== 'Lost' && (
                          <button
                            onClick={() => updateStatus(item.itemId, 'Lost')}
                            className="p-1.5 rounded-lg text-slate-500 hover:text-rose-600 hover:bg-rose-50 transition"
                            title="Mark as Lost"
                          >
                            <AlertCircle size={16} />
                          </button>
                        )}

                        {/* Delete Item */}
                        <button
                          onClick={() => setDeleteConfirmItemId(item.itemId)}
                          className="p-1.5 rounded-lg text-slate-500 hover:text-rose-600 hover:bg-rose-50 transition"
                          title="Delete from DynamoDB"
                        >
                          <Trash2 size={16} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination Bar */}
        <div className="p-4 bg-slate-50/80 border-t border-slate-200/80 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-slate-500">
          <div className="flex items-center gap-2">
            <span>Rows per page:</span>
            <select
              value={pageSize}
              onChange={(e) => {
                setPageSize(Number(e.target.value));
                setCurrentPage(1);
              }}
              className="bg-white border border-slate-200 rounded-lg px-2 py-1 text-xs focus:outline-none"
            >
              <option value={5}>5</option>
              <option value={10}>10</option>
              <option value={25}>25</option>
              <option value={50}>50</option>
            </select>
            <span>
              Showing {totalItems === 0 ? 0 : (currentPage - 1) * pageSize + 1} -{' '}
              {Math.min(currentPage * pageSize, totalItems)} of {totalItems}
            </span>
          </div>

          <div className="flex items-center gap-1.5">
            <button
              onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
              disabled={currentPage === 1}
              className="p-1.5 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 disabled:opacity-40 transition"
              title="Previous Page"
            >
              <ChevronLeft size={16} />
            </button>
            <span className="px-3 py-1 font-medium text-slate-700 bg-white border border-slate-200 rounded-lg">
              {currentPage} / {totalPages}
            </span>
            <button
              onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
              disabled={currentPage === totalPages}
              className="p-1.5 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 disabled:opacity-40 transition"
              title="Next Page"
            >
              <ChevronRight size={16} />
            </button>
          </div>
        </div>
      </div>

      {/* Delete Confirmation Modal */}
      {deleteConfirmItemId && (
        <div className="fixed inset-0 z-50 bg-black/50 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl p-6 max-w-md w-full shadow-xl border border-slate-200 space-y-4 animate-in fade-in zoom-in-95 duration-150">
            <div className="flex items-center gap-3 text-rose-600">
              <div className="p-2.5 rounded-xl bg-rose-50 border border-rose-200">
                <Trash2 size={22} />
              </div>
              <h3 className="text-base font-bold text-slate-900">
                Confirm Item Deletion
              </h3>
            </div>

            <p className="text-xs text-slate-600 leading-relaxed">
              Are you sure you want to permanently delete item <code className="font-mono font-semibold px-1 py-0.5 bg-slate-100 rounded text-slate-800">{deleteConfirmItemId}</code> from Amazon DynamoDB? This operation cannot be reversed.
            </p>

            <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-100">
              <button
                onClick={() => setDeleteConfirmItemId(null)}
                className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-600 hover:bg-slate-100 transition"
              >
                Cancel
              </button>
              <button
                onClick={() => handleDelete(deleteConfirmItemId)}
                disabled={isLoading}
                className="px-4 py-2 rounded-xl text-xs font-semibold bg-rose-600 hover:bg-rose-700 text-white shadow-sm transition disabled:opacity-50"
              >
                {isLoading ? 'Deleting...' : 'Delete Permanently'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
