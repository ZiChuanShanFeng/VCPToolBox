const WebSocket = require('ws');
const axios = require('axios');

let pluginConfig;
let wsClient;
let wsReconnectTimer;

function log(message, level = 'info') {
    if (pluginConfig && pluginConfig.DebugMode) {
        const timestamp = new Date().toISOString();
        console[level](`[Gotify] [${timestamp}] ${message}`);
    }
}

async function sendGotifyNotification(logData) {
    if (!pluginConfig || !pluginConfig.Enable_Gotify_Push) {
        return; // Feature disabled
    }

    if (!pluginConfig.Gotify_Url || !pluginConfig.Gotify_App_Token) {
        log('Gotify URL or App Token is not configured. Cannot send notification.', 'warn');
        return;
    }

    const { tool_name, status, content, source } = logData;
    const title = `VCP Event: ${tool_name} (${status})`;
    
    let message = `Source: ${source || 'N/A'}\n`;
    let contentString = content;
    if (typeof content === 'object') {
        contentString = JSON.stringify(content, null, 2);
    }
    message += `Content: ${contentString}`;

    const gotifyUrl = `${pluginConfig.Gotify_Url}/message?token=${pluginConfig.Gotify_App_Token}`;

    try {
        log(`Sending notification to Gotify: ${title}`);
        const response = await axios.post(gotifyUrl, {
            title: title,
            message: message,
            priority: pluginConfig.Gotify_Priority || 2,
        });
        log(`Successfully sent notification to Gotify. Response ID: ${response.data.id}`);
    } catch (error) {
        const errorMessage = error.response ? JSON.stringify(error.response.data) : error.message;
        log(`Error sending Gotify notification: ${errorMessage}`, 'error');
    }
}

function connectToWebSocketLogSource() {
    if (!pluginConfig || !pluginConfig.VCP_Key || !pluginConfig.SERVER_PORT) {
        log('Cannot connect to WebSocket: VCP_Key or SERVER_PORT missing in config.', 'error');
        clearTimeout(wsReconnectTimer);
        wsReconnectTimer = setTimeout(connectToWebSocketLogSource, 15000);
        return;
    }

    const wsUrl = `ws://localhost:${pluginConfig.SERVER_PORT}/VCPlog/VCP_Key=${pluginConfig.VCP_Key}`;
    log(`Attempting to connect to VCPLog WebSocket at: ${wsUrl}`);

    if (wsClient && (wsClient.readyState === WebSocket.OPEN || wsClient.readyState === WebSocket.CONNECTING)) {
        log('WebSocket client already open or connecting.');
        return;
    }

    wsClient = new WebSocket(wsUrl);

    wsClient.on('open', () => {
        log('Successfully connected to VCPLog WebSocket source.');
        clearTimeout(wsReconnectTimer);
    });

    wsClient.on('message', async (data) => {
        try {
            const message = JSON.parse(data.toString());
            log(`Received message from WebSocket: ${message.type}`);
            if (message.type === 'vcp_log') {
                await sendGotifyNotification(message.data);
            }
        } catch (error) {
            log(`Error processing message from WebSocket: ${error.message}`, 'error');
        }
    });

    wsClient.on('close', (code, reason) => {
        log(`WebSocket disconnected. Code: ${code}, Reason: ${String(reason)}. Reconnecting...`, 'warn');
        wsClient = null;
        clearTimeout(wsReconnectTimer);
        wsReconnectTimer = setTimeout(connectToWebSocketLogSource, 5000);
    });

    wsClient.on('error', (error) => {
        log(`WebSocket connection error: ${error.message}`, 'error');
        if (wsClient) {
            wsClient.close();
        }
    });
}

function registerRoutes(app, config, projectBasePath) {
    pluginConfig = config;
    if (!pluginConfig.SERVER_PORT && process.env.PORT) {
        pluginConfig.SERVER_PORT = process.env.PORT;
    }
    log('Plugin registered and config loaded.');
    if (pluginConfig.Enable_Gotify_Push) {
        connectToWebSocketLogSource();
    } else {
        log('Gotify push is disabled in config.');
    }
}

function shutdown() {
    log('Shutting down...');
    clearTimeout(wsReconnectTimer);
    if (wsClient) {
        wsClient.removeAllListeners();
        wsClient.close();
        wsClient = null;
        log('WebSocket client disconnected.');
    }
}

module.exports = {
    registerRoutes,
    shutdown
};
