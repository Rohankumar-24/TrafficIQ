import React, { createContext, useState, useEffect, useRef } from 'react';
import axios from 'axios';

export const TrafficContext = createContext();

export const TrafficProvider = ({ children }) => {
    const [isRunning, setIsRunning] = useState(false);
    const [backendError, setBackendError] = useState(null);
    const [isUploading, setIsUploading] = useState(false);

    // Global Traffic Data
    const [lane1Data, setLane1Data] = useState({ vehicleCount: 0, congestionLevel: 'Low', signal: 'Red' });
    const [lane2Data, setLane2Data] = useState({ vehicleCount: 0, congestionLevel: 'Low', signal: 'Red' });
    const [lane1Image, setLane1Image] = useState(null);
    const [lane2Image, setLane2Image] = useState(null);
    const [emergencyAlert, setEmergencyAlert] = useState(false);

    // Accumulated Data for Analytics & History
    const [analyticsData, setAnalyticsData] = useState({ timeSeriesData: [], congestionData: [] });
    const [historyLogs, setHistoryLogs] = useState([]);

    const intervalRef = useRef(null);
    const frameIntervalRef = useRef(null);
    
    // Refs for persisting mock detections across frames so they don't teleport
    const activeDetections1 = useRef([]);
    const activeDetections2 = useRef([]);

    // Stop polling when unmounted or stopped
    const clearPolls = () => {
        if (intervalRef.current) clearInterval(intervalRef.current);
        if (frameIntervalRef.current) clearInterval(frameIntervalRef.current);
    };

    const fetchStatus = async () => {
        try {
            const res = await axios.get('/flask-api/status');
            return res.data.running;
        } catch (err) {
            console.error("Status check failed", err);
            return false;
        }
    };

    const startSystem = async (video1Path, video2Path, hour) => {
        setIsUploading(true);
        setBackendError(null);
        setAnalyticsData({ timeSeriesData: [], congestionData: [] });

        try {
            const isCurrentlyRunning = await fetchStatus();
            if (isCurrentlyRunning) {
                // If it's already running, we just set running to true to connect to the stream
                setIsRunning(true);
                startPolling();
                setIsUploading(false);
                return;
            }

            const formData = new FormData();
            formData.append('video1', video1Path);
            formData.append('video2', video2Path);
            
            const uploadRes = await axios.post('/flask-api/upload', formData, {
                headers: { 'Content-Type': 'multipart/form-data' }
            });
            
            const v1 = uploadRes.data.video1 || uploadRes.data.video1_path;
            const v2 = uploadRes.data.video2 || uploadRes.data.video2_path;

            await axios.post('/flask-api/start', {
                video1: v1,
                video2: v2,
                hour: parseInt(hour)
            });

            setIsRunning(true);
            startPolling();
        } catch (error) {
            console.error("Start System Error:", error);
            const errMsg = error.response?.data?.error || error.response?.statusText || error.message;
            setBackendError(`Failed: ${errMsg}`);
            setIsRunning(false);
        } finally {
            setIsUploading(false);
        }
    };

    const stopSystem = async () => {
        setIsRunning(false);
        try {
            await axios.post('/flask-api/stop');
        } catch(err) {
            console.error("Stop API Error:", err);
        }
        clearPolls();
        setLane1Image(null);
        setLane2Image(null);
    };

    const startPolling = () => {
        clearPolls();

        intervalRef.current = setInterval(async () => {
            try {
                const dataRes = await axios.get('/flask-api/data');
                const { running, lane1, lane2 } = dataRes.data;
                
                if (running === false) {
                    stopSystem();
                    return;
                }

                const updateMockDetections = (activeRef, count, hasEmergency) => {
                    // Move existing boxes down to simulate driving
                    let current = activeRef.current
                        .map(d => ({ ...d, y: d.y + 4, x: d.x + (Math.random() * 1 - 0.5) })) // Move down and slight sway
                        .filter(d => d.y < 85); // Remove if off bottom screen
                    
                    // Add new boxes if we need more to match count
                    while(current.length < count) {
                        const types = ['Car', 'Truck', 'Bus'];
                        const isEmergency = hasEmergency && current.filter(c => c.isEmergency).length === 0;
                        const type = isEmergency ? 'Emergency' : types[Math.floor(Math.random() * types.length)];
                        
                        current.push({
                            id: Math.random().toString(36).substr(2, 9),
                            type: type.toUpperCase(),
                            isEmergency,
                            // Spawn in the upper-middle of the screen (simulating the road vanishing point)
                            x: Math.floor(Math.random() * 40) + 30, // 30% to 70% width
                            y: Math.floor(Math.random() * 20) + 30, // 30% to 50% height
                            width: Math.floor(Math.random() * 8) + 8,
                            height: Math.floor(Math.random() * 12) + 12
                        });
                    }
                    
                    // Remove if we have too many
                    if (current.length > count) {
                        current = current.slice(0, count);
                    }
                    
                    activeRef.current = current;
                    
                    let breakdown = { Car: 0, Truck: 0, Bus: 0, Emergency: 0 };
                    current.forEach(d => {
                        const t = d.type === 'EMERGENCY' ? 'Emergency' : d.type.charAt(0) + d.type.slice(1).toLowerCase();
                        breakdown[t] = (breakdown[t] || 0) + 1;
                    });
                    
                    return { detections: current, breakdown };
                };

                const l1Emergency = lane1?.emergency || false;
                const l2Emergency = lane2?.emergency || false;
                
                let l1Mock = { detections: lane1?.detections, breakdown: lane1?.breakdown };
                let l2Mock = { detections: lane2?.detections, breakdown: lane2?.breakdown };

                if (!lane1?.detections) {
                    l1Mock = updateMockDetections(activeDetections1, lane1?.count || 0, l1Emergency);
                }
                if (!lane2?.detections) {
                    l2Mock = updateMockDetections(activeDetections2, lane2?.count || 0, l2Emergency);
                }

                // Dynamic Traffic Signal Logic
                const count1 = lane1?.count || l1Mock.detections?.length || 0;
                const count2 = lane2?.count || l2Mock.detections?.length || 0;
                
                let signal1 = 'Red';
                let signal2 = 'Green';
                
                if (l1Emergency) {
                    signal1 = 'Green';
                    signal2 = 'Red';
                } else if (l2Emergency) {
                    signal1 = 'Red';
                    signal2 = 'Green';
                } else if (count1 > count2) {
                    signal1 = 'Green';
                    signal2 = 'Red';
                } else if (count1 === count2 && count1 > 0) {
                    signal1 = 'Yellow';
                    signal2 = 'Yellow';
                }
                
                if (lane1) {
                    setLane1Data({ 
                        vehicleCount: lane1.count || 0, 
                        congestionLevel: lane1.congestion || 'Low', 
                        signal: lane1.signal || signal1,
                        duration: lane1.duration || 0,
                        types: lane1.types || {},
                        detections: l1Mock.detections,
                        breakdown: l1Mock.breakdown,
                        emergency: l1Emergency
                    });
                }
                
                if (lane2) {
                    setLane2Data({ 
                        vehicleCount: lane2.count || 0, 
                        congestionLevel: lane2.congestion || 'Low', 
                        signal: lane2.signal || signal2,
                        duration: lane2.duration || 0,
                        types: lane2.types || {},
                        detections: l2Mock.detections,
                        breakdown: l2Mock.breakdown,
                        emergency: l2Emergency
                    });
                }
                
                setEmergencyAlert(l1Emergency || l2Emergency);

                // Accumulate Data Locally
                const timestamp = new Date().toLocaleTimeString();
                
                setAnalyticsData(prev => {
                    const newSeries = [...prev.timeSeriesData, {
                        time: timestamp,
                        lane1: lane1?.count || 0,
                        lane2: lane2?.count || 0
                    }].slice(-20); // Keep last 20 points

                    const c1 = lane1?.congestion || 'Low';
                    const c2 = lane2?.congestion || 'Low';
                    
                    const prevCong = prev.congestionData?.length === 3 ? prev.congestionData : [
                        { name: 'Low', value: 0 },
                        { name: 'Medium', value: 0 },
                        { name: 'High', value: 0 }
                    ];

                    const newCongestion = prevCong.map(c => {
                        let add = 0;
                        if (c1 === c.name || (c1 === 'EMERGENCY' && c.name === 'High')) add++;
                        if (c2 === c.name || (c2 === 'EMERGENCY' && c.name === 'High')) add++;
                        return { ...c, value: c.value + add };
                    });

                    return { timeSeriesData: newSeries, congestionData: newCongestion };
                });

                setHistoryLogs(prev => {
                    const newLog = {
                        _id: Date.now(),
                        timestamp: new Date().toISOString(),
                        lane1: { 
                            name: 'Lane 1', 
                            vehicleCount: lane1?.count || 0, 
                            congestionLevel: lane1?.congestion || 'Low',
                            breakdown: l1Mock.breakdown
                        },
                        lane2: { 
                            name: 'Lane 2', 
                            vehicleCount: lane2?.count || 0, 
                            congestionLevel: lane2?.congestion || 'Low',
                            breakdown: l2Mock.breakdown
                        },
                        emergencyAlert: l1Emergency || l2Emergency
                    };
                    return [newLog, ...prev].slice(0, 50); // Keep last 50 logs locally
                });

            } catch(err) {
                console.error("Data Poll Error:", err);
                setBackendError("Lost connection to Flask backend.");
            }
        }, 500);

        frameIntervalRef.current = setInterval(async () => {
            try {
                const f1Res = await axios.get('/flask-api/frame/1');
                if (f1Res.data?.frame) setLane1Image(`data:image/jpeg;base64,${f1Res.data.frame}`);
                else if (typeof f1Res.data === 'string') setLane1Image(`data:image/jpeg;base64,${f1Res.data}`);
                
                const f2Res = await axios.get('/flask-api/frame/2');
                if (f2Res.data?.frame) setLane2Image(`data:image/jpeg;base64,${f2Res.data.frame}`);
                else if (typeof f2Res.data === 'string') setLane2Image(`data:image/jpeg;base64,${f2Res.data}`);
            } catch(err) {
                console.error("Frame Poll Error:", err);
            }
        }, 100);
    };

    useEffect(() => {
        return () => clearPolls();
    }, []);

    return (
        <TrafficContext.Provider value={{
            isRunning, isUploading, backendError, 
            lane1Data, lane2Data, lane1Image, lane2Image, emergencyAlert,
            analyticsData, historyLogs,
            startSystem, stopSystem
        }}>
            {children}
        </TrafficContext.Provider>
    );
};
