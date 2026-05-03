const express = require('express');
const router = express.Router();
const TrafficLog = require('../models/TrafficLog');
const { protect } = require('../middleware/authMiddleware');

router.post('/save', protect, async (req, res) => {
    try {
        const { lane1, lane2, emergencyAlert } = req.body;
        
        const log = await TrafficLog.create({
            userId: req.user.id,
            lane1,
            lane2,
            emergencyAlert
        });

        res.status(201).json(log);
    } catch (error) {
        res.status(500).json({ message: 'Server error saving log' });
    }
});

router.get('/history', protect, async (req, res) => {
    try {
        const page = parseInt(req.query.page) || 1;
        const limit = parseInt(req.query.limit) || 10;
        const skip = (page - 1) * limit;

        const logs = await TrafficLog.find({ userId: req.user.id })
            .sort({ timestamp: -1 })
            .skip(skip)
            .limit(limit);
            
        const total = await TrafficLog.countDocuments({ userId: req.user.id });

        res.json({
            logs,
            page,
            pages: Math.ceil(total / limit),
            total
        });
    } catch (error) {
        res.status(500).json({ message: 'Server error fetching history' });
    }
});

router.get('/analytics', protect, async (req, res) => {
    try {
        const logs = await TrafficLog.find({ userId: req.user.id }).sort({ timestamp: 1 });
        
        // Basic analytics aggregation
        const timeSeriesData = logs.map(log => ({
            time: new Date(log.timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}),
            totalVehicles: (log.lane1?.vehicleCount || 0) + (log.lane2?.vehicleCount || 0),
            lane1: log.lane1?.vehicleCount || 0,
            lane2: log.lane2?.vehicleCount || 0
        }));

        const congestionStats = { Low: 0, Medium: 0, High: 0 };
        logs.forEach(log => {
            if (log.lane1?.congestionLevel) congestionStats[log.lane1.congestionLevel]++;
            if (log.lane2?.congestionLevel) congestionStats[log.lane2.congestionLevel]++;
        });

        const congestionData = Object.keys(congestionStats).map(key => ({
            name: key,
            value: congestionStats[key]
        }));

        res.json({
            timeSeriesData,
            congestionData
        });
    } catch (error) {
        res.status(500).json({ message: 'Server error fetching analytics' });
    }
});

module.exports = router;
