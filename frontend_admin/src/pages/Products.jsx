import React, { useState, useEffect } from 'react';
import { 
  Package, 
  Plus, 
  Search, 
  Edit3, 
  Trash2, 
  Check, 
  X, 
  Upload, 
  Image as ImageIcon,
  AlertCircle,
  ToggleLeft,
  ToggleRight
} from 'lucide-react';
import { api, getApiUrl } from '../api';
import Modal from '../components/Modal';

export default function Products() {
  const [products, setProducts] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [search, setSearch] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('all');

  // Modal State
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingProduct, setEditingProduct] = useState(null);
  const [modalLoading, setModalLoading] = useState(false);
  const [modalError, setModalError] = useState('');

  // Form State
  const [formData, setFormData] = useState({
    name: '',
    name_kh: '',
    category_id: '',
    price_usd: '',
    price_khr: '',
    description: '',
    description_kh: '',
    image_url: '',
    is_active: true,
  });

  const [uploadingImage, setUploadingImage] = useState(false);

  const loadData = async () => {
    setLoading(true);
    setError('');
    try {
      const [prodData, catData] = await Promise.all([
        api.getProducts(),
        api.getCategories(),
      ]);
      setProducts(prodData || []);
      setCategories(catData || []);
    } catch (err) {
      setError(err.message || 'Failed to load products');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const openAddModal = () => {
    setEditingProduct(null);
    setFormData({
      name: '',
      name_kh: '',
      category_id: categories[0]?.id || '',
      price_usd: '',
      price_khr: '',
      description: '',
      description_kh: '',
      image_url: '',
      is_active: true,
    });
    setModalError('');
    setIsModalOpen(true);
  };

  const openEditModal = (product) => {
    setEditingProduct(product);
    setFormData({
      name: product.name || '',
      name_kh: product.name_kh || '',
      category_id: product.category_id || categories[0]?.id || '',
      price_usd: product.price_usd?.toString() || '',
      price_khr: product.price_khr?.toString() || '',
      description: product.description || '',
      description_kh: product.description_kh || '',
      image_url: product.image_url || '',
      is_active: product.is_active !== false,
    });
    setModalError('');
    setIsModalOpen(true);
  };

  const handlePriceUsdChange = (val) => {
    const usd = parseFloat(val);
    const khr = !isNaN(usd) ? Math.round(usd * 4100) : '';
    setFormData(prev => ({
      ...prev,
      price_usd: val,
      price_khr: khr.toString(),
    }));
  };

  const handleImageFileUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploadingImage(true);
    try {
      const res = await api.uploadImage(file);
      if (res.url) {
        setFormData(prev => ({ ...prev, image_url: res.url }));
      }
    } catch (err) {
      alert('Image upload failed: ' + err.message);
    } finally {
      setUploadingImage(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.name || !formData.name_kh) {
      setModalError('Both English and Khmer names are required');
      return;
    }
    if (!formData.price_usd && !formData.price_khr) {
      setModalError('Please specify the price');
      return;
    }

    setModalLoading(true);
    setModalError('');

    try {
      const payload = {
        name: formData.name.trim(),
        name_kh: formData.name_kh.trim(),
        category_id: parseInt(formData.category_id) || null,
        price_usd: parseFloat(formData.price_usd) || 0,
        price_khr: parseInt(formData.price_khr) || 0,
        description: formData.description.trim(),
        description_kh: formData.description_kh.trim(),
        image_url: formData.image_url.trim(),
        is_active: formData.is_active,
      };

      if (editingProduct) {
        await api.updateProduct(editingProduct.id, payload);
      } else {
        await api.createProduct(payload);
      }

      setIsModalOpen(false);
      loadData();
    } catch (err) {
      setModalError(err.message || 'Failed to save product');
    } finally {
      setModalLoading(false);
    }
  };

  const handleToggleActive = async (id, currentStatus) => {
    // Optimistic update
    setProducts(prev => prev.map(p => p.id === id ? { ...p, is_active: !currentStatus } : p));
    try {
      await api.toggleProduct(id);
    } catch (err) {
      // Revert if error
      setProducts(prev => prev.map(p => p.id === id ? { ...p, is_active: currentStatus } : p));
      alert('Failed to toggle product status: ' + err.message);
    }
  };

  const handleDelete = async (id, name) => {
    if (!window.confirm(`Are you sure you want to delete "${name}"?`)) return;

    try {
      await api.deleteProduct(id);
      setProducts(prev => prev.filter(p => p.id !== id));
    } catch (err) {
      alert('Failed to delete product: ' + err.message);
    }
  };

  const filteredProducts = products.filter(p => {
    const matchesCategory = selectedCategory === 'all' || p.category_id?.toString() === selectedCategory;
    const matchesSearch = 
      p.name?.toLowerCase().includes(search.toLowerCase()) || 
      p.name_kh?.toLowerCase().includes(search.toLowerCase()) ||
      p.description?.toLowerCase().includes(search.toLowerCase());
    return matchesCategory && matchesSearch;
  });

  const getFullImageUrl = (url) => {
    if (!url) return null;
    if (url.startsWith('http://') || url.startsWith('https://')) return url;
    return `${getApiUrl()}${url.startsWith('/') ? '' : '/'}${url}`;
  };

  return (
    <div className="space-y-6">
      {/* Header and Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
            <Package className="w-5 h-5 text-emerald-400" />
            <span>Product Inventory</span>
            <span className="text-xs px-2.5 py-0.5 rounded-full bg-slate-800 text-slate-300 font-mono">
              {filteredProducts.length} items
            </span>
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Add foods, adjust prices, upload photos, and toggle stock availability
          </p>
        </div>

        <button
          onClick={openAddModal}
          className="flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-gradient-to-r from-brand-500 to-emerald-600 hover:from-brand-600 hover:to-emerald-700 text-white font-semibold text-sm shadow-lg shadow-brand-500/20 transition-all transform hover:-translate-y-0.5"
        >
          <Plus className="w-4 h-4" />
          <span>Add New Product</span>
        </button>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3.5 top-3 w-4 h-4 text-slate-400" />
          <input
            type="text"
            placeholder="Search products by English or Khmer name..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-slate-900 border border-slate-700/80 text-white text-sm placeholder-slate-500 focus:outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500"
          />
        </div>

        {/* Category Filter Pills */}
        <div className="flex items-center gap-1.5 overflow-x-auto pb-1 sm:pb-0">
          <button
            onClick={() => setSelectedCategory('all')}
            className={`px-3 py-2 rounded-xl text-xs font-semibold whitespace-nowrap transition-colors ${
              selectedCategory === 'all'
                ? 'bg-brand-500 text-white shadow-md shadow-brand-500/20'
                : 'bg-slate-900 text-slate-400 hover:text-slate-200 border border-slate-800'
            }`}
          >
            All Categories
          </button>
          {categories.map((c) => (
            <button
              key={c.id}
              onClick={() => setSelectedCategory(c.id.toString())}
              className={`px-3 py-2 rounded-xl text-xs font-semibold whitespace-nowrap transition-colors ${
                selectedCategory === c.id.toString()
                  ? 'bg-brand-500 text-white shadow-md shadow-brand-500/20'
                  : 'bg-slate-900 text-slate-400 hover:text-slate-200 border border-slate-800'
              }`}
            >
              {c.icon ? `${c.icon} ` : ''}{c.name}
            </button>
          ))}
        </div>
      </div>

      {/* Product Table */}
      <div className="rounded-2xl bg-slate-900/90 border border-slate-800 overflow-hidden shadow-xl">
        {loading ? (
          <div className="p-16 text-center text-slate-400">Loading products...</div>
        ) : filteredProducts.length === 0 ? (
          <div className="p-16 text-center text-slate-400">
            <Package className="w-12 h-12 mx-auto mb-3 text-slate-600" />
            <p className="font-semibold text-slate-300">No products found</p>
            <p className="text-xs text-slate-500 mt-1">Try adjusting your search or add a new product</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-950/60 text-xs font-semibold text-slate-400 uppercase tracking-wider border-b border-slate-800">
                <tr>
                  <th className="px-6 py-4">Item</th>
                  <th className="px-6 py-4">Category</th>
                  <th className="px-6 py-4">Price</th>
                  <th className="px-6 py-4">Stock Status</th>
                  <th className="px-6 py-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {filteredProducts.map((p) => {
                  const cat = categories.find(c => c.id === p.category_id);
                  const img = getFullImageUrl(p.image_url);

                  return (
                    <tr key={p.id} className="hover:bg-slate-800/40 transition-colors">
                      <td className="px-6 py-4">
                        <div className="flex items-center space-x-3.5">
                          <div className="w-12 h-12 rounded-xl bg-slate-800 border border-slate-700/80 overflow-hidden flex-shrink-0 flex items-center justify-center">
                            {img ? (
                              <img src={img} alt={p.name} className="w-full h-full object-cover" />
                            ) : (
                              <ImageIcon className="w-6 h-6 text-slate-500" />
                            )}
                          </div>
                          <div>
                            <div className="font-bold text-white text-sm flex items-center gap-1.5">
                              <span>{p.name}</span>
                            </div>
                            <div className="text-xs text-brand-400 font-medium font-['Kantumruy_Pro',sans-serif]">
                              {p.name_kh}
                            </div>
                            {p.description && (
                              <p className="text-xs text-slate-400 max-w-xs truncate mt-0.5">
                                {p.description}
                              </p>
                            )}
                          </div>
                        </div>
                      </td>

                      <td className="px-6 py-4">
                        <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-slate-800 border border-slate-700 text-xs text-slate-300 font-medium">
                          {cat?.icon || '📁'} {cat?.name || 'General'}
                        </span>
                      </td>

                      <td className="px-6 py-4">
                        <div className="font-bold text-emerald-400">
                          ${p.price_usd ? Number(p.price_usd).toFixed(2) : '0.00'}
                        </div>
                        <div className="text-xs text-slate-400">
                          ៛{Number(p.price_khr || 0).toLocaleString()}
                        </div>
                      </td>

                      <td className="px-6 py-4">
                        <button
                          onClick={() => handleToggleActive(p.id, p.is_active)}
                          className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold transition-all ${
                            p.is_active 
                              ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 hover:bg-emerald-500/30' 
                              : 'bg-rose-500/20 text-rose-300 border border-rose-500/40 hover:bg-rose-500/30'
                          }`}
                        >
                          <span className={`w-2 h-2 rounded-full ${p.is_active ? 'bg-emerald-400 animate-pulse' : 'bg-rose-400'}`}></span>
                          {p.is_active ? 'In Stock' : 'Out of Stock'}
                        </button>
                      </td>

                      <td className="px-6 py-4 text-right">
                        <div className="flex items-center justify-end space-x-2">
                          <button
                            onClick={() => openEditModal(p)}
                            className="p-2 rounded-lg bg-slate-800 text-slate-300 hover:text-white hover:bg-slate-700 border border-slate-700/80 transition-colors"
                            title="Edit Product"
                          >
                            <Edit3 className="w-4 h-4" />
                          </button>
                          <button
                            onClick={() => handleDelete(p.id, p.name)}
                            className="p-2 rounded-lg bg-slate-800 text-rose-400 hover:text-rose-300 hover:bg-rose-500/10 border border-rose-500/20 transition-colors"
                            title="Delete Product"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Add / Edit Modal */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title={editingProduct ? 'Edit Product' : 'Add New Product'}
        maxWidth="max-w-2xl"
      >
        <form onSubmit={handleSubmit} className="space-y-4">
          {modalError && (
            <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-center gap-2">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              <span>{modalError}</span>
            </div>
          )}

          {/* Bilingual Names */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">
                Product Name (English) *
              </label>
              <input
                type="text"
                required
                placeholder="e.g. Fresh Mango Salad"
                value={formData.name}
                onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                className="w-full px-3.5 py-2 rounded-xl bg-slate-800 border border-slate-700 text-white text-sm focus:outline-none focus:border-brand-500"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">
                Product Name (Khmer) *
              </label>
              <input
                type="text"
                required
                placeholder="e.g. ញាំស្វាយស្រស់"
                value={formData.name_kh}
                onChange={(e) => setFormData(prev => ({ ...prev, name_kh: e.target.value }))}
                className="w-full px-3.5 py-2 rounded-xl bg-slate-800 border border-slate-700 text-white text-sm focus:outline-none focus:border-brand-500 font-['Kantumruy_Pro',sans-serif]"
              />
            </div>
          </div>

          {/* Category & Stock Status */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">
                Category
              </label>
              <select
                value={formData.category_id}
                onChange={(e) => setFormData(prev => ({ ...prev, category_id: e.target.value }))}
                className="w-full px-3.5 py-2 rounded-xl bg-slate-800 border border-slate-700 text-white text-sm focus:outline-none focus:border-brand-500"
              >
                <option value="">None / General</option>
                {categories.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.icon || ''} {c.name} ({c.name_kh || c.name})
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">
                Stock Availability
              </label>
              <button
                type="button"
                onClick={() => setFormData(prev => ({ ...prev, is_active: !prev.is_active }))}
                className={`w-full flex items-center justify-between px-3.5 py-2 rounded-xl text-sm font-medium border transition-colors ${
                  formData.is_active 
                    ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400' 
                    : 'bg-rose-500/10 border-rose-500/30 text-rose-400'
                }`}
              >
                <span>{formData.is_active ? 'In Stock (Available on MiniApp)' : 'Out of Stock (Hidden)'}</span>
                {formData.is_active ? <ToggleRight className="w-5 h-5 text-emerald-400" /> : <ToggleLeft className="w-5 h-5 text-rose-400" />}
              </button>
            </div>
          </div>

          {/* Prices */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">
                Price (USD $) *
              </label>
              <input
                type="number"
                step="0.01"
                min="0"
                placeholder="2.50"
                value={formData.price_usd}
                onChange={(e) => handlePriceUsdChange(e.target.value)}
                className="w-full px-3.5 py-2 rounded-xl bg-slate-800 border border-slate-700 text-white text-sm focus:outline-none focus:border-brand-500 font-mono"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">
                Price (KHR ៛)
              </label>
              <input
                type="number"
                step="100"
                min="0"
                placeholder="10000"
                value={formData.price_khr}
                onChange={(e) => setFormData(prev => ({ ...prev, price_khr: e.target.value }))}
                className="w-full px-3.5 py-2 rounded-xl bg-slate-800 border border-slate-700 text-white text-sm focus:outline-none focus:border-brand-500 font-mono"
              />
            </div>
          </div>

          {/* Image Upload and URL */}
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">
              Product Image
            </label>
            <div className="flex items-center gap-3">
              <input
                type="text"
                placeholder="https://... or /static/uploads/..."
                value={formData.image_url}
                onChange={(e) => setFormData(prev => ({ ...prev, image_url: e.target.value }))}
                className="flex-1 px-3.5 py-2 rounded-xl bg-slate-800 border border-slate-700 text-white text-sm focus:outline-none focus:border-brand-500"
              />
              <label className="cursor-pointer flex items-center gap-2 px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-300 hover:text-white text-xs font-medium transition-colors">
                <Upload className="w-4 h-4 text-emerald-400" />
                <span>{uploadingImage ? 'Uploading...' : 'Upload'}</span>
                <input
                  type="file"
                  accept="image/*"
                  className="hidden"
                  onChange={handleImageFileUpload}
                  disabled={uploadingImage}
                />
              </label>
            </div>
            {formData.image_url && (
              <div className="mt-2 flex items-center gap-3 p-2 rounded-lg bg-slate-950/60 border border-slate-800">
                <img
                  src={getFullImageUrl(formData.image_url)}
                  alt="Preview"
                  className="w-12 h-12 object-cover rounded-lg"
                />
                <span className="text-xs text-slate-400 truncate">{formData.image_url}</span>
              </div>
            )}
          </div>

          {/* Descriptions */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">
                Description (English)
              </label>
              <textarea
                rows="2"
                placeholder="Description of the dish..."
                value={formData.description}
                onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                className="w-full px-3.5 py-2 rounded-xl bg-slate-800 border border-slate-700 text-white text-sm focus:outline-none focus:border-brand-500"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">
                Description (Khmer)
              </label>
              <textarea
                rows="2"
                placeholder="ការពិពណ៌នាអំពីម្ហូប..."
                value={formData.description_kh}
                onChange={(e) => setFormData(prev => ({ ...prev, description_kh: e.target.value }))}
                className="w-full px-3.5 py-2 rounded-xl bg-slate-800 border border-slate-700 text-white text-sm focus:outline-none focus:border-brand-500 font-['Kantumruy_Pro',sans-serif]"
              />
            </div>
          </div>

          {/* Submit */}
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
              {modalLoading ? 'Saving...' : editingProduct ? 'Update Product' : 'Create Product'}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
