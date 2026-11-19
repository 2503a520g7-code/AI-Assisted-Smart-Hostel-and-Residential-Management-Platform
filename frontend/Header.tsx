import React from 'react';
import { 
  Menu, 
  Search, 
  RotateCw, 
  Plus, 
  CloudCheck, 
  CloudOff, 
  AlertTriangle 
} from 'lucide-react';
import { useApp } from '../../context/AppContext';
import { NavigationPage } from '../../types/item';

interface HeaderProps {
  setMobileOpen: (open: boolean) => void;
}

export const Header: React.FC<HeaderProps> = ({ setMobileOpen }) => {
  const { 
    activePage, 
    setActivePage, 
    refreshData, 
    isLoading, 
    awsStatus, 
    searchQuery, 
    setSearchQuery 
  } = useApp();

  const getPageTitle = (page: NavigationPage) => {
    switch (page) {
      case 'dashboard':
        return { title: 'Dashboard', desc: 'Real-time overview of lost, found, and returned campus items' };
      case 'all-items':
        return { title: 'All Items', desc: 'Browse, search, and manage all campus lost and found records' };
      case 'register':
        return { title: 'Register Item', desc: 'Add a newly reported or smart box collected item to DynamoDB' };
      case 'lost-items':
        return { title: 'Lost Items', desc: 'Items reported missing by students, faculty, and campus staff' };
      case 'found-items':
        return { title: 'Found Items', desc: 'Items checked in to Smart Box lockers awaiting collection' };
      case 'returned-items':
        return { title: 'Returned Items', desc: 'Items checked out and successfully returned to verified owners' };
      case 'settings':
        return { title: 'AWS Cloud Settings', desc: 'API Gateway endpoint, DynamoDB connection, and setup instructions' };
    }
  };

  const { title, desc } = getPageTitle(activePage);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (activePage !== 'all-items') {
      setActivePage('all-items');
    }
  };

  return (
    <header className="sticky top-0 z-30 bg-white/80 backdrop-blur-md border-b border-slate-200/80 px-4 sm:px-8 py-3.5 flex items-center justify-between gap-4">
      {/* Left side: Hamburger & Titles */}
      <div className="flex items-center gap-3 sm:gap-4 min-w-0">
        <button
          onClick={() => setMobileOpen(true)}
          className="lg:hidden p-2 rounded-lg text-slate-600 hover:text-slate-900 hover:bg-slate-100 transition"
          aria-label="Open sidebar menu"
        >
          <Menu size={22} />
        </button>

        <div className="min-w-0">
          <h2 className="text-lg sm:text-xl font-bold text-slate-900 tracking-tight truncate">
            {title}
          </h2>
          <p className="text-xs text-slate-500 hidden sm:block truncate">
            {desc}
          </p>
        </div>
      </div>

      {/* Center/Right: Search, Status, Refresh & Register */}
      <div className="flex items-center gap-2.5 sm:gap-4">
        {/* Search input (visible on md+) */}
        <form onSubmit={handleSearchSubmit} className="relative hidden md:block w-48 lg:w-64">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            placeholder="Search items, RFID..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-3 py-1.5 text-xs bg-slate-100 border border-transparent rounded-lg focus:bg-white focus:border-blue-500 focus:outline-none transition"
          />
        </form>

        {/* AWS Connection Badge */}
        <button
          onClick={() => setActivePage('settings')}
          className={`hidden sm:inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium border transition-colors shadow-sm ${
            awsStatus === 'connected'
              ? 'bg-emerald-50 text-emerald-700 border-emerald-200 hover:bg-emerald-100'
              : awsStatus === 'checking'
              ? 'bg-blue-50 text-blue-700 border-blue-200 hover:bg-blue-100'
              : 'bg-amber-50 text-amber-700 border-amber-200 hover:bg-amber-100'
          }`}
          title="Click to view AWS API configuration"
        >
          {awsStatus === 'connected' ? (
            <>
              <CloudCheck size={14} className="text-emerald-600" />
              <span>AWS Connected</span>
            </>
          ) : awsStatus === 'checking' ? (
            <>
              <RotateCw size={14} className="text-blue-600 animate-spin" />
              <span>Checking AWS...</span>
            </>
          ) : (
            <>
              <CloudOff size={14} className="text-amber-600" />
              <span>AWS Not Connected</span>
            </>
          )}
        </button>

        {/* Refresh Button */}
        <button
          onClick={() => refreshData()}
          disabled={isLoading}
          className="p-2 text-slate-600 hover:text-slate-900 hover:bg-slate-100 rounded-lg border border-slate-200/80 transition disabled:opacity-50"
          title="Refresh data from AWS DynamoDB"
        >
          <RotateCw size={17} className={isLoading ? 'animate-spin text-blue-600' : ''} />
        </button>

        {/* Register Item Quick Action Button */}
        {activePage !== 'register' && (
          <button
            onClick={() => setActivePage('register')}
            className="inline-flex items-center gap-1.5 bg-blue-600 hover:bg-blue-700 active:bg-blue-800 text-white px-3.5 py-1.5 sm:px-4 sm:py-2 rounded-lg text-xs sm:text-sm font-semibold shadow-sm shadow-blue-600/20 transition"
          >
            <Plus size={16} />
            <span className="hidden xs:inline">Register Item</span>
          </button>
        )}
      </div>
    </header>
  );
};
