const vscode = require('vscode');
const http = require('http');

const PORT = 37123;
let server;

function activate(context) {
    server = http.createServer((req, res) => {
        if (req.method !== 'POST') {
            res.writeHead(405);
            res.end();
            return;
        }

        let body = '';
        req.on('data', chunk => { body += chunk; });
        req.on('end', async () => {
            let message = 'Proceed with this prompt?';
            try { message = JSON.parse(body).message || message; } catch {}

            const choice = await vscode.window.showWarningMessage(
                message,
                { modal: false },
                'Proceed',
                'Block'
            );

            const result = JSON.stringify({ proceed: choice === 'Proceed' });
            res.writeHead(200, { 'Content-Type': 'application/json' });
            res.end(result);
        });
    });

    server.listen(PORT, '127.0.0.1', () => {
        console.log(`[email-guard-hook] listening on 127.0.0.1:${PORT}`);
    });

    context.subscriptions.push({ dispose: () => server?.close() });
}

function deactivate() {
    server?.close();
}

module.exports = { activate, deactivate };
