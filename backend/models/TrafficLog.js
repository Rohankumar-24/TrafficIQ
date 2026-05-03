const mongoose = require('mongoose');

const trafficLogSchema = new mongoose.Schema({
    userId: {
        type: mongoose.Schema.Types.ObjectId,
        ref: 'User',
        required: true
    },
    timestamp: {
        type: Date,
        default: Date.now
    },
    lane1: {
        name: String,
        vehicleCount: Number,
        congestionLevel: String, // Low, Medium, High
        signal: String // Red, Yellow, Green
    },
    lane2: {
        name: String,
        vehicleCount: Number,
        congestionLevel: String,
        signal: String
    },
    emergencyAlert: {
        type: Boolean,
        default: false
    }
});

module.exports = mongoose.model('TrafficLog', trafficLogSchema);
