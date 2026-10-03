import React, { useState } from 'react';
import { 
  Settings as SettingsIcon, 
  Server, 
  Send, 
  ExternalLink, 
  CheckCircle2, 
  AlertCircle, 
  RefreshCw,
  ShieldCheck,
  Bot
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { api } from '../api';

export default function Settings() {
  const { apiUrl, updateApiUrl, user } = useAuth();
  const [inputUrl, setInputUrl] = useState(apiUrl);
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState(null);
  const [savedSuccess, setSavedSuccess] = useState(false);

  const handleSaveUrl = (e) => {
    e.preventDefault();
    updateApiUrl(inputUrl.trim());
    setSavedSuccess(true);
    setTimeout(() => setSavedSuccess(false), 3000);
  };

  const handleTestConnection = async () => {
    setTesting(true);
    setTestResult(null);
    try {
      // Temporarily test the new url
      const res = await fetch(`${inputUrl.trim().replace(/\/+$/, '')}/api/auth/me`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('foodkh_admin_token') || ''}`
        }
      });
      if (res.ok || res.status === 401) {
        setTestResult({ success: true, message: 'Successfully reached backend server!' });
      } else {
        setTestResult({ success: false, message: `Server replied with status ${res.status}` });
      }
    } catch (err) {
      setTestResult({ success: false, message: `Could not reach server: ${err.message}` });
    } finally {
      setTesting(false);
    }
  };

  return (
    <div className="space-y-6 max-w-4xl">
      {/* Header */}
      <div>
        <h2 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
          <SettingsIcon className="w-5 h-5 text-emerald-400" />
          <span>System & API Configuration</span>
        </h2>
        <p className="text-xs text-slate-400 mt-0.5">
          Configure your decoupled Backend API server, review bot endpoints, and manage administrative settings
        </p>
      </div>

      {/* Backend API Connection Setting */}
      <div className="p-6 rounded-2xl bg-slate-900/90 border border-slate-800 space-y-4 shadow-xl">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-brand-500/10 text-brand-400 flex items-center justify-center">
            <Server className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-base font-bold text-white">Backend REST API Endpoint</h3>
            <p className="text-xs text-slate-400">
              The React Admin panel sends REST requests to this URL. You can host Backend API on Render, VPS, or run locally.
            </p>
          </div>
        </div>

        <form onSubmit={handleSaveUrl} className="space-y-3">
          <div className="flex flex-col sm:flex-row gap-3">
            <input
              type="text"
              required
              value={inputUrl}
              onChange={(e) => setInputUrl(e.target.value)}
              placeholder="e.g. http://localhost:8000 or https://your-backend.onrender.com"
              className="flex-1 px-4 py-2.5 rounded-xl bg-slate-800 border border-slate-700 text-white text-sm font-mono focus:outline-none focus:border-brand-500"
            />
            <div className="flex gap-2">
              <button
                type="button"
                onClick={handleTestConnection}
                disabled={testing}
                className="px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold border border-slate-700 transition-colors flex items-center gap-1.5"
              >
                {testing && <RefreshCw className="w-3.5 h-3.5 animate-spin" />}
                <span>Test Connection</span>
              </button>
              <button
                type="submit"
                className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-brand-500 to-emerald-600 hover:from-brand-600 hover:to-emerald-700 text-white text-xs font-semibold shadow-lg shadow-brand-500/20 transition-all"
              >
                Save URL
              </button>
            </div>
          </div>

          {savedSuccess && (
            <div className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4" />
              <span>Backend API URL updated successfully!</span>
            </div>
          )}

          {testResult && (
            <div className={`p-3 rounded-xl text-xs flex items-center gap-2 border ${
              testResult.success 
                ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300' 
                : 'bg-rose-500/10 border-rose-500/30 text-rose-300'
            }`}>
              {testResult.success ? <CheckCircle2 className="w-4 h-4" /> : <AlertCircle className="w-4 h-4" />}
              <span>{testResult.message}</span>
            </div>
          )}
        </form>

        {/* Quick presets */}
        <div className="pt-2 flex flex-wrap items-center gap-2 text-xs text-slate-400">
          <span>Quick presets:</span>
          <button
            type="button"
            onClick={() => setInputUrl('http://localhost:8000')}
            className="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 font-mono text-[11px]"
          >
            Localhost (:8000)
          </button>
          <button
            type="button"
            onClick={() => setInputUrl('https://fruitshop-backendapi.onrender.com')}
            className="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 font-mono text-[11px]"
          >
            Render Production
          </button>
        </div>
      </div>

      {/* Telegram Bot & MiniApp Info */}
      <div className="p-6 rounded-2xl bg-slate-900/90 border border-slate-800 space-y-4 shadow-xl">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-blue-500/10 text-blue-400 flex items-center justify-center">
            <Bot className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-base font-bold text-white">Telegram Bot & MiniApp Integration</h3>
            <p className="text-xs text-slate-400">
              Customers interact with this bot and open the shopping MiniApp directly inside Telegram.
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
          <div className="p-4 rounded-xl bg-slate-800/50 border border-slate-700/60">
            <span className="text-xs text-slate-400 block mb-1">Telegram Bot Handle</span>
            <div className="flex items-center justify-between">
              <span className="font-semibold text-white">@foodkhtestingbot</span>
              <a
                href="https://t.me/foodkhtestingbot"
                target="_blank"
                rel="noreferrer"
                className="text-emerald-400 hover:text-emerald-300 flex items-center gap-1 text-xs font-medium"
              >
                <span>Open Bot</span>
                <ExternalLink className="w-3.5 h-3.5" />
              </a>
            </div>
          </div>

          <div className="p-4 rounded-xl bg-slate-800/50 border border-slate-700/60">
            <span className="text-xs text-slate-400 block mb-1">Security & Encryption</span>
            <div className="flex items-center gap-2 text-emerald-400 text-xs font-semibold">
              <ShieldCheck className="w-4 h-4" />
              <span>Token Protected & Rate Limited</span>
            </div>
          </div>
        </div>
      </div>

      {/* Admin Profile */}
      <div className="p-6 rounded-2xl bg-slate-900/90 border border-slate-800 flex items-center justify-between shadow-xl">
        <div>
          <h3 className="text-sm font-bold text-white">Logged In Administrator</h3>
          <p className="text-xs text-slate-400">Username: <span className="font-mono text-emerald-400 font-semibold">{user?.username || 'admin'}</span></p>
        </div>
        <div className="text-right">
          <span className="text-xs px-3 py-1 rounded-full bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 font-semibold">
            SuperAdmin
          </span>
        </div>
      </div>
    </div>
  );
}
