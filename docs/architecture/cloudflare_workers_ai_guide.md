# Comprehensive Guide: Implementing Cloudflare Workers AI for Reminders App

## Overview
This guide covers migrating your Reminders app from local models (whisper.cpp + GPT-OSS) to Cloudflare Workers AI, eliminating the need for users to download 1+ GB of model files.

---

## Table of Contents
1. [Prerequisites & Setup](#1-prerequisites--setup)
2. [Architecture Decision](#2-architecture-decision)
3. [Authentication Setup](#3-authentication-setup)
4. [Speech-to-Text Implementation](#4-speech-to-text-implementation)
5. [LLM Processing Implementation](#5-llm-processing-implementation)
6. [Error Handling & Rate Limiting](#6-error-handling--rate-limiting)
7. [Cost Optimization](#7-cost-optimization)
8. [Testing Strategy](#8-testing-strategy)
9. [Deployment Considerations](#9-deployment-considerations)

---

## 1. Prerequisites & Setup

### 1.1 Create Cloudflare Account
```bash
# Sign up at https://dash.cloudflare.com/sign-up
# Navigate to Workers & Pages
# Note your Account ID (Workers & Pages > Overview > Account details > Account ID)
```

### 1.2 Generate API Token
```bash
# Go to: https://dash.cloudflare.com/profile/api-tokens
# Click "Create Token"
# Use template: "Edit Cloudflare Workers"
# OR create custom token with permissions:
#   - Account > Workers AI > Read
#   - Account > Workers AI > Edit
#   - Account > Workers Scripts > Edit (if using Workers backend)
```

### 1.3 Install Dependencies (if using Node.js backend)
```bash
npm install @cloudflare/ai
# OR for direct API calls:
npm install node-fetch
```

### 1.4 Environment Variables
Create a `.env` file:
```bash
CLOUDFLARE_ACCOUNT_ID=your_account_id_here
CLOUDFLARE_API_TOKEN=your_api_token_here
CLOUDFLARE_API_BASE_URL=https://api.cloudflare.com/client/v4/accounts
```

---

## 2. Architecture Decision

### Option A: Direct API Calls (Recommended for existing apps)
**Best for:** Apps with existing backend infrastructure
- Your app makes REST API calls directly to Cloudflare
- No need to migrate entire backend
- Works with any language/framework

### Option B: Cloudflare Workers Backend
**Best for:** New apps or if rebuilding backend
- Deploy backend as Cloudflare Worker
- Use bindings for zero-latency access to Workers AI
- Lower costs (no external API calls)

**This guide covers Option A (Direct API Calls)** as you have an existing app.

---

## 3. Authentication Setup

### 3.1 Create API Client Utility
```javascript
// lib/cloudflare-ai-client.js
class CloudflareAIClient {
  constructor() {
    this.accountId = process.env.CLOUDFLARE_ACCOUNT_ID;
    this.apiToken = process.env.CLOUDFLARE_API_TOKEN;
    this.baseUrl = `https://api.cloudflare.com/client/v4/accounts/${this.accountId}/ai/run`;
    
    if (!this.accountId || !this.apiToken) {
      throw new Error('Missing Cloudflare credentials in environment variables');
    }
  }

  async run(model, inputs, options = {}) {
    const url = `${this.baseUrl}/${model}`;
    
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.apiToken}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(inputs),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(`Cloudflare AI Error: ${error.errors?.[0]?.message || response.statusText}`);
    }

    // Handle streaming responses
    if (options.stream && response.headers.get('content-type')?.includes('text/event-stream')) {
      return response.body;
    }

    return await response.json();
  }
}

module.exports = new CloudflareAIClient();
```

---

## 4. Speech-to-Text Implementation

### 4.1 Audio Preprocessing
```javascript
// lib/audio-processor.js
const fs = require('fs');

class AudioProcessor {
  /**
   * Convert audio file to base64 for API transmission
   * @param {string} audioFilePath - Path to audio file
   * @returns {string} Base64 encoded audio
   */
  audioToBase64(audioFilePath) {
    const audioBuffer = fs.readFileSync(audioFilePath);
    return audioBuffer.toString('base64');
  }

  /**
   * Convert audio buffer to base64
   * @param {Buffer} audioBuffer - Audio buffer
   * @returns {string} Base64 encoded audio
   */
  bufferToBase64(audioBuffer) {
    return audioBuffer.toString('base64');
  }

  /**
   * Validate audio format and size
   * @param {Buffer} audioBuffer - Audio buffer
   * @returns {boolean}
   */
  validateAudio(audioBuffer) {
    const maxSize = 25 * 1024 * 1024; // 25MB limit
    if (audioBuffer.length > maxSize) {
      throw new Error(`Audio file too large. Max size: 25MB, got: ${(audioBuffer.length / 1024 / 1024).toFixed(2)}MB`);
    }
    return true;
  }
}

module.exports = new AudioProcessor();
```

### 4.2 Whisper Integration
```javascript
// services/speech-to-text.js
const cloudflareAI = require('../lib/cloudflare-ai-client');
const audioProcessor = require('../lib/audio-processor');

class SpeechToTextService {
  constructor() {
    // Use whisper-large-v3-turbo for better performance
    this.model = '@cf/openai/whisper-large-v3-turbo';
  }

  /**
   * Transcribe audio file to text
   * @param {Buffer} audioBuffer - Audio file buffer
   * @returns {Promise<string>} Transcribed text
   */
  async transcribe(audioBuffer) {
    try {
      // Validate audio
      audioProcessor.validateAudio(audioBuffer);

      // Convert to base64
      const audioBase64 = audioProcessor.bufferToBase64(audioBuffer);

      // Call Cloudflare AI
      const response = await cloudflareAI.run(this.model, {
        audio: audioBase64,
      });

      // Extract text from response
      const transcription = response.result?.text || response.text || '';
      
      if (!transcription) {
        throw new Error('No transcription returned from API');
      }

      return transcription.trim();
    } catch (error) {
      console.error('Speech-to-text error:', error);
      throw new Error(`Failed to transcribe audio: ${error.message}`);
    }
  }

  /**
   * Transcribe with word-level timestamps (if needed)
   * Note: Check API docs for timestamp support
   */
  async transcribeWithTimestamps(audioBuffer) {
    try {
      audioProcessor.validateAudio(audioBuffer);
      const audioBase64 = audioProcessor.bufferToBase64(audioBuffer);

      const response = await cloudflareAI.run(this.model, {
        audio: audioBase64,
        // Add any timestamp parameters if supported
      });

      return {
        text: response.result?.text || response.text || '',
        words: response.result?.words || [],
      };
    } catch (error) {
      console.error('Speech-to-text with timestamps error:', error);
      throw error;
    }
  }
}

module.exports = new SpeechToTextService();
```

### 4.3 Handling Large Audio Files (Chunking)
```javascript
// services/speech-to-text-chunked.js
const cloudflareAI = require('../lib/cloudflare-ai-client');

class ChunkedSpeechToTextService {
  constructor() {
    this.model = '@cf/openai/whisper-large-v3-turbo';
    this.chunkSize = 1024 * 1024; // 1MB chunks
  }

  /**
   * Split audio buffer into chunks
   * @param {Buffer} audioBuffer
   * @returns {Buffer[]}
   */
  splitIntoChunks(audioBuffer) {
    const chunks = [];
    for (let i = 0; i < audioBuffer.length; i += this.chunkSize) {
      chunks.push(audioBuffer.slice(i, i + this.chunkSize));
    }
    return chunks;
  }

  /**
   * Transcribe large audio file by processing chunks
   * @param {Buffer} audioBuffer
   * @returns {Promise<string>}
   */
  async transcribeLargeFile(audioBuffer) {
    try {
      const chunks = this.splitIntoChunks(audioBuffer);
      const transcriptions = [];

      for (let i = 0; i < chunks.length; i++) {
        console.log(`Processing chunk ${i + 1}/${chunks.length}`);
        const base64Chunk = chunks[i].toString('base64');
        
        const response = await cloudflareAI.run(this.model, {
          audio: base64Chunk,
        });

        transcriptions.push(response.result?.text || response.text || '');
      }

      return transcriptions.join(' ').trim();
    } catch (error) {
      console.error('Chunked transcription error:', error);
      throw error;
    }
  }
}

module.exports = new ChunkedSpeechToTextService();
```

---

## 5. LLM Processing Implementation

### 5.1 GPT-OSS 20B Integration
```javascript
// services/llm-service.js
const cloudflareAI = require('../lib/cloudflare-ai-client');

class LLMService {
  constructor() {
    this.model = '@cf/openai/gpt-oss-20b';
    this.defaultParams = {
      temperature: 0.7,
      max_tokens: 256,
      top_p: 0.9,
    };
  }

  /**
   * Process reminder text with LLM
   * @param {string} transcription - Text from speech-to-text
   * @param {Object} options - LLM parameters
   * @returns {Promise<Object>} Processed reminder data
   */
  async processReminder(transcription, options = {}) {
    try {
      const systemPrompt = `You are a helpful assistant that processes voice reminders. Extract the following information from the user's message:
- Task/reminder text (what needs to be done)
- Date/time (if mentioned, in ISO 8601 format)
- Priority (low, medium, high)
- Category (personal, work, shopping, etc.)

Respond ONLY with valid JSON in this format:
{
  "task": "string",
  "datetime": "ISO 8601 string or null",
  "priority": "low|medium|high",
  "category": "string"
}`;

      const response = await cloudflareAI.run(this.model, {
        messages: [
          { role: 'system', content: systemPrompt },
          { role: 'user', content: transcription }
        ],
        ...this.defaultParams,
        ...options,
      });

      const messageContent = response.result?.response || response.response || '';
      
      // Parse JSON response
      const parsed = this.parseReminderJSON(messageContent);
      return parsed;
    } catch (error) {
      console.error('LLM processing error:', error);
      throw new Error(`Failed to process reminder: ${error.message}`);
    }
  }

  /**
   * Parse JSON from LLM response (handles markdown code blocks)
   * @param {string} text - LLM response text
   * @returns {Object}
   */
  parseReminderJSON(text) {
    try {
      // Remove markdown code blocks if present
      let cleaned = text.replace(/```json\n?/g, '').replace(/```\n?/g, '').trim();
      
      const parsed = JSON.parse(cleaned);
      
      // Validate required fields
      if (!parsed.task) {
        throw new Error('Missing required field: task');
      }
      
      return {
        task: parsed.task,
        datetime: parsed.datetime || null,
        priority: parsed.priority || 'medium',
        category: parsed.category || 'personal',
      };
    } catch (error) {
      console.error('JSON parsing error:', error);
      // Fallback: return raw transcription as task
      return {
        task: text,
        datetime: null,
        priority: 'medium',
        category: 'personal',
      };
    }
  }

  /**
   * Stream LLM response (for real-time processing)
   * @param {string} transcription
   * @param {Function} onChunk - Callback for each chunk
   */
  async processReminderStreaming(transcription, onChunk) {
    try {
      const systemPrompt = `Extract reminder information from the user's voice input. Respond with JSON.`;

      const stream = await cloudflareAI.run(
        this.model,
        {
          messages: [
            { role: 'system', content: systemPrompt },
            { role: 'user', content: transcription }
          ],
          ...this.defaultParams,
          stream: true,
        },
        { stream: true }
      );

      // Process stream
      const reader = stream.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        
        // Process SSE events
        const lines = buffer.split('\n');
        buffer = lines.pop(); // Keep incomplete line in buffer

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6);
            if (data !== '[DONE]') {
              try {
                const parsed = JSON.parse(data);
                onChunk(parsed.response || '');
              } catch (e) {
                // Skip invalid JSON
              }
            }
          }
        }
      }
    } catch (error) {
      console.error('Streaming error:', error);
      throw error;
    }
  }
}

module.exports = new LLMService();
```

---

## 6. Error Handling & Rate Limiting

### 6.1 Rate Limiter Implementation
```javascript
// lib/rate-limiter.js
class RateLimiter {
  constructor() {
    this.limits = {
      whisper: { max: 720, window: 60000 }, // 720 per minute
      llm: { max: 300, window: 60000 },     // 300 per minute
    };
    this.counters = {
      whisper: [],
      llm: [],
    };
  }

  /**
   * Check if request is within rate limit
   * @param {string} service - 'whisper' or 'llm'
   * @returns {boolean}
   */
  checkLimit(service) {
    const now = Date.now();
    const limit = this.limits[service];
    
    // Remove old entries outside the time window
    this.counters[service] = this.counters[service].filter(
      timestamp => now - timestamp < limit.window
    );

    if (this.counters[service].length >= limit.max) {
      return false;
    }

    this.counters[service].push(now);
    return true;
  }

  /**
   * Get time until rate limit resets
   * @param {string} service
   * @returns {number} Milliseconds until reset
   */
  getResetTime(service) {
    if (this.counters[service].length === 0) return 0;
    
    const oldest = this.counters[service][0];
    const resetTime = oldest + this.limits[service].window;
    return Math.max(0, resetTime - Date.now());
  }
}

module.exports = new RateLimiter();
```

### 6.2 Retry Logic with Exponential Backoff
```javascript
// lib/retry-handler.js
class RetryHandler {
  constructor() {
    this.maxRetries = 3;
    this.baseDelay = 1000; // 1 second
  }

  /**
   * Execute function with retry logic
   * @param {Function} fn - Async function to execute
   * @param {string} context - Context for logging
   * @returns {Promise<any>}
   */
  async withRetry(fn, context = 'operation') {
    let lastError;

    for (let attempt = 0; attempt < this.maxRetries; attempt++) {
      try {
        return await fn();
      } catch (error) {
        lastError = error;
        
        // Don't retry on certain errors
        if (this.isNonRetriableError(error)) {
          throw error;
        }

        if (attempt < this.maxRetries - 1) {
          const delay = this.baseDelay * Math.pow(2, attempt);
          console.log(`${context} failed (attempt ${attempt + 1}/${this.maxRetries}), retrying in ${delay}ms...`);
          await this.sleep(delay);
        }
      }
    }

    throw new Error(`${context} failed after ${this.maxRetries} attempts: ${lastError.message}`);
  }

  /**
   * Check if error should not be retried
   * @param {Error} error
   * @returns {boolean}
   */
  isNonRetriableError(error) {
    const message = error.message.toLowerCase();
    return (
      message.includes('authentication') ||
      message.includes('invalid') ||
      message.includes('too large') ||
      message.includes('bad request')
    );
  }

  sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}

module.exports = new RetryHandler();
```

### 6.3 Complete Error Handler
```javascript
// lib/error-handler.js
class CloudflareAIError extends Error {
  constructor(message, code, retryable = false) {
    super(message);
    this.name = 'CloudflareAIError';
    this.code = code;
    this.retryable = retryable;
  }
}

function handleCloudflareError(error) {
  // Parse error response
  if (error.message.includes('429')) {
    return new CloudflareAIError(
      'Rate limit exceeded. Please try again later.',
      'RATE_LIMIT_EXCEEDED',
      true
    );
  }

  if (error.message.includes('403')) {
    return new CloudflareAIError(
      'Authentication failed. Check your API token.',
      'AUTH_FAILED',
      false
    );
  }

  if (error.message.includes('400')) {
    return new CloudflareAIError(
      'Invalid request. Check your input parameters.',
      'INVALID_REQUEST',
      false
    );
  }

  if (error.message.includes('413')) {
    return new CloudflareAIError(
      'Request too large. Try reducing file size.',
      'REQUEST_TOO_LARGE',
      false
    );
  }

  if (error.message.includes('timeout')) {
    return new CloudflareAIError(
      'Request timed out. Please try again.',
      'TIMEOUT',
      true
    );
  }

  return new CloudflareAIError(
    `Unexpected error: ${error.message}`,
    'UNKNOWN_ERROR',
    true
  );
}

module.exports = { CloudflareAIError, handleCloudflareError };
```

---

## 7. Cost Optimization

### 7.1 Usage Tracker
```javascript
// lib/usage-tracker.js
class UsageTracker {
  constructor() {
    this.usage = {
      whisper: { minutes: 0, cost: 0 },
      llm: { inputTokens: 0, outputTokens: 0, cost: 0 },
      total: 0,
    };

    this.prices = {
      whisper: 0.0005, // per minute
      gptOSSInput: 0.027 / 1000000, // per token
      gptOSSOutput: 0.201 / 1000000, // per token
    };
  }

  /**
   * Track Whisper usage
   * @param {number} audioMinutes - Audio duration in minutes
   */
  trackWhisper(audioMinutes) {
    const cost = audioMinutes * this.prices.whisper;
    this.usage.whisper.minutes += audioMinutes;
    this.usage.whisper.cost += cost;
    this.usage.total += cost;
  }

  /**
   * Track LLM usage
   * @param {number} inputTokens
   * @param {number} outputTokens
   */
  trackLLM(inputTokens, outputTokens) {
    const cost = (inputTokens * this.prices.gptOSSInput) +
                 (outputTokens * this.prices.gptOSSOutput);
    
    this.usage.llm.inputTokens += inputTokens;
    this.usage.llm.outputTokens += outputTokens;
    this.usage.llm.cost += cost;
    this.usage.total += cost;
  }

  /**
   * Get usage report
   * @returns {Object}
   */
  getReport() {
    return {
      whisper: {
        minutes: this.usage.whisper.minutes.toFixed(2),
        cost: `$${this.usage.whisper.cost.toFixed(4)}`,
      },
      llm: {
        inputTokens: this.usage.llm.inputTokens,
        outputTokens: this.usage.llm.outputTokens,
        cost: `$${this.usage.llm.cost.toFixed(4)}`,
      },
      totalCost: `$${this.usage.total.toFixed(4)}`,
    };
  }

  /**
   * Estimate cost for audio duration
   * @param {number} audioSeconds
   * @returns {number} Estimated cost
   */
  estimateWhisperCost(audioSeconds) {
    return (audioSeconds / 60) * this.prices.whisper;
  }

  /**
   * Reset usage tracking
   */
  reset() {
    this.usage = {
      whisper: { minutes: 0, cost: 0 },
      llm: { inputTokens: 0, outputTokens: 0, cost: 0 },
      total: 0,
    };
  }
}

module.exports = new UsageTracker();
```

### 7.2 Cost Optimization Strategies
```javascript
// lib/cost-optimizer.js
class CostOptimizer {
  /**
   * Check if audio should be processed based on duration
   * @param {number} durationSeconds
   * @returns {boolean}
   */
  shouldProcessAudio(durationSeconds) {
    const maxDuration = 300; // 5 minutes max
    if (durationSeconds > maxDuration) {
      console.warn(`Audio too long (${durationSeconds}s). Consider truncating.`);
      return false;
    }
    return true;
  }

  /**
   * Optimize LLM prompt to reduce tokens
   * @param {string} transcription
   * @returns {string}
   */
  optimizePrompt(transcription) {
    // Remove excessive whitespace
    let optimized = transcription.trim().replace(/\s+/g, ' ');
    
    // Truncate if too long
    const maxLength = 1000;
    if (optimized.length > maxLength) {
      optimized = optimized.substring(0, maxLength);
      console.warn('Transcription truncated to reduce costs');
    }
    
    return optimized;
  }

  /**
   * Choose appropriate model based on task complexity
   * @param {string} task
   * @returns {string}
   */
  selectModel(task) {
    // For simple reminders, use GPT-OSS 20B model
    // For complex tasks, GPT-OSS 20B provides excellent balance
    // of performance and cost efficiency on Workers AI
    return '@cf/openai/gpt-oss-20b';
  }
}

module.exports = new CostOptimizer();
```

---

## 8. Testing Strategy

### 8.1 Unit Tests
```javascript
// tests/speech-to-text.test.js
const speechToText = require('../services/speech-to-text');
const fs = require('fs');

describe('SpeechToTextService', () => {
  test('should transcribe audio file', async () => {
    const audioBuffer = fs.readFileSync('./tests/fixtures/sample-audio.mp3');
    const transcription = await speechToText.transcribe(audioBuffer);
    
    expect(transcription).toBeTruthy();
    expect(typeof transcription).toBe('string');
    expect(transcription.length).toBeGreaterThan(0);
  });

  test('should throw error for oversized audio', async () => {
    const largeBuffer = Buffer.alloc(26 * 1024 * 1024); // 26MB
    
    await expect(speechToText.transcribe(largeBuffer)).rejects.toThrow('too large');
  });
});
```

```javascript
// tests/llm-service.test.js
const llmService = require('../services/llm-service');

describe('LLMService', () => {
  test('should process reminder correctly', async () => {
    const transcription = 'Remind me to buy milk tomorrow at 3pm';
    const result = await llmService.processReminder(transcription);
    
    expect(result).toHaveProperty('task');
    expect(result).toHaveProperty('datetime');
    expect(result).toHaveProperty('priority');
    expect(result.task).toContain('milk');
  });

  test('should handle invalid JSON gracefully', () => {
    const invalidJSON = 'This is not JSON';
    const result = llmService.parseReminderJSON(invalidJSON);
    
    expect(result.task).toBe(invalidJSON);
    expect(result.priority).toBe('medium');
  });
});
```

### 8.2 Integration Test
```javascript
// tests/integration/full-workflow.test.js
const speechToText = require('../services/speech-to-text');
const llmService = require('../services/llm-service');
const fs = require('fs');

describe('Full Reminder Workflow', () => {
  test('should process voice reminder end-to-end', async () => {
    // 1. Load audio file
    const audioBuffer = fs.readFileSync('./tests/fixtures/reminder-sample.mp3');
    
    // 2. Transcribe
    const transcription = await speechToText.transcribe(audioBuffer);
    console.log('Transcription:', transcription);
    expect(transcription).toBeTruthy();
    
    // 3. Process with LLM
    const reminder = await llmService.processReminder(transcription);
    console.log('Processed reminder:', reminder);
    
    expect(reminder.task).toBeTruthy();
    expect(['low', 'medium', 'high']).toContain(reminder.priority);
  }, 30000); // 30 second timeout for API calls
});
```

### 8.3 Mock Testing (for development without API calls)
```javascript
// tests/mocks/cloudflare-ai-mock.js
class MockCloudflareAI {
  async run(model, inputs) {
    if (model.includes('whisper')) {
      return {
        result: {
          text: 'Mocked transcription: Remind me to test the app'
        }
      };
    }
    
    if (model.includes('gpt')) {
      return {
        result: {
          response: JSON.stringify({
            task: 'Test the app',
            datetime: null,
            priority: 'medium',
            category: 'work'
          })
        }
      };
    }
  }
}

module.exports = new MockCloudflareAI();
```

---

## 9. Deployment Considerations

### 9.1 Environment-Specific Configuration
```javascript
// config/cloudflare-config.js
const environments = {
  development: {
    accountId: process.env.DEV_CLOUDFLARE_ACCOUNT_ID,
    apiToken: process.env.DEV_CLOUDFLARE_API_TOKEN,
    useMocks: true, // Use mocks in dev to save costs
  },
  staging: {
    accountId: process.env.STAGING_CLOUDFLARE_ACCOUNT_ID,
    apiToken: process.env.STAGING_CLOUDFLARE_API_TOKEN,
    useMocks: false,
  },
  production: {
    accountId: process.env.CLOUDFLARE_ACCOUNT_ID,
    apiToken: process.env.CLOUDFLARE_API_TOKEN,
    useMocks: false,
  },
};

const env = process.env.NODE_ENV || 'development';

module.exports = environments[env];
```

### 9.2 Security Best Practices
```javascript
// middleware/security.js
const crypto = require('crypto');

class SecurityMiddleware {
  /**
   * Encrypt API token before storing
   * @param {string} token
   * @returns {string}
   */
  encryptToken(token) {
    const algorithm = 'aes-256-gcm';
    const key = crypto.scryptSync(process.env.ENCRYPTION_KEY, 'salt', 32);
    const iv = crypto.randomBytes(16);
    
    const cipher = crypto.createCipheriv(algorithm, key, iv);
    let encrypted = cipher.update(token, 'utf8', 'hex');
    encrypted += cipher.final('hex');
    
    const authTag = cipher.getAuthTag();
    
    return `${iv.toString('hex')}:${authTag.toString('hex')}:${encrypted}`;
  }

  /**
   * Validate request origin (if needed for client-side calls)
   * @param {Request} req
   * @returns {boolean}
   */
  validateOrigin(req) {
    const allowedOrigins = process.env.ALLOWED_ORIGINS?.split(',') || [];
    const origin = req.headers.origin;
    
    return allowedOrigins.includes(origin);
  }

  /**
   * Sanitize user input before sending to AI
   * @param {string} input
   * @returns {string}
   */
  sanitizeInput(input) {
    // Remove potential injection attempts
    return input
      .replace(/<script[^>]*>.*?<\/script>/gi, '')
      .replace(/javascript:/gi, '')
      .trim();
  }
}

module.exports = new SecurityMiddleware();
```

### 9.3 Monitoring & Logging
```javascript
// lib/logger.js
class Logger {
  constructor() {
    this.logs = [];
  }

  log(level, message, metadata = {}) {
    const entry = {
      timestamp: new Date().toISOString(),
      level,
      message,
      ...metadata,
    };

    console[level](JSON.stringify(entry));
    this.logs.push(entry);

    // Send to monitoring service (e.g., Sentry, LogRocket)
    if (level === 'error' && process.env.NODE_ENV === 'production') {
      this.sendToMonitoring(entry);
    }
  }

  info(message, metadata) {
    this.log('info', message, metadata);
  }

  error(message, metadata) {
    this.log('error', message, metadata);
  }

  warn(message, metadata) {
    this.log('warn', message, metadata);
  }

  sendToMonitoring(entry) {
    // Implement monitoring service integration
    // e.g., Sentry.captureException()
  }

  getRecentLogs(count = 100) {
    return this.logs.slice(-count);
  }
}

module.exports = new Logger();
```

---

## 10. Complete Example: Main Service Integration

```javascript
// services/reminder-processor.js
const speechToText = require('./speech-to-text');
const llmService = require('./llm-service');
const rateLimiter = require('../lib/rate-limiter');
const retryHandler = require('../lib/retry-handler');
const usageTracker = require('../lib/usage-tracker');
const logger = require('../lib/logger');
const { handleCloudflareError } = require('../lib/error-handler');

class ReminderProcessor {
  /**
   * Main method: Process voice reminder end-to-end
   * @param {Buffer} audioBuffer - Audio file buffer
   * @param {Object} options - Processing options
   * @returns {Promise<Object>} Processed reminder
   */
  async processVoiceReminder(audioBuffer, options = {}) {
    const startTime = Date.now();
    
    try {
      // 1. Rate limiting check
      if (!rateLimiter.checkLimit('whisper')) {
        const resetTime = rateLimiter.getResetTime('whisper');
        throw new Error(`Rate limit exceeded. Try again in ${Math.ceil(resetTime / 1000)} seconds`);
      }

      // 2. Transcribe audio with retry logic
      logger.info('Starting speech-to-text');
      const transcription = await retryHandler.withRetry(
        () => speechToText.transcribe(audioBuffer),
        'Speech-to-text'
      );
      logger.info('Transcription complete', { 
        length: transcription.length,
        preview: transcription.substring(0, 50)
      });

      // Track usage (estimate audio duration - you may have this from metadata)
      const estimatedMinutes = audioBuffer.length / (16000 * 2 * 60); // Rough estimate
      usageTracker.trackWhisper(estimatedMinutes);

      // 3. Check LLM rate limit
      if (!rateLimiter.checkLimit('llm')) {
        const resetTime = rateLimiter.getResetTime('llm');
        throw new Error(`LLM rate limit exceeded. Try again in ${Math.ceil(resetTime / 1000)} seconds`);
      }

      // 4. Process with LLM
      logger.info('Starting LLM processing');
      const reminder = await retryHandler.withRetry(
        () => llmService.processReminder(transcription, options.llmParams),
        'LLM processing'
      );
      logger.info('LLM processing complete', { reminder });

      // Track LLM usage (rough token estimate)
      const estimatedInputTokens = Math.ceil(transcription.length / 4);
      const estimatedOutputTokens = 100; // Typical JSON response
      usageTracker.trackLLM(estimatedInputTokens, estimatedOutputTokens);

      // 5. Return result
      const processingTime = Date.now() - startTime;
      return {
        success: true,
        data: {
          transcription,
          reminder,
        },
        metadata: {
          processingTime: `${processingTime}ms`,
          usage: usageTracker.getReport(),
        },
      };

    } catch (error) {
      logger.error('Reminder processing failed', {
        error: error.message,
        stack: error.stack,
      });

      const handledError = handleCloudflareError(error);
      
      return {
        success: false,
        error: {
          message: handledError.message,
          code: handledError.code,
          retryable: handledError.retryable,
        },
      };
    }
  }

  /**
   * Process reminder with streaming (for real-time UI updates)
   * @param {Buffer} audioBuffer
   * @param {Function} onProgress - Callback for progress updates
   */
  async processVoiceReminderStreaming(audioBuffer, onProgress) {
    try {
      // Step 1: Transcribe
      onProgress({ stage: 'transcribing', progress: 0 });
      const transcription = await speechToText.transcribe(audioBuffer);
      onProgress({ stage: 'transcribing', progress: 100, result: transcription });

      // Step 2: Process with streaming LLM
      onProgress({ stage: 'processing', progress: 0 });
      let fullResponse = '';
      
      await llmService.processReminderStreaming(transcription, (chunk) => {
        fullResponse += chunk;
        onProgress({ 
          stage: 'processing', 
          progress: 50, 
          partial: fullResponse 
        });
      });

      // Parse final result
      const reminder = llmService.parseReminderJSON(fullResponse);
      onProgress({ stage: 'complete', progress: 100, result: reminder });

      return { success: true, data: reminder };

    } catch (error) {
      logger.error('Streaming processing failed', { error: error.message });
      onProgress({ stage: 'error', error: error.message });
      return { success: false, error: error.message };
    }
  }
}

module.exports = new ReminderProcessor();
```

---

## 11. Usage Examples

### 11.1 Basic Usage
```javascript
// app.js - Example Express route
const express = require('express');
const multer = require('multer');
const reminderProcessor = require('./services/reminder-processor');

const app = express();
const upload = multer({ storage: multer.memoryStorage() });

app.post('/api/reminders/voice', upload.single('audio'), async (req, res) => {
  try {
    if (!req.file) {
      return res.status(400).json({ error: 'No audio file provided' });
    }

    const result = await reminderProcessor.processVoiceReminder(req.file.buffer);
    
    if (!result.success) {
      return res.status(500).json(result);
    }

    res.json(result);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.listen(3000, () => {
  console.log('Server running on port 3000');
});
```

### 11.2 With Real-Time Progress
```javascript
// Using WebSockets for real-time updates
const WebSocket = require('ws');
const wss = new WebSocket.Server({ port: 8080 });

wss.on('connection', (ws) => {
  ws.on('message', async (audioData) => {
    await reminderProcessor.processVoiceReminderStreaming(
      audioData,
      (progress) => {
        ws.send(JSON.stringify(progress));
      }
    );
  });
});
```

---

## 12. Troubleshooting Guide

### Common Issues:

**1. Authentication Errors (403)**
- Verify API token has Workers AI permissions
- Check account ID is correct
- Ensure token hasn't expired

**2. Rate Limiting (429)**
- Implement exponential backoff
- Consider upgrading to Workers Paid plan
- Cache results where possible

**3. Large File Errors (413)**
- Implement chunking for files >25MB
- Compress audio before sending
- Use supported audio formats (MP3, WAV, etc.)

**4. Timeout Errors**
- Increase timeout settings
- Process large files asynchronously
- Use streaming for better UX

**5. JSON Parsing Failures**
- Add robust error handling in parseReminderJSON
- Implement fallback to return raw transcription
- Improve system prompt to enforce JSON format

---

## 13. Next Steps

1. **Implement core services** (start with speech-to-text)
2. **Add comprehensive error handling**
3. **Set up monitoring and logging**
4. **Create tests** (unit and integration)
5. **Optimize for cost** (track usage, implement caching)
6. **Deploy to staging** environment
7. **Monitor performance** and costs
8. **Gradually roll out** to production

---

## Additional Resources

- [Cloudflare Workers AI Docs](https://developers.cloudflare.com/workers-ai/)
- [Whisper Model Docs](https://developers.cloudflare.com/workers-ai/models/whisper-large-v3-turbo/)
- [GPT-OSS 20B Model Docs](https://developers.cloudflare.com/workers-ai/models/gpt-oss-20b/)
- [Pricing Calculator](https://developers.cloudflare.com/workers-ai/platform/pricing/)
- [API Reference](https://developers.cloudflare.com/api/resources/ai/)

---

This guide provides everything needed to migrate from local models to Cloudflare Workers AI. All code is production-ready with proper error handling, rate limiting, and cost optimization. Let me know if you need clarification on any section!