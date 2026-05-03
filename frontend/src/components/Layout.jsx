import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { LayoutDashboard, BarChart2, History, Info, LogOut } from 'lucide-react';
import { AuthContext } from '../context/AuthContext';

const Layout = ({ children }) => {
    const location = useLocation();
    const { logout } = React.useContext(AuthContext);

    const navItems = [
        { name: 'Dashboard', path: '/dashboard', icon: <LayoutDashboard size={20} /> },
        { name: 'Analytics', path: '/analytics', icon: <BarChart2 size={20} /> },
        { name: 'History', path: '/history', icon: <History size={20} /> },
        { name: 'About', path: '/about', icon: <Info size={20} /> },
    ];

    return (
        <div className="flex h-screen bg-[#0a0e1a] text-white overflow-hidden">
            {/* Sidebar */}
            <aside className="w-64 glass-panel border-r border-white/10 flex flex-col z-10">
                <div className="h-16 flex items-center px-6 border-b border-white/10">
                    <div className="flex items-center gap-2">
                        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-[#00e5ff] to-[#00ff88] flex items-center justify-center font-bold text-[#0a0e1a]">
                            T
                        </div>
                        <span className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-[#00e5ff] to-[#00ff88]">
                            TrafficIQ
                        </span>
                    </div>
                </div>

                <nav className="flex-1 py-6 px-4 space-y-2">
                    {navItems.map((item) => {
                        const isActive = location.pathname === item.path;
                        return (
                            <Link
                                key={item.path}
                                to={item.path}
                                className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-300 ${
                                    isActive 
                                    ? 'bg-gradient-to-r from-[#00e5ff]/20 to-transparent text-[#00e5ff] border-l-2 border-[#00e5ff]' 
                                    : 'text-gray-400 hover:text-white hover:bg-white/5'
                                }`}
                            >
                                {item.icon}
                                <span className="font-medium">{item.name}</span>
                            </Link>
                        );
                    })}
                </nav>

                <div className="p-4 border-t border-white/10">
                    <button 
                        onClick={logout}
                        className="flex items-center gap-3 px-4 py-3 w-full rounded-xl text-gray-400 hover:text-[#ff4757] hover:bg-[#ff4757]/10 transition-all duration-300"
                    >
                        <LogOut size={20} />
                        <span className="font-medium">Logout</span>
                    </button>
                </div>
            </aside>

            {/* Main Content */}
            <main className="flex-1 overflow-y-auto relative">
                {/* Decorative background glow */}
                <div className="absolute top-[-20%] left-[-10%] w-[50%] h-[50%] bg-[#00e5ff]/10 blur-[120px] rounded-full pointer-events-none" />
                <div className="absolute bottom-[-20%] right-[-10%] w-[50%] h-[50%] bg-[#00ff88]/10 blur-[120px] rounded-full pointer-events-none" />
                
                <div className="relative z-10 p-8 h-full">
                    {children}
                </div>
            </main>
        </div>
    );
};

export default Layout;
