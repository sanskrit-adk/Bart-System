"""
BART Transportation System — Modern Dark UI
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from typing import Optional

from backend.bart_system import BARTSystem
from backend.models import (
    User, Passenger, Admin, SuperAdmin,
    Station, Train, Card, PassengerType,
    StationStatus, TrainStatus, AlertType, InputValidator
)

# ── THEME ──────────────────────────────────────────────────
BG       = "#0d0d1a"
SURFACE  = "#1a1a2e"
SURFACE2 = "#111128"
BORDER   = "#252545"

BLUE   = "#4f72ff"
CYAN   = "#00d4ff"
GREEN  = "#22d97e"
YELLOW = "#f5c518"
RED    = "#ef4444"
PURPLE = "#a855f7"
ORANGE = "#f97316"
TEAL   = "#14b8a6"

TEXT     = "#f0f0ff"
TEXT_DIM = "#6a6a9a"

BART_BLUE = "#003f87"
BART_RED  = "#e31c23"
F = "Helvetica"


def configure_styles():
    s = ttk.Style()
    s.theme_use('clam')
    s.configure('D.Treeview', background=SURFACE, foreground=TEXT,
        fieldbackground=SURFACE, rowheight=34, font=(F, 10), borderwidth=0)
    s.configure('D.Treeview.Heading', background=SURFACE2, foreground=CYAN,
        font=(F, 10, 'bold'), relief='flat', padding=10)
    s.map('D.Treeview', background=[('selected', BLUE)], foreground=[('selected', TEXT)])
    s.configure('D.Vertical.TScrollbar', background=SURFACE2,
        troughcolor=SURFACE, arrowcolor=TEXT_DIM, borderwidth=0)
    s.configure('D.TCombobox', fieldbackground=SURFACE2, background=SURFACE2,
        foreground=TEXT, selectbackground=BLUE, selectforeground=TEXT,
        arrowcolor=CYAN, padding=8)
    s.map('D.TCombobox', fieldbackground=[('readonly', SURFACE2)],
        foreground=[('readonly', TEXT)], selectbackground=[('readonly', BLUE)])
    s.configure('D.TNotebook', background=BG, borderwidth=0, tabmargins=[0, 0, 0, 0])
    s.configure('D.TNotebook.Tab', background=SURFACE2, foreground=TEXT_DIM,
        padding=[20, 10], font=(F, 10, 'bold'), borderwidth=0)
    s.map('D.TNotebook.Tab', background=[('selected', BLUE)], foreground=[('selected', TEXT)])


def start_live_clock(root, label):
    try:
        if label.winfo_exists():
            label.config(text=datetime.now().strftime("%I:%M:%S %p"))
            root.after(1000, lambda: start_live_clock(root, label))
    except Exception:
        pass


def make_entry(parent, show=None):
    wrap = tk.Frame(parent, bg=BORDER, padx=1, pady=1)
    inner = tk.Frame(wrap, bg=SURFACE2)
    inner.pack(fill=tk.X)
    kw = dict(font=(F, 12), bg=SURFACE2, fg=TEXT, relief=tk.FLAT,
              insertbackground=CYAN, bd=0)
    if show:
        kw['show'] = show
    e = tk.Entry(inner, **kw)
    e.pack(fill=tk.X, padx=12, pady=10)
    e.bind('<FocusIn>',  lambda _: wrap.config(bg=CYAN))
    e.bind('<FocusOut>', lambda _: wrap.config(bg=BORDER))
    return wrap, e


def dark_combo(parent, var, values, width=30):
    return ttk.Combobox(parent, textvariable=var, values=values,
                        state='readonly', width=width, style='D.TCombobox')


def card(parent, title, icon, accent, **pk):
    """Dark section card with a colored title bar."""
    f = tk.Frame(parent, bg=SURFACE)
    f.pack(**pk)
    hdr = tk.Frame(f, bg=accent, padx=16, pady=10)
    hdr.pack(fill=tk.X)
    tk.Label(hdr, text=f"{icon}  {title}", font=(F, 11, 'bold'),
             bg=accent, fg='white').pack(anchor=tk.W)
    body = tk.Frame(f, bg=SURFACE, padx=16, pady=14)
    body.pack(fill=tk.BOTH, expand=True)
    return f, body


# ── WIDGETS ────────────────────────────────────────────────

class Toast:
    def __init__(self, root, msg, color=GREEN, dur=3000):
        self.root, self.dur, self._y = root, dur, -80
        self.f = tk.Frame(root, bg=color, padx=32, pady=18)
        tk.Label(self.f, text=msg, font=(F, 12, 'bold'),
                 bg=color, fg='white', wraplength=560).pack()
        self.f.place(relx=.5, rely=0, anchor='n', y=self._y)
        self.f.lift()
        self._in()

    def _in(self):
        try:
            if self._y < 20:
                self._y += 10
                self.f.place(relx=.5, rely=0, anchor='n', y=self._y)
                self.f.lift()
                self.root.after(10, self._in)
            else:
                self.root.after(self.dur, self._out)
        except Exception:
            pass

    def _out(self):
        try:
            if self._y > -90:
                self._y -= 10
                self.f.place(relx=.5, rely=0, anchor='n', y=self._y)
                self.root.after(10, self._out)
            else:
                self.f.destroy()
        except Exception:
            pass


class ModernButton(tk.Button):
    def __init__(self, parent, **kw):
        self._bg = kw.get('bg', BLUE)
        super().__init__(parent, relief=tk.FLAT, bd=0,
                         highlightthickness=0, cursor='hand2', **kw)
        self.bind('<Enter>',          lambda e: self._s(40))
        self.bind('<Leave>',          lambda e: self._s(0))
        self.bind('<ButtonPress-1>',  lambda e: self._s(-30))
        self.bind('<ButtonRelease-1>',lambda e: self._s(0))

    def _s(self, amt):
        try:
            h = self._bg.lstrip('#')
            r = max(0, min(255, int(h[0:2], 16) + amt))
            g = max(0, min(255, int(h[2:4], 16) + amt))
            b = max(0, min(255, int(h[4:6], 16) + amt))
            self.config(bg=f'#{r:02x}{g:02x}{b:02x}')
        except Exception:
            pass


# ── LOGIN ──────────────────────────────────────────────────

class BARTLoginApp:
    def __init__(self, root):
        self.root = root
        self.root.title("BART Transportation System")
        self.root.configure(bg=BG)
        configure_styles()
        self.bart_system = BARTSystem()
        self.current_user: Optional[User] = None
        self.show_login_screen()
        self.root.after(30000, self._service_hours_loop)

    def _service_hours_loop(self):
        try:
            result = self.bart_system.run_service_hours_check()
            if result == 'suspended':
                Toast(self.root,
                      "🌙  Night service — All trains suspended until 5:00 AM",
                      color=PURPLE, dur=6000)
            elif result == 'resumed':
                Toast(self.root,
                      "🌅  Morning service active — All trains now running",
                      color=GREEN, dur=5000)
        except Exception:
            pass
        finally:
            if self.root.winfo_exists():
                self.root.after(60000, self._service_hours_loop)

    def show_login_screen(self):
        for w in self.root.winfo_children():
            w.destroy()
        # Center window on screen at ~half-screen size
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        w, h = min(980, sw - 80), min(680, sh - 80)
        x, y = (sw - w) // 2, (sh - h) // 2
        self.root.geometry(f"{w}x{h}+{x}+{y}")
        self.root.resizable(True, True)
        self.root.minsize(800, 580)

        # ── Top strip: window controls ─────────────────────
        topbar = tk.Frame(self.root, bg=SURFACE2, height=30)
        topbar.pack(fill=tk.X)
        topbar.pack_propagate(False)

        self._fullscreen = False
        def _toggle_fullscreen():
            self._fullscreen = not self._fullscreen
            if self._fullscreen:
                self.root.state('zoomed')
                fs_btn.config(text="⧉  Windowed")
            else:
                self.root.state('normal')
                self.root.geometry(f"{w}x{h}+{x}+{y}")
                fs_btn.config(text="⛶  Fullscreen")

        fs_btn = tk.Button(topbar, text="⛶  Fullscreen", font=(F, 9),
            bg=SURFACE2, fg=TEXT_DIM, relief=tk.FLAT, bd=0, cursor='hand2',
            activebackground=SURFACE, activeforeground=CYAN,
            command=_toggle_fullscreen)
        fs_btn.pack(side=tk.RIGHT, padx=12, pady=4)
        tk.Label(topbar, text="BART Transportation System", font=(F, 9),
                 bg=SURFACE2, fg=TEXT_DIM).pack(side=tk.LEFT, padx=12)

        wrap = tk.Frame(self.root, bg=BG)
        wrap.pack(fill=tk.BOTH, expand=True)

        # Left branding panel
        left = tk.Frame(wrap, bg=BART_BLUE, width=340)
        left.pack(side=tk.LEFT, fill=tk.Y)
        left.pack_propagate(False)
        tk.Frame(left, bg=BART_RED, height=5).pack(fill=tk.X)

        brand = tk.Frame(left, bg=BART_BLUE)
        brand.pack(expand=True, fill=tk.BOTH, padx=40, pady=50)

        self.logo_label = tk.Label(brand, text="BART",
            font=(F, 64, 'bold'), bg=BART_BLUE, fg='white')
        self.logo_label.pack(anchor=tk.W)
        tk.Label(brand, text="Bay Area Rapid Transit",
            font=(F, 13), bg=BART_BLUE, fg="#99bbff").pack(anchor=tk.W)
        tk.Frame(brand, bg=BART_RED, height=3, width=70).pack(anchor=tk.W, pady=22)

        for icon, txt in [("🚇", "15 Stations across the Bay"),
                           ("🚆", "6 Active Train Lines"),
                           ("💳", "Clipper Card Support"),
                           ("📍", "Real-time Train Tracking")]:
            r = tk.Frame(brand, bg=BART_BLUE)
            r.pack(anchor=tk.W, pady=7)
            tk.Label(r, text=icon, font=(F, 15), bg=BART_BLUE).pack(side=tk.LEFT)
            tk.Label(r, text=f"  {txt}", font=(F, 11),
                     bg=BART_BLUE, fg="#b0c8ff").pack(side=tk.LEFT)

        tk.Label(brand, text="© 2026 BART System", font=(F, 9),
                 bg=BART_BLUE, fg="#446699").pack(side=tk.BOTTOM, anchor=tk.W)

        # Right form panel
        right = tk.Frame(wrap, bg=SURFACE)
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        form = tk.Frame(right, bg=SURFACE)
        form.place(relx=.5, rely=.5, anchor='center')

        tk.Label(form, text="Welcome Back", font=(F, 28, 'bold'),
                 bg=SURFACE, fg=TEXT).pack(anchor=tk.W)
        tk.Label(form, text="Sign in to your BART account",
                 font=(F, 11), bg=SURFACE, fg=TEXT_DIM).pack(anchor=tk.W, pady=(4, 30))

        tk.Label(form, text="USERNAME", font=(F, 9, 'bold'),
                 bg=SURFACE, fg=TEXT_DIM).pack(anchor=tk.W, pady=(0, 5))
        uf, self.username_entry = make_entry(form)
        uf.pack(fill=tk.X, pady=(0, 16))

        tk.Label(form, text="PASSWORD", font=(F, 9, 'bold'),
                 bg=SURFACE, fg=TEXT_DIM).pack(anchor=tk.W, pady=(0, 5))
        pf, self.password_entry = make_entry(form, show='●')
        pf.pack(fill=tk.X, pady=(0, 28))

        self.login_error_label = tk.Label(form, text="", font=(F, 9, 'bold'),
            bg=SURFACE, fg=RED, wraplength=340)
        self.login_error_label.pack(anchor=tk.W, pady=(0, 8))

        ModernButton(form, text="  SIGN IN  ", font=(F, 13, 'bold'),
            bg=BLUE, fg='white', padx=10, pady=14,
            command=self.handle_login).pack(fill=tk.X, pady=(0, 10))
        ModernButton(form, text="Create Account", font=(F, 11),
            bg=SURFACE2, fg=CYAN, padx=10, pady=12,
            command=self.show_register_screen).pack(fill=tk.X, pady=(0, 8))
        ModernButton(form, text="👤  Continue as Guest", font=(F, 10),
            bg=SURFACE2, fg=TEXT_DIM, padx=10, pady=10,
            command=self.open_guest_mode).pack(fill=tk.X, pady=(0, 22))

        demo = tk.Frame(form, bg=SURFACE2, padx=16, pady=12)
        demo.pack(fill=tk.X)
        tk.Label(demo, text="DEMO ACCOUNTS", font=(F, 8, 'bold'),
                 bg=SURFACE2, fg=CYAN).pack(anchor=tk.W, pady=(0, 8))
        for role, user, pwd, col in [
            ("Passenger",  "alice",      "password123", TEXT),
            ("Admin",      "admin",      "admin123",    ORANGE),
            ("Super Admin","superadmin", "admin123",    PURPLE),
        ]:
            r = tk.Frame(demo, bg=SURFACE2)
            r.pack(anchor=tk.W, pady=2)
            tk.Label(r, text=f"{role}:", font=(F, 9, 'bold'), bg=SURFACE2, fg=col, width=12, anchor=tk.W).pack(side=tk.LEFT)
            def _fill(u=user, p=pwd):
                self.username_entry.delete(0, tk.END); self.username_entry.insert(0, u)
                self.password_entry.delete(0, tk.END); self.password_entry.insert(0, p)
            tk.Button(r, text=f"{user} / {pwd}", font=(F, 9), bg=SURFACE2, fg=TEXT_DIM,
                      relief=tk.FLAT, bd=0, cursor='hand2', activebackground=SURFACE,
                      activeforeground=CYAN, command=_fill).pack(side=tk.LEFT)

        self.username_entry.bind('<Return>', lambda e: self.password_entry.focus())
        self.password_entry.bind('<Return>', lambda e: self.handle_login())
        self.root.after(100, self.username_entry.focus)
        self._pulse_logo()

    def _pulse_logo(self, step=0):
        colors = ["#ffffff", "#ffe082", "#ffca28", "#ffe082", "#ffffff"]
        try:
            if hasattr(self, 'logo_label') and self.logo_label.winfo_exists():
                self.logo_label.config(fg=colors[step % len(colors)])
                self.root.after(450, lambda: self._pulse_logo(step + 1))
        except Exception:
            pass

    def _flash_entries(self):
        for e in [self.username_entry, self.password_entry]:
            try:
                e.config(bg="#2a0a0a")
            except Exception:
                pass
        self.root.after(600, self._restore_entries)

    def _restore_entries(self):
        for e in [self.username_entry, self.password_entry]:
            try:
                e.config(bg=SURFACE2)
            except Exception:
                pass

    def handle_login(self):
        u = self.username_entry.get().strip()
        p = self.password_entry.get()
        if not u or not p:
            self.login_error_label.config(text="Please enter both username and password.")
            self._flash_entries()
            return
        ok, user, msg = self.bart_system.login(u, p)
        if ok:
            self.login_error_label.config(text="")
            self.current_user = user
            self.open_dashboard()
        else:
            self.login_error_label.config(text=f"✗  {msg}")
            self._flash_entries()

    def open_guest_mode(self):
        self.current_user = None
        GuestDashboard(self.root, self.bart_system, self)

    def show_register_screen(self):
        dlg = tk.Toplevel(self.root)
        dlg.title("Create Account")
        dlg.geometry("500x680")
        dlg.resizable(False, True)
        dlg.configure(bg=SURFACE)
        dlg.transient(self.root)
        dlg.grab_set()

        tk.Frame(dlg, bg=BLUE, height=5).pack(fill=tk.X)
        tk.Label(dlg, text="Create Passenger Account",
                 font=(F, 16, 'bold'), bg=SURFACE, fg=TEXT).pack(pady=(14, 2))
        tk.Label(dlg, text="All fields are required", font=(F, 9),
                 bg=SURFACE, fg=TEXT_DIM).pack(pady=(0, 8))

        fields = {}
        err_labels = {}
        wrap = tk.Frame(dlg, bg=SURFACE, padx=36)
        wrap.pack(fill=tk.X)

        field_specs = [
            ("Full Name",    "name",     None,  "e.g. Alice Johnson"),
            ("Username",     "username", None,  "3–30 chars, letters/numbers/_"),
            ("Password",     "password", '●',   "Minimum 6 characters"),
            ("Email",        "email",    None,  "e.g. user@example.com"),
        ]

        for lbl, key, show, hint in field_specs:
            tk.Label(wrap, text=lbl.upper(), font=(F, 8, 'bold'),
                     bg=SURFACE, fg=TEXT_DIM).pack(anchor=tk.W, pady=(8, 2))
            wf, en = make_entry(wrap, show=show)
            wf.pack(fill=tk.X)
            tk.Label(wrap, text=hint, font=(F, 8), bg=SURFACE, fg=TEXT_DIM).pack(anchor=tk.W)
            err_lbl = tk.Label(wrap, text="", font=(F, 8, 'bold'), bg=SURFACE, fg=RED)
            err_lbl.pack(anchor=tk.W)
            fields[key] = en
            err_labels[key] = err_lbl

        validators = {
            "name":     InputValidator.validate_name,
            "username": InputValidator.validate_username,
            "password": InputValidator.validate_password,
            "email":    InputValidator.validate_email,
        }

        def validate_field(key):
            try:
                validators[key](fields[key].get())
                err_labels[key].config(text="")
                return True
            except ValueError as e:
                err_labels[key].config(text=f"✗  {e}")
                return False

        for key in fields:
            fields[key].bind('<FocusOut>', lambda e, k=key: validate_field(k))

        tk.Label(wrap, text="ACCOUNT TYPE", font=(F, 8, 'bold'),
                 bg=SURFACE, fg=TEXT_DIM).pack(anchor=tk.W, pady=(14, 6))
        type_var = tk.StringVar(value="REGULAR")
        tf = tk.Frame(wrap, bg=SURFACE)
        tf.pack(anchor=tk.W)
        for pt, col in [("REGULAR", BLUE), ("STUDENT", TEAL), ("SENIOR", ORANGE)]:
            tk.Radiobutton(tf, text=pt, variable=type_var, value=pt,
                           font=(F, 10, 'bold'), bg=SURFACE, fg=TEXT_DIM,
                           selectcolor=col, activebackground=SURFACE,
                           indicatoron=0, padx=14, pady=7, relief=tk.FLAT,
                           bd=1, highlightthickness=0).pack(side=tk.LEFT, padx=(0, 6))

        def register():
            all_valid = all(validate_field(k) for k in fields)
            if not all_valid:
                return
            try:
                pt = PassengerType[type_var.get()]
                uname = fields["username"].get().strip()
                self.bart_system.register(
                    uname, fields["password"].get(),
                    fields["email"].get().strip(),
                    fields["name"].get().strip(), pt)
                dlg.destroy()
                Toast(self.root, f"✓  Account created!  Sign in as  {uname}", color=GREEN)
            except Exception as e:
                messagebox.showerror("Registration Failed", str(e))

        ModernButton(wrap, text="CREATE ACCOUNT", font=(F, 12, 'bold'),
            bg=GREEN, fg='white', padx=10, pady=13,
            command=register).pack(fill=tk.X, pady=(14, 20))

    def open_dashboard(self):
        if isinstance(self.current_user, Passenger):
            PassengerDashboard(self.root, self.bart_system, self.current_user, self)
        elif isinstance(self.current_user, SuperAdmin):
            SuperAdminDashboard(self.root, self.bart_system, self.current_user, self)
        elif isinstance(self.current_user, Admin):
            AdminDashboard(self.root, self.bart_system, self.current_user, self)
        else:
            messagebox.showerror("Error", "Unknown user type")


# ── PASSENGER DASHBOARD ────────────────────────────────────

class PassengerDashboard:
    def __init__(self, root, bart_system: BARTSystem, passenger: Passenger, app):
        self.root = root
        self.bart_system = bart_system
        self.passenger = passenger
        self.app = app
        if passenger.card:
            self.card: Card = passenger.card
        else:
            self.card = bart_system.create_card_for_passenger(passenger, 50.00)
        self._displayed_balance = self.card.balance
        self._animating = False

        for w in self.root.winfo_children():
            w.destroy()
        self.root.title(f"BART — {passenger.name}")
        self.root.geometry("1420x900")
        self.root.resizable(True, True)
        self.root.configure(bg=BG)
        self._build()
        self.update_displays()
        self.root.after(900, self._notify_active_alerts)
        self._start_alert_refresh()

    def _notify_active_alerts(self):
        """Show a popup dialog when passenger logs in with active alerts."""
        try:
            alerts = [a for a in self.bart_system.alerts.values() if a.is_active]
            if not alerts:
                return
            n = len(alerts)
            dlg = tk.Toplevel(self.root)
            dlg.title("Service Alerts")
            dlg.configure(bg=RED)
            dlg.resizable(False, False)
            dlg.transient(self.root)
            dlg.grab_set()

            # Center on parent window
            dlg.update_idletasks()
            pw, ph = self.root.winfo_width(), self.root.winfo_height()
            px, py = self.root.winfo_x(), self.root.winfo_y()
            dw, dh = 440, min(120 + n * 80, 420)
            dlg.geometry(f"{dw}x{dh}+{px + (pw - dw) // 2}+{py + (ph - dh) // 2}")

            tk.Frame(dlg, bg='#8b0000', height=4).pack(fill=tk.X)
            tk.Label(dlg, text=f"⚠  {n} ACTIVE SERVICE ALERT{'S' if n > 1 else ''}",
                     font=(F, 14, 'bold'), bg=RED, fg='white').pack(pady=(16, 10), padx=20)

            for a in alerts[:4]:
                row = tk.Frame(dlg, bg='#c0392b', padx=16, pady=8)
                row.pack(fill=tk.X, padx=12, pady=(0, 6))
                tk.Label(row, text=f"[{a.alert_type.value}]  {a.title}",
                         font=(F, 11, 'bold'), bg='#c0392b', fg='white',
                         anchor=tk.W, wraplength=380).pack(anchor=tk.W)
                tk.Label(row, text=a.message, font=(F, 9),
                         bg='#c0392b', fg='#ffdddd',
                         anchor=tk.W, wraplength=380).pack(anchor=tk.W)

            ModernButton(dlg, text="Got it  ✓", font=(F, 11, 'bold'),
                bg='#8b0000', fg='white', padx=24, pady=10,
                command=dlg.destroy).pack(pady=14)
            dlg.after(8000, lambda: dlg.destroy() if dlg.winfo_exists() else None)
        except Exception:
            pass

    def _start_alert_refresh(self):
        try:
            if self.root.winfo_exists():
                self.root.after(8000, self._start_alert_refresh)
                self.update_alerts()
        except Exception:
            pass

    def _build(self):
        # ── Header ────────────────────────────────────────────
        hdr = tk.Frame(self.root, bg=BART_BLUE, height=68)
        hdr.pack(fill=tk.X)
        hdr.pack_propagate(False)
        tk.Frame(hdr, bg=BART_RED, height=4).pack(fill=tk.X, side=tk.BOTTOM)

        lf = tk.Frame(hdr, bg=BART_BLUE)
        lf.pack(side=tk.LEFT, padx=24)
        tk.Label(lf, text="🚇 BART", font=(F, 22, 'bold'), bg=BART_BLUE, fg='white').pack(side=tk.LEFT)
        badge_col = {PassengerType.REGULAR: BLUE, PassengerType.STUDENT: TEAL, PassengerType.SENIOR: ORANGE}
        bc = badge_col.get(self.passenger.passenger_type, BLUE)
        tk.Label(lf, text=f"  {self.passenger.name}", font=(F, 13), bg=BART_BLUE, fg="#aaccff").pack(side=tk.LEFT, padx=(8, 0))
        tk.Label(lf, text=f" {self.passenger.passenger_type.value} ", font=(F, 9, 'bold'),
                 bg=bc, fg='white', padx=6, pady=3).pack(side=tk.LEFT, padx=8)

        rf = tk.Frame(hdr, bg=BART_BLUE)
        rf.pack(side=tk.RIGHT, padx=20)
        ModernButton(rf, text="Logout", font=(F, 10, 'bold'),
            bg=RED, fg='white', padx=14, pady=7, command=self.logout).pack(side=tk.RIGHT, padx=6)
        ModernButton(rf, text="⚙ Profile", font=(F, 10),
            bg=SURFACE2, fg=TEXT_DIM, padx=12, pady=7,
            command=self.edit_profile).pack(side=tk.RIGHT, padx=4)
        self._win_maximized = False
        def _toggle_win():
            self._win_maximized = not self._win_maximized
            self.root.state('zoomed' if self._win_maximized else 'normal')
        ModernButton(rf, text="⛶", font=(F, 13),
            bg=BART_BLUE, fg=TEXT_DIM, padx=8, pady=7,
            command=_toggle_win).pack(side=tk.RIGHT, padx=2)
        self.clock_label = tk.Label(rf, font=(F, 13, 'bold'), bg=BART_BLUE, fg="#ffe082")
        self.clock_label.pack(side=tk.RIGHT, padx=16)
        start_live_clock(self.root, self.clock_label)

        # ── Body: LEFT panel + RIGHT panel ────────────────────
        body = tk.Frame(self.root, bg=BG)
        body.pack(fill=tk.BOTH, expand=True, padx=14, pady=10)

        # ── LEFT (60%): Card | Gates | History ────────────────
        left = tk.Frame(body, bg=BG)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        top_left = tk.Frame(left, bg=BG)
        top_left.pack(fill=tk.X, pady=(0, 8))

        _, b1 = card(top_left, "My Clipper Card", "💳", BLUE,
                     side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 8))
        self._build_card_section(b1)

        _, b2 = card(top_left, "Station Gates", "🚪", GREEN,
                     side=tk.LEFT, fill=tk.BOTH, expand=True)
        self._build_gates_section(b2)

        _, b3 = card(left, "Trip History", "📋", TEAL,
                     fill=tk.BOTH, expand=True)
        self._build_history_section(b3)

        # ── RIGHT (40%): Alerts | Planner | Trains ────────────
        right = tk.Frame(body, bg=BG, width=430)
        right.pack(side=tk.LEFT, fill=tk.BOTH)
        right.pack_propagate(False)

        # Alerts — always at top of right panel, always visible
        alerts_frame, b4 = card(right, "Service Alerts", "⚠", RED, fill=tk.X, pady=(0, 8))
        self._build_alerts_section(b4)

        _, b5 = card(right, "Plan Your Trip", "🗺", PURPLE, fill=tk.X, pady=(0, 8))
        self._build_planner_section(b5)

        _, b6 = card(right, "Live Train Status", "🚆", ORANGE,
                     fill=tk.BOTH, expand=True)
        self._build_trains_section(b6)

    def _build_card_section(self, parent):
        tk.Label(parent, text=f"Card  {self.card.card_id}",
            font=(F, 9), bg=SURFACE, fg=TEXT_DIM).pack(anchor=tk.W)

        self.active_trip_frame = tk.Frame(parent, bg=YELLOW, padx=10, pady=6)
        self.active_trip_label = tk.Label(self.active_trip_frame, text="",
            font=(F, 9, 'bold'), bg=YELLOW, fg="#111")
        self.active_trip_label.pack()

        tk.Label(parent, text="Balance", font=(F, 9),
                 bg=SURFACE, fg=TEXT_DIM).pack(anchor=tk.W, pady=(10, 0))
        self.balance_label = tk.Label(parent, text="$0.00",
            font=(F, 32, 'bold'), bg=SURFACE, fg=GREEN)
        self.balance_label.pack(anchor=tk.W)

        st_color = GREEN if self.card.is_active() else RED
        tk.Label(parent, text=f"  {self.card.status.value}  ",
                 font=(F, 9, 'bold'), bg=st_color, fg='white').pack(anchor=tk.W, pady=(4, 12))

        ModernButton(parent, text="💳  Add Funds", font=(F, 10, 'bold'),
            bg=GREEN, fg='white', padx=12, pady=8,
            command=self._payment_dialog).pack(fill=tk.X, pady=(6, 0))

    def _build_gates_section(self, parent):
        stations = [f"{s.name} (Z{s.zone})" for s in self.bart_system.get_all_stations()]
        tk.Label(parent, text="Select Station", font=(F, 9, 'bold'),
                 bg=SURFACE, fg=TEXT_DIM).pack(anchor=tk.W, pady=(0, 6))
        self.gate_station_var = tk.StringVar()
        dark_combo(parent, self.gate_station_var, stations, width=22).pack(fill=tk.X, pady=(0, 12))

        ModernButton(parent, text="▶  TAP IN", font=(F, 12, 'bold'),
            bg=GREEN, fg='white', padx=10, pady=12,
            command=self.tap_in).pack(fill=tk.X, pady=(0, 6))
        ModernButton(parent, text="◀  TAP OUT", font=(F, 12, 'bold'),
            bg=RED, fg='white', padx=10, pady=12,
            command=self.tap_out).pack(fill=tk.X)

    def _build_planner_section(self, parent):
        stations = [f"{s.name} (Z{s.zone})" for s in self.bart_system.get_all_stations()]
        row = tk.Frame(parent, bg=SURFACE)
        row.pack(fill=tk.X, pady=(0, 8))

        lc = tk.Frame(row, bg=SURFACE)
        lc.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 8))
        tk.Label(lc, text="FROM", font=(F, 8, 'bold'), bg=SURFACE, fg=TEXT_DIM).pack(anchor=tk.W, pady=(0, 4))
        self.from_station_var = tk.StringVar()
        dark_combo(lc, self.from_station_var, stations, width=18).pack(fill=tk.X)

        rc = tk.Frame(row, bg=SURFACE)
        rc.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tk.Label(rc, text="TO", font=(F, 8, 'bold'), bg=SURFACE, fg=TEXT_DIM).pack(anchor=tk.W, pady=(0, 4))
        self.to_station_var = tk.StringVar()
        dark_combo(rc, self.to_station_var, stations, width=18).pack(fill=tk.X)

        ModernButton(parent, text="Calculate Fare & Time", font=(F, 10, 'bold'),
            bg=PURPLE, fg='white', padx=10, pady=9,
            command=self.plan_trip).pack(fill=tk.X, pady=(0, 6))

        self.plan_result_label = tk.Label(parent, text="",
            font=(F, 10), bg=SURFACE, fg=TEXT, justify=tk.LEFT, wraplength=380)
        self.plan_result_label.pack(anchor=tk.W)

    def _build_history_section(self, parent):
        cols = ("From", "To", "Date", "Fare", "Status")
        sb = ttk.Scrollbar(parent, style='D.Vertical.TScrollbar')
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.trip_tree = ttk.Treeview(parent, columns=cols, show='headings',
                                       yscrollcommand=sb.set, height=10, style='D.Treeview')
        for c, w in [("From", 130), ("To", 130), ("Date", 90), ("Fare", 80), ("Status", 90)]:
            self.trip_tree.heading(c, text=c)
            self.trip_tree.column(c, width=w, anchor=tk.CENTER)
        self.trip_tree.pack(fill=tk.BOTH, expand=True)
        sb.config(command=self.trip_tree.yview)

    def _build_trains_section(self, parent):
        cols = ("Line", "Status", "Location", "ETA")
        sb = ttk.Scrollbar(parent, style='D.Vertical.TScrollbar')
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.live_train_tree = ttk.Treeview(parent, columns=cols, show='headings',
                                             yscrollcommand=sb.set, height=6, style='D.Treeview')
        for c, w in [("Line", 110), ("Status", 100), ("Location", 130), ("ETA", 60)]:
            self.live_train_tree.heading(c, text=c)
            self.live_train_tree.column(c, width=w, anchor=tk.CENTER)
        self.live_train_tree.pack(fill=tk.BOTH, expand=True)
        sb.config(command=self.live_train_tree.yview)
        ModernButton(parent, text="↻ Refresh", font=(F, 9),
            bg=ORANGE, fg='white', padx=10, pady=4,
            command=self.update_live_trains).pack(pady=(6, 0), anchor=tk.E)

    def _build_alerts_section(self, parent):
        """Alerts rendered as stacked cards, refreshable."""
        self.alerts_list_frame = tk.Frame(parent, bg=SURFACE)
        self.alerts_list_frame.pack(fill=tk.X)
        ModernButton(parent, text="↻ Refresh", font=(F, 8),
            bg=SURFACE2, fg=TEXT_DIM, padx=8, pady=3,
            command=self.update_alerts).pack(anchor=tk.E, pady=(4, 0))

    # Data methods
    def _animate_balance(self, start, end, step=0, steps=20):
        try:
            if not self.root.winfo_exists():
                return
            if step <= steps:
                val = start + (end - start) * (step / steps)
                color = GREEN if end >= start else RED
                self.balance_label.config(text=f"${val:.2f}", fg=color)
                self._anim_id = self.root.after(
                    18, lambda: self._animate_balance(start, end, step + 1, steps))
            else:
                self.balance_label.config(text=f"${end:.2f}", fg=GREEN)
                self._displayed_balance = end
                self._animating = False
        except Exception:
            self._animating = False

    def update_displays(self):
        if self.card:
            nb = self.card.balance
            if abs(nb - self._displayed_balance) > 0.001 and not self._animating:
                self._animating = True
                self._animate_balance(self._displayed_balance, nb)
            else:
                self.balance_label.config(text=f"${nb:.2f}")

            active = self.bart_system.get_active_trip(self.card)
            if active:
                self.active_trip_frame.pack(fill=tk.X, pady=(8, 0))
                self.active_trip_label.config(
                    text=f"🟡  Active from {active.entry_station.name}  •  {active.start_time.strftime('%H:%M')}")
            else:
                self.active_trip_frame.pack_forget()

            self.update_trip_history()
            self.update_live_trains()
            self.update_alerts()

    def update_trip_history(self):
        for i in self.trip_tree.get_children():
            self.trip_tree.delete(i)
        for trip in self.bart_system.get_passenger_trips(self.passenger)[:25]:
            to = trip.exit_station.name if trip.exit_station else "In Progress"
            self.trip_tree.insert("", tk.END, values=(
                trip.entry_station.name, to,
                trip.start_time.strftime("%m/%d"),
                f"${trip.fare:.2f}" if trip.fare else "—",
                trip.status.value))

    def update_live_trains(self):
        for i in self.live_train_tree.get_children():
            self.live_train_tree.delete(i)
        for train in self.bart_system.get_all_trains():
            loc = train.current_station.name if train.current_station else "In Transit"
            eta = f"{train.eta_minutes}m" if train.eta_minutes else "—"
            tag = "delayed" if train.status.value == "DELAYED" else "ok"
            self.live_train_tree.insert("", tk.END,
                values=(train.line, train.status.value, loc, eta), tags=(tag,))
        self.live_train_tree.tag_configure("delayed", foreground=YELLOW)
        self.live_train_tree.tag_configure("ok", foreground=GREEN)

    def update_alerts(self):
        for w in self.alerts_list_frame.winfo_children():
            w.destroy()
        alerts = [a for a in self.bart_system.alerts.values() if a.is_active]
        if not alerts:
            tk.Label(self.alerts_list_frame,
                     text="✓  All systems operational",
                     font=(F, 10), bg=SURFACE, fg=GREEN,
                     pady=14).pack(fill=tk.X, padx=10)
        else:
            for a in alerts[:5]:
                row = tk.Frame(self.alerts_list_frame, bg=SURFACE2, padx=12, pady=8)
                row.pack(fill=tk.X, pady=(0, 4))
                hdr_row = tk.Frame(row, bg=SURFACE2)
                hdr_row.pack(fill=tk.X)
                tk.Label(hdr_row, text=f"⚠  [{a.alert_type.value}]",
                         font=(F, 8, 'bold'), bg=SURFACE2, fg=RED).pack(side=tk.LEFT)
                tk.Label(hdr_row, text=f"  {a.title}",
                         font=(F, 10, 'bold'), bg=SURFACE2, fg=YELLOW).pack(side=tk.LEFT)
                tk.Label(row, text=a.message, font=(F, 9),
                         bg=SURFACE2, fg=TEXT_DIM, wraplength=380,
                         justify=tk.LEFT).pack(anchor=tk.W, pady=(4, 0))

    def plan_trip(self):
        ft = self.from_station_var.get()
        tt = self.to_station_var.get()
        if not ft or not tt:
            messagebox.showerror("Error", "Please select both stations")
            return
        fn = ft.split(" (Z")[0]
        tn = tt.split(" (Z")[0]
        fs = ts = None
        for s in self.bart_system.get_all_stations():
            if s.name == fn: fs = s
            if s.name == tn: ts = s
        if not fs or not ts:
            messagebox.showerror("Error", "Could not find selected station(s)")
            return
        p = self.bart_system.plan_trip(fs, ts, self.passenger)
        disc = f"\n✓ {self.passenger.passenger_type.value} discount applied" if p['discount_applied'] else ""
        self.plan_result_label.config(text=(
            f"💰  Fare: ${p['fare']:.2f}{disc}\n"
            f"⏱  Est. Time: {p['estimated_time']} min\n"
            f"🗺  Zone diff: {p['zones']}"))

    def tap_in(self):
        st = self.gate_station_var.get()
        if not st:
            messagebox.showerror("Error", "Please select a station")
            return
        name = st.split(" (Z")[0]
        station = next((s for s in self.bart_system.get_all_stations() if s.name == name), None)
        if station:
            try:
                trip = self.bart_system.tap_entry(self.card, station)
                Toast(self.root,
                      f"✓  Tapped in at {station.name}  •  {trip.start_time.strftime('%H:%M:%S')}",
                      color=GREEN)
                self.update_displays()
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def tap_out(self):
        st = self.gate_station_var.get()
        if not st:
            messagebox.showerror("Error", "Please select a station")
            return
        name = st.split(" (Z")[0]
        station = next((s for s in self.bart_system.get_all_stations() if s.name == name), None)
        if station:
            try:
                trip, fare = self.bart_system.tap_exit(self.card, station)
                disc = f"  ({self.passenger.passenger_type.value} discount)" if self.passenger.get_discount_rate() > 0 else ""
                Toast(self.root,
                      f"✓  {trip.entry_station.name} → {station.name}  |  Fare: ${fare:.2f}{disc}  |  Balance: ${self.card.balance:.2f}",
                      color=TEAL, dur=4000)
                self.update_displays()
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def _payment_dialog(self):
        dlg = tk.Toplevel(self.root)
        dlg.title("Add Funds — Clipper Card")
        dlg.geometry("520x620")
        dlg.resizable(False, False)
        dlg.configure(bg=SURFACE)
        dlg.transient(self.root)
        dlg.grab_set()

        tk.Frame(dlg, bg=GREEN, height=5).pack(fill=tk.X)
        tk.Label(dlg, text="💳  Add Funds to Clipper Card",
                 font=(F, 16, 'bold'), bg=SURFACE, fg=TEXT).pack(pady=(16, 2))
        tk.Label(dlg, text=f"Card {self.card.card_id}  •  Balance: ${self.card.balance:.2f}",
                 font=(F, 10), bg=SURFACE, fg=TEXT_DIM).pack()

        # ── Amount ──────────────────────────────────────────
        amt_frame = tk.Frame(dlg, bg=SURFACE, padx=30)
        amt_frame.pack(fill=tk.X, pady=(14, 0))
        tk.Label(amt_frame, text="AMOUNT TO ADD", font=(F, 8, 'bold'),
                 bg=SURFACE, fg=TEXT_DIM).pack(anchor=tk.W, pady=(0, 6))
        amt_row = tk.Frame(amt_frame, bg=SURFACE2, padx=12, pady=8)
        amt_row.pack(fill=tk.X)
        tk.Label(amt_row, text="$", font=(F, 18, 'bold'), bg=SURFACE2, fg=GREEN).pack(side=tk.LEFT)
        amt_entry = tk.Entry(amt_row, font=(F, 18, 'bold'), width=8,
            bg=SURFACE2, fg=GREEN, relief=tk.FLAT, insertbackground=CYAN, bd=0)
        amt_entry.insert(0, "20.00")
        amt_entry.pack(side=tk.LEFT, padx=6)
        # Quick-fill buttons
        quick_row = tk.Frame(amt_frame, bg=SURFACE)
        quick_row.pack(fill=tk.X, pady=(6, 0))
        for qv in ["10", "20", "50", "100"]:
            def _fill(v=qv): amt_entry.delete(0, tk.END); amt_entry.insert(0, v + ".00")
            tk.Button(quick_row, text=f"${qv}", font=(F, 9, 'bold'), bg=SURFACE2, fg=TEXT_DIM,
                relief=tk.FLAT, bd=0, cursor='hand2', padx=10, pady=4,
                activebackground=BLUE, activeforeground='white',
                command=_fill).pack(side=tk.LEFT, padx=(0, 6))

        # ── Payment Method ───────────────────────────────────
        method_frame = tk.Frame(dlg, bg=SURFACE, padx=30)
        method_frame.pack(fill=tk.X, pady=(16, 0))
        tk.Label(method_frame, text="PAYMENT METHOD", font=(F, 8, 'bold'),
                 bg=SURFACE, fg=TEXT_DIM).pack(anchor=tk.W, pady=(0, 8))

        method_var = tk.StringVar(value="quick")
        btn_row = tk.Frame(method_frame, bg=SURFACE)
        btn_row.pack(fill=tk.X)
        method_btns = {}
        for mid, label, icon in [("quick", "Quick Add", "⚡"),
                                   ("card",  "Bank Card", "💳"),
                                   ("apple", "Apple Pay", "")]:
            def _sel(m=mid):
                method_var.set(m)
                for k, b in method_btns.items():
                    b.config(bg=BLUE if k == m else SURFACE2,
                             fg='white' if k == m else TEXT_DIM)
                _show_panel()
            b = tk.Button(btn_row, text=f"{icon}  {label}", font=(F, 10, 'bold'),
                bg=BLUE if mid == "quick" else SURFACE2,
                fg='white' if mid == "quick" else TEXT_DIM,
                relief=tk.FLAT, bd=0, cursor='hand2', padx=14, pady=10,
                activebackground=BLUE, activeforeground='white', command=_sel)
            b.pack(side=tk.LEFT, padx=(0, 6))
            method_btns[mid] = b

        # ── Dynamic panel ────────────────────────────────────
        panel_host = tk.Frame(dlg, bg=SURFACE, padx=30)
        panel_host.pack(fill=tk.X, pady=12)
        panel_host.pack_propagate(False)
        panel_host.config(height=160)

        # Card fields (hidden by default)
        card_panel = tk.Frame(panel_host, bg=SURFACE)
        # Card number with auto-spacing
        tk.Label(card_panel, text="CARD NUMBER", font=(F, 8, 'bold'),
                 bg=SURFACE, fg=TEXT_DIM).pack(anchor=tk.W, pady=(0, 4))
        card_num_var = tk.StringVar()
        def _fmt_card(*_):
            raw = card_num_var.get().replace(" ", "").replace("-", "")[:16]
            spaced = " ".join(raw[i:i+4] for i in range(0, len(raw), 4))
            if card_num_var.get() != spaced:
                card_num_var.set(spaced)
        card_num_e = tk.Entry(card_panel, textvariable=card_num_var,
            font=(F, 14, 'bold'), bg=SURFACE2, fg=CYAN,
            relief=tk.FLAT, bd=0, insertbackground=CYAN, width=24)
        card_num_e.pack(fill=tk.X, ipady=8, pady=(0, 8))
        card_num_var.trace_add('write', _fmt_card)

        sub_row = tk.Frame(card_panel, bg=SURFACE)
        sub_row.pack(fill=tk.X, pady=(0, 8))
        for lbl, w in [("NAME ON CARD", 18), ("EXPIRY MM/YY", 8), ("CVV", 5)]:
            col = tk.Frame(sub_row, bg=SURFACE)
            col.pack(side=tk.LEFT, padx=(0, 12))
            tk.Label(col, text=lbl, font=(F, 7, 'bold'), bg=SURFACE, fg=TEXT_DIM).pack(anchor=tk.W)
            e = tk.Entry(col, font=(F, 11), width=w, bg=SURFACE2, fg=TEXT,
                         relief=tk.FLAT, bd=0, insertbackground=CYAN)
            e.pack(ipady=6)
        card_panel.pack_forget()

        # Apple Pay panel
        apple_panel = tk.Frame(panel_host, bg=SURFACE)
        tk.Label(apple_panel, text=" Pay", font=("Helvetica", 26, 'bold'),
                 bg=SURFACE, fg=TEXT).pack(pady=(10, 4))
        tk.Label(apple_panel, text="Double-click to authenticate with Face ID",
                 font=(F, 10), bg=SURFACE, fg=TEXT_DIM).pack()
        apple_panel.pack_forget()

        # Quick panel
        quick_panel = tk.Frame(panel_host, bg=SURFACE)
        tk.Label(quick_panel, text="⚡  Funds added instantly — no card required",
                 font=(F, 11), bg=SURFACE, fg=TEXT_DIM).pack(pady=20)
        quick_panel.pack(fill=tk.X)

        def _show_panel():
            quick_panel.pack_forget()
            card_panel.pack_forget()
            apple_panel.pack_forget()
            m = method_var.get()
            if m == "card":   card_panel.pack(fill=tk.X)
            elif m == "apple": apple_panel.pack(fill=tk.X)
            else:             quick_panel.pack(fill=tk.X)

        # ── Error + confirm ──────────────────────────────────
        err_lbl = tk.Label(dlg, text="", font=(F, 9, 'bold'), bg=SURFACE, fg=RED)
        err_lbl.pack(padx=30, anchor=tk.W)

        def _process():
            try:
                amt = float(amt_entry.get())
                if amt <= 0:
                    err_lbl.config(text="✗  Amount must be greater than $0.00"); return
                if amt > 500:
                    err_lbl.config(text="✗  Maximum single top-up is $500.00"); return
                method = method_var.get()
                if method == "card":
                    raw = card_num_var.get().replace(" ", "")
                    if len(raw) != 16 or not raw.isdigit():
                        err_lbl.config(text="✗  Enter a valid 16-digit card number"); return
                self.bart_system.top_up_card(self.card, amt)
                method_label = {"quick": "Quick Add", "card": "Bank Card", "apple": "Apple Pay"}[method]
                Toast(self.root,
                      f"✓  +${amt:.2f} added via {method_label}  •  Balance: ${self.card.balance:.2f}",
                      color=GREEN, dur=4000)
                dlg.destroy()
                self.update_displays()
            except ValueError as e:
                err_lbl.config(text=f"✗  {e}")

        ModernButton(dlg, text="✓  Confirm & Add Funds", font=(F, 12, 'bold'),
            bg=GREEN, fg='white', padx=16, pady=14,
            command=_process).pack(fill=tk.X, padx=30, pady=(4, 6))
        ModernButton(dlg, text="Cancel", font=(F, 10),
            bg=SURFACE2, fg=TEXT_DIM, padx=16, pady=10,
            command=dlg.destroy).pack(fill=tk.X, padx=30)

    def edit_profile(self):
        dlg = tk.Toplevel(self.root)
        dlg.title("Edit Profile")
        dlg.geometry("460x430")
        dlg.configure(bg=SURFACE)
        dlg.transient(self.root)
        dlg.grab_set()

        tk.Frame(dlg, bg=PURPLE, height=5).pack(fill=tk.X)
        tk.Label(dlg, text="Edit Profile", font=(F, 18, 'bold'),
                 bg=SURFACE, fg=TEXT).pack(pady=20)

        info = tk.Frame(dlg, bg=SURFACE2, padx=16, pady=12)
        info.pack(fill=tk.X, padx=30, pady=(0, 16))
        for lbl in [f"User ID: {self.passenger.user_id}", f"Email: {self.passenger.email}"]:
            tk.Label(info, text=lbl, font=(F, 10), bg=SURFACE2, fg=TEXT_DIM).pack(anchor=tk.W, pady=2)

        wrap = tk.Frame(dlg, bg=SURFACE, padx=30)
        wrap.pack(fill=tk.X)
        tk.Label(wrap, text="DISPLAY NAME", font=(F, 8, 'bold'),
                 bg=SURFACE, fg=TEXT_DIM).pack(anchor=tk.W, pady=(0, 5))
        nf, name_entry = make_entry(wrap)
        name_entry.insert(0, self.passenger.name)
        nf.pack(fill=tk.X, pady=(0, 14))

        tk.Label(wrap, text="ACCOUNT TYPE", font=(F, 8, 'bold'),
                 bg=SURFACE, fg=TEXT_DIM).pack(anchor=tk.W, pady=(0, 6))
        type_var = tk.StringVar(value=self.passenger.passenger_type.name)
        tf = tk.Frame(wrap, bg=SURFACE)
        tf.pack(anchor=tk.W)
        for pt in ["REGULAR", "STUDENT", "SENIOR"]:
            tk.Radiobutton(tf, text=pt, variable=type_var, value=pt,
                           font=(F, 10, 'bold'), bg=SURFACE, fg=TEXT_DIM,
                           selectcolor=SURFACE2, activebackground=SURFACE,
                           indicatoron=0, padx=14, pady=7, relief=tk.FLAT,
                           bd=1, highlightthickness=0).pack(side=tk.LEFT, padx=(0, 6))

        def save():
            try:
                nn = InputValidator.validate_name(name_entry.get())
            except ValueError as e:
                messagebox.showerror("Invalid Name", str(e))
                return
            try:
                self.passenger.name = nn
                self.passenger.passenger_type = PassengerType[type_var.get()]
                self.root.title(f"BART — {nn}")
                Toast(self.root, f"✓  Profile updated — {nn}", color=PURPLE)
                dlg.destroy()
            except Exception as e:
                messagebox.showerror("Error", str(e))

        ModernButton(wrap, text="SAVE CHANGES", font=(F, 12, 'bold'),
            bg=GREEN, fg='white', padx=10, pady=12, command=save).pack(fill=tk.X, pady=18)

    def logout(self):
        self.app.current_user = None
        self.app.show_login_screen()


# ── GUEST DASHBOARD ────────────────────────────────────────

class GuestDashboard:
    def __init__(self, root, bart_system: BARTSystem, app):
        self.root = root
        self.bart_system = bart_system
        self.app = app
        for w in self.root.winfo_children():
            w.destroy()
        self.root.title("BART — Guest Mode")
        self.root.geometry("1000x720")
        self.root.configure(bg=BG)
        self._build()
        self.update_displays()

    def _build(self):
        hdr = tk.Frame(self.root, bg=SURFACE2, height=70)
        hdr.pack(fill=tk.X)
        hdr.pack_propagate(False)
        tk.Frame(hdr, bg=BART_RED, height=4).pack(fill=tk.X, side=tk.BOTTOM)

        lf = tk.Frame(hdr, bg=SURFACE2)
        lf.pack(side=tk.LEFT, padx=24, pady=14)
        tk.Label(lf, text="🚇 BART", font=(F, 20, 'bold'), bg=SURFACE2, fg=TEXT).pack(side=tk.LEFT)
        tk.Label(lf, text="  Guest Mode — Plan trips & check arrivals",
                 font=(F, 10), bg=SURFACE2, fg=TEXT_DIM).pack(side=tk.LEFT, pady=4)
        ModernButton(hdr, text="Sign In / Register", font=(F, 11, 'bold'),
            bg=GREEN, fg='white', padx=16, pady=10,
            command=self.go_to_login).pack(side=tk.RIGHT, padx=20)

        body = tk.Frame(self.root, bg=BG)
        body.pack(fill=tk.BOTH, expand=True, padx=16, pady=12)

        left = tk.Frame(body, bg=BG)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 8))
        right = tk.Frame(body, bg=BG, width=340)
        right.pack(side=tk.LEFT, fill=tk.BOTH)
        right.pack_propagate(False)

        _, pb = card(left, "Plan Your Trip", "🗺", PURPLE, fill=tk.X, pady=(0, 8))
        self._build_planner(pb)
        _, tb = card(left, "Real-time Train Info", "🚆", ORANGE, fill=tk.BOTH, expand=True)
        self._build_trains(tb)

        _, ab = card(right, "Service Alerts", "⚠", RED, fill=tk.X, pady=(0, 8))
        self.alerts_text = tk.Text(ab, height=7, font=(F, 9), bg=SURFACE2, fg=TEXT,
                                    relief=tk.FLAT, wrap=tk.WORD, bd=0, state=tk.DISABLED)
        self.alerts_text.pack(fill=tk.X)

        _, sb2 = card(right, "Station Status", "📍", TEAL, fill=tk.BOTH, expand=True)
        self._build_stations(sb2)

    def _build_planner(self, parent):
        stations = [f"{s.name} (Z{s.zone})" for s in self.bart_system.get_all_stations()]
        tk.Label(parent, text="FROM", font=(F, 9, 'bold'), bg=SURFACE, fg=TEXT_DIM).pack(anchor=tk.W, pady=(0, 4))
        self.from_station_var = tk.StringVar()
        dark_combo(parent, self.from_station_var, stations, width=38).pack(fill=tk.X, pady=(0, 10))
        tk.Label(parent, text="TO", font=(F, 9, 'bold'), bg=SURFACE, fg=TEXT_DIM).pack(anchor=tk.W, pady=(0, 4))
        self.to_station_var = tk.StringVar()
        dark_combo(parent, self.to_station_var, stations, width=38).pack(fill=tk.X, pady=(0, 12))
        ModernButton(parent, text="Calculate Fare & Time", font=(F, 11, 'bold'),
            bg=PURPLE, fg='white', padx=10, pady=10,
            command=self.plan_trip).pack(fill=tk.X, pady=(0, 10))
        self.plan_result_label = tk.Label(parent, text="", font=(F, 10),
            bg=SURFACE, fg=TEXT, justify=tk.LEFT, wraplength=400)
        self.plan_result_label.pack(anchor=tk.W)

    def _build_trains(self, parent):
        cols = ("Train", "Line", "Status", "Location")
        sb = ttk.Scrollbar(parent, style='D.Vertical.TScrollbar')
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.train_tree = ttk.Treeview(parent, columns=cols, show='headings',
                                        yscrollcommand=sb.set, height=8, style='D.Treeview')
        for c in cols:
            self.train_tree.heading(c, text=c)
            self.train_tree.column(c, width=120, anchor=tk.CENTER)
        self.train_tree.pack(fill=tk.BOTH, expand=True)
        sb.config(command=self.train_tree.yview)

    def _build_stations(self, parent):
        cols = ("Station", "Zone", "Status")
        self.station_tree = ttk.Treeview(parent, columns=cols, show='headings',
                                          height=10, style='D.Treeview')
        for c in cols:
            self.station_tree.heading(c, text=c)
            self.station_tree.column(c, width=90, anchor=tk.CENTER)
        self.station_tree.pack(fill=tk.BOTH, expand=True)

    def update_displays(self):
        self.update_trains()
        self.update_alerts()
        self.update_stations()

    def update_trains(self):
        for i in self.train_tree.get_children():
            self.train_tree.delete(i)
        for t in self.bart_system.get_all_trains():
            loc = t.current_station.name if t.current_station else "In Transit"
            self.train_tree.insert("", tk.END, values=(t.train_id, t.line, t.status.value, loc))

    def update_alerts(self):
        self.alerts_text.config(state=tk.NORMAL)
        self.alerts_text.delete(1.0, tk.END)
        alerts = [a for a in self.bart_system.alerts.values() if a.is_active]
        if not alerts:
            self.alerts_text.config(fg=GREEN)
            self.alerts_text.insert(tk.END, "✓  All systems operational.")
        else:
            self.alerts_text.config(fg=YELLOW)
            for i, a in enumerate(alerts[:5], 1):
                self.alerts_text.insert(tk.END, f"⚠  [{a.alert_type.value}]  {a.title}\n   {a.message}\n\n")
        self.alerts_text.config(state=tk.DISABLED)

    def update_stations(self):
        for i in self.station_tree.get_children():
            self.station_tree.delete(i)
        for s in self.bart_system.get_all_stations():
            self.station_tree.insert("", tk.END, values=(s.name, s.zone, s.status.value))

    def plan_trip(self):
        ft = self.from_station_var.get()
        tt = self.to_station_var.get()
        if not ft or not tt:
            messagebox.showerror("Error", "Please select both stations")
            return
        fn = ft.split(" (Z")[0]
        tn = tt.split(" (Z")[0]
        fs = ts = None
        for s in self.bart_system.get_all_stations():
            if s.name == fn: fs = s
            if s.name == tn: ts = s
        if fs and ts:
            p = self.bart_system.plan_trip(fs, ts, None)
            self.plan_result_label.config(text=(
                f"📍  {p['start']}  →  {p['end']}\n"
                f"💰  Fare: ${p['fare']:.2f}  (sign in for discounts)\n"
                f"⏱  Est. Time: {p['estimated_time']} min  •  {p['zones']} zone(s)"))

    def go_to_login(self):
        self.app.show_login_screen()


# ── ADMIN DASHBOARD ────────────────────────────────────────

class AdminDashboard:
    def __init__(self, root, bart_system: BARTSystem, admin, app):
        self.root = root
        self.bart_system = bart_system
        self.admin = admin
        self.app = app
        for w in self.root.winfo_children():
            w.destroy()
        self.root.title(f"BART Admin — {admin.name}")
        self.root.geometry("1400x900")
        self.root.configure(bg=BG)
        self._build()
        self.update_displays()

    def _build(self):
        hdr = tk.Frame(self.root, bg=SURFACE2, height=72)
        hdr.pack(fill=tk.X)
        hdr.pack_propagate(False)
        tk.Frame(hdr, bg=ORANGE, height=4).pack(fill=tk.X, side=tk.BOTTOM)

        lf = tk.Frame(hdr, bg=SURFACE2)
        lf.pack(side=tk.LEFT, padx=24, pady=12)
        tk.Label(lf, text="🔧 BART Admin Portal", font=(F, 20, 'bold'),
                 bg=SURFACE2, fg=TEXT).pack(anchor=tk.W)
        tk.Label(lf, text=f"Operator: {self.admin.name}  •  {getattr(self.admin, 'department', 'Operations')}",
                 font=(F, 10), bg=SURFACE2, fg=TEXT_DIM).pack(anchor=tk.W)

        rf = tk.Frame(hdr, bg=SURFACE2)
        rf.pack(side=tk.RIGHT, padx=20)
        ModernButton(rf, text="Logout", font=(F, 10, 'bold'),
            bg=RED, fg='white', padx=16, pady=8, command=self.logout).pack(side=tk.RIGHT, padx=6)
        ModernButton(rf, text="↻ Refresh", font=(F, 10),
            bg=SURFACE, fg=TEXT_DIM, padx=14, pady=8,
            command=self.update_displays).pack(side=tk.RIGHT, padx=4)
        self._win_max = False
        def _toggle_win():
            self._win_max = not self._win_max
            self.root.state('zoomed' if self._win_max else 'normal')
        ModernButton(rf, text="⛶", font=(F, 13),
            bg=SURFACE2, fg=TEXT_DIM, padx=8, pady=8,
            command=_toggle_win).pack(side=tk.RIGHT, padx=2)

        body = tk.Frame(self.root, bg=BG)
        body.pack(fill=tk.BOTH, expand=True, padx=16, pady=12)

        self.notebook = ttk.Notebook(body, style='D.TNotebook')
        self.notebook.pack(fill=tk.BOTH, expand=True)

        for title, builder in [
            ("📊  Dashboard", self._build_dashboard_tab),
            ("🚉  Stations",  self._build_station_tab),
            ("🚆  Trains",    self._build_train_tab),
            ("⚠   Alerts",   self._build_alerts_tab),
        ]:
            frame = tk.Frame(self.notebook, bg=BG)
            self.notebook.add(frame, text=title)
            builder(frame)

    def _build_dashboard_tab(self, parent):
        self.stats_labels = {}
        cfg = [("Total Trips", "total_trips", BLUE),
               ("Active Trips", "active_trips", RED),
               ("Revenue", "total_revenue", GREEN),
               ("Total Users", "total_users", PURPLE)]

        wrap = tk.Frame(parent, bg=BG, padx=16, pady=16)
        wrap.pack(fill=tk.BOTH, expand=True)

        # Service status banner
        in_svc = BARTSystem.is_service_hours()
        svc_col = GREEN if in_svc else PURPLE
        svc_txt = "🟢  BART IN SERVICE  (5:00 AM – 12:30 AM)" if in_svc \
            else "🌙  NIGHT SUSPENSION  (12:30 AM – 5:00 AM)  — Trains halted"
        self.service_banner = tk.Label(wrap, text=svc_txt, font=(F, 10, 'bold'),
            bg=svc_col, fg='white', padx=16, pady=8, anchor=tk.W)
        self.service_banner.pack(fill=tk.X, pady=(0, 16))

        tk.Label(wrap, text="System Overview", font=(F, 18, 'bold'),
                 bg=BG, fg=TEXT).pack(anchor=tk.W, pady=(0, 14))

        row = tk.Frame(wrap, bg=BG)
        row.pack(fill=tk.X)
        for label, key, color in cfg:
            c = tk.Frame(row, bg=SURFACE)
            c.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
            tk.Frame(c, bg=color, height=5).pack(fill=tk.X)
            inner = tk.Frame(c, bg=SURFACE, padx=20, pady=16)
            inner.pack(fill=tk.BOTH, expand=True)
            tk.Label(inner, text=label, font=(F, 9, 'bold'),
                     bg=SURFACE, fg=TEXT_DIM).pack(anchor=tk.W)
            vl = tk.Label(inner, text="0", font=(F, 28, 'bold'), bg=SURFACE, fg=color)
            vl.pack(anchor=tk.W, pady=(6, 0))
            self.stats_labels[key] = vl

        ModernButton(wrap, text="📊  Generate Ridership Report", font=(F, 11, 'bold'),
            bg=BLUE, fg='white', padx=20, pady=12,
            command=self.generate_report).pack(anchor=tk.W, pady=16)

    def _build_station_tab(self, parent):
        _, b = card(parent, "Station Management", "🚉", TEAL,
                    fill=tk.BOTH, expand=True, padx=16, pady=16)
        cols = ("Name", "Zone", "Status")
        sb = ttk.Scrollbar(b, style='D.Vertical.TScrollbar')
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.station_tree = ttk.Treeview(b, columns=cols, show='headings',
                                          yscrollcommand=sb.set, height=16, style='D.Treeview')
        for c in cols:
            self.station_tree.heading(c, text=c)
            self.station_tree.column(c, width=180, anchor=tk.CENTER)
        self.station_tree.pack(fill=tk.BOTH, expand=True)
        sb.config(command=self.station_tree.yview)
        bf = tk.Frame(b, bg=SURFACE)
        bf.pack(fill=tk.X, pady=(10, 0))
        ModernButton(bf, text="Close Station", bg=RED, fg='white', padx=14, pady=8,
            command=self.close_selected_station).pack(side=tk.LEFT, padx=(0, 8))
        ModernButton(bf, text="Open Station", bg=GREEN, fg='white', padx=14, pady=8,
            command=self.open_selected_station).pack(side=tk.LEFT)

    def _build_train_tab(self, parent):
        _, b = card(parent, "Train Management", "🚆", ORANGE,
                    fill=tk.BOTH, expand=True, padx=16, pady=16)
        cols = ("ID", "Line", "Status", "Location")
        sb = ttk.Scrollbar(b, style='D.Vertical.TScrollbar')
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.train_tree = ttk.Treeview(b, columns=cols, show='headings',
                                        yscrollcommand=sb.set, height=16, style='D.Treeview')
        for c, w in [("ID", 80), ("Line", 140), ("Status", 120), ("Location", 180)]:
            self.train_tree.heading(c, text=c)
            self.train_tree.column(c, width=w, anchor=tk.CENTER)
        self.train_tree.pack(fill=tk.BOTH, expand=True)
        sb.config(command=self.train_tree.yview)
        bf = tk.Frame(b, bg=SURFACE)
        bf.pack(fill=tk.X, pady=(10, 0))
        for txt, st, col in [("Set Running", TrainStatus.RUNNING, GREEN),
                               ("Set Delayed", TrainStatus.DELAYED, YELLOW),
                               ("Out of Service", TrainStatus.OUT_OF_SERVICE, RED)]:
            ModernButton(bf, text=txt, bg=col, fg='white' if col != YELLOW else '#111',
                padx=12, pady=8, command=lambda s=st: self.update_train_status(s)).pack(side=tk.LEFT, padx=(0, 8))

    def _build_alerts_tab(self, parent):
        _, b = card(parent, "Service Alerts", "⚠", RED,
                    fill=tk.BOTH, expand=True, padx=16, pady=16)
        cols = ("Type", "Title", "Created", "Status")
        sb = ttk.Scrollbar(b, style='D.Vertical.TScrollbar')
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.alert_tree = ttk.Treeview(b, columns=cols, show='headings',
                                        yscrollcommand=sb.set, height=14, style='D.Treeview')
        for c, w in [("Type", 100), ("Title", 280), ("Created", 150), ("Status", 80)]:
            self.alert_tree.heading(c, text=c)
            self.alert_tree.column(c, width=w, anchor=tk.CENTER)
        self.alert_tree.pack(fill=tk.BOTH, expand=True)
        sb.config(command=self.alert_tree.yview)
        bf = tk.Frame(b, bg=SURFACE)
        bf.pack(fill=tk.X, pady=(10, 0))
        ModernButton(bf, text="+ Create Alert", bg=YELLOW, fg='#111',
            font=(F, 10, 'bold'), padx=16, pady=9,
            command=self.create_alert).pack(side=tk.LEFT, padx=(0, 8))
        ModernButton(bf, text="Close Alert", bg=RED, fg='white', padx=14, pady=9,
            command=self.close_selected_alert).pack(side=tk.LEFT)

    def update_displays(self):
        self.update_stats()
        self.update_stations()
        self.update_trains()
        self.update_alerts()

    def update_stats(self):
        s = self.bart_system.get_system_stats()
        self.stats_labels["total_trips"].config(text=str(s["total_trips"]))
        self.stats_labels["active_trips"].config(text=str(s["active_trips"]))
        self.stats_labels["total_revenue"].config(text=f"${s['total_revenue']:.2f}")
        self.stats_labels["total_users"].config(text=str(s["total_users"]))
        try:
            in_svc = BARTSystem.is_service_hours()
            svc_col = GREEN if in_svc else PURPLE
            svc_txt = "🟢  BART IN SERVICE  (5:00 AM – 12:30 AM)" if in_svc \
                else "🌙  NIGHT SUSPENSION  (12:30 AM – 5:00 AM)  — Trains halted"
            self.service_banner.config(text=svc_txt, bg=svc_col)
        except Exception:
            pass

    def update_stations(self):
        for i in self.station_tree.get_children(): self.station_tree.delete(i)
        for s in self.bart_system.get_all_stations():
            tag = "closed" if not s.is_operational() else "open"
            self.station_tree.insert("", tk.END,
                values=(s.name, s.zone, s.status.value), tags=(s.station_id, tag))
        self.station_tree.tag_configure("closed", foreground=RED)
        self.station_tree.tag_configure("open", foreground=GREEN)

    def update_trains(self):
        for i in self.train_tree.get_children(): self.train_tree.delete(i)
        for t in self.bart_system.get_all_trains():
            loc = t.current_station.name if t.current_station else "In Transit"
            self.train_tree.insert("", tk.END,
                values=(t.train_id, t.line, t.status.value, loc), tags=(t.train_id,))

    def update_alerts(self):
        for i in self.alert_tree.get_children(): self.alert_tree.delete(i)
        for a in self.bart_system.alerts.values():
            status = "Active" if a.is_active else "Closed"
            self.alert_tree.insert("", tk.END, values=(
                a.alert_type.value, a.title,
                a.start_time.strftime("%Y-%m-%d %H:%M"), status), tags=(a.alert_id,))

    def close_selected_station(self):
        sel = self.station_tree.selection()
        if not sel: messagebox.showerror("Error", "Select a station first"); return
        sid = self.station_tree.item(sel[0])["tags"][0]
        s = self.bart_system.get_station(sid)
        if not s: return
        if not s.is_operational():
            messagebox.showinfo("Info", f"{s.name} is already closed"); return
        self._station_close_dialog(s)

    def _station_close_dialog(self, station):
        dlg = tk.Toplevel(self.root)
        dlg.title(f"Close Station — {station.name}")
        dlg.geometry("480x420")
        dlg.resizable(False, False)
        dlg.configure(bg=SURFACE)
        dlg.transient(self.root)
        dlg.grab_set()

        tk.Frame(dlg, bg=RED, height=5).pack(fill=tk.X)
        tk.Label(dlg, text=f"🔒  Close {station.name}",
                 font=(F, 16, 'bold'), bg=SURFACE, fg=RED).pack(pady=(18, 4))
        tk.Label(dlg, text=f"Zone {station.zone}  •  All entry/exit gates will be locked",
                 font=(F, 10), bg=SURFACE, fg=TEXT_DIM).pack()

        wrap = tk.Frame(dlg, bg=SURFACE, padx=30)
        wrap.pack(fill=tk.X, pady=10)

        # Closure type
        tk.Label(wrap, text="CLOSURE TYPE", font=(F, 8, 'bold'),
                 bg=SURFACE, fg=TEXT_DIM).pack(anchor=tk.W, pady=(0, 6))
        closure_types = [
            "🔧 Maintenance",
            "⚡ Power Outage",
            "🔍 Safety Inspection",
            "🚨 Emergency",
            "🛤  Track Inspection",
            "👥 Overcrowding",
            "🏗  Infrastructure Work",
            "🔥 Fire / Safety Hazard",
            "🚫 Vandalism / Security",
            "🗂  Other",
        ]
        type_var = tk.StringVar(value=closure_types[0])
        type_cb = dark_combo(wrap, type_var, closure_types, width=36)
        type_cb.pack(fill=tk.X, pady=(0, 10))

        tk.Label(wrap, text="ADDITIONAL DETAILS (OPTIONAL)", font=(F, 8, 'bold'),
                 bg=SURFACE, fg=TEXT_DIM).pack(anchor=tk.W, pady=(0, 6))
        reason_box = tk.Text(wrap, height=3, font=(F, 11), bg=SURFACE2, fg=TEXT,
                             relief=tk.FLAT, bd=0, insertbackground=CYAN, padx=8, pady=8)
        reason_box.pack(fill=tk.X)

        auto_alert_var = tk.BooleanVar(value=True)
        tk.Checkbutton(wrap, text="Automatically create closure alert for passengers",
                       variable=auto_alert_var, font=(F, 10),
                       bg=SURFACE, fg=TEXT, selectcolor=SURFACE2,
                       activebackground=SURFACE).pack(anchor=tk.W, pady=(10, 0))

        err = tk.Label(wrap, text="", font=(F, 9, 'bold'), bg=SURFACE, fg=RED)
        err.pack(anchor=tk.W)

        def confirm():
            ctype = type_var.get()
            details = reason_box.get(1.0, tk.END).strip()
            reason = f"{ctype}" + (f" — {details}" if details else "")
            try:
                self.bart_system.admin_close_station(
                    self.admin, station, reason if auto_alert_var.get() else "")
                Toast(self.root, f"🔒  {station.name} closed  ({ctype})", color=RED)
                dlg.destroy()
                self.update_displays()
            except Exception as e:
                messagebox.showerror("Error", str(e))

        bf = tk.Frame(wrap, bg=SURFACE)
        bf.pack(fill=tk.X, pady=10)
        ModernButton(bf, text="Close Station", font=(F, 11, 'bold'),
            bg=RED, fg='white', padx=16, pady=10,
            command=confirm).pack(side=tk.LEFT, padx=(0, 8))
        ModernButton(bf, text="Cancel", font=(F, 11),
            bg=SURFACE2, fg=TEXT_DIM, padx=16, pady=10,
            command=dlg.destroy).pack(side=tk.LEFT)

    def open_selected_station(self):
        sel = self.station_tree.selection()
        if not sel: messagebox.showerror("Error", "Select a station first"); return
        sid = self.station_tree.item(sel[0])["tags"][0]
        s = self.bart_system.get_station(sid)
        if not s: return
        if s.is_operational():
            messagebox.showinfo("Info", f"{s.name} is already open"); return
        if messagebox.askyesno("Confirm", f"Reopen {s.name}?\n\nThis will also close any active closure alerts."):
            try:
                self.bart_system.admin_open_station(self.admin, s)
                Toast(self.root, f"✓  {s.name} reopened", color=GREEN)
                self.update_displays()
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def update_train_status(self, status: TrainStatus):
        sel = self.train_tree.selection()
        if not sel: messagebox.showerror("Error", "Select a train first"); return
        tid = self.train_tree.item(sel[0])["tags"][0]
        t = self.bart_system.get_train(tid)
        if not t: return

        if status == TrainStatus.DELAYED:
            self._train_delay_dialog(t)
        else:
            col = {TrainStatus.RUNNING: GREEN, TrainStatus.OUT_OF_SERVICE: RED}.get(status, ORANGE)
            try:
                self.bart_system.admin_update_train_status(self.admin, t, status)
                Toast(self.root, f"Train {t.train_id} ({t.line}) → {status.value}", color=col)
                self.update_displays()
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def _train_delay_dialog(self, train):
        dlg = tk.Toplevel(self.root)
        dlg.title(f"Mark Train Delayed")
        dlg.geometry("480x340")
        dlg.configure(bg=SURFACE)
        dlg.transient(self.root)
        dlg.grab_set()

        tk.Frame(dlg, bg=YELLOW, height=5).pack(fill=tk.X)
        tk.Label(dlg, text="⚠  Mark Train as Delayed",
                 font=(F, 16, 'bold'), bg=SURFACE, fg=YELLOW).pack(pady=(18, 4))
        tk.Label(dlg, text=f"Train {train.train_id}  •  {train.line}",
                 font=(F, 11), bg=SURFACE, fg=TEXT_DIM).pack(pady=(0, 16))

        wrap = tk.Frame(dlg, bg=SURFACE, padx=30)
        wrap.pack(fill=tk.X)
        tk.Label(wrap, text="REASON FOR DELAY", font=(F, 8, 'bold'),
                 bg=SURFACE, fg=TEXT_DIM).pack(anchor=tk.W, pady=(0, 6))
        reason_box = tk.Text(wrap, height=4, font=(F, 11), bg=SURFACE2, fg=TEXT,
                             relief=tk.FLAT, bd=0, insertbackground=CYAN, padx=8, pady=8)
        reason_box.pack(fill=tk.X)
        reason_box.insert(tk.END, "Operational delay due to ")

        auto_alert_var = tk.BooleanVar(value=True)
        tk.Checkbutton(wrap, text="Automatically create service alert",
                       variable=auto_alert_var, font=(F, 10),
                       bg=SURFACE, fg=TEXT, selectcolor=SURFACE2,
                       activebackground=SURFACE).pack(anchor=tk.W, pady=(12, 0))

        err = tk.Label(wrap, text="", font=(F, 9, 'bold'), bg=SURFACE, fg=RED)
        err.pack(anchor=tk.W)

        def confirm():
            reason = reason_box.get(1.0, tk.END).strip()
            if not reason:
                err.config(text="✗  Reason is required")
                return
            try:
                if auto_alert_var.get():
                    self.bart_system.admin_update_train_status_with_alert(
                        self.admin, train, TrainStatus.DELAYED, reason)
                else:
                    self.bart_system.admin_update_train_status(self.admin, train, TrainStatus.DELAYED)
                Toast(self.root,
                      f"⚠  Train {train.train_id} marked DELAYED", color=YELLOW)
                dlg.destroy()
                self.update_displays()
            except Exception as e:
                messagebox.showerror("Error", str(e))

        bf = tk.Frame(wrap, bg=SURFACE)
        bf.pack(fill=tk.X, pady=14)
        ModernButton(bf, text="Confirm Delay", font=(F, 11, 'bold'),
            bg=YELLOW, fg='#111', padx=16, pady=10,
            command=confirm).pack(side=tk.LEFT, padx=(0, 8))
        ModernButton(bf, text="Cancel", font=(F, 11),
            bg=SURFACE2, fg=TEXT_DIM, padx=16, pady=10,
            command=dlg.destroy).pack(side=tk.LEFT)

    def create_alert(self):
        dlg = tk.Toplevel(self.root)
        dlg.title("Create Service Alert")
        dlg.geometry("500x420")
        dlg.configure(bg=SURFACE)
        dlg.transient(self.root)
        dlg.grab_set()
        tk.Frame(dlg, bg=YELLOW, height=5).pack(fill=tk.X)
        tk.Label(dlg, text="Create Service Alert", font=(F, 18, 'bold'),
                 bg=SURFACE, fg=TEXT).pack(pady=20)
        wrap = tk.Frame(dlg, bg=SURFACE, padx=30)
        wrap.pack(fill=tk.X)
        tk.Label(wrap, text="ALERT TITLE", font=(F, 8, 'bold'),
                 bg=SURFACE, fg=TEXT_DIM).pack(anchor=tk.W, pady=(0, 5))
        tf, title_e = make_entry(wrap)
        tf.pack(fill=tk.X, pady=(0, 14))
        tk.Label(wrap, text="MESSAGE", font=(F, 8, 'bold'),
                 bg=SURFACE, fg=TEXT_DIM).pack(anchor=tk.W, pady=(0, 5))
        msg_box = tk.Text(wrap, height=5, font=(F, 11), bg=SURFACE2, fg=TEXT,
                          relief=tk.FLAT, bd=0, insertbackground=CYAN)
        msg_box.pack(fill=tk.X, pady=(0, 14))
        tk.Label(wrap, text="ALERT TYPE", font=(F, 8, 'bold'),
                 bg=SURFACE, fg=TEXT_DIM).pack(anchor=tk.W, pady=(0, 8))
        type_var = tk.StringVar(value="DELAY")
        rf = tk.Frame(wrap, bg=SURFACE)
        rf.pack(anchor=tk.W, pady=(0, 14))
        for at in ["DELAY", "CLOSURE", "MAINTENANCE"]:
            tk.Radiobutton(rf, text=at, variable=type_var, value=at,
                           font=(F, 10, 'bold'), bg=SURFACE, fg=TEXT_DIM,
                           selectcolor=SURFACE2, activebackground=SURFACE,
                           indicatoron=0, padx=14, pady=6, relief=tk.FLAT,
                           bd=1, highlightthickness=0).pack(side=tk.LEFT, padx=(0, 6))

        def create():
            t = title_e.get().strip()
            m = msg_box.get(1.0, tk.END).strip()
            if not t or not m: messagebox.showerror("Error", "Fill all fields"); return
            try:
                at = AlertType[type_var.get()]
                affected = list(self.bart_system.stations.values())[:3]
                self.bart_system.admin_create_alert(self.admin, at, t, m, affected)
                Toast(self.root, f"Alert created: {t}", color=YELLOW)
                dlg.destroy()
                self.update_displays()
            except Exception as e: messagebox.showerror("Error", str(e))

        ModernButton(wrap, text="CREATE ALERT", font=(F, 12, 'bold'),
            bg=YELLOW, fg='#111', padx=10, pady=12, command=create).pack(fill=tk.X)

    def close_selected_alert(self):
        sel = self.alert_tree.selection()
        if not sel: messagebox.showerror("Error", "Select an alert"); return
        aid = self.alert_tree.item(sel[0])["tags"][0]
        alert = self.bart_system.alerts.get(aid)
        if alert:
            try:
                self.bart_system.admin_close_alert(self.admin, alert)
                Toast(self.root, "Alert closed", color=GREEN)
                self.update_displays()
            except Exception as e: messagebox.showerror("Error", str(e))

    def generate_report(self):
        try:
            s = self.bart_system.admin_get_ridership_stats(self.admin)
            report = (f"BART RIDERSHIP REPORT\n"
                      f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
                      f"Total Trips: {s['total_trips']}\n"
                      f"Closed: {s['closed_trips']}  •  Active: {s['active_trips']}\n"
                      f"Total Revenue: ${s['total_revenue']:.2f}\n"
                      f"Average Fare: ${s['average_fare']:.2f}\n\n"
                      f"Busiest Stations:\n")
            for i, (stn, cnt) in enumerate(s['busiest_stations'], 1):
                report += f"  {i}. {stn}: {cnt} trips\n"
            messagebox.showinfo("Ridership Report", report)
        except Exception as e: messagebox.showerror("Error", str(e))

    def logout(self):
        self.app.current_user = None
        self.app.show_login_screen()


# ── SUPER ADMIN DASHBOARD ──────────────────────────────────

class SuperAdminDashboard:
    def __init__(self, root, bart_system: BARTSystem, admin: SuperAdmin, app):
        self.root = root
        self.bart_system = bart_system
        self.admin = admin
        self.app = app
        for w in self.root.winfo_children():
            w.destroy()
        self.root.title(f"BART Super Admin — {admin.name}")
        self.root.geometry("1500x950")
        self.root.configure(bg=BG)
        self._build()
        self.update_displays()

    def _build(self):
        hdr = tk.Frame(self.root, bg=SURFACE2, height=72)
        hdr.pack(fill=tk.X)
        hdr.pack_propagate(False)
        tk.Frame(hdr, bg=PURPLE, height=4).pack(fill=tk.X, side=tk.BOTTOM)

        lf = tk.Frame(hdr, bg=SURFACE2)
        lf.pack(side=tk.LEFT, padx=24, pady=12)
        tk.Label(lf, text="🛡 BART Super Admin Control Panel",
                 font=(F, 20, 'bold'), bg=SURFACE2, fg=TEXT).pack(anchor=tk.W)
        tk.Label(lf, text=f"Full System Access  •  {self.admin.name}",
                 font=(F, 10), bg=SURFACE2, fg=TEXT_DIM).pack(anchor=tk.W)

        sa_rf = tk.Frame(hdr, bg=SURFACE2)
        sa_rf.pack(side=tk.RIGHT, padx=20)
        ModernButton(sa_rf, text="Logout", font=(F, 10, 'bold'),
            bg=RED, fg='white', padx=16, pady=8,
            command=self.logout).pack(side=tk.RIGHT, padx=6)
        ModernButton(sa_rf, text="↻ Refresh", font=(F, 10),
            bg=SURFACE, fg=TEXT_DIM, padx=14, pady=8,
            command=self.update_displays).pack(side=tk.RIGHT, padx=4)
        self._win_max = False
        def _sa_toggle_win():
            self._win_max = not self._win_max
            self.root.state('zoomed' if self._win_max else 'normal')
        ModernButton(sa_rf, text="⛶", font=(F, 13),
            bg=SURFACE2, fg=TEXT_DIM, padx=8, pady=8,
            command=_sa_toggle_win).pack(side=tk.RIGHT, padx=2)

        body = tk.Frame(self.root, bg=BG)
        body.pack(fill=tk.BOTH, expand=True, padx=16, pady=12)

        self.notebook = ttk.Notebook(body, style='D.TNotebook')
        self.notebook.pack(fill=tk.BOTH, expand=True)

        for title, builder in [
            ("📊  Dashboard",  self._build_dashboard_tab),
            ("🚉  Stations",   self._build_station_tab),
            ("🚆  Trains",     self._build_train_tab),
            ("💰  Fare Rules", self._build_fare_tab),
            ("👥  Admins",     self._build_admin_tab),
            ("⚠   Alerts",    self._build_alerts_tab),
        ]:
            frame = tk.Frame(self.notebook, bg=BG)
            self.notebook.add(frame, text=title)
            builder(frame)

    def _build_dashboard_tab(self, parent):
        self.stats_labels = {}
        cfg = [("Total Users",  "total_users",    GREEN),
               ("Total Trips",  "total_trips",    BLUE),
               ("Active Trips", "active_trips",   RED),
               ("Revenue",      "total_revenue",  YELLOW),
               ("Stations",     "total_stations", TEAL),
               ("Trains",       "total_trains",   ORANGE)]

        wrap = tk.Frame(parent, bg=BG)
        wrap.pack(fill=tk.BOTH, expand=True, padx=16, pady=16)

        # Service status banner
        in_svc = BARTSystem.is_service_hours()
        svc_col = GREEN if in_svc else PURPLE
        svc_txt = "🟢  BART IN SERVICE  (5:00 AM – 12:30 AM)" if in_svc \
            else "🌙  NIGHT SUSPENSION  (12:30 AM – 5:00 AM)  — Trains halted"
        self.service_banner = tk.Label(wrap, text=svc_txt, font=(F, 10, 'bold'),
            bg=svc_col, fg='white', padx=16, pady=8, anchor=tk.W)
        self.service_banner.pack(fill=tk.X, pady=(0, 12))

        left = tk.Frame(wrap, bg=BG)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tk.Label(left, text="System Statistics", font=(F, 18, 'bold'),
                 bg=BG, fg=TEXT).pack(anchor=tk.W, pady=(0, 14))

        grid = tk.Frame(left, bg=BG)
        grid.pack(fill=tk.X)
        for i, (lbl, key, color) in enumerate(cfg):
            c = tk.Frame(grid, bg=SURFACE)
            c.grid(row=i // 3, column=i % 3, padx=(0, 10), pady=(0, 10), sticky="nsew")
            tk.Frame(c, bg=color, height=5).pack(fill=tk.X)
            inner = tk.Frame(c, bg=SURFACE, padx=20, pady=16)
            inner.pack(fill=tk.BOTH, expand=True)
            tk.Label(inner, text=lbl, font=(F, 9, 'bold'), bg=SURFACE, fg=TEXT_DIM).pack(anchor=tk.W)
            vl = tk.Label(inner, text="0", font=(F, 26, 'bold'), bg=SURFACE, fg=color)
            vl.pack(anchor=tk.W, pady=(6, 0))
            self.stats_labels[key] = vl

        ModernButton(left, text="📊  Full Ridership Report", font=(F, 11, 'bold'),
            bg=BLUE, fg='white', padx=20, pady=12,
            command=self.generate_report).pack(anchor=tk.W, pady=16)

        right = tk.Frame(wrap, bg=SURFACE, width=280)
        right.pack(side=tk.LEFT, fill=tk.Y, padx=(16, 0))
        right.pack_propagate(False)
        tk.Frame(right, bg=PURPLE, height=5).pack(fill=tk.X)
        ri = tk.Frame(right, bg=SURFACE, padx=16, pady=16)
        ri.pack(fill=tk.BOTH, expand=True)
        tk.Label(ri, text="Quick Actions", font=(F, 13, 'bold'),
                 bg=SURFACE, fg=TEXT).pack(anchor=tk.W, pady=(0, 14))
        for txt, cmd, col in [
            ("🚫  Emergency Close All", self.emergency_close_all, RED),
            ("✅  Open All Stations",   self.open_all_stations,    GREEN),
            ("⚠  Create System Alert", self.create_alert,          YELLOW),
            ("↻  Refresh All Data",    self.update_displays,       BLUE),
        ]:
            ModernButton(ri, text=txt, bg=col,
                fg='white' if col != YELLOW else '#111',
                font=(F, 10), padx=10, pady=10,
                command=cmd).pack(fill=tk.X, pady=(0, 8))

    def _build_station_tab(self, parent):
        _, b = card(parent, "Station Management", "🚉", TEAL,
                    fill=tk.BOTH, expand=True, padx=16, pady=16)

        # ── Station list ─────────────────────────────────────
        cols = ("ID", "Name", "Zone", "Status")
        sb = ttk.Scrollbar(b, style='D.Vertical.TScrollbar')
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.station_tree = ttk.Treeview(b, columns=cols, show='headings',
                                          yscrollcommand=sb.set, height=13, style='D.Treeview')
        for c, w in [("ID", 80), ("Name", 210), ("Zone", 80), ("Status", 110)]:
            self.station_tree.heading(c, text=c)
            self.station_tree.column(c, width=w, anchor=tk.CENTER)
        self.station_tree.pack(fill=tk.BOTH, expand=True)
        sb.config(command=self.station_tree.yview)

        # ── Action panel ─────────────────────────────────────
        action_panel = tk.Frame(b, bg=SURFACE2, padx=14, pady=12)
        action_panel.pack(fill=tk.X, pady=(10, 0))

        tk.Label(action_panel, text="STATION CONTROL  —  Select a station above, then choose an action",
                 font=(F, 8, 'bold'), bg=SURFACE2, fg=TEXT_DIM).pack(anchor=tk.W, pady=(0, 10))

        btn_row = tk.Frame(action_panel, bg=SURFACE2)
        btn_row.pack(fill=tk.X)

        # Close station — red safety button
        close_col = tk.Frame(btn_row, bg='#3d0000', padx=14, pady=10)
        close_col.pack(side=tk.LEFT, padx=(0, 10))
        tk.Label(close_col, text="🔒  CLOSE STATION", font=(F, 10, 'bold'),
                 bg='#3d0000', fg=RED).pack(anchor=tk.W)
        tk.Label(close_col, text="Locks all gates  •  Broadcasts passenger alert",
                 font=(F, 8), bg='#3d0000', fg='#ff8888').pack(anchor=tk.W, pady=(2, 8))
        ModernButton(close_col, text="Close Selected Station",
            font=(F, 10, 'bold'), bg=RED, fg='white', padx=14, pady=9,
            command=self.close_selected_station).pack(anchor=tk.W)

        # Divider
        tk.Frame(btn_row, bg=BORDER, width=1).pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))

        # Open station — green clearance button
        open_col = tk.Frame(btn_row, bg='#003d10', padx=14, pady=10)
        open_col.pack(side=tk.LEFT, padx=(0, 10))
        tk.Label(open_col, text="✅  OPEN STATION", font=(F, 10, 'bold'),
                 bg='#003d10', fg=GREEN).pack(anchor=tk.W)
        tk.Label(open_col, text="Safety checklist required  •  Notifies passengers",
                 font=(F, 8), bg='#003d10', fg='#88ffaa').pack(anchor=tk.W, pady=(2, 8))
        ModernButton(open_col, text="Open Selected Station",
            font=(F, 10, 'bold'), bg=GREEN, fg='white', padx=14, pady=9,
            command=self.open_selected_station).pack(anchor=tk.W)

        # Divider
        tk.Frame(btn_row, bg=BORDER, width=1).pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))

        # Add station
        add_col = tk.Frame(btn_row, bg=SURFACE2, padx=14, pady=10)
        add_col.pack(side=tk.LEFT)
        tk.Label(add_col, text="➕  ADD STATION", font=(F, 10, 'bold'),
                 bg=SURFACE2, fg=CYAN).pack(anchor=tk.W)
        tk.Label(add_col, text="Register a new BART station",
                 font=(F, 8), bg=SURFACE2, fg=TEXT_DIM).pack(anchor=tk.W, pady=(2, 8))
        ModernButton(add_col, text="Add New Station",
            font=(F, 10, 'bold'), bg=BLUE, fg='white', padx=14, pady=9,
            command=self.add_station_dialog).pack(anchor=tk.W)

    def _build_train_tab(self, parent):
        _, b = card(parent, "Train Management", "🚆", ORANGE,
                    fill=tk.BOTH, expand=True, padx=16, pady=16)
        cols = ("ID", "Line", "Cap", "Status", "Current", "Next", "ETA")
        sb = ttk.Scrollbar(b, style='D.Vertical.TScrollbar')
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.train_tree = ttk.Treeview(b, columns=cols, show='headings',
                                        yscrollcommand=sb.set, height=16, style='D.Treeview')
        for c, w in [("ID",70),("Line",120),("Cap",60),("Status",100),
                      ("Current",130),("Next",130),("ETA",60)]:
            self.train_tree.heading(c, text=c)
            self.train_tree.column(c, width=w, anchor=tk.CENTER)
        self.train_tree.pack(fill=tk.BOTH, expand=True)
        sb.config(command=self.train_tree.yview)
        bf = tk.Frame(b, bg=SURFACE)
        bf.pack(fill=tk.X, pady=(10, 0))
        for txt, arg, col in [("Set Running", TrainStatus.RUNNING, GREEN),
                                ("Set Delayed", TrainStatus.DELAYED, YELLOW),
                                ("Out of Service", TrainStatus.OUT_OF_SERVICE, RED)]:
            ModernButton(bf, text=txt, bg=col, fg='white' if col != YELLOW else '#111',
                padx=12, pady=8,
                command=lambda s=arg: self.update_train_status(s)).pack(side=tk.LEFT, padx=(0, 8))
        ModernButton(bf, text="Update Location", bg=PURPLE, fg='white', padx=12, pady=8,
            command=self.update_train_location_dialog).pack(side=tk.LEFT, padx=(0, 8))
        ModernButton(bf, text="Add Train", bg=BLUE, fg='white', padx=12, pady=8,
            command=self.add_train_dialog).pack(side=tk.LEFT)

    def _build_fare_tab(self, parent):
        from backend.models import FareCalculator
        _, b = card(parent, "Fare Configuration  —  Super Admin Only", "💰", YELLOW,
                    fill=tk.BOTH, expand=True, padx=16, pady=16)
        tk.Label(b, text="🔒  Changes affect all fare calculations system-wide",
                 font=(F, 10), bg=SURFACE, fg=RED).pack(anchor=tk.W, pady=(0, 16))

        for lbl, attr, entry_attr, cmd_name in [
            ("Base Fare ($)",    "BASE_FARE", "base_fare_entry", "update_base_fare"),
            ("Per-Zone Rate ($)","ZONE_RATE", "zone_rate_entry", "update_zone_rate"),
        ]:
            row = tk.Frame(b, bg=SURFACE2, padx=16, pady=14)
            row.pack(fill=tk.X, pady=(0, 8))
            tk.Label(row, text=lbl, font=(F, 12, 'bold'), bg=SURFACE2, fg=TEXT).pack(side=tk.LEFT)
            e = tk.Entry(row, font=(F, 12), width=10, bg=SURFACE, fg=TEXT,
                         relief=tk.FLAT, insertbackground=CYAN, bd=0)
            e.insert(0, f"{getattr(FareCalculator, attr):.2f}")
            e.pack(side=tk.LEFT, padx=16, ipady=6)
            setattr(self, entry_attr, e)
            ModernButton(row, text="Update", bg=GREEN, fg='white', padx=12, pady=6,
                command=getattr(self, cmd_name)).pack(side=tk.LEFT)

        disc = tk.Frame(b, bg=SURFACE2, padx=16, pady=14)
        disc.pack(fill=tk.X, pady=(16, 0))
        tk.Label(disc, text="Discount Rates (read only)", font=(F, 11, 'bold'),
                 bg=SURFACE2, fg=TEXT).pack(anchor=tk.W, pady=(0, 10))
        for pt, pct in [("Student", "25%"), ("Senior", "37.5%")]:
            tk.Label(disc, text=f"  {pt}:  {pct} discount",
                     font=(F, 10), bg=SURFACE2, fg=TEXT_DIM).pack(anchor=tk.W, pady=3)

    def _build_admin_tab(self, parent):
        _, b = card(parent, "Admin Account Management", "👥", PURPLE,
                    fill=tk.BOTH, expand=True, padx=16, pady=16)
        cols = ("ID", "Username", "Name", "Role", "Department")
        sb = ttk.Scrollbar(b, style='D.Vertical.TScrollbar')
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.admin_tree = ttk.Treeview(b, columns=cols, show='headings',
                                        yscrollcommand=sb.set, height=14, style='D.Treeview')
        for c, w in [("ID",80),("Username",120),("Name",160),("Role",110),("Department",160)]:
            self.admin_tree.heading(c, text=c)
            self.admin_tree.column(c, width=w, anchor=tk.CENTER)
        self.admin_tree.pack(fill=tk.BOTH, expand=True)
        sb.config(command=self.admin_tree.yview)
        ModernButton(b, text="+ Create Admin Account", bg=GREEN, fg='white',
            font=(F, 11, 'bold'), padx=16, pady=10,
            command=self.create_admin_dialog).pack(anchor=tk.W, pady=(10, 0))

    def _build_alerts_tab(self, parent):
        _, b = card(parent, "Service Alerts", "⚠", RED,
                    fill=tk.BOTH, expand=True, padx=16, pady=16)
        cols = ("ID", "Type", "Title", "Created", "Status")
        sb = ttk.Scrollbar(b, style='D.Vertical.TScrollbar')
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.alert_tree = ttk.Treeview(b, columns=cols, show='headings',
                                        yscrollcommand=sb.set, height=14, style='D.Treeview')
        for c, w in [("ID",80),("Type",100),("Title",260),("Created",150),("Status",80)]:
            self.alert_tree.heading(c, text=c)
            self.alert_tree.column(c, width=w, anchor=tk.CENTER)
        self.alert_tree.pack(fill=tk.BOTH, expand=True)
        sb.config(command=self.alert_tree.yview)
        bf = tk.Frame(b, bg=SURFACE)
        bf.pack(fill=tk.X, pady=(10, 0))
        ModernButton(bf, text="+ Create Alert", bg=YELLOW, fg='#111',
            font=(F, 10, 'bold'), padx=16, pady=9,
            command=self.create_alert).pack(side=tk.LEFT, padx=(0, 8))
        ModernButton(bf, text="Close Alert", bg=RED, fg='white', padx=14, pady=9,
            command=self.close_selected_alert).pack(side=tk.LEFT)

    # Data methods
    def update_displays(self):
        self.update_stats()
        self.update_stations()
        self.update_trains()
        self.update_admins()
        self.update_alerts()

    def update_stats(self):
        s = self.bart_system.get_system_stats()
        for key, lbl in self.stats_labels.items():
            val = s.get(key, 0)
            lbl.config(text=f"${val:.2f}" if key == "total_revenue" else str(val))
        try:
            in_svc = BARTSystem.is_service_hours()
            svc_col = GREEN if in_svc else PURPLE
            svc_txt = "🟢  BART IN SERVICE  (5:00 AM – 12:30 AM)" if in_svc \
                else "🌙  NIGHT SUSPENSION  (12:30 AM – 5:00 AM)  — Trains halted"
            self.service_banner.config(text=svc_txt, bg=svc_col)
        except Exception:
            pass

    def update_stations(self):
        for i in self.station_tree.get_children(): self.station_tree.delete(i)
        for s in self.bart_system.get_all_stations():
            tag = "closed" if not s.is_operational() else "open"
            self.station_tree.insert("", tk.END,
                values=(s.station_id, s.name, s.zone, s.status.value), tags=(s.station_id, tag))
        self.station_tree.tag_configure("closed", foreground=RED)
        self.station_tree.tag_configure("open", foreground=GREEN)

    def update_trains(self):
        for i in self.train_tree.get_children(): self.train_tree.delete(i)
        for t in self.bart_system.get_all_trains():
            cur = t.current_station.name if t.current_station else "In Transit"
            nxt = t.next_station.name if t.next_station else "—"
            eta = f"{t.eta_minutes}m" if t.eta_minutes else "—"
            self.train_tree.insert("", tk.END,
                values=(t.train_id, t.line, t.capacity, t.status.value, cur, nxt, eta),
                tags=(t.train_id,))

    def update_admins(self):
        for i in self.admin_tree.get_children(): self.admin_tree.delete(i)
        for u in self.bart_system.auth_service.users.values():
            if isinstance(u, (Admin, SuperAdmin)):
                role = "Super Admin" if isinstance(u, SuperAdmin) else "Admin"
                dept = getattr(u, 'department', 'N/A')
                self.admin_tree.insert("", tk.END,
                    values=(u.user_id, u.username, u.name, role, dept))

    def update_alerts(self):
        for i in self.alert_tree.get_children(): self.alert_tree.delete(i)
        for a in self.bart_system.alerts.values():
            status = "Active" if a.is_active else "Closed"
            self.alert_tree.insert("", tk.END,
                values=(a.alert_id, a.alert_type.value, a.title,
                        a.start_time.strftime("%Y-%m-%d %H:%M"), status),
                tags=(a.alert_id,))

    def close_selected_station(self):
        sel = self.station_tree.selection()
        if not sel: messagebox.showerror("Error", "Select a station first"); return
        sid = self.station_tree.item(sel[0])["tags"][0]
        s = self.bart_system.get_station(sid)
        if not s: return
        if not s.is_operational():
            messagebox.showinfo("Info", f"{s.name} is already closed"); return
        self._station_close_dialog(s)

    def _station_close_dialog(self, station):
        dlg = tk.Toplevel(self.root)
        dlg.title(f"Safety Alert — Close {station.name}")
        dlg.geometry("540x580")
        dlg.resizable(False, False)
        dlg.configure(bg=SURFACE)
        dlg.transient(self.root)
        dlg.grab_set()

        # ── Red alert header ────────────────────────────────
        hdr = tk.Frame(dlg, bg='#8b0000')
        hdr.pack(fill=tk.X)
        tk.Frame(hdr, bg=RED, height=4).pack(fill=tk.X)
        tk.Label(hdr, text="⚠  STATION CLOSURE — SAFETY NOTICE",
                 font=(F, 11, 'bold'), bg='#8b0000', fg='white',
                 padx=20, pady=10).pack(anchor=tk.W)

        # ── Station info banner ──────────────────────────────
        info = tk.Frame(dlg, bg=SURFACE2, padx=20, pady=12)
        info.pack(fill=tk.X)
        left_i = tk.Frame(info, bg=SURFACE2)
        left_i.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tk.Label(left_i, text=station.name, font=(F, 20, 'bold'),
                 bg=SURFACE2, fg=RED).pack(anchor=tk.W)
        tk.Label(left_i, text=f"Station ID: {station.station_id}  •  Zone {station.zone}",
                 font=(F, 10), bg=SURFACE2, fg=TEXT_DIM).pack(anchor=tk.W)
        tk.Label(left_i, text=f"Current Status:  OPEN", font=(F, 10, 'bold'),
                 bg=SURFACE2, fg=GREEN).pack(anchor=tk.W, pady=(4, 0))
        right_i = tk.Frame(info, bg=SURFACE2, padx=10)
        right_i.pack(side=tk.RIGHT)
        tk.Label(right_i, text="🚨", font=(F, 36), bg=SURFACE2).pack()

        # ── Passenger impact notice ──────────────────────────
        notice = tk.Frame(dlg, bg='#1a0a00', padx=20, pady=10)
        notice.pack(fill=tk.X)
        tk.Label(notice,
                 text="This action will immediately lock all entry/exit gates and\n"
                      "broadcast a safety alert to all passengers in the system.",
                 font=(F, 10), bg='#1a0a00', fg='#ffaa55',
                 justify=tk.LEFT).pack(anchor=tk.W)

        # ── Form fields ──────────────────────────────────────
        wrap = tk.Frame(dlg, bg=SURFACE, padx=24)
        wrap.pack(fill=tk.X, pady=(12, 0))

        tk.Label(wrap, text="CLOSURE TYPE", font=(F, 8, 'bold'),
                 bg=SURFACE, fg=TEXT_DIM).pack(anchor=tk.W, pady=(0, 5))
        closure_types = [
            "🔧  Maintenance",
            "⚡  Power Outage",
            "🔍  Safety Inspection",
            "🚨  Emergency",
            "🛤   Track Inspection",
            "👥  Overcrowding",
            "🏗   Infrastructure Work",
            "🔥  Fire / Safety Hazard",
            "🚫  Vandalism / Security",
            "🗂   Other",
        ]
        type_var = tk.StringVar(value=closure_types[0])
        dark_combo(wrap, type_var, closure_types, width=40).pack(fill=tk.X, pady=(0, 12))

        tk.Label(wrap, text="MESSAGE TO PASSENGERS", font=(F, 8, 'bold'),
                 bg=SURFACE, fg=TEXT_DIM).pack(anchor=tk.W, pady=(0, 5))
        reason_box = tk.Text(wrap, height=3, font=(F, 11), bg=SURFACE2, fg=TEXT,
                             relief=tk.FLAT, bd=0, insertbackground=CYAN, padx=10, pady=8)
        reason_box.pack(fill=tk.X)
        reason_box.insert(tk.END, f"Service at {station.name} is temporarily suspended. ")

        opts = tk.Frame(wrap, bg=SURFACE)
        opts.pack(fill=tk.X, pady=(10, 0))
        auto_alert_var = tk.BooleanVar(value=True)
        tk.Checkbutton(opts, text="Broadcast passenger alert immediately",
                       variable=auto_alert_var, font=(F, 10, 'bold'),
                       bg=SURFACE, fg=YELLOW, selectcolor=SURFACE2,
                       activebackground=SURFACE).pack(anchor=tk.W)
        tk.Label(opts, text="    Passengers will see this alert on their dashboard",
                 font=(F, 9), bg=SURFACE, fg=TEXT_DIM).pack(anchor=tk.W)

        err = tk.Label(wrap, text="", font=(F, 9, 'bold'), bg=SURFACE, fg=RED)
        err.pack(anchor=tk.W, pady=(6, 0))

        # ── Action buttons ───────────────────────────────────
        bf = tk.Frame(dlg, bg=SURFACE2, padx=24, pady=14)
        bf.pack(fill=tk.X, side=tk.BOTTOM)
        tk.Label(bf, text="This action is logged and cannot be undone without a reopen.",
                 font=(F, 8), bg=SURFACE2, fg=TEXT_DIM).pack(anchor=tk.W, pady=(0, 8))
        btn_row = tk.Frame(bf, bg=SURFACE2)
        btn_row.pack(fill=tk.X)

        def confirm():
            ctype = type_var.get()
            msg = reason_box.get(1.0, tk.END).strip()
            if not msg:
                err.config(text="✗  Please provide a message for passengers"); return
            reason = f"{ctype} — {msg}"
            try:
                self.bart_system.admin_close_station(
                    self.admin, station, reason if auto_alert_var.get() else "")
                Toast(self.root,
                      f"🔒  {station.name} CLOSED  •  Passenger alert broadcast",
                      color=RED, dur=4000)
                dlg.destroy()
                self.update_displays()
            except Exception as e:
                messagebox.showerror("Error", str(e))

        ModernButton(btn_row, text="🔒  Confirm Station Closure", font=(F, 11, 'bold'),
            bg=RED, fg='white', padx=18, pady=11,
            command=confirm).pack(side=tk.LEFT, padx=(0, 10))
        ModernButton(btn_row, text="Cancel", font=(F, 11),
            bg=SURFACE, fg=TEXT_DIM, padx=18, pady=11,
            command=dlg.destroy).pack(side=tk.LEFT)

    def open_selected_station(self):
        sel = self.station_tree.selection()
        if not sel: messagebox.showerror("Error", "Select a station first"); return
        sid = self.station_tree.item(sel[0])["tags"][0]
        s = self.bart_system.get_station(sid)
        if not s: return
        if s.is_operational():
            messagebox.showinfo("Info", f"{s.name} is already open"); return
        self._station_open_dialog(s)

    def _station_open_dialog(self, station):
        dlg = tk.Toplevel(self.root)
        dlg.title(f"Safety Clearance — Reopen {station.name}")
        dlg.geometry("540x500")
        dlg.resizable(False, False)
        dlg.configure(bg=SURFACE)
        dlg.transient(self.root)
        dlg.grab_set()

        # ── Green clearance header ───────────────────────────
        hdr = tk.Frame(dlg, bg='#064020')
        hdr.pack(fill=tk.X)
        tk.Frame(hdr, bg=GREEN, height=4).pack(fill=tk.X)
        tk.Label(hdr, text="✓  STATION REOPENING — SAFETY CLEARANCE",
                 font=(F, 11, 'bold'), bg='#064020', fg='white',
                 padx=20, pady=10).pack(anchor=tk.W)

        # ── Station info banner ──────────────────────────────
        info = tk.Frame(dlg, bg=SURFACE2, padx=20, pady=12)
        info.pack(fill=tk.X)
        left_i = tk.Frame(info, bg=SURFACE2)
        left_i.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tk.Label(left_i, text=station.name, font=(F, 20, 'bold'),
                 bg=SURFACE2, fg=GREEN).pack(anchor=tk.W)
        tk.Label(left_i, text=f"Station ID: {station.station_id}  •  Zone {station.zone}",
                 font=(F, 10), bg=SURFACE2, fg=TEXT_DIM).pack(anchor=tk.W)
        tk.Label(left_i, text=f"Current Status:  CLOSED",
                 font=(F, 10, 'bold'), bg=SURFACE2, fg=RED).pack(anchor=tk.W, pady=(4, 0))
        tk.Label(info, text="✅", font=(F, 36), bg=SURFACE2).pack(side=tk.RIGHT, padx=10)

        # ── Safety checklist ─────────────────────────────────
        chk_frame = tk.Frame(dlg, bg='#001a0a', padx=20, pady=12)
        chk_frame.pack(fill=tk.X)
        tk.Label(chk_frame, text="SAFETY CHECKLIST  —  Confirm all before reopening",
                 font=(F, 9, 'bold'), bg='#001a0a', fg=GREEN).pack(anchor=tk.W, pady=(0, 8))
        checks = [
            ("Platform and gates are clear and safe for passengers", True),
            ("All systems (power, lighting, escalators) are operational", True),
            ("Security personnel have cleared the station", True),
        ]
        check_vars = []
        for text, default in checks:
            var = tk.BooleanVar(value=default)
            check_vars.append(var)
            tk.Checkbutton(chk_frame, text=text, variable=var,
                           font=(F, 10), bg='#001a0a', fg='#aaffcc',
                           selectcolor='#003015', activebackground='#001a0a').pack(anchor=tk.W, pady=2)

        # ── Passenger message ────────────────────────────────
        wrap = tk.Frame(dlg, bg=SURFACE, padx=24)
        wrap.pack(fill=tk.X, pady=(12, 0))
        tk.Label(wrap, text="PASSENGER NOTIFICATION MESSAGE", font=(F, 8, 'bold'),
                 bg=SURFACE, fg=TEXT_DIM).pack(anchor=tk.W, pady=(0, 5))
        msg_box = tk.Text(wrap, height=3, font=(F, 11), bg=SURFACE2, fg=TEXT,
                          relief=tk.FLAT, bd=0, insertbackground=CYAN, padx=10, pady=8)
        msg_box.pack(fill=tk.X)
        msg_box.insert(tk.END,
            f"{station.name} has reopened. Normal service has resumed. "
            "We apologize for any inconvenience.")

        notify_var = tk.BooleanVar(value=True)
        tk.Checkbutton(wrap, text="Notify passengers that station has reopened",
                       variable=notify_var, font=(F, 10, 'bold'),
                       bg=SURFACE, fg=CYAN, selectcolor=SURFACE2,
                       activebackground=SURFACE).pack(anchor=tk.W, pady=(10, 0))

        err = tk.Label(wrap, text="", font=(F, 9, 'bold'), bg=SURFACE, fg=RED)
        err.pack(anchor=tk.W, pady=(4, 0))

        # ── Action buttons ───────────────────────────────────
        bf = tk.Frame(dlg, bg=SURFACE2, padx=24, pady=14)
        bf.pack(fill=tk.X, side=tk.BOTTOM)
        btn_row = tk.Frame(bf, bg=SURFACE2)
        btn_row.pack(fill=tk.X)

        def confirm():
            if not all(v.get() for v in check_vars):
                err.config(text="✗  Complete all safety checks before reopening"); return
            try:
                self.bart_system.admin_open_station(self.admin, station)
                if notify_var.get():
                    msg = msg_box.get(1.0, tk.END).strip()
                    if msg:
                        from backend.models import AlertType
                        self.bart_system.admin_create_alert(
                            self.admin, AlertType.MAINTENANCE,
                            f"{station.name} Station Reopened", msg, [station])
                Toast(self.root,
                      f"✓  {station.name} REOPENED  •  Passengers notified",
                      color=GREEN, dur=4000)
                dlg.destroy()
                self.update_displays()
            except Exception as e:
                messagebox.showerror("Error", str(e))

        ModernButton(btn_row, text="✓  Confirm & Reopen Station", font=(F, 11, 'bold'),
            bg=GREEN, fg='white', padx=18, pady=11,
            command=confirm).pack(side=tk.LEFT, padx=(0, 10))
        ModernButton(btn_row, text="Cancel", font=(F, 11),
            bg=SURFACE, fg=TEXT_DIM, padx=18, pady=11,
            command=dlg.destroy).pack(side=tk.LEFT)

    def emergency_close_all(self):
        if messagebox.askyesno("Emergency", "Close ALL stations? This is an emergency action."):
            for s in self.bart_system.get_all_stations():
                try: self.bart_system.admin_close_station(self.admin, s)
                except: pass
            Toast(self.root, "All stations closed!", color=RED)
            self.update_displays()

    def open_all_stations(self):
        if messagebox.askyesno("Confirm", "Open ALL stations?"):
            for s in self.bart_system.get_all_stations():
                try: self.bart_system.admin_open_station(self.admin, s)
                except: pass
            Toast(self.root, "All stations opened!", color=GREEN)
            self.update_displays()

    def update_train_status(self, status: TrainStatus):
        sel = self.train_tree.selection()
        if not sel: messagebox.showerror("Error", "Select a train first"); return
        tid = self.train_tree.item(sel[0])["tags"][0]
        t = self.bart_system.get_train(tid)
        if not t: return

        if status == TrainStatus.DELAYED:
            self._train_delay_dialog(t)
        else:
            col = {TrainStatus.RUNNING: GREEN, TrainStatus.OUT_OF_SERVICE: RED}.get(status, ORANGE)
            try:
                self.bart_system.admin_update_train_status(self.admin, t, status)
                Toast(self.root, f"Train {t.train_id} ({t.line}) → {status.value}", color=col)
                self.update_displays()
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def _train_delay_dialog(self, train):
        dlg = tk.Toplevel(self.root)
        dlg.title("Mark Train Delayed")
        dlg.geometry("480x340")
        dlg.configure(bg=SURFACE)
        dlg.transient(self.root)
        dlg.grab_set()

        tk.Frame(dlg, bg=YELLOW, height=5).pack(fill=tk.X)
        tk.Label(dlg, text="⚠  Mark Train as Delayed",
                 font=(F, 16, 'bold'), bg=SURFACE, fg=YELLOW).pack(pady=(18, 4))
        tk.Label(dlg, text=f"Train {train.train_id}  •  {train.line}",
                 font=(F, 11), bg=SURFACE, fg=TEXT_DIM).pack(pady=(0, 16))

        wrap = tk.Frame(dlg, bg=SURFACE, padx=30)
        wrap.pack(fill=tk.X)
        tk.Label(wrap, text="REASON FOR DELAY", font=(F, 8, 'bold'),
                 bg=SURFACE, fg=TEXT_DIM).pack(anchor=tk.W, pady=(0, 6))
        reason_box = tk.Text(wrap, height=4, font=(F, 11), bg=SURFACE2, fg=TEXT,
                             relief=tk.FLAT, bd=0, insertbackground=CYAN, padx=8, pady=8)
        reason_box.pack(fill=tk.X)
        reason_box.insert(tk.END, "Operational delay due to ")

        auto_alert_var = tk.BooleanVar(value=True)
        tk.Checkbutton(wrap, text="Automatically create service alert",
                       variable=auto_alert_var, font=(F, 10),
                       bg=SURFACE, fg=TEXT, selectcolor=SURFACE2,
                       activebackground=SURFACE).pack(anchor=tk.W, pady=(12, 0))

        err = tk.Label(wrap, text="", font=(F, 9, 'bold'), bg=SURFACE, fg=RED)
        err.pack(anchor=tk.W)

        def confirm():
            reason = reason_box.get(1.0, tk.END).strip()
            if not reason:
                err.config(text="✗  Reason is required")
                return
            try:
                if auto_alert_var.get():
                    self.bart_system.admin_update_train_status_with_alert(
                        self.admin, train, TrainStatus.DELAYED, reason)
                else:
                    self.bart_system.admin_update_train_status(
                        self.admin, train, TrainStatus.DELAYED)
                Toast(self.root, f"⚠  Train {train.train_id} marked delayed", color=YELLOW)
                dlg.destroy()
                self.update_displays()
            except Exception as e:
                messagebox.showerror("Error", str(e))

        bf = tk.Frame(wrap, bg=SURFACE)
        bf.pack(fill=tk.X, pady=10)
        ModernButton(bf, text="Mark Delayed", font=(F, 11, 'bold'),
            bg=YELLOW, fg='#111', padx=16, pady=10,
            command=confirm).pack(side=tk.LEFT, padx=(0, 8))
        ModernButton(bf, text="Cancel", font=(F, 11),
            bg=SURFACE2, fg=TEXT_DIM, padx=16, pady=10,
            command=dlg.destroy).pack(side=tk.LEFT)

    def update_train_location_dialog(self):
        sel = self.train_tree.selection()
        if not sel: messagebox.showwarning("No Selection", "Select a train first"); return
        tid = self.train_tree.item(sel[0])["values"][0]
        train = self.bart_system.trains.get(str(tid))
        if not train: return

        dlg = tk.Toplevel(self.root)
        dlg.title(f"Update Location — {tid}")
        dlg.geometry("420x340")
        dlg.configure(bg=SURFACE)
        dlg.transient(self.root)
        dlg.grab_set()
        tk.Frame(dlg, bg=PURPLE, height=5).pack(fill=tk.X)
        tk.Label(dlg, text=f"📍 Update Train {tid} Location",
                 font=(F, 16, 'bold'), bg=SURFACE, fg=TEXT).pack(pady=18)
        tk.Label(dlg, text=f"Line: {train.line}", font=(F, 11), bg=SURFACE, fg=TEXT_DIM).pack()

        stations = list(self.bart_system.stations.values())
        snames = ["None (In Transit)"] + [s.name for s in stations]

        wrap = tk.Frame(dlg, bg=SURFACE, padx=30)
        wrap.pack(fill=tk.X, pady=14)

        cur_var = tk.StringVar()
        nxt_var = tk.StringVar()
        for label_text, var, attr in [("Current Station", cur_var, "current_station"),
                                       ("Next Station",    nxt_var, "next_station")]:
            row = tk.Frame(wrap, bg=SURFACE)
            row.pack(fill=tk.X, pady=(0, 10))
            tk.Label(row, text=label_text, font=(F, 10, 'bold'),
                     bg=SURFACE, fg=TEXT_DIM, width=16, anchor=tk.W).pack(side=tk.LEFT)
            cb = dark_combo(row, var, snames, width=22)
            cb.pack(side=tk.LEFT)
            curr = getattr(train, attr, None)
            cb.set(curr.name if curr else "None (In Transit)")

        row_eta = tk.Frame(wrap, bg=SURFACE)
        row_eta.pack(fill=tk.X, pady=(0, 16))
        tk.Label(row_eta, text="ETA (minutes)", font=(F, 10, 'bold'),
                 bg=SURFACE, fg=TEXT_DIM, width=16, anchor=tk.W).pack(side=tk.LEFT)
        eta_e = tk.Entry(row_eta, font=(F, 11), width=8, bg=SURFACE2, fg=TEXT,
                          relief=tk.FLAT, bd=0, insertbackground=CYAN)
        eta_e.insert(0, str(train.eta_minutes or 0))
        eta_e.pack(side=tk.LEFT, ipady=6, padx=8)

        def save():
            cur_st = next((s for s in stations if s.name == cur_var.get()), None)
            nxt_st = next((s for s in stations if s.name == nxt_var.get()), None)
            try: eta = int(eta_e.get()) if eta_e.get() else None
            except ValueError: eta = None
            train.update_location(cur_st, nxt_st, eta)
            self.update_trains()
            dlg.destroy()
            Toast(self.root, f"Train {tid} location updated", color=PURPLE)

        bf = tk.Frame(wrap, bg=SURFACE)
        bf.pack(fill=tk.X)
        ModernButton(bf, text="Save", bg=GREEN, fg='white', padx=20, pady=8,
            command=save).pack(side=tk.LEFT, padx=(0, 8))
        ModernButton(bf, text="Cancel", bg=RED, fg='white', padx=20, pady=8,
            command=dlg.destroy).pack(side=tk.LEFT)

    def add_station_dialog(self):
        dlg = tk.Toplevel(self.root)
        dlg.title("Add New Station")
        dlg.geometry("420x340")
        dlg.configure(bg=SURFACE)
        dlg.transient(self.root)
        dlg.grab_set()
        tk.Frame(dlg, bg=TEAL, height=5).pack(fill=tk.X)
        tk.Label(dlg, text="Add New Station", font=(F, 18, 'bold'), bg=SURFACE, fg=TEXT).pack(pady=20)
        fields = {}
        wrap = tk.Frame(dlg, bg=SURFACE, padx=30)
        wrap.pack(fill=tk.X)
        for lbl, key in [("Station ID", "id"), ("Station Name", "name"), ("Zone (1-5)", "zone")]:
            tk.Label(wrap, text=lbl.upper(), font=(F, 8, 'bold'),
                     bg=SURFACE, fg=TEXT_DIM).pack(anchor=tk.W, pady=(8, 4))
            wf, en = make_entry(wrap)
            wf.pack(fill=tk.X)
            fields[key] = en

        def add():
            try:
                s = self.bart_system.admin_add_station(
                    self.admin, fields["id"].get(), fields["name"].get(),
                    int(fields["zone"].get()), 0.0, 0.0)
                Toast(self.root, f"Station {s.name} added!", color=TEAL)
                dlg.destroy()
                self.update_displays()
            except Exception as e: messagebox.showerror("Error", str(e))

        ModernButton(wrap, text="ADD STATION", bg=TEAL, fg='white',
            font=(F, 12, 'bold'), padx=10, pady=12, command=add).pack(fill=tk.X, pady=18)

    def add_train_dialog(self):
        dlg = tk.Toplevel(self.root)
        dlg.title("Add New Train")
        dlg.geometry("420x360")
        dlg.configure(bg=SURFACE)
        dlg.transient(self.root)
        dlg.grab_set()
        tk.Frame(dlg, bg=ORANGE, height=5).pack(fill=tk.X)
        tk.Label(dlg, text="Add New Train", font=(F, 18, 'bold'), bg=SURFACE, fg=TEXT).pack(pady=20)
        fields = {}
        wrap = tk.Frame(dlg, bg=SURFACE, padx=30)
        wrap.pack(fill=tk.X)
        for lbl, key in [("Train ID", "id"), ("Line Name", "line"), ("Capacity", "capacity")]:
            tk.Label(wrap, text=lbl.upper(), font=(F, 8, 'bold'),
                     bg=SURFACE, fg=TEXT_DIM).pack(anchor=tk.W, pady=(8, 4))
            wf, en = make_entry(wrap)
            wf.pack(fill=tk.X)
            fields[key] = en

        def add():
            try:
                t = self.bart_system.admin_add_train(
                    self.admin, fields["id"].get(), fields["line"].get(),
                    int(fields["capacity"].get()))
                Toast(self.root, f"Train {t.train_id} added!", color=ORANGE)
                dlg.destroy()
                self.update_displays()
            except Exception as e: messagebox.showerror("Error", str(e))

        ModernButton(wrap, text="ADD TRAIN", bg=ORANGE, fg='white',
            font=(F, 12, 'bold'), padx=10, pady=12, command=add).pack(fill=tk.X, pady=18)

    def create_alert(self):
        dlg = tk.Toplevel(self.root)
        dlg.title("Create Service Alert")
        dlg.geometry("500x430")
        dlg.configure(bg=SURFACE)
        dlg.transient(self.root)
        dlg.grab_set()
        tk.Frame(dlg, bg=YELLOW, height=5).pack(fill=tk.X)
        tk.Label(dlg, text="Create Service Alert", font=(F, 18, 'bold'),
                 bg=SURFACE, fg=TEXT).pack(pady=20)
        wrap = tk.Frame(dlg, bg=SURFACE, padx=30)
        wrap.pack(fill=tk.X)
        tk.Label(wrap, text="ALERT TITLE", font=(F, 8, 'bold'),
                 bg=SURFACE, fg=TEXT_DIM).pack(anchor=tk.W, pady=(0, 5))
        tf, title_e = make_entry(wrap)
        tf.pack(fill=tk.X, pady=(0, 14))
        tk.Label(wrap, text="MESSAGE", font=(F, 8, 'bold'),
                 bg=SURFACE, fg=TEXT_DIM).pack(anchor=tk.W, pady=(0, 5))
        msg_box = tk.Text(wrap, height=5, font=(F, 11), bg=SURFACE2, fg=TEXT,
                          relief=tk.FLAT, bd=0, insertbackground=CYAN)
        msg_box.pack(fill=tk.X, pady=(0, 14))
        tk.Label(wrap, text="ALERT TYPE", font=(F, 8, 'bold'),
                 bg=SURFACE, fg=TEXT_DIM).pack(anchor=tk.W, pady=(0, 8))
        type_var = tk.StringVar(value="DELAY")
        rf = tk.Frame(wrap, bg=SURFACE)
        rf.pack(anchor=tk.W, pady=(0, 14))
        for at in ["DELAY", "CLOSURE", "MAINTENANCE"]:
            tk.Radiobutton(rf, text=at, variable=type_var, value=at,
                           font=(F, 10, 'bold'), bg=SURFACE, fg=TEXT_DIM,
                           selectcolor=SURFACE2, activebackground=SURFACE,
                           indicatoron=0, padx=14, pady=6, relief=tk.FLAT,
                           bd=1, highlightthickness=0).pack(side=tk.LEFT, padx=(0, 6))

        def create():
            t = title_e.get().strip()
            m = msg_box.get(1.0, tk.END).strip()
            if not t or not m: messagebox.showerror("Error", "Fill all fields"); return
            try:
                at = AlertType[type_var.get()]
                affected = list(self.bart_system.stations.values())[:3]
                self.bart_system.admin_create_alert(self.admin, at, t, m, affected)
                Toast(self.root, f"Alert created: {t}", color=YELLOW)
                dlg.destroy()
                self.update_displays()
            except Exception as e: messagebox.showerror("Error", str(e))

        ModernButton(wrap, text="CREATE ALERT", bg=YELLOW, fg='#111',
            font=(F, 12, 'bold'), padx=10, pady=12, command=create).pack(fill=tk.X)

    def close_selected_alert(self):
        sel = self.alert_tree.selection()
        if not sel: messagebox.showerror("Error", "Select an alert"); return
        aid = self.alert_tree.item(sel[0])["values"][0]
        alert = self.bart_system.alerts.get(aid)
        if alert:
            try:
                self.bart_system.admin_close_alert(self.admin, alert)
                Toast(self.root, "Alert closed", color=GREEN)
                self.update_displays()
            except Exception as e: messagebox.showerror("Error", str(e))

    def update_base_fare(self):
        try:
            nf = float(self.base_fare_entry.get())
            self.bart_system.admin_update_base_fare(self.admin, nf)
            Toast(self.root, f"Base fare updated to ${nf:.2f}", color=GREEN)
        except Exception as e: messagebox.showerror("Error", str(e))

    def update_zone_rate(self):
        try:
            nr = float(self.zone_rate_entry.get())
            self.bart_system.admin_update_zone_rate(self.admin, nr)
            Toast(self.root, f"Zone rate updated to ${nr:.2f}", color=GREEN)
        except Exception as e: messagebox.showerror("Error", str(e))

    def create_admin_dialog(self):
        dlg = tk.Toplevel(self.root)
        dlg.title("Create Admin Account")
        dlg.geometry("460x500")
        dlg.configure(bg=SURFACE)
        dlg.transient(self.root)
        dlg.grab_set()
        tk.Frame(dlg, bg=PURPLE, height=5).pack(fill=tk.X)
        tk.Label(dlg, text="Create Admin Account", font=(F, 18, 'bold'),
                 bg=SURFACE, fg=TEXT).pack(pady=20)
        fields = {}
        wrap = tk.Frame(dlg, bg=SURFACE, padx=30)
        wrap.pack(fill=tk.X)
        for lbl, key in [("Username","username"),("Password","password"),
                          ("Full Name","name"),("Email","email"),("Department","department")]:
            tk.Label(wrap, text=lbl.upper(), font=(F, 8, 'bold'),
                     bg=SURFACE, fg=TEXT_DIM).pack(anchor=tk.W, pady=(8, 4))
            show = '●' if key == 'password' else None
            wf, en = make_entry(wrap, show=show)
            wf.pack(fill=tk.X)
            fields[key] = en

        def create():
            try:
                admin = self.bart_system.auth_service.register_user(
                    fields["username"].get(), fields["password"].get(),
                    fields["email"].get(), "admin",
                    name=fields["name"].get(),
                    department=fields["department"].get())
                Toast(self.root, f"Admin {admin.username} created!", color=GREEN)
                dlg.destroy()
                self.update_displays()
            except Exception as e: messagebox.showerror("Error", str(e))

        ModernButton(wrap, text="CREATE ADMIN", bg=PURPLE, fg='white',
            font=(F, 12, 'bold'), padx=10, pady=12, command=create).pack(fill=tk.X, pady=18)

    def generate_report(self):
        try:
            s = self.bart_system.admin_get_ridership_stats(self.admin)
            report = (f"{'='*50}\n  BART SYSTEM RIDERSHIP REPORT\n{'='*50}\n"
                      f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
                      f"Report By: {self.admin.name} (Super Admin)\n\n"
                      f"SUMMARY:\n"
                      f"  Total Trips: {s['total_trips']}\n"
                      f"  Closed: {s['closed_trips']}  •  Active: {s['active_trips']}\n"
                      f"  Total Revenue: ${s['total_revenue']:.2f}\n"
                      f"  Average Fare: ${s['average_fare']:.2f}\n\n"
                      f"BUSIEST STATIONS:\n")
            for i, (stn, cnt) in enumerate(s['busiest_stations'], 1):
                report += f"  {i}. {stn}: {cnt} trips\n"
            messagebox.showinfo("Full Report", report)
        except Exception as e: messagebox.showerror("Error", str(e))

    def logout(self):
        self.app.current_user = None
        self.app.show_login_screen()


def main():
    root = tk.Tk()
    BARTLoginApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
