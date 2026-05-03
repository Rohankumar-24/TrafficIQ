import React, { useState, useEffect, useContext } from 'react';
import axios from 'axios';
import { TrafficContext } from '../context/TrafficContext';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

const Analytics = () => {
    const { isRunning, analyticsData } = useContext(TrafficContext);
    const [loading, setLoading] = useState(false);

    const COLORS = ['#00ff88', '#ffd700', '#ff4757'];

    const data = analyticsData;

    // ── Congestion Distribution from Flask /analytics ──────────────────
    const [congDist, setCongDist] = useState({ Low: 0, Medium: 0, High: 0 });

    useEffect(() => {
        const fetchAnalytics = async () => {
            try {
                const res = await axios.get('/flask-api/analytics');
                if (res.data?.congestion_dist) {
                    setCongDist(prev => ({ ...prev, ...res.data.congestion_dist }));
                }
            } catch (err) {
                // Flask may not be running; silently ignore
            }
        };
        fetchAnalytics();
        // Poll every 3 s while running
        const id = isRunning ? setInterval(fetchAnalytics, 3000) : null;
        return () => { if (id) clearInterval(id); };
    }, [isRunning]);

    // Congestion distribution levels
    const total = (congDist.Low || 0) + (congDist.Medium || 0) + (congDist.High || 0);

    const levels = [
        {
            label:   'LOW TRAFFIC',
            key:     'Low',
            icon:    '🟢',
            color:   '#00ff88',
            bgColor: 'rgba(0,255,136,0.08)',
            border:  'rgba(0,255,136,0.2)',
            value:   congDist.Low || 0
        },
        {
            label:   'MEDIUM TRAFFIC',
            key:     'Medium',
            icon:    '🟡',
            color:   '#ffd700',
            bgColor: 'rgba(255,215,0,0.08)',
            border:  'rgba(255,215,0,0.2)',
            value:   congDist.Medium || 0
        },
        {
            label:   'HIGH TRAFFIC',
            key:     'High',
            icon:    '🔴',
            color:   '#ff4757',
            bgColor: 'rgba(255,71,87,0.08)',
            border:  'rgba(255,71,87,0.2)',
            value:   congDist.High || 0
        }
    ];

    if (loading) return <div className="flex items-center justify-center h-full text-[#00e5ff] animate-pulse">Loading Analytics...</div>;

    return (
        <div className="flex flex-col gap-6 h-full pb-10">
            <header className="mb-4">
                <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-[#00e5ff] to-[#00ff88]">
                    Traffic Analytics
                </h1>
                <p className="text-gray-400 mt-1">Data insights from past monitoring sessions</p>
                {isRunning && <span className="text-xs text-[#00ff88] font-bold animate-pulse mt-2 inline-block">LIVE UPDATING</span>}
            </header>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Traffic Volume Over Time */}
                <div className="glass-panel p-6 rounded-2xl border border-white/5 lg:col-span-2">
                    <h2 className="text-xl font-bold text-white mb-6">Traffic Volume Over Time</h2>
                    <div className="h-80 w-full">
                        <ResponsiveContainer width="100%" height="100%">
                            <LineChart data={data.timeSeriesData || []}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#ffffff10" />
                                <XAxis dataKey="time" stroke="#9ca3af" />
                                <YAxis stroke="#9ca3af" />
                                <Tooltip 
                                    contentStyle={{ backgroundColor: '#0a0e1a', borderColor: '#00e5ff30', borderRadius: '8px' }}
                                    itemStyle={{ color: '#fff' }}
                                />
                                <Legend />
                                <Line type="monotone" dataKey="lane1" stroke="#00e5ff" strokeWidth={3} dot={{ r: 4, fill: '#00e5ff' }} activeDot={{ r: 8 }} name="Lane 1" />
                                <Line type="monotone" dataKey="lane2" stroke="#00ff88" strokeWidth={3} dot={{ r: 4, fill: '#00ff88' }} activeDot={{ r: 8 }} name="Lane 2" />
                            </LineChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                {/* Congestion Distribution — 3 progress-bar cards */}
                <div style={{
                    background:   '#0f1623',
                    border:       '1px solid #1a2535',
                    borderRadius: '14px',
                    padding:      '24px'
                }}>

                    {/* Title */}
                    <div style={{ marginBottom: '20px' }}>
                        <h2 style={{
                            fontFamily:    'Rajdhani, sans-serif',
                            fontSize:      '20px',
                            fontWeight:    700,
                            color:         '#f1f5f9',
                            margin:        0
                        }}>
                            Congestion Distribution
                        </h2>
                        <p style={{
                            fontSize:     '12px',
                            color:        '#475569',
                            marginTop:    '4px',
                            marginBottom: 0
                        }}>
                            How traffic was distributed this session
                        </p>
                    </div>

                    {/* 3 Progress Cards */}
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                        {levels.map((level) => {
                            const pct = total > 0
                                ? Math.round((level.value / total) * 100)
                                : 0;

                            return (
                                <div
                                    key={level.key}
                                    style={{
                                        background:   level.bgColor,
                                        border:       `1px solid ${level.border}`,
                                        borderRadius: '10px',
                                        padding:      '16px 20px'
                                    }}
                                >
                                    {/* Top row */}
                                    <div style={{
                                        display:        'flex',
                                        justifyContent: 'space-between',
                                        alignItems:     'center',
                                        marginBottom:   '10px'
                                    }}>
                                        {/* Left — icon + label */}
                                        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                                            <span style={{ fontSize: '18px' }}>{level.icon}</span>
                                            <span style={{
                                                fontSize:      '13px',
                                                fontWeight:    700,
                                                color:         level.color,
                                                letterSpacing: '0.5px'
                                            }}>
                                                {level.label}
                                            </span>
                                        </div>

                                        {/* Right — percentage badge */}
                                        <span style={{
                                            fontFamily: 'JetBrains Mono, monospace',
                                            fontSize:   '20px',
                                            fontWeight: 700,
                                            color:      level.color
                                        }}>
                                            {pct}%
                                        </span>
                                    </div>

                                    {/* Progress bar */}
                                    <div style={{
                                        background:   'rgba(255,255,255,0.05)',
                                        borderRadius: '4px',
                                        height:       '8px',
                                        overflow:     'hidden',
                                        marginBottom: '8px'
                                    }}>
                                        <div style={{
                                            width:        `${pct}%`,
                                            height:       '100%',
                                            background:   level.color,
                                            borderRadius: '4px',
                                            transition:   'width 0.6s ease',
                                            boxShadow:    `0 0 8px ${level.color}60`
                                        }} />
                                    </div>

                                    {/* Bottom — reading count */}
                                    <div style={{ fontSize: '12px', color: '#475569' }}>
                                        {level.value} {level.value === 1 ? 'reading' : 'readings'} recorded
                                    </div>
                                </div>
                            );
                        })}
                    </div>

                    {/* Empty state */}
                    {total === 0 && (
                        <div style={{
                            textAlign: 'center',
                            padding:   '40px 20px',
                            color:     '#334155'
                        }}>
                            <div style={{ fontSize: '40px', marginBottom: '12px' }}>📊</div>
                            <p style={{ margin: 0, fontSize: '15px' }}>No data yet</p>
                            <p style={{
                                margin:   '6px 0 0',
                                fontSize: '12px',
                                color:    '#1e293b'
                            }}>
                                Start detection to see congestion distribution
                            </p>
                        </div>
                    )}
                </div>

                {/* Bar Chart - Total Vehicles Comparison */}
                <div className="glass-panel p-6 rounded-2xl border border-white/5">
                    <h2 className="text-xl font-bold text-white mb-6">Recent Lane Comparison</h2>
                    <div className="h-64 w-full">
                        <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={(data.timeSeriesData || []).slice(-5)}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#ffffff10" />
                                <XAxis dataKey="time" stroke="#9ca3af" />
                                <YAxis stroke="#9ca3af" />
                                <Tooltip contentStyle={{ backgroundColor: '#0a0e1a', borderColor: '#333' }} />
                                <Legend />
                                <Bar dataKey="lane1" fill="#00e5ff" radius={[4, 4, 0, 0]} name="Lane 1" />
                                <Bar dataKey="lane2" fill="#00ff88" radius={[4, 4, 0, 0]} name="Lane 2" />
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Analytics;
