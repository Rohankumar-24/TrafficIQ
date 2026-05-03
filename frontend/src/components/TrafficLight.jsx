import React from 'react';

const TrafficLight = ({ signal }) => {
    const getSignalColor = (s) => {
        const normalized = s ? s.toString().toLowerCase() : '';
        switch(normalized) {
            case 'green': return 'bg-[#00ff88] shadow-[0_0_20px_#00ff88]';
            case 'yellow': return 'bg-[#ffd700] shadow-[0_0_20px_#ffd700]';
            case 'red': return 'bg-[#ff4757] shadow-[0_0_20px_#ff4757]';
            default: return 'bg-gray-600';
        }
    };

    return (
        <div className={`w-12 h-12 rounded-full ${getSignalColor(signal)} border-4 border-[#0a0e1a] transition-all duration-500`} />
    );
};

export default TrafficLight;
