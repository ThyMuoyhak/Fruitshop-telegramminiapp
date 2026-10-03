import React, { useState, useEffect } from 'react';
import { 
  DollarSign, 
  ShoppingBag, 
  Package, 
  Clock, 
  TrendingUp, 
  Plus, 
  ArrowRight,
  CheckCircle2,
  AlertTriangle,
  Layers
} from 'lucide-react';
import { api } from '../api';

export default function Dashboard({ setCurrentTab }) {
  const [stats, setStats] = useState(null);
  const [recentOrders, setRecentOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const loadData = async () => {
    setLoading(true);
    setError('');
    try {
      const [statsData, ordersData] = await Promise.all([
        api.getStats().catch(() => null),
        api.getOrders().catch(() => [])
      ]);

      if (statsData) {
        setStats(statsData);
      } else {
        // Fallback calculation from orders if stats endpoint isn't fully ready
        const orders = ordersData || [];
        const paidOrders = orders.filter(o => o.status === 'paid' || o.status === 'completed');
        const revUSD = paidOrders.reduce((sum, o) => sum + (o.total_usd || 0), 0);
        const revKHR = paidOrders.reduce((sum, o) => sum + (o.total_khr || 0), 0);
        const pendingCount = orders.filter(o => o.status === 'pending').length;

        setStats({
          total_revenue_usd: revUSD,
          total_revenue_khr: revKHR,
          total_orders: orders.length,
          pending_orders: pendingCount,
          total_products: 0,
        });
      }

      setRecentOrders((ordersData || []).slice(0, 6));
    } catch (err) {
      setError(err.message || 'Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const getStatusBadge = (status) => {
    switch (status?.toLowerCase()) {
      case 'paid':
        return <span className="px-2.5 py-1 text-xs rounded-full bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 font-medium">Paid</span>;
      case 'completed':
        return <span className="px-2.5 py-1 text-xs rounded-full bg-blue-500/20 text-blue-400 border border-blue-500/30 font-medium">Completed</span>;
      case 'pending':
        return <span className="px-2.5 py-1 text-xs rounded-full bg-amber-500/20 text-amber-400 border border-amber-500/30 font-medium animate-pulse">Pending</span>;
      case 'cancelled':
        return <span className="px-2.5 py-1 text-xs rounded-full bg-rose-500/20 text-rose-400 border border-rose-500/30 font-medium">Cancelled</span>;
      default:
        return <span className="px-2.5 py-1 text-xs rounded-full bg-slate-700 text-slate-300 font-medium">{status}</span>;
    }
  };

  return (
    <div className="space-y-6">
      {error && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-sm flex items-center justify-between">
          <span>{error}</span>
          <button onClick={loadData} className="underline font-semibold hover:text-white">Retry</button>
        </div>
      )}

      {/* Hero Welcome & Quick Action */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-brand-900/60 via-slate-900 to-slate-900 border border-brand-500/30 p-6 sm:p-8">
        <div className="absolute top-0 right-0 -mr-16 -mt-16 w-64 h-64 bg-brand-500/10 rounded-full blur-3xl pointer-events-none" />
        
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-brand-500/20 text-brand-300 text-xs font-semibold border border-brand-500/30 mb-2">
              <TrendingUp className="w-3.5 h-3.5 text-brand-400" />
              Live Store Analytics
            </span>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
              Welcome back to <span className="text-transparent bg-clip-text bg-gradient-to-r from-brand-400 to-emerald-300">Food KH</span> Admin
            </h1>
            <p className="text-slate-400 text-sm mt-1 max-w-xl">
              Manage your food items, monitor incoming Telegram bot orders, track KHQR ABA payments, and control stock in real time.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={() => setCurrentTab('products')}
              className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-gradient-to-r from-brand-500 to-emerald-600 hover:from-brand-600 hover:to-emerald-700 text-white font-semibold text-sm shadow-lg shadow-brand-500/25 transition-all transform hover:-translate-y-0.5"
            >
              <Plus className="w-4 h-4" />
              <span>Add Product</span>
            </button>
            <button
              onClick={() => setCurrentTab('orders')}
              className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-slate-800/90 hover:bg-slate-700 text-slate-200 font-semibold text-sm border border-slate-700 transition-colors"
            >
              <ShoppingBag className="w-4 h-4" />
              <span>Orders</span>
            </button>
          </div>
        </div>
      </div>

      {/* Key Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Card 1: Revenue USD */}
        <div className="p-5 rounded-2xl bg-slate-900/90 border border-slate-800 hover:border-brand-500/40 transition-colors relative group">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-medium uppercase tracking-wider">Total Revenue (USD)</span>
            <div className="w-8 h-8 rounded-lg bg-emerald-500/10 text-emerald-400 flex items-center justify-center">
              <DollarSign className="w-4 h-4" />
            </div>
          </div>
          <div className="text-2xl font-bold text-white tracking-tight">
            ${stats?.total_revenue_usd?.toFixed(2) || '0.00'}
          </div>
          <p className="text-xs text-slate-400 mt-1 flex items-center gap-1">
            <span>៛{(stats?.total_revenue_khr || 0).toLocaleString()} KHR</span>
          </p>
        </div>

        {/* Card 2: Total Orders */}
        <div className="p-5 rounded-2xl bg-slate-900/90 border border-slate-800 hover:border-brand-500/40 transition-colors relative group">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-medium uppercase tracking-wider">Total Orders</span>
            <div className="w-8 h-8 rounded-lg bg-blue-500/10 text-blue-400 flex items-center justify-center">
              <ShoppingBag className="w-4 h-4" />
            </div>
          </div>
          <div className="text-2xl font-bold text-white tracking-tight">
            {stats?.total_orders ?? 0}
          </div>
          <p className="text-xs text-blue-400 mt-1">
            Through Telegram MiniApp
          </p>
        </div>

        {/* Card 3: Pending Orders */}
        <div className="p-5 rounded-2xl bg-slate-900/90 border border-slate-800 hover:border-amber-500/40 transition-colors relative group">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-medium uppercase tracking-wider">Pending Orders</span>
            <div className="w-8 h-8 rounded-lg bg-amber-500/10 text-amber-400 flex items-center justify-center">
              <Clock className="w-4 h-4" />
            </div>
          </div>
          <div className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
            {stats?.pending_orders ?? 0}
            {(stats?.pending_orders || 0) > 0 && (
              <span className="text-xs px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-300 font-semibold border border-amber-500/30">
                Action Required
              </span>
            )}
          </div>
          <p className="text-xs text-amber-400/80 mt-1">
            Awaiting payment / confirmation
          </p>
        </div>

        {/* Card 4: Products Count */}
        <div className="p-5 rounded-2xl bg-slate-900/90 border border-slate-800 hover:border-brand-500/40 transition-colors relative group">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-medium uppercase tracking-wider">Products in Catalog</span>
            <div className="w-8 h-8 rounded-lg bg-purple-500/10 text-purple-400 flex items-center justify-center">
              <Package className="w-4 h-4" />
            </div>
          </div>
          <div className="text-2xl font-bold text-white tracking-tight">
            {stats?.total_products ?? 0}
          </div>
          <p className="text-xs text-purple-400 mt-1">
            Available on MiniApp
          </p>
        </div>
      </div>

      {/* Recent Orders Preview */}
      <div className="rounded-2xl bg-slate-900/90 border border-slate-800 overflow-hidden shadow-xl">
        <div className="p-6 border-b border-slate-800 flex items-center justify-between">
          <div>
            <h3 className="text-lg font-bold text-white tracking-tight">Recent Telegram Orders</h3>
            <p className="text-xs text-slate-400 mt-0.5">Live orders submitted from customers</p>
          </div>
          <button
            onClick={() => setCurrentTab('orders')}
            className="flex items-center gap-1.5 text-xs font-semibold text-emerald-400 hover:text-emerald-300 transition-colors"
          >
            <span>View All Orders</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>

        {loading ? (
          <div className="p-12 text-center text-slate-400">Loading recent orders...</div>
        ) : recentOrders.length === 0 ? (
          <div className="p-12 text-center text-slate-400">
            <ShoppingBag className="w-10 h-10 mx-auto mb-3 text-slate-600" />
            <p className="font-medium text-slate-300">No orders received yet</p>
            <p className="text-xs text-slate-500 mt-1">Orders from the Telegram bot will appear here instantly</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-950/60 text-xs font-semibold text-slate-400 uppercase tracking-wider border-b border-slate-800">
                <tr>
                  <th className="px-6 py-3.5">Order ID</th>
                  <th className="px-6 py-3.5">Customer / Telegram</th>
                  <th className="px-6 py-3.5">Total Amount</th>
                  <th className="px-6 py-3.5">Payment</th>
                  <th className="px-6 py-3.5">Status</th>
                  <th className="px-6 py-3.5">Date</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {recentOrders.map((order) => (
                  <tr key={order.id} className="hover:bg-slate-800/40 transition-colors">
                    <td className="px-6 py-4 font-mono font-bold text-white text-xs">
                      #{order.id}
                    </td>
                    <td className="px-6 py-4">
                      <div className="font-medium text-slate-200">
                        {order.customer_name || `User #${order.telegram_user_id || 'Guest'}`}
                      </div>
                      <div className="text-xs text-slate-400">
                        {order.customer_phone || (order.telegram_username ? `@${order.telegram_username}` : 'No phone')}
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="font-semibold text-emerald-400">
                        ${Number(order.total_usd || 0).toFixed(2)}
                      </div>
                      <div className="text-[11px] text-slate-400">
                        ៛{Number(order.total_khr || 0).toLocaleString()}
                      </div>
                    </td>
                    <td className="px-6 py-4 text-xs">
                      <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700 font-mono">
                        {order.payment_method || 'KHQR'}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      {getStatusBadge(order.status)}
                    </td>
                    <td className="px-6 py-4 text-xs text-slate-400">
                      {order.created_at ? new Date(order.created_at).toLocaleDateString() : 'Today'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
