import React, { useState, useEffect } from 'react';
import { FolderTree, Plus, Trash2, AlertCircle } from 'lucide-react';
import { api } from '../api';
import Modal from '../components/Modal';

export default function Categories() {
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [modalLoading, setModalLoading] = useState(false);
  const [modalError, setModalError] = useState('');

  const [formData, setFormData] = useState({
    name: '',
    name_kh: '',
    icon: '🍎',
    sort_order: 0,
  });

  const loadCategories = async () => {
    setLoading(true);
    setError('');
    try {
      const data = await api.getCategories();
      setCategories(data || []);
    } catch (err) {
      setError(err.message || 'Failed to load categories');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadCategories();
  }, []);

  const openAddModal = () => {
    setFormData({
      name: '',
      name_kh: '',
      icon: '🍎',
      sort_order: categories.length + 1,
    });
    setModalError('');
    setIsModalOpen(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.name) {
      setModalError('Category name is required');
      return;
    }

    setModalLoading(true);
    setModalError('');
    try {
      await api.createCategory({
        name: formData.name.trim(),
        name_kh: formData.name_kh.trim() || formData.name.trim(),
        icon: formData.icon.trim() || '📁',
        sort_order: parseInt(formData.sort_order) || 0,
      });
      setIsModalOpen(false);
      loadCategories();
    } catch (err) {
      setModalError(err.message || 'Failed to create category');
    } finally {
      setModalLoading(false);
    }
  };

  const handleDelete = async (id, name) => {
    if (!window.confirm(`Are you sure you want to delete category "${name}"?`)) return;

    try {
      await api.deleteCategory(id);
      setCategories(prev => prev.filter(c => c.id !== id));
    } catch (err) {
      alert('Failed to delete category: ' + err.message);
    }
  };

  const sampleIcons = ['🍎', '🍉', '🥗', '🍔', '🥤', '☕', '🍰', '🍜', '🍣', '🥑', '🥭', '🍇'];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
            <FolderTree className="w-5 h-5 text-emerald-400" />
            <span>Category Management</span>
            <span className="text-xs px-2.5 py-0.5 rounded-full bg-slate-800 text-slate-300 font-mono">
              {categories.length} categories
            </span>
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Organize products into categories for easy customer browsing
          </p>
        </div>

        <button
          onClick={openAddModal}
          className="flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-gradient-to-r from-brand-500 to-emerald-600 hover:from-brand-600 hover:to-emerald-700 text-white font-semibold text-sm shadow-lg shadow-brand-500/20 transition-all transform hover:-translate-y-0.5"
        >
          <Plus className="w-4 h-4" />
          <span>Add Category</span>
        </button>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-sm">
          {error}
        </div>
      )}

      {/* Grid of Categories */}
      {loading ? (
        <div className="p-16 text-center text-slate-400">Loading categories...</div>
      ) : categories.length === 0 ? (
        <div className="p-16 text-center text-slate-400 bg-slate-900/60 rounded-2xl border border-slate-800">
          <FolderTree className="w-12 h-12 mx-auto mb-3 text-slate-600" />
          <p className="font-semibold text-slate-300">No categories found</p>
          <p className="text-xs text-slate-500 mt-1">Create your first category to group your products</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {categories.map((c) => (
            <div
              key={c.id}
              className="p-5 rounded-2xl bg-slate-900/90 border border-slate-800 hover:border-brand-500/40 transition-all flex flex-col justify-between group shadow-lg"
            >
              <div className="flex items-start justify-between">
                <div className="w-12 h-12 rounded-xl bg-slate-800 border border-slate-700/80 flex items-center justify-center text-2xl shadow-inner">
                  {c.icon || '📁'}
                </div>
                <button
                  onClick={() => handleDelete(c.id, c.name)}
                  className="p-1.5 rounded-lg text-slate-500 hover:text-rose-400 hover:bg-rose-500/10 transition-colors"
                  title="Delete category"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>

              <div className="mt-4">
                <h3 className="font-bold text-white text-base tracking-tight">{c.name}</h3>
                <p className="text-xs text-brand-400 font-medium font-['Kantumruy_Pro',sans-serif]">
                  {c.name_kh || c.name}
                </p>
              </div>

              <div className="mt-4 pt-3 border-t border-slate-800/80 flex items-center justify-between text-xs text-slate-400">
                <span>Order index: {c.sort_order ?? 0}</span>
                <span className="font-mono text-slate-500">ID #{c.id}</span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Add Modal */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title="Add New Category"
        maxWidth="max-w-md"
      >
        <form onSubmit={handleSubmit} className="space-y-4">
          {modalError && (
            <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-center gap-2">
              <AlertCircle className="w-4 h-4" />
              <span>{modalError}</span>
            </div>
          )}

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">
              Category Name (English) *
            </label>
            <input
              type="text"
              required
              placeholder="e.g. Fresh Fruits"
              value={formData.name}
              onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
              className="w-full px-3.5 py-2 rounded-xl bg-slate-800 border border-slate-700 text-white text-sm focus:outline-none focus:border-brand-500"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">
              Category Name (Khmer)
            </label>
            <input
              type="text"
              placeholder="e.g. ផ្លែឈើស្រស់"
              value={formData.name_kh}
              onChange={(e) => setFormData(prev => ({ ...prev, name_kh: e.target.value }))}
              className="w-full px-3.5 py-2 rounded-xl bg-slate-800 border border-slate-700 text-white text-sm focus:outline-none focus:border-brand-500 font-['Kantumruy_Pro',sans-serif]"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">
              Category Icon / Emoji
            </label>
            <div className="flex items-center gap-2 mb-2">
              <input
                type="text"
                maxLength={4}
                value={formData.icon}
                onChange={(e) => setFormData(prev => ({ ...prev, icon: e.target.value }))}
                className="w-16 text-center text-xl px-2 py-1.5 rounded-xl bg-slate-800 border border-slate-700 text-white focus:outline-none focus:border-brand-500"
              />
              <span className="text-xs text-slate-400">Select an icon or pick from below:</span>
            </div>
            <div className="flex flex-wrap gap-1.5 p-2 rounded-xl bg-slate-950/60 border border-slate-800">
              {sampleIcons.map((ic) => (
                <button
                  type="button"
                  key={ic}
                  onClick={() => setFormData(prev => ({ ...prev, icon: ic }))}
                  className={`w-8 h-8 rounded-lg flex items-center justify-center text-lg hover:bg-slate-800 transition-colors ${
                    formData.icon === ic ? 'bg-brand-500/20 border border-brand-500' : ''
                  }`}
                >
                  {ic}
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">
              Sort Order
            </label>
            <input
              type="number"
              value={formData.sort_order}
              onChange={(e) => setFormData(prev => ({ ...prev, sort_order: e.target.value }))}
              className="w-full px-3.5 py-2 rounded-xl bg-slate-800 border border-slate-700 text-white text-sm focus:outline-none focus:border-brand-500 font-mono"
            />
          </div>

          <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-800">
            <button
              type="button"
              onClick={() => setIsModalOpen(false)}
              className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-sm font-semibold transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={modalLoading}
              className="px-5 py-2 rounded-xl bg-gradient-to-r from-brand-500 to-emerald-600 hover:from-brand-600 hover:to-emerald-700 text-white text-sm font-semibold shadow-lg shadow-brand-500/25 transition-all disabled:opacity-50"
            >
              {modalLoading ? 'Creating...' : 'Create Category'}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
