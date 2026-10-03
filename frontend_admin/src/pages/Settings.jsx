import React, { useState, useEffect } from 'react';
import { 
  Settings as SettingsIcon, 
  Server, 
  Send, 
  ExternalLink, 
  CheckCircle2, 
  AlertCircle, 
  RefreshCw,
  ShieldCheck,
  Bot,
  Download,
  Upload,
  Archive,
  Database,
  AlertTriangle,
  HardDrive
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { api } from '../api';
import Modal from '../components/Modal';

export default function Settings() {
  const { apiUrl, updateApiUrl, user } = useAuth();
  const [inputUrl, setInputUrl] = useState(apiUrl);
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState(null);
  const [savedSuccess, setSavedSuccess] = useState(false);

  // Disk & Storage states
  const [diskInfo, setDiskInfo] = useState(null);
  const [loadingDisk, setLoadingDisk] = useState(false);

  // Backup & Restore states
  const [isBackingUp, setIsBackingUp] = useState(false);
  const [isRestoring, setIsRestoring] = useState(false);
  const [backupMsg, setBackupMsg] = useState(null);
  const [selectedBackupFile, setSelectedBackupFile] = useState(null);
  const [showRestoreModal, setShowRestoreModal] = useState(false);

  const fetchDiskStatus = async () => {
    setLoadingDisk(true);
    try {
      const data = await api.getDiskStatus();
      setDiskInfo(data);
    } catch (err) {
      console.warn('Could not fetch disk status:', err.message);
    } finally {
      setLoadingDisk(false);
    }
  };

  useEffect(() => {
    fetchDiskStatus();
  }, [apiUrl]);

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

  const handleDownloadBackup = async () => {
    setIsBackingUp(true);
    setBackupMsg(null);
    try {
      const res = await api.downloadBackup();
      setBackupMsg({
        type: 'success',
        text: `Full Backup ZIP (${res.filename}) downloaded successfully with database and all uploaded images!`
      });
    } catch (err) {
      setBackupMsg({
        type: 'error',
        text: `Backup download failed: ${err.message}`
      });
    } finally {
      setIsBackingUp(false);
    }
  };

  const handleFileSelect = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!file.name.toLowerCase().endsWith('.zip')) {
      setBackupMsg({
        type: 'error',
        text: 'Invalid file format. Please upload a valid .ZIP backup file.'
      });
      e.target.value = '';
      return;
    }

    setSelectedBackupFile(file);
    setShowRestoreModal(true);
    e.target.value = '';
  };

  const handleExecuteRestore = async () => {
    if (!selectedBackupFile) return;
    setIsRestoring(true);
    setShowRestoreModal(false);
    setBackupMsg(null);

    try {
      const res = await api.restoreBackup(selectedBackupFile);
      setBackupMsg({
        type: 'success',
        text: res.message || 'Backup restored successfully! Database and all images restored.'
      });
    } catch (err) {
      setBackupMsg({
        type: 'error',
        text: `Restore failed: ${err.message}`
      });
    } finally {
      setIsRestoring(false);
      setSelectedBackupFile(null);
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
          Configure your decoupled Backend API server, backup & restore database and media, and review bot settings
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

      {/* Render Persistent Disk & Storage Status */}
      <div className="p-6 rounded-2xl bg-slate-900/90 border border-slate-800 space-y-4 shadow-xl">
        <div className="flex items-center justify-between flex-wrap gap-3">
          <div className="flex items-center gap-3">
            <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${
              diskInfo?.is_persistent 
                ? 'bg-emerald-500/10 text-emerald-400' 
                : 'bg-amber-500/10 text-amber-400'
            }`}>
              <HardDrive className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <span>Render Persistent Disk (/var/data)</span>
                {loadingDisk ? (
                  <RefreshCw className="w-3.5 h-3.5 animate-spin text-slate-400" />
                ) : diskInfo?.is_persistent ? (
                  <span className="text-[10px] px-2.5 py-0.5 rounded-full bg-emerald-500/20 text-emerald-400 font-semibold border border-emerald-500/30 flex items-center gap-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
                    Mounted & Persistent
                  </span>
                ) : (
                  <span className="text-[10px] px-2.5 py-0.5 rounded-full bg-rose-500/20 text-rose-400 font-semibold border border-rose-500/30 flex items-center gap-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-rose-400"></span>
                    Not Mounted (Ephemeral)
                  </span>
                )}
              </h3>
              <p className="text-xs text-slate-400">
                Persistent disk status and directory verification on Render cloud.
              </p>
            </div>
          </div>

          <button
            type="button"
            onClick={fetchDiskStatus}
            disabled={loadingDisk}
            className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 text-xs font-medium transition-colors flex items-center gap-1.5"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loadingDisk ? 'animate-spin' : ''}`} />
            <span>Check Disk</span>
          </button>
        </div>

        {/* Message Banner */}
        {diskInfo && (
          <div className={`p-3.5 rounded-xl text-xs flex items-start gap-2.5 border ${
            diskInfo.is_persistent
              ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'
              : 'bg-amber-500/10 border-amber-500/30 text-amber-300'
          }`}>
            {diskInfo.is_persistent ? (
              <CheckCircle2 className="w-4 h-4 shrink-0 mt-0.5 text-emerald-400" />
            ) : (
              <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5 text-amber-400" />
            )}
            <div className="space-y-1">
              <p className="font-semibold">{diskInfo.message}</p>
              {!diskInfo.is_persistent && (
                <div className="text-slate-300 text-[11px] space-y-1 pt-1.5 border-t border-amber-500/20">
                  <p className="font-bold text-amber-200">How to mount your Render Disk so data NEVER clears on redeploy:</p>
                  <ol className="list-decimal list-inside space-y-1 text-slate-300">
                    <li>Go to Render Dashboard &gt; <strong>FruitShop_backendAPI</strong> &gt; <strong>Disks</strong>.</li>
                    <li>Click <strong>Edit</strong> on your 5 GB disk and set <strong>Mount Path</strong> to: <code className="text-amber-200 font-mono bg-slate-800 px-1 py-0.5 rounded">/var/data</code>.</li>
                    <li>Go to <strong>Environment</strong> tab on Render and add variable: <code className="text-amber-200 font-mono bg-slate-800 px-1 py-0.5 rounded">DATA_DIR = /var/data</code>.</li>
                    <li>Update your Render payment method under <a href="https://dashboard.render.com/billing#payment-method" target="_blank" rel="noreferrer" className="text-amber-300 underline font-semibold">Render Billing</a> to keep the disk active.</li>
                  </ol>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Disk Info Grid */}
        {diskInfo && (
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-1 text-xs">
            <div className="p-3 rounded-xl bg-slate-800/40 border border-slate-700/60">
              <span className="text-slate-400 block text-[11px]">Database Path</span>
              <span className="font-mono text-white text-[11px] truncate block" title={diskInfo.db_path}>
                {diskInfo.db_path}
              </span>
              <span className="text-[10px] text-emerald-400 mt-1 block">
                {diskInfo.db_exists ? `${(diskInfo.db_size_bytes / 1024).toFixed(1)} KB` : 'New File'}
              </span>
            </div>

            <div className="p-3 rounded-xl bg-slate-800/40 border border-slate-700/60">
              <span className="text-slate-400 block text-[11px]">Uploads Directory</span>
              <span className="font-mono text-white text-[11px] truncate block" title={diskInfo.upload_dir}>
                {diskInfo.upload_dir}
              </span>
              <span className="text-[10px] text-emerald-400 mt-1 block">
                {diskInfo.upload_count} uploaded image(s)
              </span>
            </div>

            <div className="p-3 rounded-xl bg-slate-800/40 border border-slate-700/60">
              <span className="text-slate-400 block text-[11px]">Storage Persistence</span>
              <span className="font-semibold text-white block mt-0.5">
                {diskInfo.is_persistent ? 'Persistent Disk (/var/data)' : 'Local Container (Ephemeral)'}
              </span>
              <span className={`text-[10px] mt-1 block font-medium ${diskInfo.is_persistent ? 'text-emerald-400' : 'text-rose-400'}`}>
                {diskInfo.is_persistent ? '✅ Safe across redeploys' : '⚠️ Cleared on redeploy!'}
              </span>
            </div>
          </div>
        )}
      </div>

      {/* Database & Media Backup & Restore Center */}
      <div className="p-6 rounded-2xl bg-slate-900/90 border border-slate-800 space-y-5 shadow-xl relative overflow-hidden">
        <div className="flex items-center justify-between flex-wrap gap-3">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-emerald-500/10 text-emerald-400 flex items-center justify-center">
              <Archive className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <span>Backup & Import Data (ZIP)</span>
                <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-400 font-semibold border border-emerald-500/30">
                  SQLite + Images
                </span>
              </h3>
              <p className="text-xs text-slate-400">
                Safely backup and restore your complete store: database tables (<code className="text-slate-300">food_kh.db</code>) and product photos (<code className="text-slate-300">uploads/</code>).
              </p>
            </div>
          </div>
        </div>

        {/* Status notification */}
        {backupMsg && (
          <div className={`p-4 rounded-xl text-xs flex items-center justify-between gap-3 border ${
            backupMsg.type === 'success' 
              ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300' 
              : 'bg-rose-500/10 border-rose-500/30 text-rose-300'
          }`}>
            <div className="flex items-center gap-2.5">
              {backupMsg.type === 'success' ? (
                <CheckCircle2 className="w-5 h-5 shrink-0 text-emerald-400" />
              ) : (
                <AlertCircle className="w-5 h-5 shrink-0 text-rose-400" />
              )}
              <span className="font-medium leading-relaxed">{backupMsg.text}</span>
            </div>
            <button 
              onClick={() => setBackupMsg(null)}
              className="text-slate-400 hover:text-white text-xs px-2 py-1 rounded bg-slate-800/60"
            >
              Dismiss
            </button>
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Card 1: Download Backup */}
          <div className="p-5 rounded-xl bg-slate-800/40 border border-slate-700/60 flex flex-col justify-between space-y-4 hover:border-slate-600 transition-colors">
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-emerald-400 uppercase tracking-wider flex items-center gap-1.5">
                  <Download className="w-3.5 h-3.5" />
                  <span>Download Backup</span>
                </span>
                <span className="text-[11px] px-2 py-0.5 rounded-md bg-slate-700/70 text-slate-300 font-mono">
                  .ZIP Archive
                </span>
              </div>
              <h4 className="text-sm font-semibold text-white">Export Full Store Backup</h4>
              <p className="text-xs text-slate-400 leading-relaxed">
                Generates and downloads an encrypted ZIP archive containing the live SQLite database (<code className="text-emerald-300 text-[11px]">food_kh.db</code>) and every uploaded product image (<code className="text-emerald-300 text-[11px]">uploads/</code>).
              </p>
            </div>

            <button
              type="button"
              onClick={handleDownloadBackup}
              disabled={isBackingUp || isRestoring}
              className="w-full py-2.5 px-4 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white text-xs font-semibold shadow-lg shadow-emerald-600/20 transition-all flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isBackingUp ? (
                <>
                  <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                  <span>Packaging Database & Images...</span>
                </>
              ) : (
                <>
                  <Download className="w-4 h-4" />
                  <span>Download Backup ZIP</span>
                </>
              )}
            </button>
          </div>

          {/* Card 2: Import / Restore */}
          <div className="p-5 rounded-xl bg-slate-800/40 border border-slate-700/60 flex flex-col justify-between space-y-4 hover:border-slate-600 transition-colors">
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-amber-400 uppercase tracking-wider flex items-center gap-1.5">
                  <Upload className="w-3.5 h-3.5" />
                  <span>Import / Restore</span>
                </span>
                <span className="text-[11px] px-2 py-0.5 rounded-md bg-amber-500/10 text-amber-300 border border-amber-500/20 font-mono">
                  Safe Restore
                </span>
              </div>
              <h4 className="text-sm font-semibold text-white">Import Backup ZIP</h4>
              <p className="text-xs text-slate-400 leading-relaxed">
                Upload a previous Food KH backup ZIP to restore all products, categories, orders, and product image files into the server.
              </p>
            </div>

            <div>
              <input
                type="file"
                id="backup-file-input"
                accept=".zip,application/zip,application/x-zip-compressed"
                className="hidden"
                onChange={handleFileSelect}
                disabled={isRestoring || isBackingUp}
              />
              <button
                type="button"
                onClick={() => document.getElementById('backup-file-input')?.click()}
                disabled={isRestoring || isBackingUp}
                className="w-full py-2.5 px-4 rounded-xl bg-slate-800 hover:bg-slate-700 text-amber-300 hover:text-amber-200 border border-amber-500/30 text-xs font-semibold transition-all flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isRestoring ? (
                  <>
                    <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                    <span>Extracting & Restoring...</span>
                  </>
                ) : (
                  <>
                    <Upload className="w-4 h-4" />
                    <span>Select & Import Backup ZIP</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Confirmation Modal for Restore */}
      <Modal
        isOpen={showRestoreModal}
        onClose={() => {
          if (!isRestoring) {
            setShowRestoreModal(false);
            setSelectedBackupFile(null);
          }
        }}
        title="Confirm Data Import & Restore"
      >
        <div className="space-y-4">
          <div className="p-3.5 rounded-xl bg-amber-500/10 border border-amber-500/30 flex items-start gap-3 text-amber-300">
            <AlertTriangle className="w-5 h-5 shrink-0 mt-0.5 text-amber-400" />
            <div className="text-xs space-y-1">
              <p className="font-bold text-amber-200">Warning: Existing Data Overwrite</p>
              <p className="text-amber-300/90 leading-relaxed">
                Restoring this backup ZIP will replace your current SQLite database (<code className="text-white">food_kh.db</code>) and extract all included fruit images to <code className="text-white">uploads/</code>.
              </p>
            </div>
          </div>

          {selectedBackupFile && (
            <div className="p-3.5 rounded-xl bg-slate-800/80 border border-slate-700 space-y-2 text-xs">
              <div className="flex justify-between items-center text-slate-300">
                <span className="text-slate-400">Selected File:</span>
                <span className="font-mono text-emerald-400 font-semibold">{selectedBackupFile.name}</span>
              </div>
              <div className="flex justify-between items-center text-slate-300">
                <span className="text-slate-400">File Size:</span>
                <span className="font-mono text-white">{(selectedBackupFile.size / 1024 / 1024).toFixed(2)} MB</span>
              </div>
            </div>
          )}

          <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-800">
            <button
              type="button"
              onClick={() => {
                setShowRestoreModal(false);
                setSelectedBackupFile(null);
              }}
              disabled={isRestoring}
              className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium transition-colors"
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={handleExecuteRestore}
              disabled={isRestoring}
              className="px-5 py-2 rounded-xl bg-gradient-to-r from-amber-600 to-rose-600 hover:from-amber-500 hover:to-rose-500 text-white text-xs font-bold shadow-lg shadow-amber-600/20 transition-all flex items-center gap-1.5"
            >
              {isRestoring ? (
                <>
                  <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                  <span>Restoring...</span>
                </>
              ) : (
                <>
                  <Upload className="w-3.5 h-3.5" />
                  <span>Yes, Restore Backup</span>
                </>
              )}
            </button>
          </div>
        </div>
      </Modal>

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
