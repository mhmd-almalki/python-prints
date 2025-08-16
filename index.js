const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

// --- Resolve binary path ---
function getBinaryDir() {
    // Go up from src/ to package root, then into bin/<platform>/python-prints
    const base = path.join(__dirname, '..', 'bin');
    if (process.platform === 'win32') {
        return path.join(base, 'win', 'python-prints');
    }
    if (process.platform === 'darwin') {
        return path.join(base, 'mac', 'python-prints');
    }
    return path.join(base, 'linux', 'python-prints');
}

function getBinaryPath() {
    return path.join(
        getBinaryDir(),
        process.platform === 'win32' ? 'python-prints.exe' : 'python-prints'
    );
}

function ensureExec(p) {
    if (process.platform !== 'win32') {
        try { fs.chmodSync(p, 0o755); } catch { }
    }
}

// --- Helper to run the binary ---
function runTool(args) {
    return new Promise((resolve, reject) => {
        const exe = getBinaryPath();
        ensureExec(exe);

        const child = spawn(exe, args, {
            cwd: getBinaryDir(),   // must be cwd so bundled DLLs are found
            windowsHide: true,
            env: process.env,
        });

        let out = '';
        let err = '';

        child.stdout.on('data', d => (out += d.toString()));
        child.stderr.on('data', d => (err += d.toString()));

        child.on('close', code => {
            if (code === 0) resolve(out.trim());
            else reject(new Error(err.trim() || out.trim() || `exit ${code}`));
        });

        child.on('error', reject);
    });
}

// --- Public API ---
async function list() {
    const res = await runTool(['list', '--json']);
    return JSON.parse(res);
}

async function setDefault(printer) {
    if (!printer) throw new Error('printer name required');
    await runTool(['set-default', printer]);
    return { ok: true };
}

async function printPdf(filePath, options = {}) {
    if (!filePath) throw new Error('filePath is required');

    const args = ['print', filePath];
    if (options.printer) args.push('--printer', options.printer);
    if (options.copies) args.push('--copies', String(options.copies));

    const msg = await runTool(args);
    return { ok: true, message: msg };
}

module.exports = { list, setDefault, printPdf };
