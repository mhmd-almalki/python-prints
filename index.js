// index.js
const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

function getBinaryPath() {
    const root = __dirname;
    if (process.platform === 'win32') {
        return path.join(root, 'bin', 'win', 'python-prints', 'python-prints.exe');
    }
    throw new Error('python-prints: this build currently includes only the Windows binary.');
}

function getBinaryDir() {
    return path.dirname(getBinaryPath());
}

function runTool(args) {
    const exe = getBinaryPath();
    const cwd = getBinaryDir();

    if (process.platform !== 'win32') {
        try { fs.chmodSync(exe, 0o755); } catch { }
    }

    return new Promise((resolve, reject) => {
        const child = spawn(exe, args, {
            cwd,
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

async function list() {
    const res = await runTool(['list', '--json']);
    return JSON.parse(res || '{}');
}

async function setDefault(printer) {
    if (!printer) throw new Error('printer name required');
    await runTool(['set-default', printer]);
    return { ok: true };
}

async function printPdf(filePath, options = {}) {
    if (!filePath) {
        throw new Error('filePath is required');
    }

    if (!path.isAbsolute(filePath) || !fs.existsSync(filePath)) {
        throw new Error('File in not Found (Note: File path should be absolute)');
    }

    const args = ['print', filePath];
    if (options.printer) args.push('--printer', options.printer);
    if (options.copies) args.push('--copies', String(options.copies));

    const message = await runTool(args);
    return { ok: true, message };
}

module.exports = { list, setDefault, printPdf };