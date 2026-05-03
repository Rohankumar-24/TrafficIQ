import React, { useState, useEffect, useContext } from 'react';
import axios from 'axios';
import { Download, Search } from 'lucide-react';
import { TrafficContext } from '../context/TrafficContext';

const History = () => {
    const { isRunning, historyLogs } = useContext(TrafficContext);
    const [page, setPage] = useState(1);
    const [expandedRows, setExpandedRows] = useState(new Set());
    
    // We'll use the local history logs from the live context to prevent blank screens
    const flattenedLogs = [];
    historyLogs.forEach(log => {
        if (log.lane1) flattenedLogs.push({
            id: `${log._id}_L1`,
            time: new Date(log.timestamp).toLocaleString(),
            laneName: log.lane1.name || 'Lane 1',
            totalCount: log.lane1.vehicleCount || 0,
            emergency: log.lane1.emergency || log.lane1.breakdown?.Emergency > 0 || log.emergencyAlert,
            congestion: log.lane1.congestionLevel || 'Low',
            breakdown: log.lane1.breakdown
        });
        if (log.lane2) flattenedLogs.push({
            id: `${log._id}_L2`,
            time: new Date(log.timestamp).toLocaleString(),
            laneName: log.lane2.name || 'Lane 2',
            totalCount: log.lane2.vehicleCount || 0,
            emergency: log.lane2.emergency || log.lane2.breakdown?.Emergency > 0 || log.emergencyAlert,
            congestion: log.lane2.congestionLevel || 'Low',
            breakdown: log.lane2.breakdown
        });
    });

    const totalPages = Math.max(1, Math.ceil(flattenedLogs.length / 10));
    const loading = false;

    // Remove backend fetch if we are using purely local data
    // The user wants exactly the data from the dashboard.

    const exportCSV = async () => {
        try {
            const res = await axios.get('/flask-api/export/csv', { responseType: 'blob' });
            const url = window.URL.createObjectURL(new Blob([res.data]));
            const link = document.createElement('a');
            link.href = url;
            link.setAttribute('download', 'traffic_history.csv');
            document.body.appendChild(link);
            link.click();
            link.remove();
        } catch (err) {
            console.error("Failed to export CSV:", err);
        }
    };

    const toggleRow = (id) => {
        const newSet = new Set(expandedRows);
        if (newSet.has(id)) newSet.delete(id);
        else newSet.add(id);
        setExpandedRows(newSet);
    };

    const formatBreakdown = (br) => {
        if (!br) return 'No detailed data';
        const parts = [];
        if (br.Car) parts.push(`Cars: ${br.Car}`);
        if (br.Truck) parts.push(`Trucks: ${br.Truck}`);
        if (br.Bus) parts.push(`Buses: ${br.Bus}`);
        if (br.Emergency) parts.push(`Emergency: ${br.Emergency}`);
        return parts.length > 0 ? parts.join(', ') : 'None';
    };

    return (
        <div className="flex flex-col gap-6 pb-10">
            <header className="flex justify-between items-end mb-2">
                <div>
                    <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-gray-400">
                        Session History
                    </h1>
                    <p className="text-gray-400 mt-1">Review past traffic logs and events</p>
                </div>
                
                <button onClick={exportCSV} className="bg-[#00e5ff]/10 text-[#00e5ff] border border-[#00e5ff]/50 px-4 py-2 rounded-xl flex items-center gap-2 hover:bg-[#00e5ff]/20 transition-all">
                    <Download size={18} /> Export CSV
                </button>
            </header>

            <div className="glass-panel rounded-2xl border border-white/5 overflow-hidden flex flex-col">
                <div className="p-4 border-b border-white/10 flex items-center gap-3">
                    <Search className="text-gray-400" size={20} />
                    <input 
                        type="text" 
                        placeholder="Search logs..." 
                        className="bg-transparent border-none text-white focus:outline-none w-full"
                    />
                </div>

                <div className="overflow-x-auto">
                    <table className="w-full text-left border-collapse">
                        <thead>
                            <tr className="bg-white/5 text-gray-400 text-sm">
                                <th className="p-4 border-b border-white/10 font-medium">Time</th>
                                <th className="p-4 border-b border-white/10 font-medium">Lane Name</th>
                                <th className="p-4 border-b border-white/10 font-medium">Total Count</th>
                                <th className="p-4 border-b border-white/10 font-medium">Emergency Detected</th>
                                <th className="p-4 border-b border-white/10 font-medium">Congestion Level</th>
                            </tr>
                        </thead>
                        <tbody>
                            {loading ? (
                                <tr><td colSpan="5" className="p-8 text-center text-[#00e5ff] animate-pulse">Loading...</td></tr>
                            ) : (!flattenedLogs || flattenedLogs.length === 0) ? (
                                <tr><td colSpan="5" className="p-8 text-center text-gray-500">No logs found.</td></tr>
                            ) : (
                                flattenedLogs.slice((page - 1) * 10, page * 10).map((log, i) => {
                                    const isExpanded = expandedRows.has(log.id);
                                    return (
                                        <React.Fragment key={log.id}>
                                            <tr onClick={() => toggleRow(log.id)} className="border-b border-white/5 hover:bg-white/5 transition-colors cursor-pointer">
                                                <td className="p-4 text-sm text-gray-300">{log.time}</td>
                                                <td className="p-4 text-sm text-gray-300 font-bold">{log.laneName}</td>
                                                <td className="p-4 text-sm text-gray-300">{log.totalCount}</td>
                                                <td className="p-4">
                                                    {log.emergency ? (
                                                        <span className="text-xs px-2 py-1 rounded-full bg-[#ff4757]/20 text-[#ff4757] border border-[#ff4757]/50 font-bold shadow-[0_0_10px_rgba(255,71,87,0.4)]">Yes</span>
                                                    ) : (
                                                        <span className="text-xs px-2 py-1 rounded-full bg-white/10 text-gray-400 border border-white/10">No</span>
                                                    )}
                                                </td>
                                                <td className="p-4">
                                                    <span className={`text-xs px-2 py-1 rounded-full border ${log.congestion === 'High' ? 'bg-[#ff4757]/20 text-[#ff4757] border-[#ff4757]/50' : log.congestion === 'Medium' ? 'bg-[#ffd700]/20 text-[#ffd700] border-[#ffd700]/50' : 'bg-[#00ff88]/20 text-[#00ff88] border-[#00ff88]/50'}`}>
                                                        {log.congestion}
                                                    </span>
                                                </td>
                                            </tr>
                                            {isExpanded && (
                                                <tr className="bg-black/20 border-b border-white/5">
                                                    <td colSpan="5" className="p-4 text-sm text-gray-400">
                                                        <span className="text-[#00e5ff] font-medium mr-2">Vehicle Breakdown:</span>
                                                        {formatBreakdown(log.breakdown)}
                                                    </td>
                                                </tr>
                                            )}
                                        </React.Fragment>
                                    );
                                })
                            )}
                        </tbody>
                    </table>
                </div>

                <div className="p-4 flex items-center justify-between border-t border-white/10 text-sm">
                    <span className="text-gray-400">Page {page} of {totalPages || 1}</span>
                    <div className="flex gap-2">
                        <button 
                            onClick={() => setPage(p => Math.max(1, p - 1))}
                            disabled={page === 1}
                            className="px-3 py-1 rounded bg-white/5 hover:bg-white/10 disabled:opacity-50 transition-colors"
                        >
                            Prev
                        </button>
                        <button 
                            onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                            disabled={page >= totalPages}
                            className="px-3 py-1 rounded bg-white/5 hover:bg-white/10 disabled:opacity-50 transition-colors"
                        >
                            Next
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default History;
