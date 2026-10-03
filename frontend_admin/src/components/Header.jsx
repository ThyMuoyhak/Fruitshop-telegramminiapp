import React, { useState, useEffect } from 'react';
import { Menu, Server, RefreshCw, CheckCircle2, AlertCircle, Download } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { api } from '../api';

export default function Header({ title, subtitle, onRefresh, setIsMobileOpen }) {
  const { apiUrl } = useAuth();
  const [isBackendHealthy, setIsBackendHealthy] = useState(null);
  const [checking, setChecking] = useState(false);
  const [backingUp, setBackingUp] = useState(false);

  const checkConnection = async () => {
    setChecking(true);
    try {
      await api.getMe();
      setIsBackendHealthy(true);
    } catch (e) {
      setIsBackendHealthy(false);
    } finally {
      setChecking(false);
    }
  };

  const handleQuickBackup = async () => {
    setBackingUp(true);
    try {
      await api.downloadBackup();
    } catch (err) {
      alert(`Backup failed: ${err.message}`);
    } finally {
      setBackingUp(false);
    }
  };

  useEffect(() => {
    checkConnection();
    const interval = setInterval(checkConnection, 30000);
    return () => clearInterval(interval);
  }, [apiUrl]);

  return (
    <header className="sticky top-0 z-30 bg-slate-900/80 backdrop-blur-md border-b border-slate-800/80 px-4 sm:px-8 py-4 flex items-center justify-between">
      <div className="flex items-center space-x-3">
        <button
          onClick={() => setIsMobileOpen(true)}
          className="lg:hidden p-2 rounded-lg bg-slate-800 text-slate-300 hover:text-white"
        >
          <Menu className="w-5 h-5" />
        </button>
        <div>
          <h2 className="text-xl font-bold text-white tracking-tight">{title}</h2>
          {subtitle && <p className="text-xs text-slate-400 hidden sm:block">{subtitle}</p>}
        </div>
      </div>

      <div className="flex items-center space-x-3">
        {/* Backend Host Badge */}
        <div 
          onClick={checkConnection}
          className="cursor-pointer flex items-center space-x-2 px-3 py-1.5 rounded-full bg-slate-800/90 border border-slate-700/80 hover:border-slate-600 transition-colors"
          title="Click to re-check API connection"
        >
          <Server className="w-3.5 h-3.5 text-slate-400" />
          <span className="text-[11px] font-medium text-slate-300 max-w-[120px] sm:max-w-[200px] truncate">
            {apiUrl.replace(/^https?:\/\//, '')}
          </span>
          {checking ? (
            <RefreshCw className="w-3 h-3 text-slate-400 animate-spin" />
          ) : isBackendHealthy ? (
            <span className="flex items-center text-[10px] text-emerald-400 font-semibold gap-1">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
              Live
            </span>
          ) : (
            <span className="flex items-center text-[10px] text-rose-400 font-semibold gap-1">
              <span className="w-2 h-2 rounded-full bg-rose-400"></span>
              Offline
            </span>
          )}
        </div>

        {/* Quick Backup ZIP Button */}
        <button
          onClick={handleQuickBackup}
          disabled={backingUp}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 text-xs font-medium transition-colors disabled:opacity-50"
          title="Download Full Backup ZIP (Database & Images)"
        >
          {backingUp ? (
            <RefreshCw className="w-3.5 h-3.5 animate-spin" />
          ) : (
            <Download className="w-3.5 h-3.5" />
          )}
          <span className="hidden sm:inline">{backingUp ? 'Backing up...' : 'Backup ZIP'}</span>
        </button>

        {onRefresh && (
          <button
            onClick={onRefresh}
            className="p-2 rounded-lg bg-slate-800/80 hover:bg-slate-700 text-slate-300 hover:text-white border border-slate-700/60 transition-colors"
            title="Refresh Data"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        )}
      </div>
    </header>
  );
}

