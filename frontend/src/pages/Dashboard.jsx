import React, { useState, useContext } from 'react';
import { Play, Square, AlertTriangle, Activity } from 'lucide-react';
import { TrafficContext } from '../context/TrafficContext';
import VideoFeed from '../components/VideoFeed';
import StatCard from '../components/StatCard';

const Dashboard = () => {
    const { 
        isRunning, isUploading, backendError, 
        lane1Data, lane2Data, lane1Image, lane2Image, emergencyAlert,
        startSystem, stopSystem 
    } = useContext(TrafficContext);
    
    // Inputs
    const [inputs, setInputs] = useState({
        video1_path: null,
        video2_path: null,
        lane1_name: 'Main Street',
        lane2_name: 'Cross Avenue',
        hour: 12,
        frame_skip: 5
    });

    const handleInputChange = (e) => {
        const { name, value, type, files } = e.target;
        if (type === 'file') {
            setInputs(prev => ({ ...prev, [name]: files[0] }));
        } else {
            setInputs(prev => ({ ...prev, [name]: value }));
        }
    };

    const handleStart = () => {
        if (!inputs.video1_path || !inputs.video2_path) {
            alert("Please provide both videos");
            return;
        }
        startSystem(inputs.video1_path, inputs.video2_path, inputs.hour);
    };

    return (
        <div className="flex flex-col gap-6">
            <header className="flex justify-between items-center mb-2">
                <div>
                    <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-gray-400">
                        Live Traffic Control
                    </h1>
                    <p className="text-gray-400 mt-1">Real-time AI surveillance and signal management</p>
                </div>
                
                {emergencyAlert && (
                    <div className="animate-pulse bg-[#ff4757]/20 border border-[#ff4757] px-6 py-3 rounded-xl flex items-center gap-3">
                        <AlertTriangle className="text-[#ff4757]" />
                        <span className="text-[#ff4757] font-bold tracking-wide">EMERGENCY VEHICLE DETECTED</span>
                    </div>
                )}
            </header>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Control Panel */}
                <div className="glass-panel p-6 rounded-2xl flex flex-col gap-5 h-fit">
                    <h2 className="text-xl font-bold flex items-center gap-2 border-b border-white/10 pb-3">
                        <Activity className="text-[#00e5ff]" size={20} />
                        System Controls
                    </h2>
                    
                    <div className="space-y-4">
                        <div>
                            <label className="text-sm text-gray-400 mb-1 block">Video 1</label>
                            <input type="file" accept="video/*" name="video1_path" onChange={handleInputChange} className="w-full bg-[#0a0e1a] border border-white/10 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-[#00e5ff] text-gray-300 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-[#00e5ff]/20 file:text-[#00e5ff] hover:file:bg-[#00e5ff]/30 cursor-pointer" />
                        </div>
                        <div>
                            <label className="text-sm text-gray-400 mb-1 block">Video 2</label>
                            <input type="file" accept="video/*" name="video2_path" onChange={handleInputChange} className="w-full bg-[#0a0e1a] border border-white/10 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-[#00e5ff] text-gray-300 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-[#00ff88]/20 file:text-[#00ff88] hover:file:bg-[#00ff88]/30 cursor-pointer" />
                        </div>
                        
                        <div className="grid grid-cols-2 gap-4">
                            <div>
                                <label className="text-sm text-gray-400 mb-1 block">Lane 1 Name</label>
                                <input name="lane1_name" value={inputs.lane1_name} onChange={handleInputChange} className="w-full bg-[#0a0e1a] border border-white/10 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-[#00e5ff]" />
                            </div>
                            <div>
                                <label className="text-sm text-gray-400 mb-1 block">Lane 2 Name</label>
                                <input name="lane2_name" value={inputs.lane2_name} onChange={handleInputChange} className="w-full bg-[#0a0e1a] border border-white/10 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-[#00e5ff]" />
                            </div>
                        </div>

                        <div>
                            <label className="text-sm text-gray-400 mb-1 flex justify-between">
                                <span>Hour of Day</span>
                                <span className="text-[#00e5ff] font-mono">{inputs.hour}:00</span>
                            </label>
                            <input type="range" name="hour" min="0" max="23" value={inputs.hour} onChange={handleInputChange} className="w-full accent-[#00e5ff]" />
                        </div>
                    </div>

                    <div className="flex flex-col gap-2 mt-4">
                        <div className="flex gap-4">
                            {!isRunning ? (
                                <button onClick={handleStart} disabled={isUploading} className="flex-1 bg-gradient-to-r from-[#00ff88] to-[#00b35f] text-[#0a0e1a] font-bold py-3 rounded-xl flex items-center justify-center gap-2 hover:shadow-[0_0_15px_rgba(0,255,136,0.4)] transition-all disabled:opacity-50 disabled:cursor-not-allowed">
                                    {isUploading ? (
                                        <><div className="animate-spin rounded-full h-5 w-5 border-b-2 border-[#0a0e1a]"></div> STARTING...</>
                                    ) : (
                                        <><Play size={18} fill="currentColor" /> START AI</>
                                    )}
                                </button>
                            ) : (
                                <button onClick={stopSystem} className="flex-1 bg-gradient-to-r from-[#ff4757] to-[#cc3946] text-white font-bold py-3 rounded-xl flex items-center justify-center gap-2 hover:shadow-[0_0_15px_rgba(255,71,87,0.4)] transition-all">
                                    <Square size={18} fill="currentColor" /> STOP SYSTEM
                                </button>
                            )}
                        </div>
                        {backendError && (
                            <div className="text-sm text-[#ff4757] flex items-center gap-2 bg-[#ff4757]/10 p-2 rounded-lg border border-[#ff4757]/30">
                                <AlertTriangle size={16} /> {backendError}
                            </div>
                        )}
                    </div>
                </div>

                {/* Video Panels */}
                <div className="lg:col-span-2 grid grid-cols-1 md:grid-cols-2 gap-6">
                    {/* Lane 1 */}
                    <div className="flex flex-col relative h-full">
                        <VideoFeed 
                            isRunning={isRunning} 
                            image={lane1Image} 
                            label={inputs.lane1_name} 
                            signal={lane1Data.signal}
                            detections={lane1Data.detections || []} 
                        />
                        <StatCard 
                            laneName={inputs.lane1_name} 
                            vehicleCount={lane1Data.vehicleCount} 
                            congestionLevel={lane1Data.congestionLevel} 
                            colorHex="#00e5ff"
                            signal={lane1Data.signal}
                            duration={lane1Data.duration || 0}
                            types={lane1Data.types || {}}
                            emergency={lane1Data.emergency}
                            breakdown={lane1Data.breakdown || {}} 
                        />
                    </div>

                    {/* Lane 2 */}
                    <div className="flex flex-col relative h-full">
                        <VideoFeed 
                            isRunning={isRunning} 
                            image={lane2Image} 
                            label={inputs.lane2_name} 
                            signal={lane2Data.signal}
                            detections={lane2Data.detections || []} 
                        />
                        <StatCard 
                            laneName={inputs.lane2_name} 
                            vehicleCount={lane2Data.vehicleCount} 
                            congestionLevel={lane2Data.congestionLevel} 
                            colorHex="#00ff88"
                            signal={lane2Data.signal}
                            duration={lane2Data.duration || 0}
                            types={lane2Data.types || {}}
                            emergency={lane2Data.emergency}
                            breakdown={lane2Data.breakdown || {}} 
                        />
                    </div>
                </div>

            </div>
        </div>
    );
};

export default Dashboard;
