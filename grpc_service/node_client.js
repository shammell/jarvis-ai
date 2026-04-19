// ==========================================================
// JARVIS v9.0 - gRPC Node.js Client
// Connects to Python gRPC server from WhatsApp bridge
// Expected: <10ms latency
// ==========================================================

const grpc = require('@grpc/grpc-js');
const protoLoader = require('@grpc/proto-loader');
const path = require('path');

// Load proto file
const PROTO_PATH = path.join(__dirname, 'jarvis.proto');
const packageDefinition = protoLoader.loadSync(PROTO_PATH, {
    keepCase: true,
    longs: String,
    enums: String,
    defaults: true,
    oneofs: true
});

const jarvisProto = grpc.loadPackageDefinition(packageDefinition).jarvis;

class JarvisGRPCClient {
    constructor(host = 'localhost:50051') {
        this.client = new jarvisProto.JarvisService(
            host,
            grpc.credentials.createInsecure()
        );
        this.host = host;
        this.authToken = null;
        this.refreshToken = null;
        console.log(`🔌 gRPC Client connected to ${host}`);
    }

    setAuthTokens(accessToken, refreshToken = null) {
        this.authToken = accessToken;
        if (refreshToken) this.refreshToken = refreshToken;
    }

    async authenticate(username, password) {
        return new Promise((resolve, reject) => {
            this.client.Authenticate({ username, password, grant_type: 'password' }, (error, response) => {
                if (error) return reject(error);
                if (!response.success) return reject(new Error(response.error || 'Authentication failed'));
                this.setAuthTokens(response.access_token, response.refresh_token);
                resolve(response);
            });
        });
    }

    async refreshAuthToken() {
        return new Promise((resolve, reject) => {
            if (!this.refreshToken) return reject(new Error('No refresh token set'));
            this.client.RefreshToken({ refresh_token: this.refreshToken }, (error, response) => {
                if (error) return reject(error);
                if (!response.success) return reject(new Error(response.error || 'Token refresh failed'));
                this.setAuthTokens(response.access_token, response.refresh_token);
                resolve(response);
            });
        });
    }

    ensureAuthToken() {
        if (!this.authToken) throw new Error('Authentication token required. Call authenticate() first.');
        return this.authToken;
    }

    /**
     * Process incoming WhatsApp message
     */
    async processMessage(from, text, messageId) {
        return new Promise((resolve, reject) => {
            const request = {
                from,
                text,
                message_id: messageId,
                timestamp: Date.now(),
                metadata: {},
                auth_token: this.ensureAuthToken()
            };

            this.client.ProcessMessage(request, (error, response) => {
                if (error) {
                    console.error('❌ gRPC ProcessMessage error:', error);
                    reject(error);
                } else {
                    console.log(`✅ Message processed in ${response.processing_time_ms}ms`);
                    resolve(response);
                }
            });
        });
    }

    /**
     * Execute agent task
     */
    async executeAgent(agentType, task, context = '', parameters = {}) {
        return new Promise((resolve, reject) => {
            const request = {
                agent_type: agentType,
                task,
                context,
                parameters,
                auth_token: this.ensureAuthToken()
            };

            this.client.ExecuteAgent(request, (error, response) => {
                if (error) {
                    console.error('❌ gRPC ExecuteAgent error:', error);
                    reject(error);
                } else {
                    resolve(response);
                }
            });
        });
    }

    /**
     * Store memory
     */
    async storeMemory(text, type = 'conversation', metadata = {}) {
        return new Promise((resolve, reject) => {
            const request = {
                text,
                type,
                metadata,
                auth_token: this.ensureAuthToken()
            };

            this.client.StoreMemory(request, (error, response) => {
                if (error) {
                    console.error('❌ gRPC StoreMemory error:', error);
                    reject(error);
                } else {
                    resolve(response);
                }
            });
        });
    }

    /**
     * Retrieve memory
     */
    async retrieveMemory(query, limit = 5, type = '') {
        return new Promise((resolve, reject) => {
            const request = {
                query,
                limit,
                type,
                auth_token: this.ensureAuthToken()
            };

            this.client.RetrieveMemory(request, (error, response) => {
                if (error) {
                    console.error('❌ gRPC RetrieveMemory error:', error);
                    reject(error);
                } else {
                    resolve(response);
                }
            });
        });
    }

    /**
     * Health check
     */
    async healthCheck() {
        return new Promise((resolve, reject) => {
            const request = { service: 'jarvis', auth_token: this.authToken || '' };

            this.client.HealthCheck(request, (error, response) => {
                if (error) {
                    console.error('❌ gRPC HealthCheck error:', error);
                    reject(error);
                } else {
                    resolve(response);
                }
            });
        });
    }

    /**
     * Stream events (for real-time updates)
     */
    streamEvents(clientId, onEvent) {
        const request = { client_id: clientId, auth_token: this.ensureAuthToken() };
        const call = this.client.StreamEvents(request);

        call.on('data', (event) => {
            onEvent(event);
        });

        call.on('end', () => {
            console.log('📡 Event stream ended');
        });

        call.on('error', (error) => {
            console.error('❌ Event stream error:', error);
        });

        return call;
    }
}

// Export
module.exports = JarvisGRPCClient;

// Test if run directly
if (require.main === module) {
    (async () => {
        const client = new JarvisGRPCClient();

        try {
            // Test health check
            console.log('\n🏥 Testing health check...');
            const health = await client.healthCheck();
            console.log('Health:', health);

            // Test message processing
            console.log('\n📨 Testing message processing...');
            const msgResponse = await client.processMessage(
                '1234567890@s.whatsapp.net',
                'Hello JARVIS!',
                'test-msg-123'
            );
            console.log('Response:', msgResponse);

            // Test agent execution
            console.log('\n🤖 Testing agent execution...');
            const agentResponse = await client.executeAgent(
                'dev',
                'Test task',
                'Test context'
            );
            console.log('Agent response:', agentResponse);

            console.log('\n✅ All tests passed!');
        } catch (error) {
            console.error('❌ Test failed:', error);
        }
    })();
}
