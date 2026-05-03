import React from 'react';
import TrafficLight from './TrafficLight';

const VideoFeed = ({ isRunning, image, label, signal, detections }) => {
    const hasEmergency = detections && detections.some(d => d.isEmergency);
    return (
        <div className={`glass-panel rounded-2xl overflow-hidden flex flex-col relative border transition-all duration-300 ${hasEmergency ? 'border-[#ff0000] shadow-[0_0_20px_rgba(255,0,0,0.5)]' : 'border-white/5'}`}>
            {isRunning && (
                <div className="absolute top-4 left-4 z-10 flex items-center gap-2 bg-black/60 backdrop-blur-md px-3 py-1 rounded-full border border-[#ff4757]/30">
                    <div className="w-2.5 h-2.5 rounded-full bg-[#ff4757] animate-pulse" />
                    <span className="text-xs font-bold text-[#ff4757] tracking-wider">LIVE AI</span>
                </div>
            )}
            
            <div className="aspect-video bg-[#05070d] relative flex items-center justify-center overflow-hidden">
                {!isRunning ? (
                    <span className="text-gray-600 font-medium">Video Feed Offline</span>
                ) : image ? (
                    <>
                        <img src={image} alt={`${label} Feed`} className="w-full h-full object-cover" />
                        

                        {/* Emergency Blue Bar (Optional bottom notification like Screenshot 2) */}
                        {detections && detections.some(d => d.isEmergency) && (
                            <div className="absolute bottom-0 left-0 right-0 bg-blue-700/80 text-white text-xs font-bold px-3 py-1 flex items-center justify-between">
                                <span>EMERGENCY DETECTED</span>
                            </div>
                        )}
                    </>
                ) : (
                    <div className="absolute inset-0 opacity-20 bg-[url('data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSI0IiBoZWlnaHQ9IjQiPgo8cmVjdCB3aWR0aD0iNCIgaGVpZ2h0PSI0IiBmaWxsPSIjZmZmIiBmaWxsLW9wYWNpdHk9IjAuMDUiLz4KPC9zdmc+')] animate-[slide_10s_linear_infinite]" />
                )}
                <div className="absolute bottom-4 right-4 flex gap-2 flex-col items-end">
                    <TrafficLight signal={signal} />
                </div>
            </div>
        </div>
    );
};

export default VideoFeed;
