import React from 'react';
import { Link } from 'react-router-dom';
import { Activity, Shield, Zap } from 'lucide-react';

const Landing = () => {
    return (
        <div className="min-h-screen bg-[#0a0e1a] text-white flex flex-col relative overflow-hidden">
            <div className="absolute top-[-20%] left-[-10%] w-[50%] h-[50%] bg-[#00e5ff]/10 blur-[120px] rounded-full pointer-events-none" />
            <div className="absolute bottom-[-20%] right-[-10%] w-[50%] h-[50%] bg-[#00ff88]/10 blur-[120px] rounded-full pointer-events-none" />
            
            <header className="px-8 py-6 flex justify-between items-center relative z-10">
                <div className="flex items-center gap-2">
                    <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-[#00e5ff] to-[#00ff88] flex items-center justify-center font-bold text-[#0a0e1a] text-xl">
                        T
                    </div>
                    <span className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-[#00e5ff] to-[#00ff88]">
                        TrafficIQ
                    </span>
                </div>
                <div className="flex gap-4">
                    <Link to="/login" className="px-6 py-2 rounded-xl text-gray-300 hover:text-white transition-colors">Login</Link>
                    <Link to="/register" className="px-6 py-2 rounded-xl bg-white/10 hover:bg-white/20 transition-colors border border-white/10">Register</Link>
                </div>
            </header>

            <main className="flex-1 flex flex-col items-center justify-center px-4 relative z-10 text-center">
                <div className="inline-block mb-6 px-4 py-1.5 rounded-full bg-[#00e5ff]/10 border border-[#00e5ff]/30 text-[#00e5ff] text-sm font-semibold tracking-wide">
                    POWERED BY YOLOv8 EDGE AI
                </div>
                <h1 className="text-5xl md:text-7xl font-bold mb-6 max-w-4xl leading-tight">
                    Next-Gen <span className="bg-clip-text text-transparent bg-gradient-to-r from-[#00e5ff] to-[#00ff88]">Smart Traffic</span> Control System
                </h1>
                <p className="text-xl text-gray-400 mb-10 max-w-2xl">
                    Dynamically optimize traffic signals in real-time using advanced computer vision and machine learning.
                </p>
                <div className="flex gap-4">
                    <Link to="/login" className="px-8 py-4 rounded-xl bg-gradient-to-r from-[#00e5ff] to-[#00ff88] text-[#0a0e1a] font-bold text-lg hover:shadow-[0_0_20px_rgba(0,229,255,0.4)] transition-all">
                        Get Started
                    </Link>
                    <Link to="/about" className="px-8 py-4 rounded-xl bg-white/5 hover:bg-white/10 text-white font-bold text-lg border border-white/10 transition-all">
                        Learn More
                    </Link>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-20 max-w-5xl w-full text-left">
                    <div className="glass-panel p-6 rounded-2xl border border-white/5">
                        <Activity className="text-[#00e5ff] mb-4" size={32} />
                        <h3 className="text-xl font-bold mb-2">Real-Time Analytics</h3>
                        <p className="text-gray-400">Process live video streams with zero latency to calculate precise vehicle density and flow rates.</p>
                    </div>
                    <div className="glass-panel p-6 rounded-2xl border border-white/5">
                        <Zap className="text-[#ffd700] mb-4" size={32} />
                        <h3 className="text-xl font-bold mb-2">Dynamic Timing</h3>
                        <p className="text-gray-400">Automatically adjust green light phases based on immediate demand, reducing overall wait times.</p>
                    </div>
                    <div className="glass-panel p-6 rounded-2xl border border-white/5">
                        <Shield className="text-[#ff4757] mb-4" size={32} />
                        <h3 className="text-xl font-bold mb-2">Emergency Priority</h3>
                        <p className="text-gray-400">Instantly detect ambulances and fire trucks to clear their path and ensure rapid response.</p>
                    </div>
                </div>
            </main>
        </div>
    );
};

export default Landing;
