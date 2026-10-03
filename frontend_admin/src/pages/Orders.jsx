import React, { useState, useEffect } from 'react';
import { 
  ShoppingBag, 
  Search, 
  Eye, 
  CheckCircle2, 
  Clock, 
  XCircle, 
  PackageCheck, 
  Phone, 
  MapPin, 
  User, 
  CreditCard,
  Calendar,
  AlertCircle
} from 'lucide-react';
import { api } from '../api';
import Modal from '../components/Modal';

export default function Orders() {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [search, setSearch] = useState('');

  // Selected Order for detail modal
  const [selectedOrder, setSelectedOrder] = useState(null);
  const [statusUpdating, setStatusUpdating] = useState(false);

  const loadOrders = async () => {
    setLoading(true);
    setError('');
    try {
      const data = await api.getOrders();
      setOrders(data || []);
    } catch (err) {
      setError(err.message || 'Failed to load orders');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadOrders();
  }, []);

  const handleUpdateStatus = async (orderId, newStatus) => {
    setStatusUpdating(true);
    try {
      await api.updateOrderStatus(orderId, newStatus);
      setOrders(prev => prev.map(o => o.id === orderId ? { ...o, status: newStatus } : o));
      if (selectedOrder && selectedOrder.id === orderId) {
        setSelectedOrder(prev => ({ ...prev, status: newStatus }));
      }
    } catch (err) {
      alert('Failed to update order status: ' + err.message);
    } finally {
      setStatusUpdating(false);
    }
  };

  const filteredOrders = orders.filter((o) => {
    const matchesStatus = statusFilter === 'all' || o.status?.toLowerCase() === statusFilter.toLowerCase();
    const matchesSearch = 
      o.id?.toString().includes(search) ||
      o.customer_name?.toLowerCase().includes(search.toLowerCase()) ||
      o.customer_phone?.includes(search) ||
      o.telegram_username?.toLowerCase().includes(search.toLowerCase());
    return matchesStatus && matchesSearch;
  });

  const getStatusBadge = (status) => {
    switch (status?.toLowerCase()) {
      case 'paid':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 text-xs font-semibold">
            <CheckCircle2 className="w-3.5 h-3.5" />
            Paid
          </span>
        );
      case 'completed':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-blue-500/20 text-blue-400 border border-blue-500/30 text-xs font-semibold">
            <PackageCheck className="w-3.5 h-3.5" />
            Completed
          </span>
        );
      case 'pending':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-amber-500/20 text-amber-400 border border-amber-500/30 text-xs font-semibold animate-pulse">
            <Clock className="w-3.5 h-3.5" />
            Pending
          </span>
        );
      case 'cancelled':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-rose-500/20 text-rose-400 border border-rose-500/30 text-xs font-semibold">
            <XCircle className="w-3.5 h-3.5" />
            Cancelled
          </span>
        );
      default:
        return <span className="px-2.5 py-1 rounded-full bg-slate-800 text-slate-300 text-xs font-semibold">{status}</span>;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
            <ShoppingBag className="w-5 h-5 text-emerald-400" />
            <span>Orders & Sales</span>
            <span className="text-xs px-2.5 py-0.5 rounded-full bg-slate-800 text-slate-300 font-mono">
              {filteredOrders.length} orders
            </span>
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Real-time orders received from Telegram MiniApp with KHQR payment receipts
          </p>
        </div>

        <button
          onClick={loadOrders}
          className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-sm font-semibold border border-slate-700 transition-colors"
        >
          Refresh Orders
        </button>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-sm">
          {error}
        </div>
      )}

      {/* Filter and Search */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3.5 top-3 w-4 h-4 text-slate-400" />
          <input
            type="text"
            placeholder="Search by order ID, customer name, phone, or Telegram username..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-slate-900 border border-slate-700/80 text-white text-sm placeholder-slate-500 focus:outline-none focus:border-brand-500"
          />
        </div>

        <div className="flex items-center gap-1.5 overflow-x-auto pb-1 sm:pb-0">
          {['all', 'pending', 'paid', 'completed', 'cancelled'].map((status) => (
            <button
              key={status}
              onClick={() => setStatusFilter(status)}
              className={`px-3.5 py-2 rounded-xl text-xs font-semibold capitalize whitespace-nowrap transition-colors ${
                statusFilter === status
                  ? 'bg-brand-500 text-white shadow-md shadow-brand-500/20'
                  : 'bg-slate-900 text-slate-400 hover:text-slate-200 border border-slate-800'
              }`}
            >
              {status}
            </button>
          ))}
        </div>
      </div>

      {/* Orders Table */}
      <div className="rounded-2xl bg-slate-900/90 border border-slate-800 overflow-hidden shadow-xl">
        {loading ? (
          <div className="p-16 text-center text-slate-400">Loading orders...</div>
        ) : filteredOrders.length === 0 ? (
          <div className="p-16 text-center text-slate-400">
            <ShoppingBag className="w-12 h-12 mx-auto mb-3 text-slate-600" />
            <p className="font-semibold text-slate-300">No matching orders</p>
            <p className="text-xs text-slate-500 mt-1">Orders from the Telegram bot will appear here</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-950/60 text-xs font-semibold text-slate-400 uppercase tracking-wider border-b border-slate-800">
                <tr>
                  <th className="px-6 py-4">Order #</th>
                  <th className="px-6 py-4">Customer</th>
                  <th className="px-6 py-4">Total Amount</th>
                  <th className="px-6 py-4">Payment</th>
                  <th className="px-6 py-4">Status</th>
                  <th className="px-6 py-4">Update Status</th>
                  <th className="px-6 py-4 text-right">Details</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {filteredOrders.map((order) => (
                  <tr key={order.id} className="hover:bg-slate-800/40 transition-colors">
                    <td className="px-6 py-4 font-mono font-bold text-white text-xs">
                      #{order.id}
                      <div className="text-[11px] font-normal text-slate-500 mt-0.5">
                        {order.created_at ? new Date(order.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : ''}
                      </div>
                    </td>

                    <td className="px-6 py-4">
                      <div className="font-semibold text-slate-200">
                        {order.customer_name || `Telegram ID: ${order.telegram_user_id || 'Guest'}`}
                      </div>
                      <div className="text-xs text-slate-400 flex items-center gap-1.5 mt-0.5">
                        {order.customer_phone && <span>{order.customer_phone}</span>}
                        {order.telegram_username && (
                          <span className="text-brand-400">@{order.telegram_username}</span>
                        )}
                      </div>
                    </td>

                    <td className="px-6 py-4">
                      <div className="font-bold text-emerald-400">
                        ${Number(order.total_usd || 0).toFixed(2)}
                      </div>
                      <div className="text-xs text-slate-400">
                        ៛{Number(order.total_khr || 0).toLocaleString()}
                      </div>
                    </td>

                    <td className="px-6 py-4">
                      <span className="px-2.5 py-1 rounded bg-slate-800 text-slate-300 border border-slate-700 text-xs font-mono">
                        {order.payment_method || 'KHQR'}
                      </span>
                    </td>

                    <td className="px-6 py-4">
                      {getStatusBadge(order.status)}
                    </td>

                    <td className="px-6 py-4">
                      <select
                        value={order.status || 'pending'}
                        onChange={(e) => handleUpdateStatus(order.id, e.target.value)}
                        disabled={statusUpdating}
                        className="px-2.5 py-1.5 rounded-lg bg-slate-800 border border-slate-700 text-slate-200 text-xs focus:outline-none focus:border-brand-500 cursor-pointer"
                      >
                        <option value="pending">Pending</option>
                        <option value="paid">Paid</option>
                        <option value="completed">Completed</option>
                        <option value="cancelled">Cancelled</option>
                      </select>
                    </td>

                    <td className="px-6 py-4 text-right">
                      <button
                        onClick={() => setSelectedOrder(order)}
                        className="p-2 rounded-lg bg-slate-800 text-slate-300 hover:text-white hover:bg-slate-700 border border-slate-700/80 transition-colors inline-flex items-center gap-1 text-xs"
                      >
                        <Eye className="w-4 h-4" />
                        <span className="hidden sm:inline">Receipt</span>
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Order Detail Receipt Modal */}
      <Modal
        isOpen={!!selectedOrder}
        onClose={() => setSelectedOrder(null)}
        title={`Order Details #${selectedOrder?.id || ''}`}
        maxWidth="max-w-xl"
      >
        {selectedOrder && (
          <div className="space-y-5 text-sm">
            {/* Status and Timestamp */}
            <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 flex items-center justify-between">
              <div>
                <span className="text-xs text-slate-400 block mb-1">Status</span>
                {getStatusBadge(selectedOrder.status)}
              </div>
              <div className="text-right">
                <span className="text-xs text-slate-400 block mb-1">Placed At</span>
                <span className="text-xs text-slate-300 font-medium">
                  {selectedOrder.created_at ? new Date(selectedOrder.created_at).toLocaleString() : 'N/A'}
                </span>
              </div>
            </div>

            {/* Customer Details */}
            <div className="p-4 rounded-xl bg-slate-800/40 border border-slate-800 space-y-2">
              <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
                Customer Information
              </h4>
              <div className="flex items-center gap-2 text-slate-200">
                <User className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                <span>{selectedOrder.customer_name || 'Anonymous Customer'}</span>
                {selectedOrder.telegram_username && (
                  <span className="text-xs text-brand-400">(@{selectedOrder.telegram_username})</span>
                )}
              </div>
              {selectedOrder.customer_phone && (
                <div className="flex items-center gap-2 text-slate-200">
                  <Phone className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                  <a href={`tel:${selectedOrder.customer_phone}`} className="hover:underline">
                    {selectedOrder.customer_phone}
                  </a>
                </div>
              )}
              {selectedOrder.delivery_address && (
                <div className="flex items-start gap-2 text-slate-200">
                  <MapPin className="w-4 h-4 text-emerald-400 flex-shrink-0 mt-0.5" />
                  <span>{selectedOrder.delivery_address}</span>
                </div>
              )}
              {selectedOrder.notes && (
                <div className="text-xs text-amber-300/90 pt-1 italic">
                  Note: "{selectedOrder.notes}"
                </div>
              )}
            </div>

            {/* Order Items */}
            <div>
              <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
                Ordered Items
              </h4>
              <div className="divide-y divide-slate-800 rounded-xl bg-slate-950/60 border border-slate-800 overflow-hidden">
                {Array.isArray(selectedOrder.items) && selectedOrder.items.length > 0 ? (
                  selectedOrder.items.map((item, idx) => (
                    <div key={idx} className="p-3 flex items-center justify-between">
                      <div>
                        <div className="font-semibold text-white">
                          {item.product_name || item.name || `Item #${item.product_id}`}
                        </div>
                        <div className="text-xs text-slate-400">
                          {item.quantity} × ${Number(item.price_usd || item.price || 0).toFixed(2)}
                        </div>
                      </div>
                      <div className="font-mono font-bold text-emerald-400">
                        ${(Number(item.quantity || 1) * Number(item.price_usd || item.price || 0)).toFixed(2)}
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="p-4 text-slate-400 text-xs text-center">
                    {selectedOrder.items_summary || 'Standard Order Items'}
                  </div>
                )}
              </div>
            </div>

            {/* Total Summary */}
            <div className="p-4 rounded-xl bg-slate-900 border border-brand-500/30 flex items-center justify-between">
              <div>
                <span className="text-xs text-slate-400 block">Total Due / Paid</span>
                <span className="text-xs text-slate-300">Method: {selectedOrder.payment_method || 'KHQR ABA'}</span>
              </div>
              <div className="text-right">
                <div className="text-xl font-bold text-emerald-400">
                  ${Number(selectedOrder.total_usd || 0).toFixed(2)}
                </div>
                <div className="text-xs text-slate-400">
                  ៛{Number(selectedOrder.total_khr || 0).toLocaleString()} KHR
                </div>
              </div>
            </div>

            {/* Quick Status Action */}
            <div className="flex items-center justify-between pt-3 border-t border-slate-800">
              <span className="text-xs text-slate-400">Quick Change Status:</span>
              <div className="flex gap-2">
                {['pending', 'paid', 'completed'].map((st) => (
                  <button
                    key={st}
                    onClick={() => handleUpdateStatus(selectedOrder.id, st)}
                    disabled={selectedOrder.status === st}
                    className={`px-3 py-1.5 rounded-lg text-xs font-semibold capitalize transition-colors ${
                      selectedOrder.status === st
                        ? 'bg-slate-800 text-slate-500 cursor-not-allowed'
                        : 'bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700'
                    }`}
                  >
                    {st}
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
}
