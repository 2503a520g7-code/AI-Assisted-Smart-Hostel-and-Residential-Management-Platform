import React from 'react';
import { 
  LayoutDashboard, 
  FolderKanban, 
  PlusCircle, 
  AlertOctagon, 
  PackageSearch, 
  CheckCircle2, 
  Settings, 
  Box, 
  Cloud, 
  Wifi, 
  WifiOff, 
  X,
  Radio
} from 'lucide-react';
import { useApp } from '../../context/AppContext';
import { NavigationPage } from '../../types/item';

interface SidebarProps {
  mobileOpen: boolean;
  setMobileOpen: (open: boolean) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ mobileOpen, setMobileOpen }) => {
  const { activePage, setActivePage, stats, awsStatus } = useApp();

  const navItems: {
    id: NavigationPage;
    label: string;
    icon: React.ElementType;
    badgeCount?: number;
    badgeColor?: string;
  }[] = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { 
      id: 'all-items', 
      label: 'All Items', 
      icon: FolderKanban, 
      badgeCount: stats?.totalItems,
      badgeColor: 'bg-slate-700 text-slate-200' 
    },
    { id: 'register', label: 'Register Item', icon: PlusCircle },
    { 
      id: 'lost-items', 
      label: 'Lost Items', 
      icon: AlertOctagon, 
      badgeCount: stats?.lostItems,
      badgeColor: 'bg-rose-500/20 text-rose-300 border border-rose-500/30' 
    },
    { 
      id: 'found-items', 
      label: 'Found Items', 
      icon: PackageSearch, 
      badgeCount: stats?.foundItems,
      badgeColor: 'bg-amber-500/20 text-amber-300 border border-amber-500/30' 
    },
    { 
      id: 'returned-items', 
      label: 'Returned Items', 
      icon: CheckCircle2, 
      badgeCount: stats?.returnedItems,
      badgeColor: 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30' 
    },
    { id: 'settings', label: 'Settings', icon: Settings },
  ];

  const handleNavClick = (page: NavigationPage) => {
    setActivePage(page);
    setMobileOpen(false);
  };

  return (
    <>
      {/* Mobile Backdrop */}
      {mobileOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/50 backdrop-blur-sm lg:hidden transition-opacity"
          onClick={() => setMobileOpen(false)}
        />
      )}

      {/* Sidebar Container */}
      <aside
        className={`fixed top-0 bottom-0 left-0 z-50 w-72 bg-slate-900 text-slate-100 flex flex-col justify-between transition-transform duration-300 ease-in-out border-r border-slate-800 shadow-xl lg:translate-x-0 ${
          mobileOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        {/* Brand & Header */}
        <div className="flex flex-col">
          <div className="flex items-center justify-between px-6 py-5 border-b border-slate-800/80">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-500 flex items-center justify-center text-white shadow-md shadow-blue-500/20">
                <Box size={22} className="stroke-[2.2]" />
              </div>
              <div>
                <h1 className="text-base font-bold tracking-tight text-white leading-tight">
                  Smart Box
                </h1>
                <p className="text-xs text-slate-400 font-medium">Campus Lost &amp; Found</p>
              </div>
            </div>
            <button
              onClick={() => setMobileOpen(false)}
              className="lg:hidden p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
              aria-label="Close sidebar"
            >
              <X size={20} />
            </button>
          </div>

          {/* Smart Box Hardware Indicator */}
          <div className="mx-4 mt-4 px-3 py-2 rounded-lg bg-slate-800/60 border border-slate-700/60 flex items-center justify-between text-xs">
            <div className="flex items-center gap-2 text-slate-300">
              <Radio size={14} className="text-blue-400 animate-pulse" />
              <span>RFID Smart Box Unit</span>
            </div>
            <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-blue-500/20 text-blue-300 font-semibold border border-blue-500/30">
              BOX-01 ONLINE
            </span>
          </div>

          {/* Navigation Items */}
          <nav className="px-3 py-4 space-y-1 overflow-y-auto">
            <div className="px-3 pb-2 text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
              Management
            </div>
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = activePage === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => handleNavClick(item.id)}
                  className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl text-sm font-medium transition-all group ${
                    isActive
                      ? 'bg-blue-600 text-white shadow-md shadow-blue-600/25 font-semibold'
                      : 'text-slate-300 hover:text-white hover:bg-slate-800/80'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <Icon
                      size={18}
                      className={`transition-colors ${
                        isActive ? 'text-white' : 'text-slate-400 group-hover:text-blue-400'
                      }`}
                    />
                    <span>{item.label}</span>
                  </div>

                  {item.badgeCount !== undefined && item.badgeCount > 0 && (
                    <span
                      className={`text-xs px-2 py-0.5 rounded-full font-semibold transition-colors ${
                        isActive
                          ? 'bg-white/20 text-white'
                          : item.badgeColor || 'bg-slate-800 text-slate-300'
                      }`}
                    >
                      {item.badgeCount}
                    </span>
                  )}
                </button>
              );
            })}
          </nav>
        </div>

        {/* Footer / AWS Connection Status */}
        <div className="p-4 border-t border-slate-800/80 bg-slate-950/40">
          <div
            onClick={() => handleNavClick('settings')}
            className="cursor-pointer p-3 rounded-xl bg-slate-800/80 hover:bg-slate-800 transition border border-slate-700/60"
            role="button"
            tabIndex={0}
            title="Click to view or edit AWS API Gateway settings"
          >
            <div className="flex items-center justify-between mb-1.5">
              <div className="flex items-center gap-2">
                <Cloud size={16} className="text-slate-400" />
                <span className="text-xs font-semibold text-slate-200">AWS Cloud Backend</span>
              </div>
              {awsStatus === 'connected' ? (
                <span className="flex items-center gap-1 text-[11px] text-emerald-400 font-medium">
                  <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                  Live
                </span>
              ) : awsStatus === 'checking' ? (
                <span className="text-[11px] text-blue-400 animate-pulse">Checking...</span>
              ) : (
                <span className="flex items-center gap-1 text-[11px] text-amber-400 font-medium">
                  <span className="w-2 h-2 rounded-full bg-amber-400" />
                  Offline
                </span>
              )}
            </div>

            <div className="flex items-center gap-2 text-[11px] text-slate-400">
              {awsStatus === 'connected' ? (
                <>
                  <Wifi size={13} className="text-emerald-400" />
                  <span className="truncate">DynamoDB &amp; API Gateway</span>
                </>
              ) : (
                <>
                  <WifiOff size={13} className="text-amber-400" />
                  <span className="truncate">Setup required in Settings</span>
                </>
              )}
            </div>
          </div>

          <div className="mt-3 text-center text-[11px] text-slate-400">
            Cloud Computing Project &bull; Product 50
          </div>
        </div>
      </aside>
    </>
  );
};
