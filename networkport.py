import socket
import threading
import time
import queue
import sys
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

# ---------------------------
# Service Map (Backend untouched)
# ---------------------------
COMMON_PORTS = {
    21: 'FTP', 22: 'SSH', 23: 'Telnet', 25: 'SMTP', 53: 'DNS',
    80: 'HTTP', 110: 'POP3', 143: 'IMAP', 443: 'HTTPS',
    3306: 'MySQL', 3389: 'RDP', 5900: 'VNC', 8080: 'HTTP-Alt'
}

# ---------------------------
# Scanner Worker (Backend untouched)
# ---------------------------
class PortScanner:
    def __init__(self, target, start_port, end_port, timeout=0.5, max_workers=500):
        self.target = target
        self.start_port = start_port
        self.end_port = end_port
        self.timeout = timeout
        self.max_workers = max_workers
        self._stop_event = threading.Event()

        self.total_ports = max(0, end_port - start_port + 1)
        self.scanned_count = 0
        self.open_ports = []
        self._lock = threading.Lock()
        self.result_queue = queue.Queue()

    def stop(self):
        self._stop_event.set()

    def _scan_port(self, port):
        if self._stop_event.is_set():
            return
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(self.timeout)
            result = s.connect_ex((self.target, port))
            if result == 0:
                service = COMMON_PORTS.get(port, 'Unknown')
                with self._lock:
                    self.open_ports.append((port, service))
                self.result_queue.put(('open', port, service))
            s.close()
        except Exception as e:
            self.result_queue.put(('error', port, str(e)))
        finally:
            with self._lock:
                self.scanned_count += 1
            self.result_queue.put(('progress', self.scanned_count, self.total_ports))

    def resolve_target(self):
        return socket.gethostbyname(self.target)

    def run(self):
        sem = threading.Semaphore(self.max_workers)
        threads = []

        for port in range(self.start_port, self.end_port + 1):
            if self._stop_event.is_set():
                break
            sem.acquire()
            t = threading.Thread(target=self._worker_wrapper, args=(sem, port), daemon=True)
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        self.result_queue.put(('done', None, None))

    def _worker_wrapper(self, sem, port):
        try:
            self._scan_port(port)
        finally:
            sem.release()

# ---------------------------
# Tkinter GUI (Colourful, Vibrant & Interactive)
# ---------------------------
class ScannerGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Network Port Scanner")
        self.geometry("740x540")
        self.minsize(680, 480)

        self.scanner_thread = None
        self.scanner = None
        self.start_time = None
        self.poll_after_ms = 40

        # High-Vibrancy Neon/Cyberpunk Color Palette
        self.bg_main = "#1A1A2A"       # Deeper background for maximum neon pop
        self.bg_frame = "#232333"      # Frame background
        self.fg_text = "#C0C0C0"       # Readability text (silver)
        self.accent_cyan = "#00FFFF"   # Super vibrant cyan for info/labels
        self.accent_green = "#00FF00"  # Bright neon green for success/start
        self.accent_red = "#FF3F3F"    # Vivid neon red for stop/errors
        self.accent_yellow = "#FFFF3F" # Bright neon yellow for warnings
        self.accent_purple = "#BD93F9" # Vibrant neon purple for port numbers
        self.accent_orange = "#FFB86C" # Bright neon orange for service names
        self.bg_hover = "#33334F"      # Lighter hover background

        self._apply_theme()
        self._build_ui()
        self._bind_events()

    def _apply_theme(self):
        style = ttk.Style(self)
        if "clam" in style.theme_names():
            style.theme_use("clam")
            
        self.configure(bg=self.bg_main)
        
        # Global ttk styles
        style.configure(".", font=("Segoe UI", 10), background=self.bg_main, foreground=self.fg_text)
        style.configure("TLabelframe", background=self.bg_frame, bordercolor=self.bg_main)
        style.configure("TLabelframe.Label", font=("Segoe UI", 10, "bold"), foreground=self.accent_cyan, background=self.bg_frame)
        
        # Standard Button
        style.configure("TButton", font=("Segoe UI", 10, "bold"), padding=4, background=self.bg_hover, borderwidth=0)
        style.map("TButton",
            background=[('active', self.accent_cyan), ('disabled', self.bg_main)],
            foreground=[('active', self.bg_main), ('disabled', "#616E88")]
        )
        
        # Colored Action Buttons
        style.configure("Start.TButton", foreground=self.accent_green)
        style.configure("Stop.TButton", foreground=self.accent_red)

        # Entries and Progressbar
        style.configure("TEntry", fieldbackground=self.bg_hover, foreground=self.fg_text, insertcolor=self.accent_cyan, borderwidth=0, padding=4)
        style.configure("TProgressbar", thickness=15, troughcolor=self.bg_hover, background=self.accent_cyan, borderwidth=0)

    def _build_ui(self):
        # Top Frame: Inputs
        frm_top = ttk.LabelFrame(self, text="Scan Settings")
        frm_top.pack(fill="x", padx=12, pady=(12, 6))

        ttk.Label(frm_top, text="Target (IP / Hostname):", background=self.bg_frame).grid(row=0, column=0, padx=8, pady=8, sticky="e")
        self.ent_target = ttk.Entry(frm_top, width=36)
        self.ent_target.grid(row=0, column=1, padx=8, pady=8, sticky="w")

        ttk.Label(frm_top, text="Start Port:", background=self.bg_frame).grid(row=0, column=2, padx=8, pady=8, sticky="e")
        self.ent_start = ttk.Entry(frm_top, width=10)
        self.ent_start.insert(0, "1")
        self.ent_start.grid(row=0, column=3, padx=8, pady=8, sticky="w")

        ttk.Label(frm_top, text="End Port:", background=self.bg_frame).grid(row=0, column=4, padx=8, pady=8, sticky="e")
        self.ent_end = ttk.Entry(frm_top, width=10)
        self.ent_end.insert(0, "1024")
        self.ent_end.grid(row=0, column=5, padx=8, pady=8, sticky="w")

        self.btn_start = ttk.Button(frm_top, text="Start Scan", style="Start.TButton", command=self.start_scan)
        self.btn_start.grid(row=1, column=4, padx=8, pady=8, sticky="e")

        self.btn_stop = ttk.Button(frm_top, text="Stop", style="Stop.TButton", command=self.stop_scan, state="disabled")
        self.btn_stop.grid(row=1, column=5, padx=8, pady=8, sticky="w")

        for i in range(6):
            frm_top.grid_columnconfigure(i, weight=1)

        # Progress / Status
        frm_status = ttk.LabelFrame(self, text="Status")
        frm_status.pack(fill="x", padx=12, pady=6)

        self.var_status = tk.StringVar(value="Idle")
        self.lbl_status = ttk.Label(frm_status, textvariable=self.var_status, font=("Segoe UI", 10, "bold"), background=self.bg_frame)
        self.lbl_status.pack(side="left", padx=10, pady=8)

        self.var_elapsed = tk.StringVar(value="Elapsed: 0.00s")
        self.lbl_elapsed = ttk.Label(frm_status, textvariable=self.var_elapsed, background=self.bg_frame)
        self.lbl_elapsed.pack(side="right", padx=10, pady=8)

        self.progress = ttk.Progressbar(frm_status, orient="horizontal", mode="determinate")
        self.progress.pack(fill="x", padx=10, pady=(0,10))

        # Results (Terminal Output)
        frm_results = ttk.LabelFrame(self, text="Terminal Output (Click a result to copy)")
        frm_results.pack(fill="both", expand=True, padx=12, pady=6)

        self.txt_results = tk.Text(
            frm_results, height=14, wrap="none",
            bg=self.bg_main, fg=self.fg_text,
            insertbackground=self.accent_cyan, selectbackground=self.bg_hover,
            font=("Consolas", 10), padx=10, pady=10, relief="flat", cursor="arrow"
        )
        self.txt_results.pack(fill="both", expand=True, side="left", padx=(2,0), pady=2)

        yscroll = ttk.Scrollbar(frm_results, orient="vertical", command=self.txt_results.yview)
        yscroll.pack(side="right", fill="y", pady=2, padx=(0, 2))
        self.txt_results.configure(yscrollcommand=yscroll.set)

        xscroll = ttk.Scrollbar(self, orient="horizontal", command=self.txt_results.xview)
        xscroll.pack(fill="x", padx=12, pady=(0, 6))
        self.txt_results.configure(xscrollcommand=xscroll.set)

        # Bottom Buttons
        frm_bottom = ttk.Frame(self)
        frm_bottom.pack(fill="x", padx=12, pady=(6, 12))

        self.btn_clear = ttk.Button(frm_bottom, text="Clear Output", command=self.clear_results)
        self.btn_clear.pack(side="left")

        self.btn_save = ttk.Button(frm_bottom, text="Save Results", command=self.save_results, state="disabled")
        self.btn_save.pack(side="right")

    def _bind_events(self):
        # Keyboard Shortcuts
        for entry in (self.ent_target, self.ent_start, self.ent_end):
            entry.bind("<Return>", lambda event: self.start_scan())
            entry.bind("<FocusIn>", lambda event: event.widget.selection_range(0, tk.END))

        # Colorful Text Tags for Syntax Highlighting
        self.txt_results.tag_configure("bullet_info", foreground=self.accent_cyan)
        self.txt_results.tag_configure("bullet_success", foreground=self.accent_green)
        self.txt_results.tag_configure("bullet_warn", foreground=self.accent_yellow)
        self.txt_results.tag_configure("text_normal", foreground=self.fg_text)
        self.txt_results.tag_configure("highlight_port", foreground=self.accent_purple, font=("Consolas", 10, "bold"))
        self.txt_results.tag_configure("highlight_service", foreground=self.accent_orange, font=("Consolas", 10, "bold"))

    # -----------------------
    # Interactive Callbacks
    # -----------------------
    def copy_to_clipboard(self, text):
        self.clipboard_clear()
        self.clipboard_append(text)
        self.var_status.set(f"Copied to clipboard!")
        self.lbl_status.configure(foreground=self.accent_green)
        self.after(2000, lambda: self.lbl_status.configure(foreground=self.fg_text))

    def write_log(self, prefix, prefix_tag, message, message_tag="text_normal"):
        """Helper to write standard colored logs"""
        self.txt_results.insert(tk.END, prefix, prefix_tag)
        self.txt_results.insert(tk.END, message + "\n", message_tag)
        self.txt_results.see(tk.END)

    # -----------------------
    # Control Handlers
    # -----------------------
    def start_scan(self):
        if self.scanner_thread and self.scanner_thread.is_alive():
            return

        target = self.ent_target.get().strip()
        if not target:
            messagebox.showerror("Input Error", "Please enter a target IP or hostname.")
            return

        try:
            start_port = int(self.ent_start.get().strip())
            end_port = int(self.ent_end.get().strip())
        except ValueError:
            messagebox.showerror("Input Error", "Ports must be integers.")
            return

        if not (0 <= start_port <= 65535 and 0 <= end_port <= 65535 and start_port <= end_port):
            messagebox.showerror("Input Error", "Port range must be within 0–65535 and start ≤ end.")
            return

        self.scanner = PortScanner(target, start_port, end_port, timeout=0.5, max_workers=500)

        try:
            resolved_ip = self.scanner.resolve_target()
            self.write_log("[*] ", "bullet_info", f"Target: {target} ({resolved_ip})")
            self.write_log("[*] ", "bullet_info", f"Scanning Ports: {start_port} - {end_port}\n")
        except Exception as e:
            messagebox.showerror("Resolution Error", f"Failed to resolve target '{target}'.\n{e}")
            self.scanner = None
            return

        self.btn_start.configure(state="disabled")
        self.btn_stop.configure(state="normal")
        self.btn_save.configure(state="disabled")
        self.clear_progress()
        self.lbl_status.configure(foreground=self.fg_text)

        self.start_time = time.time()
        self.var_status.set("Scanning...")
        self.update_elapsed()

        self.scanner_thread = threading.Thread(target=self.scanner.run, daemon=True)
        self.scanner_thread.start()
        self.after(self.poll_after_ms, self.poll_results)

    def stop_scan(self):
        if self.scanner:
            self.scanner.stop()
            self.var_status.set("Stopping...")
            self.write_log("\n[!] ", "bullet_warn", "Scan interrupted by user.", "bullet_warn")

    def clear_results(self):
        self.txt_results.delete("1.0", tk.END)
        self.clear_progress()
        self.var_status.set("Idle")
        self.lbl_status.configure(foreground=self.fg_text)
        self.var_elapsed.set("Elapsed: 0.00s")
        self.btn_save.configure(state="disabled")

    def save_results(self):
        if not self.scanner or not self.scanner.open_ports:
            return

        default_name = f"open_ports_{int(time.time())}.txt"
        file_path = filedialog.asksaveasfilename(
            title="Save results", defaultextension=".txt",
            initialfile=default_name, filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
        )
        if not file_path:
            return

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write("Open Ports:\n")
                for port, service in sorted(self.scanner.open_ports, key=lambda x: x[0]):
                    f.write(f"Port {port} ({service}) is open\n")
            messagebox.showinfo("Saved", f"Results saved to:\n{file_path}")
        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save file.\n{e}")

    # -----------------------
    # UI Helpers
    # -----------------------
    def clear_progress(self):
        self.progress.configure(value=0, maximum=1)

    def update_elapsed(self):
        if self.start_time and self.var_status.get() in ("Scanning...", "Stopping..."):
            elapsed = time.time() - self.start_time
            self.var_elapsed.set(f"Elapsed: {elapsed:.2f}s")
            self.after(200, self.update_elapsed)

    def poll_results(self):
        if not self.scanner:
            return

        try:
            while True:
                msg_type, a, b = self.scanner.result_queue.get_nowait()
                if msg_type == 'open':
                    port, service = a, b
                    row_tag = f"row_{port}"
                    
                    # Inserting multi-colored text with dual tags (color_tag, row_interactive_tag)
                    self.txt_results.insert(tk.END, "[+] ", ("bullet_success", row_tag))
                    self.txt_results.insert(tk.END, "Port ", ("text_normal", row_tag))
                    self.txt_results.insert(tk.END, f"{port:<5} ", ("highlight_port", row_tag))
                    self.txt_results.insert(tk.END, "open      Service: ", ("text_normal", row_tag))
                    self.txt_results.insert(tk.END, f"{service}\n", ("highlight_service", row_tag))
                    
                    # Add interactive hover background & cursor for the whole line
                    self.txt_results.tag_bind(row_tag, "<Enter>", lambda e, t=row_tag: (
                        self.txt_results.tag_configure(t, background=self.bg_frame),
                        self.txt_results.configure(cursor="hand2")
                    ))
                    self.txt_results.tag_bind(row_tag, "<Leave>", lambda e, t=row_tag: (
                        self.txt_results.tag_configure(t, background=""),
                        self.txt_results.configure(cursor="arrow")
                    ))
                    
                    # Add interactive click-to-copy
                    line_text = f"Port {port} open ({service})"
                    self.txt_results.tag_bind(row_tag, "<Button-1>", lambda e, txt=line_text: self.copy_to_clipboard(txt))

                    self.txt_results.see(tk.END)
                    
                elif msg_type == 'progress':
                    scanned, total = a, b
                    self.progress.configure(maximum=max(total, 1), value=scanned)
                    self.var_status.set(f"Scanning... {scanned}/{total}")
                    
                elif msg_type == 'done':
                    total_open = len(self.scanner.open_ports)
                    self.write_log("\n[*] ", "bullet_info", f"Scan complete. Total open: {total_open}")
                    self.var_status.set("Completed")
                    self.btn_start.configure(state="normal")
                    self.btn_stop.configure(state="disabled")
                    self.btn_save.configure(state="normal" if total_open else "disabled")
                    self.start_time = None
        except queue.Empty:
            pass

        if self.scanner_thread and self.scanner_thread.is_alive():
            self.after(self.poll_after_ms, self.poll_results)
        else:
            if self.var_status.get() in ("Scanning...", "Stopping..."):
                self.var_status.set("Completed")
            self.btn_start.configure(state="normal")
            self.btn_stop.configure(state="disabled")
            if self.scanner and self.scanner.open_ports:
                self.btn_save.configure(state="normal")

def main():
    if sys.platform.startswith("win"):
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            kernel32.SetConsoleMode(kernel32.GetStdHandle(-10), 7)
        except Exception:
            pass
    app = ScannerGUI()
    app.mainloop()

if __name__ == "__main__":
    main()
