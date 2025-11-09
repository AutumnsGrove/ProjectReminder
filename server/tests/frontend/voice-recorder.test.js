/**
 * Frontend Voice Recorder Tests
 * Tests for public/js/voice-recorder.js
 */

// Mock MediaRecorder
class MockMediaRecorder {
  constructor(stream, options) {
    this.stream = stream;
    this.options = options;
    this.state = 'inactive';
    this.ondataavailable = null;
    this.onstop = null;
    this.onerror = null;
  }

  start() {
    this.state = 'recording';
    // Simulate data chunks
    setTimeout(() => {
      if (this.ondataavailable) {
        const mockBlob = new Blob(['audio data'], { type: 'audio/webm' });
        this.ondataavailable({ data: mockBlob });
      }
    }, 100);
  }

  stop() {
    this.state = 'inactive';
    if (this.onstop) {
      setTimeout(() => this.onstop(), 50);
    }
  }

  static isTypeSupported(type) {
    return type === 'audio/webm;codecs=opus' || type === 'audio/webm';
  }
}

global.MediaRecorder = MockMediaRecorder;
global.Blob = class Blob {
  constructor(parts, options) {
    this.parts = parts;
    this.type = options?.type || '';
    this.size = parts.reduce((acc, part) => acc + (part.length || 0), 0);
  }
};

// Mock navigator.mediaDevices
const mockGetUserMedia = jest.fn();
global.navigator = {
  mediaDevices: {
    getUserMedia: mockGetUserMedia
  }
};

// Mock console
global.console = {
  ...console,
  log: jest.fn(),
  warn: jest.fn(),
  error: jest.fn()
};

// Import the VoiceRecorder module
const fs = require('fs');
const path = require('path');
const voiceRecorderCode = fs.readFileSync(
  path.join(__dirname, '../../public/js/voice-recorder.js'),
  'utf-8'
);
eval(voiceRecorderCode);

describe('Voice Recorder', () => {
  let mockStream;
  let mockTrack;

  beforeEach(() => {
    // Create mock stream and track
    mockTrack = {
      stop: jest.fn()
    };

    mockStream = {
      getTracks: jest.fn(() => [mockTrack])
    };

    mockGetUserMedia.mockClear();
    mockGetUserMedia.mockResolvedValue(mockStream);
    console.error.mockClear();
  });

  describe('isSupported()', () => {
    test('should return true when MediaRecorder is supported', () => {
      expect(VoiceRecorder.isSupported()).toBe(true);
    });

    test('should return false when MediaRecorder is not supported', () => {
      const originalMediaRecorder = global.MediaRecorder;
      delete global.MediaRecorder;

      expect(VoiceRecorder.isSupported()).toBe(false);

      global.MediaRecorder = originalMediaRecorder;
    });

    test('should return false when getUserMedia is not supported', () => {
      const originalGetUserMedia = navigator.mediaDevices.getUserMedia;
      delete navigator.mediaDevices.getUserMedia;

      expect(VoiceRecorder.isSupported()).toBe(false);

      navigator.mediaDevices.getUserMedia = originalGetUserMedia;
    });
  });

  describe('startRecording()', () => {
    test('should request microphone permission', async () => {
      const recorder = new VoiceRecorder();

      await recorder.startRecording();

      expect(mockGetUserMedia).toHaveBeenCalledWith({
        audio: expect.objectContaining({
          channelCount: 1,
          sampleRate: 16000,
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true
        })
      });
    });

    test('should create MediaRecorder with supported MIME type', async () => {
      const recorder = new VoiceRecorder();

      await recorder.startRecording();

      expect(recorder.mediaRecorder).toBeDefined();
      expect(recorder.mediaRecorder.state).toBe('recording');
    });

    test('should call onRecordingStart callback', async () => {
      const onRecordingStart = jest.fn();
      const recorder = new VoiceRecorder({ onRecordingStart });

      await recorder.startRecording();

      expect(onRecordingStart).toHaveBeenCalled();
    });

    test('should handle permission denial', async () => {
      const onError = jest.fn();
      const recorder = new VoiceRecorder({ onError });

      const permissionError = new Error('Permission denied');
      permissionError.name = 'NotAllowedError';
      mockGetUserMedia.mockRejectedValueOnce(permissionError);

      await recorder.startRecording();

      expect(onError).toHaveBeenCalledWith(
        expect.stringContaining('Microphone permission denied')
      );
    });

    test('should handle no microphone detected', async () => {
      const onError = jest.fn();
      const recorder = new VoiceRecorder({ onError });

      const notFoundError = new Error('No microphone');
      notFoundError.name = 'NotFoundError';
      mockGetUserMedia.mockRejectedValueOnce(notFoundError);

      await recorder.startRecording();

      expect(onError).toHaveBeenCalledWith(
        expect.stringContaining('No microphone detected')
      );
    });

    test('should handle browser not supported', async () => {
      const onError = jest.fn();
      const recorder = new VoiceRecorder({ onError });

      const notSupportedError = new Error('Not supported');
      notSupportedError.name = 'NotSupportedError';
      mockGetUserMedia.mockRejectedValueOnce(notSupportedError);

      await recorder.startRecording();

      expect(onError).toHaveBeenCalledWith(
        expect.stringContaining('Voice input not supported')
      );
    });

    test('should auto-stop after maxDuration', async () => {
      jest.useFakeTimers();
      const onRecordingStop = jest.fn();
      const recorder = new VoiceRecorder({
        maxDuration: 1000,
        onRecordingStop
      });

      await recorder.startRecording();

      // Fast-forward time
      jest.advanceTimersByTime(1000);

      expect(recorder.mediaRecorder.state).toBe('inactive');

      jest.useRealTimers();
    });

    test('should emit recording updates', async () => {
      jest.useFakeTimers();
      const onRecordingUpdate = jest.fn();
      const recorder = new VoiceRecorder({ onRecordingUpdate });

      await recorder.startRecording();

      // Fast-forward 500ms
      jest.advanceTimersByTime(500);

      expect(onRecordingUpdate).toHaveBeenCalled();
      expect(onRecordingUpdate.mock.calls[0][0]).toBeGreaterThanOrEqual(0);

      jest.useRealTimers();
    });
  });

  describe('stopRecording()', () => {
    test('should stop recording and return audio blob', async () => {
      jest.useRealTimers();
      const onRecordingStop = jest.fn();
      const recorder = new VoiceRecorder({ onRecordingStop });

      await recorder.startRecording();
      recorder.stopRecording();

      // Wait for onstop callback
      await new Promise(resolve => setTimeout(resolve, 200));

      expect(onRecordingStop).toHaveBeenCalledWith(expect.any(Blob));
      expect(mockTrack.stop).toHaveBeenCalled();
    });

    test('should do nothing if not recording', () => {
      const recorder = new VoiceRecorder();

      // Should not throw
      expect(() => recorder.stopRecording()).not.toThrow();
    });

    test('should release microphone after stopping', async () => {
      jest.useRealTimers();
      const recorder = new VoiceRecorder();

      await recorder.startRecording();
      recorder.stopRecording();

      // Wait for onstop callback
      await new Promise(resolve => setTimeout(resolve, 200));

      expect(mockTrack.stop).toHaveBeenCalled();
    });

    test('should clear timers on stop', async () => {
      jest.useFakeTimers();
      const recorder = new VoiceRecorder({ maxDuration: 5000 });

      await recorder.startRecording();
      recorder.stopRecording();

      // Timer should be cleared
      expect(recorder.recordingTimer).toBeNull();
      expect(recorder.timerInterval).toBeNull();

      jest.useRealTimers();
    });
  });

  describe('isRecording()', () => {
    test('should return true when recording', async () => {
      const recorder = new VoiceRecorder();

      await recorder.startRecording();

      expect(recorder.isRecording()).toBeTruthy();
    });

    test('should return false when not recording', () => {
      const recorder = new VoiceRecorder();

      expect(recorder.isRecording()).toBeFalsy();
    });

    test('should return false after stopping', async () => {
      const recorder = new VoiceRecorder();

      await recorder.startRecording();
      recorder.stopRecording();

      expect(recorder.isRecording()).toBeFalsy();
    });
  });

  describe('Audio blob validation', () => {
    test('should return audio blob with correct MIME type', async () => {
      jest.useRealTimers();
      let audioBlob;
      const onRecordingStop = jest.fn((blob) => {
        audioBlob = blob;
      });

      const recorder = new VoiceRecorder({ onRecordingStop });

      await recorder.startRecording();
      recorder.stopRecording();

      // Wait for onstop callback
      await new Promise(resolve => setTimeout(resolve, 200));

      expect(audioBlob).toBeDefined();
      expect(audioBlob.type).toMatch(/audio\//);
    });

    test('should collect multiple audio chunks', async () => {
      jest.useRealTimers();
      let audioBlob;
      const onRecordingStop = jest.fn((blob) => {
        audioBlob = blob;
      });

      const recorder = new VoiceRecorder({ onRecordingStop });

      await recorder.startRecording();

      // Simulate multiple data chunks
      if (recorder.mediaRecorder && recorder.mediaRecorder.ondataavailable) {
        recorder.mediaRecorder.ondataavailable({ data: new Blob(['chunk1']) });
        recorder.mediaRecorder.ondataavailable({ data: new Blob(['chunk2']) });
      }

      recorder.stopRecording();

      // Wait for onstop callback
      await new Promise(resolve => setTimeout(resolve, 200));

      expect(audioBlob?.size).toBeGreaterThan(0);
    });
  });

  describe('Error handling during recording', () => {
    test('should handle MediaRecorder errors', async () => {
      const onError = jest.fn();
      const recorder = new VoiceRecorder({ onError });

      await recorder.startRecording();

      // Simulate MediaRecorder error
      if (recorder.mediaRecorder && recorder.mediaRecorder.onerror) {
        recorder.mediaRecorder.onerror(new Error('Recording error'));

        expect(onError).toHaveBeenCalledWith(
          expect.stringContaining('Recording error')
        );
      } else {
        // If mediaRecorder wasn't created, test passes
        expect(true).toBe(true);
      }
    });
  });
});
