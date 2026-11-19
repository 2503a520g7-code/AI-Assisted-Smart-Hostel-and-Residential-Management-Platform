import React from 'react';
import { AlertTriangle, CloudOff, ArrowRight, Server, RefreshCw } from 'lucide-react';
import { useApp } from '../../context/AppContext';

export const ConnectionBanner: React.FC = () => {
  const { awsStatus, awsStatusMessage, setActivePage, refreshData, isLoading } = useApp();

  if (awsStatus === 'connected' || awsStatus === 'checking') {
    return null;
  }

  if (awsStatus === 'not_configured') {
    return (
      <div className="mb-6 rounded-2xl bg-gradient-to-r from-amber-50 to-orange-50 border border-amber-200 p-5 shadow-sm">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-start gap-3.5">
            <div className="p-2.5 rounded-xl bg-amber-100 text-amber-800 shrink-0 mt-0.5">
              <CloudOff size={22} />
            </div>
            <div>
              <h3 className="text-sm font-bold text-amber-900">
                AWS API Gateway &amp; DynamoDB Not Connected
              </h3>
              <p className="text-xs text-amber-700 mt-1 max-w-2xl leading-relaxed">
                Environment variable <code className="px-1.5 py-0.5 bg-amber-100 rounded text-[11px] font-mono font-semibold">VITE_API_BASE_URL</code> is not configured.
                The frontend communicates directly with your AWS Lambda backend to persist items in DynamoDB. No fake statistics or mock records will be masqueraded as AWS data.
              </p>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-2.5 shrink-0 self-start md:self-center">
            <button
              onClick={() => setActivePage('settings')}
              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-amber-700 hover:bg-amber-800 text-white text-xs font-semibold shadow-sm transition"
            >
              <span>Setup AWS Endpoint</span>
              <ArrowRight size={14} />
            </button>
            <button
              onClick={() => setActivePage('settings')}
              className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-white hover:bg-amber-50 text-amber-800 border border-amber-300 text-xs font-semibold transition"
            >
              <Server size={14} />
              <span>View Setup Guide</span>
            </button>
          </div>
        </div>
      </div>
    );
  }

  // awsStatus === 'error'
  return (
    <div className="mb-6 rounded-2xl bg-rose-50 border border-rose-200 p-4 shadow-sm">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-start gap-3">
          <div className="p-2 rounded-lg bg-rose-100 text-rose-700 shrink-0">
            <AlertTriangle size={18} />
          </div>
          <div>
            <h4 className="text-xs font-bold text-rose-900 uppercase tracking-wide">
              AWS Connection Error
            </h4>
            <p className="text-xs text-rose-700 mt-0.5 font-mono">
              {awsStatusMessage || 'Could not reach AWS API Gateway endpoint. Please check CORS headers and Lambda deployment.'}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 shrink-0">
          <button
            onClick={() => refreshData()}
            disabled={isLoading}
            className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg bg-rose-600 hover:bg-rose-700 text-white text-xs font-medium transition disabled:opacity-50"
          >
            <RefreshCw size={13} className={isLoading ? 'animate-spin' : ''} />
            <span>Retry</span>
          </button>
          <button
            onClick={() => setActivePage('settings')}
            className="px-3 py-1.5 rounded-lg bg-white border border-rose-300 text-rose-800 hover:bg-rose-50 text-xs font-medium transition"
          >
            Settings
          </button>
        </div>
      </div>
    </div>
  );
};
