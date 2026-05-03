import React from 'react';
import { Cpu, Shield, Zap, Database } from 'lucide-react';

const About = () => {
    return (
        <div className="flex flex-col gap-8 max-w-4xl mx-auto py-8 relative">
            {/* Background elements */}
            <div className="absolute top-[20%] left-[-20%] w-[50%] h-[50%] bg-[#00e5ff]/10 blur-[120px] rounded-full pointer-events-none" />
            <div className="absolute bottom-[20%] right-[-20%] w-[50%] h-[50%] bg-[#00ff88]/10 blur-[120px] rounded-full pointer-events-none" />

            <div className="text-center z-10">
                <h1 className="text-4xl font-bold mb-4 bg-clip-text text-transparent bg-gradient-to-r from-[#00e5ff] to-[#00ff88]">
                    About TrafficIQ
                </h1>
                <p className="text-gray-400 text-lg">Smart Traffic Signal Control System powered by YOLOv8 Edge AI</p>
            </div>

            <div className="glass-panel p-8 rounded-3xl border border-white/10 z-10">
                <h2 className="text-2xl font-bold text-white mb-4">Project Overview</h2>
                <p className="text-gray-300 leading-relaxed mb-6">
                    TrafficIQ is a state-of-the-art solution designed to dynamically optimize traffic signal timings using real-time computer vision. By connecting directly to a Flask-hosted YOLOv8 model, the system analyzes video streams from multiple lanes to count vehicles, estimate congestion levels, and adjust traffic lights accordingly to minimize wait times and reduce carbon emissions.
                </p>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-8">
                    <div className="bg-[#0a0e1a]/50 p-6 rounded-2xl border border-white/5 flex gap-4">
                        <div className="w-12 h-12 rounded-full bg-[#00e5ff]/20 flex items-center justify-center shrink-0">
                            <Cpu className="text-[#00e5ff]" />
                        </div>
                        <div>
                            <h3 className="text-white font-bold mb-1">Direct AI Integration</h3>
                            <p className="text-sm text-gray-400">React frontend connects securely to the local Flask AI engine for rapid, zero-latency inference.</p>
                        </div>
                    </div>
                    
                    <div className="bg-[#0a0e1a]/50 p-6 rounded-2xl border border-white/5 flex gap-4">
                        <div className="w-12 h-12 rounded-full bg-[#00ff88]/20 flex items-center justify-center shrink-0">
                            <Database className="text-[#00ff88]" />
                        </div>
                        <div>
                            <h3 className="text-white font-bold mb-1">Session Logging</h3>
                            <p className="text-sm text-gray-400">The system handles robust data storage, enabling detailed analytics on past traffic patterns.</p>
                        </div>
                    </div>

                    <div className="bg-[#0a0e1a]/50 p-6 rounded-2xl border border-white/5 flex gap-4">
                        <div className="w-12 h-12 rounded-full bg-[#ff4757]/20 flex items-center justify-center shrink-0">
                            <Shield className="text-[#ff4757]" />
                        </div>
                        <div>
                            <h3 className="text-white font-bold mb-1">Emergency Detection</h3>
                            <p className="text-sm text-gray-400">AI automatically detects emergency vehicles (ambulances, fire trucks) and prioritizes their route.</p>
                        </div>
                    </div>

                    <div className="bg-[#0a0e1a]/50 p-6 rounded-2xl border border-white/5 flex gap-4">
                        <div className="w-12 h-12 rounded-full bg-[#ffd700]/20 flex items-center justify-center shrink-0">
                            <Zap className="text-[#ffd700]" />
                        </div>
                        <div>
                            <h3 className="text-white font-bold mb-1">Adaptive Algorithms</h3>
                            <p className="text-sm text-gray-400">Dynamic signal timers calculate the optimal green phase length based on current lane congestion density.</p>
                        </div>
                    </div>
                </div>
            </div>
            
            <div className="text-center text-sm text-gray-500 mt-8">
                Built with React, Flask, and YOLOv8.
            </div>
        </div>
    );
};

export default About;
