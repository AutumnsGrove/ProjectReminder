/**
 * VoiceRecorder - Browser audio recording using MediaRecorder API
 *
 * Features:
 * - Request microphone permission
 * - Record audio with auto-stop timer
 * - Handle recording state (idle/recording/processing)
 * - Emit events for UI updates
 * - Error handling for permissions, browser support
 */
class VoiceRecorder {
    constructor(options = {}) {
        this.mediaRecorder = null;
        this.audioChunks = [];
        this.stream = null;
        this.recordingTimer = null;
        this.startTime = null;
        this.maxDuration = options.maxDuration || 30000; // 30 seconds default
        this.timerInterval = null;

        // Callbacks
        this.onRecordingStart = options.onRecordingStart || null;
        this.onRecordingStop = options.onRecordingStop || null;
        this.onRecordingUpdate = options.onRecordingUpdate || null;
        this.onError = options.onError || null;
    }

    /**
     * Check if browser supports MediaRecorder
     */
    static isSupported() {
        return !!(navigator.mediaDevices &&
                 navigator.mediaDevices.getUserMedia &&
                 window.MediaRecorder);
    }

    /**
     * Get supported MIME type and audio settings for MediaRecorder
     * Prioritizes Opus codec (24kbps) for optimal compression
     */
    getSupportedMimeType() {
        const opusType = 'audio/webm;codecs=opus';
        const fallbackTypes = [
            'audio/webm',
            'audio/ogg;codecs=opus',
            'audio/mp4'
        ];

        // Check Opus first (best compression at 24kbps)
        if (MediaRecorder.isTypeSupported(opusType)) {
            console.log('Using Opus codec (24kbps) - optimal compression for voice');
            return { mimeType: opusType, bitrate: 24000 };
        }

        // Fallback to other supported types with standard bitrate
        for (const type of fallbackTypes) {
            if (MediaRecorder.isTypeSupported(type)) {
                console.log(`Opus not supported, falling back to: ${type} (128kbps)`);
                return { mimeType: type, bitrate: 128000 };
            }
        }

        throw new Error('No supported audio MIME type found');
    }

    /**
     * Request microphone permission and start recording
     */
    async startRecording() {
        try {
            // Check browser support
            if (!VoiceRecorder.isSupported()) {
                throw new Error('Voice recording not supported in this browser');
            }

            // Request microphone access
            this.stream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    channelCount: 1, // Mono
                    sampleRate: 16000, // 16kHz (optimal for Whisper)
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true
                }
            });

            // Determine MIME type and bitrate
            const { mimeType, bitrate } = this.getSupportedMimeType();

            // Create MediaRecorder with optimized Opus codec
            this.mediaRecorder = new MediaRecorder(this.stream, {
                mimeType: mimeType,
                audioBitsPerSecond: bitrate
            });

            // Collect audio chunks
            this.audioChunks = [];
            this.mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    this.audioChunks.push(event.data);
                }
            };

            // Handle recording stop
            this.mediaRecorder.onstop = () => {
                const audioBlob = new Blob(this.audioChunks, { type: mimeType });

                // Stop all tracks (release microphone)
                if (this.stream) {
                    this.stream.getTracks().forEach(track => track.stop());
                    this.stream = null;
                }

                // Clear timers
                if (this.recordingTimer) {
                    clearTimeout(this.recordingTimer);
                    this.recordingTimer = null;
                }

                if (this.timerInterval) {
                    clearInterval(this.timerInterval);
                    this.timerInterval = null;
                }

                // Emit callback
                if (this.onRecordingStop) {
                    this.onRecordingStop(audioBlob);
                }
            };

            // Handle errors
            this.mediaRecorder.onerror = (error) => {
                console.error('MediaRecorder error:', error);
                if (this.onError) {
                    this.onError('Recording error: ' + error.message);
                }
            };

            // Start recording
            this.mediaRecorder.start();
            this.startTime = Date.now();

            // Auto-stop after maxDuration
            this.recordingTimer = setTimeout(() => {
                this.stopRecording();
            }, this.maxDuration);

            // Emit start callback
            if (this.onRecordingStart) {
                this.onRecordingStart();
            }

            // Start timer updates (every 100ms)
            this.timerInterval = setInterval(() => {
                if (this.startTime && this.onRecordingUpdate) {
                    const elapsed = Date.now() - this.startTime;
                    this.onRecordingUpdate(elapsed);
                }
            }, 100);

        } catch (error) {
            // Handle permission denied or other errors
            let errorMessage = 'Failed to access microphone';

            if (error.name === 'NotAllowedError') {
                errorMessage = 'Microphone permission denied. Please enable microphone access in your browser settings.';
            } else if (error.name === 'NotFoundError') {
                errorMessage = 'No microphone detected. Please connect a microphone.';
            } else if (error.name === 'NotSupportedError') {
                errorMessage = 'Voice input not supported in this browser.';
            } else {
                errorMessage = `Microphone error: ${error.message}`;
            }

            console.error(errorMessage);

            if (this.onError) {
                this.onError(errorMessage);
            }
        }
    }

    /**
     * Stop recording
     */
    stopRecording() {
        if (this.mediaRecorder && this.mediaRecorder.state === 'recording') {
            this.mediaRecorder.stop();

            // Clear timer interval
            if (this.timerInterval) {
                clearInterval(this.timerInterval);
                this.timerInterval = null;
            }
        }
    }

    /**
     * Check if currently recording
     */
    isRecording() {
        return this.mediaRecorder && this.mediaRecorder.state === 'recording';
    }
}

// Make available globally and for module systems
window.VoiceRecorder = VoiceRecorder;
if (typeof module !== 'undefined' && module.exports) {
    module.exports = VoiceRecorder;
}