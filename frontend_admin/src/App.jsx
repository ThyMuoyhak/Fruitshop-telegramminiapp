import React, { useState } from 'react';
import { AuthProvider, useAuth } from './context/AuthContext';
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import Dashboard from './pages/Dashboard';
import Products from './pages/Products';
import Categories from './pages/Categories';
import Orders from './pages/Orders';
import Settings from './pages/Settings';
import Login from './pages/Login';

function MainApp() {
  const { isAuthenticated, loading } = useAuth();
  const [currentTab, setCurrentTab] = useState('dashboard');
  const [isMobileOpen, setIsMobileOpen] = useState(false);
  const [refreshKey, setRefreshKey] = useState(0);

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-950 flex flex-col items-center justify-center text-slate-400">
        <div className="w-10 h-10 border-3 border-emerald-500/20 border-t-emerald-500 rounded-full animate-spin mb-4" />
        <p className="text-sm font-medium">Loading Food KH Admin Portal...</p>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Login />;
  }

  const getPageInfo = () => {
    switch (currentTab) {
      case 'dashboard':
        return { title: 'Dashboard Overview', subtitle: 'Real-time sales, revenue, and active orders' };
      case 'products':
        return { title: 'Products & Inventory', subtitle: 'Manage menu items, prices, and stock status' };
      case 'categories':
        return { title: 'Categories', subtitle: 'Organize your store menu items' };
      case 'orders':
        return { title: 'Orders & Receipts', subtitle: 'Review and update Telegram customer orders' };
      case 'settings':
        return { title: 'API & Configuration', subtitle: 'Backend REST API host and bot links' };
      default:
        return { title: 'Food KH Admin', subtitle: '' };
    }
  };

  const pageInfo = getPageInfo();

  return (
    <div className="min-h-screen bg-slate-950 flex">
      {/* Sidebar */}
      <Sidebar
        currentTab={currentTab}
        setCurrentTab={setCurrentTab}
        isMobileOpen={isMobileOpen}
        setIsMobileOpen={setIsMobileOpen}
      />

      {/* Main Content Area */}
      <div className="flex-1 lg:pl-64 flex flex-col min-w-0">
        <Header
          title={pageInfo.title}
          subtitle={pageInfo.subtitle}
          onRefresh={() => setRefreshKey(k => k + 1)}
          setIsMobileOpen={setIsMobileOpen}
        />

        <main className="flex-1 p-4 sm:p-8 max-w-7xl w-full mx-auto" key={refreshKey}>
          {currentTab === 'dashboard' && <Dashboard setCurrentTab={setCurrentTab} />}
          {currentTab === 'products' && <Products />}
          {currentTab === 'categories' && <Categories />}
          {currentTab === 'orders' && <Orders />}
          {currentTab === 'settings' && <Settings />}
        </main>
      </div>
    </div>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <MainApp />
    </AuthProvider>
  );
}
