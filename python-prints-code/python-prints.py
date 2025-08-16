import sys, os, platform, argparse, subprocess, shlex, time, shutil, json

IS_WINDOWS = platform.system() == "Windows"
IS_MAC = platform.system() == "Darwin"
IS_LINUX = platform.system() == "Linux"

def run(cmd, check=True, use_shell_on_windows=False):
    """
    Run a command and return (stdout, stderr, rc).
    If cmd is str, on Windows we may use shell=True to find builtins easily.
    """
    if isinstance(cmd, str):
        p = subprocess.run(
            cmd,
            shell=(use_shell_on_windows and IS_WINDOWS),
            capture_output=True,
            text=True,
        )
    else:
        p = subprocess.run(cmd, capture_output=True, text=True)
    if check and p.returncode != 0:
        msg = (p.stderr or p.stdout or "").strip()
        raise RuntimeError(msg or f"Command failed: {cmd}")
    return (p.stdout.strip(), p.stderr.strip(), p.returncode)

def ensure_exists(path):
    if not os.path.isfile(path):
        raise FileNotFoundError(f"File not found: {path}")

def list_printers():
    if IS_WINDOWS:
        try:
            import win32print
        except ImportError:
            raise RuntimeError("pywin32 is required on Windows: pip install pywin32")

        flags = win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS
        printers = win32print.EnumPrinters(flags)
        names = [p[2] for p in printers]  # p[2] is printer name
        try:
            default_name = win32print.GetDefaultPrinter()
        except Exception:
            default_name = None
        return names, default_name
    else:
        # macOS/Linux via CUPS tools
        out, _, _ = run(["lpstat", "-a"], check=False)
        names = []
        for line in (out or "").splitlines():
            line = line.strip()
            if not line:
                continue
            # Format: "<printer> accepting requests since ..."
            parts = line.split()
            if parts:
                names.append(parts[0])

        out_def, _, _ = run(["lpstat", "-d"], check=False)
        default_name = None
        # "system default destination: <printer>"
        if out_def and ":" in out_def:
            default_name = out_def.split(":", 1)[-1].strip() or None
        return names, default_name

def set_default(printer_name: str):
    if not printer_name:
        raise ValueError("Printer name is required.")

    names, _ = list_printers()
    if printer_name not in names:
        raise RuntimeError(f"Printer not found: {printer_name}")

    if IS_WINDOWS:
        import win32print
        win32print.SetDefaultPrinter(printer_name)
        return True
    else:
        # User-level default (no sudo)
        run(["lpoptions", "-d", printer_name], check=True)
        return True

def _print_pdf_unix(pdf_path, printer=None, copies=1):
    ensure_exists(pdf_path)
    cmd = ["lp"]
    if printer:
        cmd += ["-d", printer]
    if copies and copies > 1:
        cmd += ["-n", str(int(copies))]
    cmd += [pdf_path]
    out, _, _ = run(cmd, check=True)
    return out or "Submitted to print queue."

def _find_acrobat_windows():
    # Try common Adobe Reader/Acrobat paths
    possible = [
        r"C:\Program Files\Adobe\Acrobat DC\Acrobat\Acrobat.exe",
        r"C:\Program Files (x86)\Adobe\Acrobat Reader DC\Reader\AcroRd32.exe",
        r"C:\Program Files\Adobe\Acrobat Reader DC\Reader\AcroRd32.exe",
        r"C:\Program Files\Adobe\Acrobat\Acrobat.exe",
        r"C:\Program Files (x86)\Adobe\Acrobat\Acrobat.exe",
    ]
    for p in possible:
        if os.path.isfile(p):
            return p
    for name in ("Acrobat.exe", "AcroRd32.exe"):
        which = shutil.which(name)
        if which:
            return which
    return None

def _print_pdf_windows(pdf_path, printer=None, copies=1):
    ensure_exists(pdf_path)
    if printer:
        acro = _find_acrobat_windows()
        if acro:
            # Acrobat /t doesn't have copies; loop
            for _ in range(max(1, int(copies))):
                run([acro, "/t", pdf_path, printer, "", ""], check=True)
            return "Sent to printer via Adobe Reader."
        else:
            # Fallback: temporarily set default to requested printer and use Print verb
            import win32print
            names, default_name = list_printers()
            if printer not in names:
                raise RuntimeError(f"Printer not found: {printer}")
            try:
                win32print.SetDefaultPrinter(printer)
                for _ in range(max(1, int(copies))):
                    # Use PowerShell to trigger default print handler
                    cmd = [
                        "powershell",
                        "-NoProfile",
                        "-Command",
                        f'Start-Process -FilePath {shlex.quote(pdf_path)} -Verb Print'
                    ]
                    run(cmd, check=True)
                time.sleep(1.0)  # let spooler catch up
            finally:
                if default_name:
                    win32print.SetDefaultPrinter(default_name)
            return "Sent to printer via default-print fallback."
    else:
        # No printer specified -> print to system default
        for _ in range(max(1, int(copies))):
            run([
                "powershell", "-NoProfile", "-Command",
                f'Start-Process -FilePath {shlex.quote(pdf_path)} -Verb Print'
            ], check=True)
        return "Sent to default printer."

def print_pdf(pdf_path: str, printer: str = None, copies: int = 1):
    if IS_WINDOWS:
        return _print_pdf_windows(pdf_path, printer, copies)
    else:
        return _print_pdf_unix(pdf_path, printer, copies)

def main():
    parser = argparse.ArgumentParser(
        description="py-print tool: list printers, set default, print PDF."
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    # list
    p_list = sub.add_parser("list", help="List available printers and show the default printer.")
    p_list.add_argument("--json", action="store_true", help="Output as JSON {printers:[], default:'...'}.")

    # set-default
    p_set = sub.add_parser("set-default", help="Set the default printer.")
    p_set.add_argument("printer", help="Printer name.")

    # print
    p_print = sub.add_parser("print", help="Print a PDF file.")
    p_print.add_argument("pdf", help="Path to PDF file.")
    p_print.add_argument("--printer", help="Printer name (optional; uses default if omitted).")
    p_print.add_argument("--copies", type=int, default=1, help="Number of copies (default: 1)")

    args = parser.parse_args()

    try:
        if args.cmd == "list":
            names, default_name = list_printers()
            if getattr(args, "json", False):
                print(json.dumps({"printers": names, "default": default_name or None}))
            else:
                print("Printers:")
                if names:
                    for n in names:
                        mark = " (default)" if default_name and n == default_name else ""
                        print(f"  - {n}{mark}")
                else:
                    print("  (none found)")
            return 0

        if args.cmd == "set-default":
            set_default(args.printer)
            print(f"Default printer set to: {args.printer}")
            return 0

        if args.cmd == "print":
            msg = print_pdf(args.pdf, args.printer, args.copies)
            print(msg)
            return 0

        print("Unknown command.", file=sys.stderr)
        return 1

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())