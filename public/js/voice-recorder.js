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
     * Get supported MIME type for MediaRecorder
     */
    getSupportedMimeType() {
        const types = [
            'audio/webm;codecs=opus',
            'audio/webm',
            'audio/ogg;codecs=opus',
            'audio/mp4'
        ];

        for (const type of types) {
            if (MediaRecorder.isTypeSupported(type)) {
                return type;
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

            // Determine MIME type
            const mimeType = this.getSupportedMimeType();

            // Create MediaRecorder
            this.mediaRecorder = new MediaRecorder(this.stream, {
                mimeType: mimeType,
                audioBitsPerSecond: 128000 // 128kbps
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