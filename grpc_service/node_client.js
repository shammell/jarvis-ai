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
        console.log(`🔌 gRPC Client connected to ${host}`);
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
                metadata: {}
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
                parameters
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
                metadata
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
                type
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
            const request = { service: 'jarvis' };

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
        const request = { client_id: clientId };
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
