"""
BART Transportation System - Enhanced GUI with Role-Based Access
Step 3: Professional Tkinter Interface with Login and Multiple Dashboards
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import datetime
from typing import Optional
from bart_system import BARTSystem
from models import (
    User, Passenger, Admin, SuperAdmin,
    Station, Train, Card, PassengerType,
    StationStatus, TrainStatus, AlertType
)


class ModernButton(tk.Button):
    """Custom styled button"""
    def __init__(self, parent, **kwargs):
        super().__init__(
            parent,
            relief=tk.FLAT,
            bd=0,
            highlightthickness=0,
            cursor="hand2",
            **kwargs
        )


class BARTLoginApp:
    """
    BART Login and Main Application Controller
    
    Manages:
    - Login screen
    - Role-based dashboard routing
    - Session management
    """
    
    # Color scheme
    PRIMARY = "#003f87"
    SECONDARY = "#ffffff"
    ACCENT = "#e31c23"
    SUCCESS = "#28a745"
    WARNING = "#ffc107"
    DANGER = "#dc3545"
    BG_LIGHT = "#f8f9fa"
    BG_DARK = "#343a40"
    TEXT_DARK = "#212529"
    TEXT_LIGHT = "#6c757d"
    
    def __init__(self, root):
        self.root = root
        self.root.title("BART Transportation System - Login")
        self.root.geometry("500x600")
        self.root.configure(bg=self.BG_LIGHT)
        
        # Initialize system
        self.bart_system = BARTSystem()
        self.current_user: Optional[User] = None
        
        # Show login screen
        self.show_login_screen()
    
    def show_login_screen(self):
        """Display login screen"""
        # Clear window
        for widget in self.root.winfo_children():
            widget.destroy()
        
        self.root.geometry("500x600")
        
        # Header
        header = tk.Frame(self.root, bg=self.PRIMARY, height=100)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        tk.Label(
            header,
            text="BART",
            font=("Helvetica", 36, "bold"),
            bg=self.PRIMARY,
            fg=self.SECONDARY
        ).pack(pady=20)
        
        tk.Label(
            header,
            text="Transportation System",
            font=("Helvetica", 14),
            bg=self.PRIMARY,
            fg=self.SECONDARY
        ).pack()
        
        # Login form
        form_frame = tk.Frame(self.root, bg=self.SECONDARY, padx=40, pady=40)
        form_frame.pack(expand=True, fill=tk.BOTH, padx=20, pady=20)
        
        tk.Label(
            form_frame,
            text="Sign In",
            font=("Helvetica", 24, "bold"),
            bg=self.SECONDARY,
            fg=self.TEXT_DARK
        ).pack(pady=(0, 30))
        
        # Username
        tk.Label(
            form_frame,
            text="Username",
            font=("Helvetica", 11),
            bg=self.SECONDARY,
            fg=self.TEXT_DARK
        ).pack(anchor=tk.W, pady=(10, 5))
        
        self.username_entry = tk.Entry(
            form_frame,
            font=("Helvetica", 12),
            relief=tk.SOLID,
            bd=1
        )
        self.username_entry.pack(fill=tk.X, ipady=8)
        
        # Password
        tk.Label(
            form_frame,
            text="Password",
            font=("Helvetica", 11),
            bg=self.SECONDARY,
            fg=self.TEXT_DARK
        ).pack(anchor=tk.W, pady=(15, 5))
        
        self.password_entry = tk.Entry(
            form_frame,
            font=("Helvetica", 12),
            show="●",
            relief=tk.SOLID,
            bd=1
        )
        self.password_entry.pack(fill=tk.X, ipady=8)
        
        # Login button
        ModernButton(
            form_frame,
            text="Sign In",
            font=("Helvetica", 12, "bold"),
            bg=self.PRIMARY,
            fg=self.SECONDARY,
            activebackground=self.PRIMARY,
            activeforeground=self.SECONDARY,
            padx=20,
            pady=12,
            command=self.handle_login
        ).pack(fill=tk.X, pady=(30, 10))
        
        # Register button
        ModernButton(
            form_frame,
            text="Create Account",
            font=("Helvetica", 11),
            bg=self.BG_LIGHT,
            fg=self.PRIMARY,
            activebackground=self.BG_LIGHT,
            activeforeground=self.PRIMARY,
            padx=20,
            pady=10,
            command=self.show_register_screen
        ).pack(fill=tk.X, pady=(5, 10))
        
        # Guest mode button
        ModernButton(
            form_frame,
            text="👤 Continue as Guest",
            font=("Helvetica", 10),
            bg=self.TEXT_LIGHT,
            fg=self.SECONDARY,
            activebackground=self.TEXT_LIGHT,
            activeforeground=self.SECONDARY,
            padx=20,
            pady=8,
            command=self.open_guest_mode
        ).pack(fill=tk.X, pady=(0, 20))
        
        # Demo credentials
        demo_frame = tk.Frame(form_frame, bg=self.BG_LIGHT, relief=tk.SOLID, bd=1)
        demo_frame.pack(fill=tk.X, pady=10)
        
        tk.Label(
            demo_frame,
            text="Demo Accounts",
            font=("Helvetica", 10, "bold"),
            bg=self.BG_LIGHT,
            fg=self.TEXT_DARK
        ).pack(pady=(10, 5))
        
        tk.Label(
            demo_frame,
            text="Passenger: alice / password123\nAdmin: admin / admin123\nSuper Admin: superadmin / admin123",
            font=("Helvetica", 9),
            bg=self.BG_LIGHT,
            fg=self.TEXT_LIGHT,
            justify=tk.LEFT
        ).pack(pady=(0, 10))
        
        # Bind Enter key
        self.password_entry.bind('<Return>', lambda e: self.handle_login())
        
        # Focus username
        self.username_entry.focus()
    
    def handle_login(self):
        """Handle login attempt"""
        username = self.username_entry.get().strip()
        password = self.password_entry.get()
        
        if not username or not password:
            messagebox.showerror("Error", "Please enter username and password")
            return
        
        success, user, message = self.bart_system.login(username, password)
        
        if success:
            self.current_user = user
            self.open_dashboard()
        else:
            messagebox.showerror("Login Failed", message)
    
    def open_guest_mode(self):
        """Open guest mode for trip planning only"""
        self.current_user = None
        GuestDashboard(self.root, self.bart_system, self)
    
    def show_register_screen(self):
        """Show registration dialog"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Create Account")
        dialog.geometry("450x500")
        dialog.configure(bg=self.SECONDARY)
        dialog.transient(self.root)
        dialog.grab_set()
        
        tk.Label(
            dialog,
            text="Create Passenger Account",
            font=("Helvetica", 16, "bold"),
            bg=self.SECONDARY,
            fg=self.PRIMARY
        ).pack(pady=20)
        
        # Form fields
        fields = {}
        
        for label_text, key in [
            ("Full Name", "name"),
            ("Username", "username"),
            ("Password", "password"),
            ("Email", "email")
        ]:
            tk.Label(
                dialog,
                text=label_text,
                font=("Helvetica", 10),
                bg=self.SECONDARY
            ).pack(anchor=tk.W, padx=30, pady=(10, 2))
            
            entry = tk.Entry(dialog, font=("Helvetica", 11), width=35)
            if key == "password":
                entry.config(show="●")
            entry.pack(padx=30)
            fields[key] = entry
        
        # Passenger type
        tk.Label(
            dialog,
            text="Account Type",
            font=("Helvetica", 10),
            bg=self.SECONDARY
        ).pack(anchor=tk.W, padx=30, pady=(10, 2))
        
        type_var = tk.StringVar(value="REGULAR")
        type_frame = tk.Frame(dialog, bg=self.SECONDARY)
        type_frame.pack(padx=30, pady=5)
        
        for ptype in ["REGULAR", "STUDENT", "SENIOR"]:
            tk.Radiobutton(
                type_frame,
                text=ptype.title(),
                variable=type_var,
                value=ptype,
                font=("Helvetica", 10),
                bg=self.SECONDARY
            ).pack(side=tk.LEFT, padx=10)
        
        def register():
            name = fields["name"].get().strip()
            username = fields["username"].get().strip()
            password = fields["password"].get()
            email = fields["email"].get().strip()
            
            if not all([name, username, password, email]):
                messagebox.showerror("Error", "All fields are required")
                return
            
            try:
                passenger_type = PassengerType[type_var.get()]
                passenger = self.bart_system.register(
                    username, password, email, name, passenger_type
                )
                
                messagebox.showinfo(
                    "Success",
                    f"Account created successfully!\n\n"
                    f"Username: {username}\n"
                    f"Type: {passenger_type.value}\n\n"
                    f"You can now sign in."
                )
                dialog.destroy()
            except Exception as e:
                messagebox.showerror("Error", str(e))
        
        ModernButton(
            dialog,
            text="Create Account",
            font=("Helvetica", 11, "bold"),
            bg=self.PRIMARY,
            fg=self.SECONDARY,
            activebackground=self.PRIMARY,
            activeforeground=self.SECONDARY,
            padx=30,
            pady=10,
            command=register
        ).pack(pady=30)
    
    def open_dashboard(self):
        """Open appropriate dashboard based on user role"""
        if isinstance(self.current_user, Passenger):
            PassengerDashboard(self.root, self.bart_system, self.current_user, self)
        elif isinstance(self.current_user, SuperAdmin):
            SuperAdminDashboard(self.root, self.bart_system, self.current_user, self)
        elif isinstance(self.current_user, Admin):
            AdminDashboard(self.root, self.bart_system, self.current_user, self)
        else:
            messagebox.showerror("Error", "Unknown user type")


class PassengerDashboard:
    """Passenger Dashboard for trip planning and travel"""
    
    def __init__(self, root, bart_system: BARTSystem, passenger: Passenger, app):
        self.root = root
        self.bart_system = bart_system
        self.passenger = passenger
        self.app = app
        
        # Ensure card exists - create if needed
        if passenger.card:
            self.card: Card = passenger.card
        else:
            self.card = bart_system.create_card_for_passenger(passenger, 50.00)
        
        # Clear window and setup
        for widget in self.root.winfo_children():
            widget.destroy()
        
        self.root.title(f"BART - Passenger Dashboard ({passenger.name})")
        self.root.geometry("1400x900")
        self.root.configure(bg=app.BG_LIGHT)
        
        self._create_header()
        self._create_main_content()
        self._create_footer()
        
        self.update_displays()
    
    def _create_header(self):
        """Create header with user info"""
        header = tk.Frame(self.root, bg=self.app.PRIMARY, height=80)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        title_frame = tk.Frame(header, bg=self.app.PRIMARY)
        title_frame.pack(side=tk.LEFT, padx=30, pady=10)
        
        tk.Label(
            title_frame,
            text="BART",
            font=("Helvetica", 28, "bold"),
            bg=self.app.PRIMARY,
            fg=self.app.SECONDARY
        ).pack(side=tk.LEFT)
        
        tk.Label(
            title_frame,
            text=f" Passenger Portal - {self.passenger.name}",
            font=("Helvetica", 14),
            bg=self.app.PRIMARY,
            fg=self.app.SECONDARY
        ).pack(side=tk.LEFT, padx=10)
        
        # Logout button
        ModernButton(
            header,
            text="Logout",
            font=("Helvetica", 10),
            bg=self.app.DANGER,
            fg=self.app.SECONDARY,
            activebackground=self.app.DANGER,
            activeforeground=self.app.SECONDARY,
            padx=20,
            pady=8,
            command=self.logout
        ).pack(side=tk.RIGHT, padx=30)
        
        # Edit Profile button
        ModernButton(
            header,
            text="⚙️ Edit Profile",
            font=("Helvetica", 10),
            bg=self.app.TEXT_LIGHT,
            fg=self.app.SECONDARY,
            padx=15,
            pady=8,
            command=self.edit_profile
        ).pack(side=tk.RIGHT, padx=5)
        
        # User type badge
        type_color = self.app.SUCCESS if self.passenger.passenger_type == PassengerType.REGULAR else self.app.WARNING
        tk.Label(
            header,
            text=self.passenger.passenger_type.value,
            font=("Helvetica", 10, "bold"),
            bg=type_color,
            fg=self.app.SECONDARY,
            padx=15,
            pady=5
        ).pack(side=tk.RIGHT, padx=10)
    
    def _create_main_content(self):
        """Create main dashboard content"""
        main = tk.Frame(self.root, bg=self.app.BG_LIGHT)
        main.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Left panel
        left_panel = tk.Frame(main, bg=self.app.SECONDARY)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 10))
        left_panel.config(width=400)
        
        self._create_card_section(left_panel)
        self._create_trip_planner_section(left_panel)
        self._create_gates_section(left_panel)
        
        # Right panel
        right_panel = tk.Frame(main, bg=self.app.BG_LIGHT)
        right_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self._create_trip_history_section(right_panel)
        self._create_live_trains_section(right_panel)
        self._create_alerts_section(right_panel)
    
    def _create_card_section(self, parent):
        """Card information and management"""
        frame = tk.LabelFrame(
            parent,
            text="  My Clipper Card  ",
            font=("Helvetica", 13, "bold"),
            bg=self.app.SECONDARY,
            fg=self.app.PRIMARY
        )
        frame.pack(fill=tk.X, padx=15, pady=15)
        
        info_frame = tk.Frame(frame, bg=self.app.SECONDARY)
        info_frame.pack(fill=tk.X, padx=15, pady=10)
        
        self.card_id_label = tk.Label(
            info_frame,
            text=f"Card: {self.card.card_id}",
            font=("Helvetica", 12, "bold"),
            bg=self.app.SECONDARY,
            fg=self.app.TEXT_DARK
        )
        self.card_id_label.pack(anchor=tk.W)
        
        balance_frame = tk.Frame(info_frame, bg=self.app.SECONDARY)
        balance_frame.pack(fill=tk.X, pady=10)
        
        tk.Label(
            balance_frame,
            text="Balance:",
            font=("Helvetica", 10),
            bg=self.app.SECONDARY,
            fg=self.app.TEXT_LIGHT
        ).pack(side=tk.LEFT)
        
        self.balance_label = tk.Label(
            balance_frame,
            text="$0.00",
            font=("Helvetica", 22, "bold"),
            bg=self.app.SECONDARY,
            fg=self.app.SUCCESS
        )
        self.balance_label.pack(side=tk.LEFT, padx=10)
        
        # Top-up
        topup_frame = tk.Frame(frame, bg=self.app.SECONDARY)
        topup_frame.pack(fill=tk.X, padx=15, pady=(0, 15))
        
        self.topup_entry = tk.Entry(topup_frame, font=("Helvetica", 11), width=10)
        self.topup_entry.pack(side=tk.LEFT, padx=5)
        self.topup_entry.insert(0, "20.00")
        
        ModernButton(
            topup_frame,
            text="Add Funds",
            font=("Helvetica", 10, "bold"),
            bg=self.app.SUCCESS,
            fg=self.app.SECONDARY,
            padx=15,
            pady=6,
            command=self.top_up_card
        ).pack(side=tk.LEFT)
    
    def _create_trip_planner_section(self, parent):
        """Trip planning section"""
        frame = tk.LabelFrame(
            parent,
            text="  Plan Your Trip  ",
            font=("Helvetica", 13, "bold"),
            bg=self.app.SECONDARY,
            fg=self.app.PRIMARY
        )
        frame.pack(fill=tk.X, padx=15, pady=(0, 15))
        
        content = tk.Frame(frame, bg=self.app.SECONDARY)
        content.pack(fill=tk.X, padx=15, pady=15)
        
        # From station
        tk.Label(content, text="From:", font=("Helvetica", 10), bg=self.app.SECONDARY).pack(anchor=tk.W)
        self.from_station_var = tk.StringVar()
        stations = [f"{s.name} (Zone {s.zone})" for s in self.bart_system.get_all_stations()]
        ttk.Combobox(
            content,
            textvariable=self.from_station_var,
            values=stations,
            state="readonly",
            width=30
        ).pack(fill=tk.X, pady=(0, 10))
        
        # To station
        tk.Label(content, text="To:", font=("Helvetica", 10), bg=self.app.SECONDARY).pack(anchor=tk.W)
        self.to_station_var = tk.StringVar()
        ttk.Combobox(
            content,
            textvariable=self.to_station_var,
            values=stations,
            state="readonly",
            width=30
        ).pack(fill=tk.X, pady=(0, 10))
        
        ModernButton(
            content,
            text="Calculate Fare & Time",
            font=("Helvetica", 10, "bold"),
            bg=self.app.PRIMARY,
            fg=self.app.SECONDARY,
            padx=15,
            pady=8,
            command=self.plan_trip
        ).pack(fill=tk.X)
        
        self.plan_result_label = tk.Label(
            content,
            text="",
            font=("Helvetica", 9),
            bg=self.app.SECONDARY,
            fg=self.app.TEXT_DARK,
            justify=tk.LEFT
        )
        self.plan_result_label.pack(pady=(10, 0), anchor=tk.W)
    
    def _create_gates_section(self, parent):
        """Tap in/out section"""
        frame = tk.LabelFrame(
            parent,
            text="  Station Gates  ",
            font=("Helvetica", 13, "bold"),
            bg=self.app.SECONDARY,
            fg=self.app.PRIMARY
        )
        frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))
        
        content = tk.Frame(frame, bg=self.app.SECONDARY)
        content.pack(fill=tk.X, padx=15, pady=15)
        
        # Active trip indicator
        self.active_trip_frame = tk.Frame(content, bg=self.app.WARNING, relief=tk.SOLID, bd=1)
        self.active_trip_label = tk.Label(
            self.active_trip_frame,
            text="No active trip",
            font=("Helvetica", 9, "bold"),
            bg=self.app.WARNING,
            fg=self.app.TEXT_DARK,
            padx=10,
            pady=5
        )
        self.active_trip_label.pack()
        
        # Station selector
        tk.Label(
            content,
            text="Current Station:",
            font=("Helvetica", 10, "bold"),
            bg=self.app.SECONDARY
        ).pack(anchor=tk.W, pady=(15, 5))
        
        self.gate_station_var = tk.StringVar()
        stations = [f"{s.name} (Zone {s.zone})" for s in self.bart_system.get_all_stations()]
        ttk.Combobox(
            content,
            textvariable=self.gate_station_var,
            values=stations,
            state="readonly",
            width=30
        ).pack(fill=tk.X, pady=5)
        
        # Buttons
        btn_frame = tk.Frame(content, bg=self.app.SECONDARY)
        btn_frame.pack(fill=tk.X, pady=(10, 0))
        
        ModernButton(
            btn_frame,
            text="🚪 TAP IN",
            font=("Helvetica", 11, "bold"),
            bg=self.app.SUCCESS,
            fg=self.app.SECONDARY,
            padx=20,
            pady=12,
            command=self.tap_in
        ).pack(fill=tk.X, pady=3)
        
        ModernButton(
            btn_frame,
            text="🚪 TAP OUT",
            font=("Helvetica", 11, "bold"),
            bg=self.app.ACCENT,
            fg=self.app.SECONDARY,
            padx=20,
            pady=12,
            command=self.tap_out
        ).pack(fill=tk.X, pady=3)
    
    def _create_trip_history_section(self, parent):
        """Trip history table"""
        frame = tk.LabelFrame(
            parent,
            text="  My Trip History  ",
            font=("Helvetica", 13, "bold"),
            bg=self.app.SECONDARY,
            fg=self.app.PRIMARY
        )
        frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        tree_frame = tk.Frame(frame, bg=self.app.SECONDARY)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        scrollbar = ttk.Scrollbar(tree_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.trip_tree = ttk.Treeview(
            tree_frame,
            columns=("From", "To", "Date", "Time", "Fare", "Status"),
            show="headings",
            yscrollcommand=scrollbar.set,
            height=10
        )
        
        for col in ["From", "To", "Date", "Time", "Fare", "Status"]:
            self.trip_tree.heading(col, text=col)
            self.trip_tree.column(col, width=120, anchor=tk.CENTER)
        
        self.trip_tree.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.trip_tree.yview)
    
    def _create_live_trains_section(self, parent):
        """Live train tracking section"""
        frame = tk.LabelFrame(
            parent,
            text="  🚃 Live Train Status  ",
            font=("Helvetica", 13, "bold"),
            bg=self.app.SECONDARY,
            fg=self.app.PRIMARY
        )
        frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        # Train table
        table_frame = tk.Frame(frame, bg=self.app.SECONDARY)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)
        
        self.live_train_tree = ttk.Treeview(
            table_frame,
            columns=("Line", "Current", "Next", "ETA", "Status"),
            show="headings",
            height=5
        )
        
        for col, width in [("Line", 90), ("Current", 100), ("Next", 100), ("ETA", 60), ("Status", 80)]:
            self.live_train_tree.heading(col, text=col)
            self.live_train_tree.column(col, width=width, anchor=tk.CENTER)
        
        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.live_train_tree.yview)
        self.live_train_tree.configure(yscrollcommand=scrollbar.set)
        
        self.live_train_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Refresh button
        ModernButton(
            frame,
            text="↻ Refresh",
            font=("Helvetica", 9),
            bg=self.app.PRIMARY,
            fg=self.app.SECONDARY,
            padx=10,
            pady=4,
            command=self.update_live_trains
        ).pack(pady=(0, 10))
    
    def _create_alerts_section(self, parent):
        """Service alerts section"""
        frame = tk.LabelFrame(
            parent,
            text="  ⚠ Service Alerts  ",
            font=("Helvetica", 13, "bold"),
            bg=self.app.SECONDARY,
            fg=self.app.ACCENT
        )
        frame.pack(fill=tk.X)
        
        self.alerts_text = tk.Text(
            frame,
            height=4,
            font=("Helvetica", 9),
            bg=self.app.BG_LIGHT,
            relief=tk.FLAT,
            wrap=tk.WORD
        )
        self.alerts_text.pack(fill=tk.X, padx=15, pady=15)
    
    def _create_footer(self):
        """Create footer"""
        footer = tk.Frame(self.root, bg=self.app.BG_DARK, height=35)
        footer.pack(fill=tk.X)
        footer.pack_propagate(False)
        
        tk.Label(
            footer,
            text="© 2026 BART Transportation System",
            font=("Helvetica", 9),
            bg=self.app.BG_DARK,
            fg=self.app.SECONDARY
        ).pack(pady=8)
    
    # Action methods
    def update_displays(self):
        """Update all displays"""
        if self.card:
            self.balance_label.config(text=f"${self.card.balance:.2f}")
            
            # Active trip
            active_trip = self.bart_system.get_active_trip(self.card)
            if active_trip:
                self.active_trip_frame.pack(fill=tk.X, pady=(0, 10))
                self.active_trip_label.config(
                    text=f"Active: From {active_trip.entry_station.name} | {active_trip.start_time.strftime('%H:%M')}"
                )
            else:
                self.active_trip_frame.pack_forget()
            
            # Trip history
            self.update_trip_history()
            
            # Live trains
            self.update_live_trains()
            
            # Alerts
            self.update_alerts()
    
    def update_trip_history(self):
        """Update trip history table"""
        for item in self.trip_tree.get_children():
            self.trip_tree.delete(item)
        
        trips = self.bart_system.get_passenger_trips(self.passenger)
        for trip in trips[:20]:
            to_station = trip.exit_station.name if trip.exit_station else "In Progress"
            date_str = trip.start_time.strftime("%Y-%m-%d")
            time_str = trip.start_time.strftime("%H:%M")
            fare = f"${trip.fare:.2f}" if trip.fare else "-"
            status = trip.status.value
            
            self.trip_tree.insert("", tk.END, values=(
                trip.entry_station.name, to_station, date_str, time_str, fare, status
            ))
    
    def update_live_trains(self):
        """Update live train status display"""
        for item in self.live_train_tree.get_children():
            self.live_train_tree.delete(item)
        
        for train in self.bart_system.get_all_trains():
            if train.status.value == "Out of Service":
                continue  # Skip out of service trains
            
            current = train.current_station.name if train.current_station else "In Transit"
            next_st = train.next_station.name if train.next_station else "-"
            eta = f"{train.eta_minutes} min" if train.eta_minutes else "-"
            status = train.status.value
            
            # Color code by status
            tag = "delayed" if status == "Delayed" else "normal"
            self.live_train_tree.insert("", tk.END, values=(
                train.line, current, next_st, eta, status
            ), tags=(tag,))
        
        # Configure tag colors
        self.live_train_tree.tag_configure("delayed", foreground="#E53935")
        self.live_train_tree.tag_configure("normal", foreground="#333333")
    
    def update_alerts(self):
        """Update service alerts"""
        self.alerts_text.delete(1.0, tk.END)
        
        all_alerts = [a for a in self.bart_system.alerts.values() if a.is_active]
        
        if not all_alerts:
            self.alerts_text.insert(tk.END, "No active service alerts. All systems operational.")
        else:
            for i, alert in enumerate(all_alerts[:3], 1):
                self.alerts_text.insert(tk.END, f"{i}. {alert.title}: {alert.message}\n")
    
    def plan_trip(self):
        """Plan a trip and show fare estimate"""
        from_text = self.from_station_var.get()
        to_text = self.to_station_var.get()
        
        if not from_text or not to_text:
            messagebox.showerror("Error", "Please select both stations")
            return
        
        from_name = from_text.split(" (Zone")[0]
        to_name = to_text.split(" (Zone")[0]
        
        from_station = None
        to_station = None
        
        for s in self.bart_system.get_all_stations():
            if s.name == from_name:
                from_station = s
            if s.name == to_name:
                to_station = s
        
        if from_station and to_station:
            plan = self.bart_system.plan_trip(from_station, to_station, self.passenger)
            
            result_text = (
                f"Fare: ${plan['fare']:.2f}\n"
                f"Estimated Time: {plan['estimated_time']} min\n"
                f"Zones: {plan['zones']}"
            )
            
            if plan['discount_applied']:
                result_text += f"\n✓ {self.passenger.passenger_type.value} discount applied"
            
            self.plan_result_label.config(text=result_text)
    
    def tap_in(self):
        """Handle tap in"""
        station_text = self.gate_station_var.get()
        if not station_text:
            messagebox.showerror("Error", "Please select a station")
            return
        
        station_name = station_text.split(" (Zone")[0]
        station = None
        for s in self.bart_system.get_all_stations():
            if s.name == station_name:
                station = s
                break
        
        if station:
            try:
                trip = self.bart_system.tap_entry(self.card, station)
                messagebox.showinfo(
                    "Tap In Successful",
                    f"Tapped in at {station.name}\n\n"
                    f"Trip ID: {trip.trip_id}\n"
                    f"Time: {trip.start_time.strftime('%H:%M:%S')}"
                )
                self.update_displays()
            except Exception as e:
                messagebox.showerror("Error", str(e))
    
    def tap_out(self):
        """Handle tap out"""
        station_text = self.gate_station_var.get()
        if not station_text:
            messagebox.showerror("Error", "Please select a station")
            return
        
        station_name = station_text.split(" (Zone")[0]
        station = None
        for s in self.bart_system.get_all_stations():
            if s.name == station_name:
                station = s
                break
        
        if station:
            try:
                trip, fare = self.bart_system.tap_exit(self.card, station)
                discount_msg = ""
                if self.passenger.get_discount_rate() > 0:
                    discount_msg = f"\n({self.passenger.passenger_type.value} discount applied)"
                
                messagebox.showinfo(
                    "Tap Out Successful",
                    f"Tapped out at {station.name}\n\n"
                    f"From: {trip.entry_station.name}\n"
                    f"Fare: ${fare:.2f}{discount_msg}\n"
                    f"Balance: ${self.card.balance:.2f}"
                )
                self.update_displays()
            except Exception as e:
                messagebox.showerror("Error", str(e))
    
    def top_up_card(self):
        """Top up card"""
        try:
            amount = float(self.topup_entry.get())
            if amount <= 0:
                raise ValueError("Amount must be positive")
            
            self.bart_system.top_up_card(self.card, amount)
            messagebox.showinfo(
                "Top Up Successful",
                f"Added ${amount:.2f}\n"
                f"New Balance: ${self.card.balance:.2f}"
            )
            self.update_displays()
        except ValueError as e:
            messagebox.showerror("Error", str(e))
    
    def edit_profile(self):
        """Edit passenger profile"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Edit Profile")
        dialog.geometry("450x400")
        dialog.configure(bg=self.app.SECONDARY)
        dialog.transient(self.root)
        dialog.grab_set()
        
        tk.Label(
            dialog,
            text="Edit Profile",
            font=("Helvetica", 16, "bold"),
            bg=self.app.SECONDARY,
            fg=self.app.PRIMARY
        ).pack(pady=20)
        
        # Current info
        info_frame = tk.Frame(dialog, bg=self.app.BG_LIGHT, relief=tk.SOLID, bd=1)
        info_frame.pack(fill=tk.X, padx=30, pady=10)
        
        tk.Label(
            info_frame,
            text=f"User ID: {self.passenger.user_id}",
            font=("Helvetica", 10),
            bg=self.app.BG_LIGHT
        ).pack(anchor=tk.W, padx=15, pady=5)
        
        tk.Label(
            info_frame,
            text=f"Email: {self.passenger.email}",
            font=("Helvetica", 10),
            bg=self.app.BG_LIGHT
        ).pack(anchor=tk.W, padx=15, pady=5)
        
        # Editable name
        tk.Label(dialog, text="Display Name:", bg=self.app.SECONDARY).pack(anchor=tk.W, padx=30, pady=(15, 2))
        name_entry = tk.Entry(dialog, font=("Helvetica", 11), width=35)
        name_entry.insert(0, self.passenger.name)
        name_entry.pack(padx=30)
        
        # Passenger type selector
        tk.Label(dialog, text="Account Type:", bg=self.app.SECONDARY).pack(anchor=tk.W, padx=30, pady=(15, 2))
        type_var = tk.StringVar(value=self.passenger.passenger_type.name)
        type_frame = tk.Frame(dialog, bg=self.app.SECONDARY)
        type_frame.pack(pady=5)
        
        for ptype in ["REGULAR", "STUDENT", "SENIOR", "DISABLED"]:
            tk.Radiobutton(
                type_frame,
                text=ptype.title(),
                variable=type_var,
                value=ptype,
                bg=self.app.SECONDARY
            ).pack(side=tk.LEFT, padx=5)
        
        def save_profile():
            new_name = name_entry.get().strip()
            if not new_name:
                messagebox.showerror("Error", "Name cannot be empty")
                return
            
            try:
                # Update passenger info
                self.passenger.name = new_name
                self.passenger.passenger_type = PassengerType[type_var.get()]
                
                messagebox.showinfo("Success", "Profile updated successfully!")
                dialog.destroy()
                
                # Refresh the dashboard
                self.root.title(f"BART - Passenger Dashboard ({self.passenger.name})")
            except Exception as e:
                messagebox.showerror("Error", str(e))
        
        ModernButton(
            dialog,
            text="Save Changes",
            font=("Helvetica", 11, "bold"),
            bg=self.app.SUCCESS,
            fg=self.app.SECONDARY,
            padx=30,
            pady=10,
            command=save_profile
        ).pack(pady=20)
    
    def logout(self):
        """Logout and return to login screen"""
        self.app.current_user = None
        self.app.show_login_screen()


class GuestDashboard:
    """Guest Dashboard for trip planning and viewing info (read-only)"""
    
    def __init__(self, root, bart_system: BARTSystem, app):
        self.root = root
        self.bart_system = bart_system
        self.app = app
        
        # Clear window
        for widget in self.root.winfo_children():
            widget.destroy()
        
        self.root.title("BART - Guest Mode")
        self.root.geometry("900x700")
        self.root.configure(bg=app.BG_LIGHT)
        
        self._create_header()
        self._create_main_content()
        self._create_footer()
        self.update_displays()
    
    def _create_header(self):
        """Create header"""
        header = tk.Frame(self.root, bg=self.app.PRIMARY, height=80)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        title_frame = tk.Frame(header, bg=self.app.PRIMARY)
        title_frame.pack(side=tk.LEFT, padx=30, pady=10)
        
        tk.Label(
            title_frame,
            text="🚇 BART Guest Mode",
            font=("Helvetica", 20, "bold"),
            bg=self.app.PRIMARY,
            fg=self.app.SECONDARY
        ).pack(anchor=tk.W)
        
        tk.Label(
            title_frame,
            text="Plan trips and view arrivals (Sign in to purchase tickets)",
            font=("Helvetica", 10),
            bg=self.app.PRIMARY,
            fg=self.app.SECONDARY
        ).pack(anchor=tk.W)
        
        ModernButton(
            header,
            text="Sign In / Register",
            font=("Helvetica", 10, "bold"),
            bg=self.app.SUCCESS,
            fg=self.app.SECONDARY,
            padx=15,
            pady=8,
            command=self.go_to_login
        ).pack(side=tk.RIGHT, padx=30)
    
    def _create_main_content(self):
        """Create main content"""
        main = tk.Frame(self.root, bg=self.app.BG_LIGHT)
        main.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Left panel - Trip planner
        left = tk.Frame(main, bg=self.app.SECONDARY)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        self._create_trip_planner(left)
        self._create_train_arrivals(left)
        
        # Right panel - Alerts and stations
        right = tk.Frame(main, bg=self.app.BG_LIGHT)
        right.pack(side=tk.LEFT, fill=tk.BOTH, padx=(10, 0))
        right.config(width=350)
        
        self._create_alerts_section(right)
        self._create_stations_section(right)
    
    def _create_trip_planner(self, parent):
        """Trip planner section"""
        frame = tk.LabelFrame(
            parent,
            text="  🗺️ Plan Your Trip  ",
            font=("Helvetica", 13, "bold"),
            bg=self.app.SECONDARY,
            fg=self.app.PRIMARY
        )
        frame.pack(fill=tk.X, padx=15, pady=15)
        
        content = tk.Frame(frame, bg=self.app.SECONDARY)
        content.pack(fill=tk.X, padx=15, pady=15)
        
        # From station
        tk.Label(content, text="From:", font=("Helvetica", 10), bg=self.app.SECONDARY).pack(anchor=tk.W)
        self.from_station_var = tk.StringVar()
        stations = [f"{s.name} (Zone {s.zone})" for s in self.bart_system.get_all_stations()]
        ttk.Combobox(
            content,
            textvariable=self.from_station_var,
            values=stations,
            state="readonly",
            width=35
        ).pack(fill=tk.X, pady=(0, 10))
        
        # To station
        tk.Label(content, text="To:", font=("Helvetica", 10), bg=self.app.SECONDARY).pack(anchor=tk.W)
        self.to_station_var = tk.StringVar()
        ttk.Combobox(
            content,
            textvariable=self.to_station_var,
            values=stations,
            state="readonly",
            width=35
        ).pack(fill=tk.X, pady=(0, 10))
        
        ModernButton(
            content,
            text="Calculate Fare & Time",
            font=("Helvetica", 10, "bold"),
            bg=self.app.PRIMARY,
            fg=self.app.SECONDARY,
            padx=15,
            pady=8,
            command=self.plan_trip
        ).pack(fill=tk.X)
        
        self.plan_result_label = tk.Label(
            content,
            text="",
            font=("Helvetica", 10),
            bg=self.app.SECONDARY,
            fg=self.app.TEXT_DARK,
            justify=tk.LEFT
        )
        self.plan_result_label.pack(pady=(10, 0), anchor=tk.W)
    
    def _create_train_arrivals(self, parent):
        """Real-time train arrivals"""
        frame = tk.LabelFrame(
            parent,
            text="  🚆 Real-Time Train Info  ",
            font=("Helvetica", 13, "bold"),
            bg=self.app.SECONDARY,
            fg=self.app.PRIMARY
        )
        frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))
        
        self.train_tree = ttk.Treeview(
            frame,
            columns=("Train", "Line", "Status", "Location"),
            show="headings",
            height=8
        )
        
        for col in ["Train", "Line", "Status", "Location"]:
            self.train_tree.heading(col, text=col)
            self.train_tree.column(col, width=100, anchor=tk.CENTER)
        
        self.train_tree.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
    
    def _create_alerts_section(self, parent):
        """Service alerts"""
        frame = tk.LabelFrame(
            parent,
            text="  ⚠️ Service Alerts  ",
            font=("Helvetica", 13, "bold"),
            bg=self.app.SECONDARY,
            fg=self.app.ACCENT
        )
        frame.pack(fill=tk.X, pady=(0, 10))
        
        self.alerts_text = tk.Text(
            frame,
            height=6,
            font=("Helvetica", 9),
            bg=self.app.BG_LIGHT,
            relief=tk.FLAT,
            wrap=tk.WORD
        )
        self.alerts_text.pack(fill=tk.X, padx=15, pady=15)
    
    def _create_stations_section(self, parent):
        """Stations info"""
        frame = tk.LabelFrame(
            parent,
            text="  📍 Station Status  ",
            font=("Helvetica", 13, "bold"),
            bg=self.app.SECONDARY,
            fg=self.app.PRIMARY
        )
        frame.pack(fill=tk.BOTH, expand=True)
        
        self.station_tree = ttk.Treeview(
            frame,
            columns=("Station", "Zone", "Status"),
            show="headings",
            height=10
        )
        
        for col in ["Station", "Zone", "Status"]:
            self.station_tree.heading(col, text=col)
            self.station_tree.column(col, width=100, anchor=tk.CENTER)
        
        self.station_tree.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
    
    def _create_footer(self):
        """Create footer"""
        footer = tk.Frame(self.root, bg=self.app.BG_DARK, height=35)
        footer.pack(fill=tk.X)
        footer.pack_propagate(False)
        
        tk.Label(
            footer,
            text="© 2026 BART - Sign in to access full features",
            font=("Helvetica", 9),
            bg=self.app.BG_DARK,
            fg=self.app.SECONDARY
        ).pack(pady=8)
    
    def update_displays(self):
        """Update all displays"""
        self.update_trains()
        self.update_alerts()
        self.update_stations()
    
    def update_trains(self):
        """Update train info"""
        for item in self.train_tree.get_children():
            self.train_tree.delete(item)
        
        for train in self.bart_system.get_all_trains():
            location = train.current_station.name if train.current_station else "In Transit"
            self.train_tree.insert("", tk.END, values=(
                train.train_id, train.line, train.status.value, location
            ))
    
    def update_alerts(self):
        """Update alerts"""
        self.alerts_text.delete(1.0, tk.END)
        all_alerts = [a for a in self.bart_system.alerts.values() if a.is_active]
        
        if not all_alerts:
            self.alerts_text.insert(tk.END, "✓ All systems operational. No service alerts.")
        else:
            for i, alert in enumerate(all_alerts[:5], 1):
                self.alerts_text.insert(tk.END, f"{i}. [{alert.alert_type.value}] {alert.title}\n   {alert.message}\n\n")
    
    def update_stations(self):
        """Update station list"""
        for item in self.station_tree.get_children():
            self.station_tree.delete(item)
        
        for station in self.bart_system.get_all_stations():
            self.station_tree.insert("", tk.END, values=(
                station.name, station.zone, station.status.value
            ))
    
    def plan_trip(self):
        """Plan trip"""
        from_text = self.from_station_var.get()
        to_text = self.to_station_var.get()
        
        if not from_text or not to_text:
            messagebox.showerror("Error", "Please select both stations")
            return
        
        from_name = from_text.split(" (Zone")[0]
        to_name = to_text.split(" (Zone")[0]
        
        from_station = None
        to_station = None
        
        for s in self.bart_system.get_all_stations():
            if s.name == from_name:
                from_station = s
            if s.name == to_name:
                to_station = s
        
        if from_station and to_station:
            plan = self.bart_system.plan_trip(from_station, to_station, None)
            
            result_text = (
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"📍 {plan['start']} → {plan['end']}\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"💰 Fare: ${plan['fare']:.2f}\n"
                f"⏱️ Est. Time: {plan['estimated_time']} min\n"
                f"🗺️ Zones: {plan['zones']}\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"Sign in for discounts!"
            )
            
            self.plan_result_label.config(text=result_text)
    
    def go_to_login(self):
        """Return to login screen"""
        self.app.show_login_screen()


class AdminDashboard:
    """Admin Dashboard for system management (Operator level)"""
    
    def __init__(self, root, bart_system: BARTSystem, admin, app):
        self.root = root
        self.bart_system = bart_system
        self.admin = admin
        self.app = app
        
        # Clear window
        for widget in self.root.winfo_children():
            widget.destroy()
        
        self.root.title(f"BART - Admin Dashboard ({admin.name})")
        self.root.geometry("1400x900")
        self.root.configure(bg=app.BG_LIGHT)
        
        self._create_header()
        self._create_main_content()
        self._create_footer()
        
        self.update_displays()
    
    def _create_header(self):
        """Create header"""
        header = tk.Frame(self.root, bg=self.app.PRIMARY, height=80)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        title_frame = tk.Frame(header, bg=self.app.PRIMARY)
        title_frame.pack(side=tk.LEFT, padx=30, pady=10)
        
        tk.Label(
            title_frame,
            text=f"🔧 BART Admin Portal",
            font=("Helvetica", 20, "bold"),
            bg=self.app.PRIMARY,
            fg=self.app.SECONDARY
        ).pack(anchor=tk.W)
        
        tk.Label(
            title_frame,
            text=f"Operator: {self.admin.name} | {getattr(self.admin, 'department', 'Operations')}",
            font=("Helvetica", 10),
            bg=self.app.PRIMARY,
            fg=self.app.SECONDARY
        ).pack(anchor=tk.W)
        
        ModernButton(
            header,
            text="Logout",
            font=("Helvetica", 10),
            bg=self.app.DANGER,
            fg=self.app.SECONDARY,
            padx=20,
            pady=8,
            command=self.logout
        ).pack(side=tk.RIGHT, padx=30)
    
    def _create_main_content(self):
        """Create tabbed admin dashboard"""
        main = tk.Frame(self.root, bg=self.app.BG_LIGHT)
        main.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Create notebook (tabs)
        self.notebook = ttk.Notebook(main)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Tab 1: Dashboard
        self.dashboard_tab = tk.Frame(self.notebook, bg=self.app.BG_LIGHT)
        self.notebook.add(self.dashboard_tab, text="📊 Dashboard")
        self._create_dashboard_tab()
        
        # Tab 2: Station Management
        self.station_tab = tk.Frame(self.notebook, bg=self.app.BG_LIGHT)
        self.notebook.add(self.station_tab, text="🚉 Stations")
        self._create_station_tab()
        
        # Tab 3: Train Management
        self.train_tab = tk.Frame(self.notebook, bg=self.app.BG_LIGHT)
        self.notebook.add(self.train_tab, text="🚆 Trains")
        self._create_train_tab()
        
        # Tab 4: Service Alerts
        self.alerts_tab = tk.Frame(self.notebook, bg=self.app.BG_LIGHT)
        self.notebook.add(self.alerts_tab, text="⚠️ Alerts")
        self._create_alerts_tab()
    
    def _create_dashboard_tab(self):
        """Dashboard with statistics"""
        left = tk.Frame(self.dashboard_tab, bg=self.app.BG_LIGHT)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        tk.Label(
            left,
            text="System Overview",
            font=("Helvetica", 16, "bold"),
            bg=self.app.BG_LIGHT,
            fg=self.app.PRIMARY
        ).pack(anchor=tk.W, pady=(0, 15))
        
        self.stats_labels = {}
        stats_config = [
            ("Total Trips", "total_trips", "#3498db"),
            ("Active Trips", "active_trips", "#e74c3c"),
            ("Total Revenue", "total_revenue", "#f39c12"),
            ("Total Users", "total_users", "#2ecc71")
        ]
        
        cards_frame = tk.Frame(left, bg=self.app.BG_LIGHT)
        cards_frame.pack(fill=tk.X)
        
        for i, (label, key, color) in enumerate(stats_config):
            card = tk.Frame(cards_frame, bg=color, relief=tk.FLAT)
            card.grid(row=i//2, column=i%2, padx=10, pady=10, sticky="nsew")
            
            tk.Label(card, text=label, font=("Helvetica", 10, "bold"), bg=color, fg="white").pack(pady=(15, 5), padx=30)
            value_label = tk.Label(card, text="0", font=("Helvetica", 22, "bold"), bg=color, fg="white")
            value_label.pack(pady=(0, 15))
            self.stats_labels[key] = value_label
        
        # Report section
        report_frame = tk.Frame(left, bg=self.app.SECONDARY, relief=tk.SOLID, bd=1)
        report_frame.pack(fill=tk.X, pady=20)
        
        tk.Label(
            report_frame,
            text="Generate Reports",
            font=("Helvetica", 12, "bold"),
            bg=self.app.SECONDARY
        ).pack(pady=(15, 10))
        
        ModernButton(
            report_frame,
            text="📊 Ridership Report",
            font=("Helvetica", 10),
            bg=self.app.PRIMARY,
            fg=self.app.SECONDARY,
            padx=20,
            pady=10,
            command=self.generate_report
        ).pack(pady=(0, 15))
    
    def _create_station_tab(self):
        """Station management"""
        tree_frame = tk.Frame(self.station_tab, bg=self.app.BG_LIGHT)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        self.station_tree = ttk.Treeview(
            tree_frame,
            columns=("Name", "Zone", "Status"),
            show="headings",
            height=15
        )
        
        for col in ["Name", "Zone", "Status"]:
            self.station_tree.heading(col, text=col)
            self.station_tree.column(col, width=150, anchor=tk.CENTER)
        
        self.station_tree.pack(fill=tk.BOTH, expand=True)
        
        btn_frame = tk.Frame(self.station_tab, bg=self.app.BG_LIGHT)
        btn_frame.pack(fill=tk.X, padx=15, pady=(0, 15))
        
        ModernButton(btn_frame, text="Close Station", bg=self.app.DANGER, fg=self.app.SECONDARY,
                    padx=10, pady=5, command=self.close_selected_station).pack(side=tk.LEFT, padx=5)
        ModernButton(btn_frame, text="Open Station", bg=self.app.SUCCESS, fg=self.app.SECONDARY,
                    padx=10, pady=5, command=self.open_selected_station).pack(side=tk.LEFT, padx=5)
    
    def _create_train_tab(self):
        """Train management"""
        tree_frame = tk.Frame(self.train_tab, bg=self.app.BG_LIGHT)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        self.train_tree = ttk.Treeview(
            tree_frame,
            columns=("ID", "Line", "Status", "Location"),
            show="headings",
            height=15
        )
        
        for col, width in [("ID", 100), ("Line", 150), ("Status", 120), ("Location", 180)]:
            self.train_tree.heading(col, text=col)
            self.train_tree.column(col, width=width, anchor=tk.CENTER)
        
        self.train_tree.pack(fill=tk.BOTH, expand=True)
        
        btn_frame = tk.Frame(self.train_tab, bg=self.app.BG_LIGHT)
        btn_frame.pack(fill=tk.X, padx=15, pady=(0, 15))
        
        for text, status, color in [
            ("Set Running", TrainStatus.RUNNING, self.app.SUCCESS),
            ("Set Delayed", TrainStatus.DELAYED, self.app.WARNING),
            ("Out of Service", TrainStatus.OUT_OF_SERVICE, self.app.DANGER)
        ]:
            fg = "white" if color != self.app.WARNING else "black"
            ModernButton(btn_frame, text=text, bg=color, fg=fg, padx=10, pady=5,
                        command=lambda s=status: self.update_train_status(s)).pack(side=tk.LEFT, padx=5)
    
    def _create_alerts_tab(self):
        """Alert management"""
        tree_frame = tk.Frame(self.alerts_tab, bg=self.app.BG_LIGHT)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        self.alert_tree = ttk.Treeview(
            tree_frame,
            columns=("Type", "Title", "Created", "Status"),
            show="headings",
            height=12
        )
        
        for col, width in [("Type", 100), ("Title", 250), ("Created", 150), ("Status", 80)]:
            self.alert_tree.heading(col, text=col)
            self.alert_tree.column(col, width=width, anchor=tk.CENTER)
        
        self.alert_tree.pack(fill=tk.BOTH, expand=True)
        
        btn_frame = tk.Frame(self.alerts_tab, bg=self.app.BG_LIGHT)
        btn_frame.pack(fill=tk.X, padx=15, pady=(0, 15))
        
        ModernButton(btn_frame, text="+ Create Alert", bg=self.app.WARNING, fg=self.app.TEXT_DARK,
                    font=("Helvetica", 10, "bold"), padx=15, pady=8, command=self.create_alert).pack(side=tk.LEFT, padx=5)
        ModernButton(btn_frame, text="Close Alert", bg=self.app.DANGER, fg=self.app.SECONDARY,
                    padx=10, pady=8, command=self.close_selected_alert).pack(side=tk.LEFT, padx=5)
    
    def _create_footer(self):
        """Create footer"""
        footer = tk.Frame(self.root, bg=self.app.BG_DARK, height=35)
        footer.pack(fill=tk.X)
        footer.pack_propagate(False)
        
        tk.Label(
            footer,
            text="© 2026 BART Admin Portal | Operator Access",
            font=("Helvetica", 9),
            bg=self.app.BG_DARK,
            fg=self.app.SECONDARY
        ).pack(pady=8)
    
    def update_displays(self):
        """Update all displays"""
        self.update_stats()
        self.update_stations()
        self.update_trains()
        self.update_alerts()
    
    def update_stats(self):
        """Update statistics"""
        stats = self.bart_system.get_system_stats()
        self.stats_labels["total_trips"].config(text=str(stats["total_trips"]))
        self.stats_labels["active_trips"].config(text=str(stats["active_trips"]))
        self.stats_labels["total_revenue"].config(text=f"${stats['total_revenue']:.2f}")
        self.stats_labels["total_users"].config(text=str(stats["total_users"]))
    
    def update_stations(self):
        """Update station list"""
        for item in self.station_tree.get_children():
            self.station_tree.delete(item)
        
        for station in self.bart_system.get_all_stations():
            self.station_tree.insert("", tk.END, values=(
                station.name, station.zone, station.status.value
            ), tags=(station.station_id,))
    
    def update_trains(self):
        """Update train list"""
        for item in self.train_tree.get_children():
            self.train_tree.delete(item)
        
        for train in self.bart_system.get_all_trains():
            location = train.current_station.name if train.current_station else "In Transit"
            self.train_tree.insert("", tk.END, values=(
                train.train_id, train.line, train.status.value, location
            ), tags=(train.train_id,))
    
    def update_alerts(self):
        """Update alert list"""
        for item in self.alert_tree.get_children():
            self.alert_tree.delete(item)
        
        for alert in self.bart_system.alerts.values():
            status = "Active" if alert.is_active else "Closed"
            self.alert_tree.insert("", tk.END, values=(
                alert.alert_type.value, alert.title,
                alert.start_time.strftime("%Y-%m-%d %H:%M"), status
            ), tags=(alert.alert_id,))
    
    def close_selected_station(self):
        """Close selected station"""
        selection = self.station_tree.selection()
        if not selection:
            messagebox.showerror("Error", "Please select a station")
            return
        
        station_id = self.station_tree.item(selection[0])["tags"][0]
        station = self.bart_system.get_station(station_id)
        
        if station is None:
            messagebox.showerror("Error", "Station not found")
            return
        
        try:
            self.bart_system.admin_close_station(self.admin, station)
            messagebox.showinfo("Success", f"Station {station.name} closed")
            self.update_displays()
        except Exception as e:
            messagebox.showerror("Error", str(e))
    
    def open_selected_station(self):
        """Open selected station"""
        selection = self.station_tree.selection()
        if not selection:
            messagebox.showerror("Error", "Please select a station")
            return
        
        station_id = self.station_tree.item(selection[0])["tags"][0]
        station = self.bart_system.get_station(station_id)
        
        if station is None:
            messagebox.showerror("Error", "Station not found")
            return
        
        try:
            self.bart_system.admin_open_station(self.admin, station)
            messagebox.showinfo("Success", f"Station {station.name} opened")
            self.update_displays()
        except Exception as e:
            messagebox.showerror("Error", str(e))
    
    def create_alert(self):
        """Create a service alert"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Create Service Alert")
        dialog.geometry("500x400")
        dialog.configure(bg=self.app.SECONDARY)
        dialog.transient(self.root)
        dialog.grab_set()
        
        tk.Label(
            dialog,
            text="Create Service Alert",
            font=("Helvetica", 14, "bold"),
            bg=self.app.SECONDARY
        ).pack(pady=20)
        
        # Title
        tk.Label(dialog, text="Alert Title:", bg=self.app.SECONDARY).pack(anchor=tk.W, padx=30)
        title_entry = tk.Entry(dialog, width=50)
        title_entry.pack(padx=30, pady=5)
        
        # Message
        tk.Label(dialog, text="Message:", bg=self.app.SECONDARY).pack(anchor=tk.W, padx=30, pady=(10, 0))
        message_text = tk.Text(dialog, height=5, width=50)
        message_text.pack(padx=30, pady=5)
        
        # Type
        tk.Label(dialog, text="Alert Type:", bg=self.app.SECONDARY).pack(anchor=tk.W, padx=30, pady=(10, 0))
        type_var = tk.StringVar(value="DELAY")
        type_frame = tk.Frame(dialog, bg=self.app.SECONDARY)
        type_frame.pack(pady=5)
        
        for atype in ["DELAY", "CLOSURE", "MAINTENANCE"]:
            tk.Radiobutton(
                type_frame,
                text=atype,
                variable=type_var,
                value=atype,
                bg=self.app.SECONDARY
            ).pack(side=tk.LEFT, padx=10)
        
        def create():
            title = title_entry.get().strip()
            message = message_text.get(1.0, tk.END).strip()
            
            if not title or not message:
                messagebox.showerror("Error", "Please fill all fields")
                return
            
            try:
                alert_type = AlertType[type_var.get()]
                # Create alert affecting first 3 stations
                affected = list(self.bart_system.stations.values())[:3]
                alert = self.bart_system.admin_create_alert(
                    self.admin, alert_type, title, message, affected
                )
                messagebox.showinfo("Success", f"Alert created: {alert.alert_id}")
                dialog.destroy()
            except Exception as e:
                messagebox.showerror("Error", str(e))
        
        ModernButton(
            dialog,
            text="Create Alert",
            bg=self.app.WARNING,
            fg=self.app.TEXT_DARK,
            padx=30,
            pady=10,
            command=create
        ).pack(pady=20)
    
    def generate_report(self):
        """Generate ridership report"""
        try:
            stats = self.bart_system.admin_get_ridership_stats(self.admin)
            
            report = (
                f"BART RIDERSHIP REPORT\n"
                f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
                f"Total Trips: {stats['total_trips']}\n"
                f"Closed Trips: {stats['closed_trips']}\n"
                f"Active Trips: {stats['active_trips']}\n"
                f"Total Revenue: ${stats['total_revenue']:.2f}\n"
                f"Average Fare: ${stats['average_fare']:.2f}\n\n"
                f"Busiest Stations:\n"
            )
            
            for i, (station, count) in enumerate(stats['busiest_stations'], 1):
                report += f"{i}. {station}: {count} trips\n"
            
            messagebox.showinfo("Ridership Report", report)
        except Exception as e:
            messagebox.showerror("Error", str(e))
    
    def update_train_status(self, status: TrainStatus):
        """Update selected train status"""
        selection = self.train_tree.selection()
        if not selection:
            messagebox.showerror("Error", "Please select a train")
            return
        
        train_id = self.train_tree.item(selection[0])["tags"][0]
        train = self.bart_system.get_train(train_id)
        
        if train is None:
            messagebox.showerror("Error", "Train not found")
            return
        
        try:
            self.bart_system.admin_update_train_status(self.admin, train, status)
            messagebox.showinfo("Success", f"Train {train_id} status updated to {status.value}")
            self.update_displays()
        except Exception as e:
            messagebox.showerror("Error", str(e))
    
    def close_selected_alert(self):
        """Close selected alert"""
        selection = self.alert_tree.selection()
        if not selection:
            messagebox.showerror("Error", "Please select an alert")
            return
        
        alert_id = self.alert_tree.item(selection[0])["tags"][0]
        alert = self.bart_system.alerts.get(alert_id)
        
        if alert:
            try:
                self.bart_system.admin_close_alert(self.admin, alert)
                messagebox.showinfo("Success", "Alert closed")
                self.update_displays()
            except Exception as e:
                messagebox.showerror("Error", str(e))
    
    def logout(self):
        """Logout"""
        self.app.current_user = None
        self.app.show_login_screen()


class SuperAdminDashboard:
    """Super Admin Dashboard with full system control"""
    
    def __init__(self, root, bart_system: BARTSystem, admin: SuperAdmin, app):
        self.root = root
        self.bart_system = bart_system
        self.admin = admin
        self.app = app
        
        # Clear window
        for widget in self.root.winfo_children():
            widget.destroy()
        
        self.root.title(f"BART - Super Admin Control Panel ({admin.name})")
        self.root.geometry("1500x950")
        self.root.configure(bg=app.BG_LIGHT)
        
        self._create_header()
        self._create_main_content()
        self._create_footer()
        self.update_displays()
    
    def _create_header(self):
        """Create header with role badge"""
        header = tk.Frame(self.root, bg="#1a1a2e", height=90)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        title_frame = tk.Frame(header, bg="#1a1a2e")
        title_frame.pack(side=tk.LEFT, padx=30, pady=10)
        
        tk.Label(
            title_frame,
            text="🛡️ BART Super Admin Control Panel",
            font=("Helvetica", 20, "bold"),
            bg="#1a1a2e",
            fg="#eee"
        ).pack(anchor=tk.W)
        
        tk.Label(
            title_frame,
            text=f"Full System Access | {self.admin.name} | System Control",
            font=("Helvetica", 10),
            bg="#1a1a2e",
            fg="#888"
        ).pack(anchor=tk.W)
        
        ModernButton(
            header,
            text="Logout",
            font=("Helvetica", 10),
            bg=self.app.DANGER,
            fg=self.app.SECONDARY,
            padx=20,
            pady=8,
            command=self.logout
        ).pack(side=tk.RIGHT, padx=30)
    
    def _create_main_content(self):
        """Create tabbed interface"""
        main = tk.Frame(self.root, bg=self.app.BG_LIGHT)
        main.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Create notebook (tabs)
        self.notebook = ttk.Notebook(main)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Tab 1: Dashboard & Stats
        self.dashboard_tab = tk.Frame(self.notebook, bg=self.app.BG_LIGHT)
        self.notebook.add(self.dashboard_tab, text="📊 Dashboard")
        self._create_dashboard_tab()
        
        # Tab 2: Station Management
        self.station_tab = tk.Frame(self.notebook, bg=self.app.BG_LIGHT)
        self.notebook.add(self.station_tab, text="🚉 Stations")
        self._create_station_tab()
        
        # Tab 3: Train Management
        self.train_tab = tk.Frame(self.notebook, bg=self.app.BG_LIGHT)
        self.notebook.add(self.train_tab, text="🚆 Trains")
        self._create_train_tab()
        
        # Tab 4: Fare Rules (Super Admin Only)
        self.fare_tab = tk.Frame(self.notebook, bg=self.app.BG_LIGHT)
        self.notebook.add(self.fare_tab, text="💰 Fare Rules")
        self._create_fare_tab()
        
        # Tab 5: Admin Management (Super Admin Only)
        self.admin_tab = tk.Frame(self.notebook, bg=self.app.BG_LIGHT)
        self.notebook.add(self.admin_tab, text="👥 Admin Accounts")
        self._create_admin_tab()
        
        # Tab 6: Service Alerts
        self.alerts_tab = tk.Frame(self.notebook, bg=self.app.BG_LIGHT)
        self.notebook.add(self.alerts_tab, text="⚠️ Alerts")
        self._create_alerts_tab()
    
    def _create_dashboard_tab(self):
        """Dashboard with statistics"""
        # Left - Stats cards
        left = tk.Frame(self.dashboard_tab, bg=self.app.BG_LIGHT)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        tk.Label(
            left,
            text="System Statistics",
            font=("Helvetica", 16, "bold"),
            bg=self.app.BG_LIGHT,
            fg=self.app.PRIMARY
        ).pack(anchor=tk.W, pady=(0, 15))
        
        self.stats_labels = {}
        stats_config = [
            ("Total Users", "total_users", "#2ecc71"),
            ("Total Trips", "total_trips", "#3498db"),
            ("Active Trips", "active_trips", "#e74c3c"),
            ("Total Revenue", "total_revenue", "#f39c12"),
            ("Total Stations", "total_stations", "#9b59b6"),
            ("Active Trains", "total_trains", "#1abc9c")
        ]
        
        cards_frame = tk.Frame(left, bg=self.app.BG_LIGHT)
        cards_frame.pack(fill=tk.X)
        
        for i, (label, key, color) in enumerate(stats_config):
            card = tk.Frame(cards_frame, bg=color, relief=tk.FLAT)
            card.grid(row=i//3, column=i%3, padx=10, pady=10, sticky="nsew")
            
            tk.Label(
                card,
                text=label,
                font=("Helvetica", 10, "bold"),
                bg=color,
                fg="white"
            ).pack(pady=(15, 5), padx=20)
            
            value_label = tk.Label(
                card,
                text="0",
                font=("Helvetica", 24, "bold"),
                bg=color,
                fg="white"
            )
            value_label.pack(pady=(0, 15))
            self.stats_labels[key] = value_label
        
        # Report button
        ModernButton(
            left,
            text="📊 Generate Full Report",
            font=("Helvetica", 11, "bold"),
            bg=self.app.PRIMARY,
            fg=self.app.SECONDARY,
            padx=20,
            pady=12,
            command=self.generate_report
        ).pack(pady=20)
        
        # Right - Quick actions
        right = tk.Frame(self.dashboard_tab, bg=self.app.SECONDARY)
        right.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)
        right.config(width=300)
        
        tk.Label(
            right,
            text="Quick Actions",
            font=("Helvetica", 14, "bold"),
            bg=self.app.SECONDARY,
            fg=self.app.PRIMARY
        ).pack(pady=20)
        
        for text, cmd, color in [
            ("🚫 Emergency: Close All Stations", self.emergency_close_all, self.app.DANGER),
            ("✅ Open All Stations", self.open_all_stations, self.app.SUCCESS),
            ("⚠️ Create System Alert", self.create_alert, self.app.WARNING),
            ("🔄 Refresh Data", self.update_displays, self.app.PRIMARY)
        ]:
            ModernButton(
                right,
                text=text,
                font=("Helvetica", 10),
                bg=color,
                fg="white" if color != self.app.WARNING else "black",
                padx=15,
                pady=10,
                command=cmd
            ).pack(fill=tk.X, padx=20, pady=5)
    
    def _create_station_tab(self):
        """Station management"""
        # Tree view
        tree_frame = tk.Frame(self.station_tab, bg=self.app.BG_LIGHT)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        self.station_tree = ttk.Treeview(
            tree_frame,
            columns=("ID", "Name", "Zone", "Status"),
            show="headings",
            height=15
        )
        
        for col, width in [("ID", 80), ("Name", 200), ("Zone", 80), ("Status", 100)]:
            self.station_tree.heading(col, text=col)
            self.station_tree.column(col, width=width, anchor=tk.CENTER)
        
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.station_tree.yview)
        self.station_tree.configure(yscrollcommand=scrollbar.set)
        
        self.station_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Buttons
        btn_frame = tk.Frame(self.station_tab, bg=self.app.BG_LIGHT)
        btn_frame.pack(fill=tk.X, padx=15, pady=(0, 15))
        
        for text, cmd, color in [
            ("Close Selected", self.close_selected_station, self.app.DANGER),
            ("Open Selected", self.open_selected_station, self.app.SUCCESS),
            ("Add New Station", self.add_station_dialog, self.app.PRIMARY)
        ]:
            ModernButton(
                btn_frame,
                text=text,
                font=("Helvetica", 10),
                bg=color,
                fg=self.app.SECONDARY,
                padx=15,
                pady=8,
                command=cmd
            ).pack(side=tk.LEFT, padx=5)
    
    def _create_train_tab(self):
        """Train management"""
        # Tree view
        tree_frame = tk.Frame(self.train_tab, bg=self.app.BG_LIGHT)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        self.train_tree = ttk.Treeview(
            tree_frame,
            columns=("ID", "Line", "Capacity", "Status", "Current", "Next", "ETA"),
            show="headings",
            height=15
        )
        
        for col, width in [("ID", 70), ("Line", 120), ("Capacity", 70), ("Status", 100), ("Current", 130), ("Next", 130), ("ETA", 60)]:
            self.train_tree.heading(col, text=col)
            self.train_tree.column(col, width=width, anchor=tk.CENTER)
        
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.train_tree.yview)
        self.train_tree.configure(yscrollcommand=scrollbar.set)
        
        self.train_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Buttons
        btn_frame = tk.Frame(self.train_tab, bg=self.app.BG_LIGHT)
        btn_frame.pack(fill=tk.X, padx=15, pady=(0, 15))
        
        for text, cmd, color in [
            ("Set Running", lambda: self.update_train_status(TrainStatus.RUNNING), self.app.SUCCESS),
            ("Set Delayed", lambda: self.update_train_status(TrainStatus.DELAYED), self.app.WARNING),
            ("Out of Service", lambda: self.update_train_status(TrainStatus.OUT_OF_SERVICE), self.app.DANGER),
            ("Update Location", self.update_train_location_dialog, "#9C27B0"),
            ("Add New Train", self.add_train_dialog, self.app.PRIMARY)
        ]:
            ModernButton(
                btn_frame,
                text=text,
                font=("Helvetica", 10),
                bg=color,
                fg="white" if color != self.app.WARNING else "black",
                padx=12,
                pady=8,
                command=cmd
            ).pack(side=tk.LEFT, padx=5)
    
    def update_train_location_dialog(self):
        """Dialog to update train's current and next station"""
        selected = self.train_tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select a train first")
            return
        
        train_id = self.train_tree.item(selected[0])["values"][0]
        train = self.bart_system.trains.get(str(train_id))
        if not train:
            return
        
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Update Location - {train_id}")
        dialog.geometry("400x350")
        dialog.configure(bg=self.app.SECONDARY)
        dialog.transient(self.root)
        dialog.grab_set()
        
        tk.Label(
            dialog,
            text=f"📍 Update Train {train_id} Location",
            font=("Helvetica", 14, "bold"),
            bg=self.app.SECONDARY,
            fg=self.app.PRIMARY
        ).pack(pady=15)
        
        tk.Label(
            dialog,
            text=f"Line: {train.line}",
            font=("Helvetica", 11),
            bg=self.app.SECONDARY
        ).pack(pady=5)
        
        # Station list for dropdowns
        stations = list(self.bart_system.stations.values())
        station_names = ["None (In Transit)"] + [s.name for s in stations]
        
        # Current Station
        frame1 = tk.Frame(dialog, bg=self.app.SECONDARY)
        frame1.pack(fill=tk.X, padx=30, pady=10)
        
        tk.Label(
            frame1,
            text="Current Station:",
            font=("Helvetica", 11, "bold"),
            bg=self.app.SECONDARY,
            width=15,
            anchor=tk.W
        ).pack(side=tk.LEFT)
        
        current_var = tk.StringVar()
        current_combo = ttk.Combobox(frame1, textvariable=current_var, values=station_names, width=25, state="readonly")
        if train.current_station:
            current_combo.set(train.current_station.name)
        else:
            current_combo.set("None (In Transit)")
        current_combo.pack(side=tk.LEFT, padx=10)
        
        # Next Station
        frame2 = tk.Frame(dialog, bg=self.app.SECONDARY)
        frame2.pack(fill=tk.X, padx=30, pady=10)
        
        tk.Label(
            frame2,
            text="Next Station:",
            font=("Helvetica", 11, "bold"),
            bg=self.app.SECONDARY,
            width=15,
            anchor=tk.W
        ).pack(side=tk.LEFT)
        
        next_var = tk.StringVar()
        next_combo = ttk.Combobox(frame2, textvariable=next_var, values=station_names, width=25, state="readonly")
        if train.next_station:
            next_combo.set(train.next_station.name)
        else:
            next_combo.set("None (In Transit)")
        next_combo.pack(side=tk.LEFT, padx=10)
        
        # ETA
        frame3 = tk.Frame(dialog, bg=self.app.SECONDARY)
        frame3.pack(fill=tk.X, padx=30, pady=10)
        
        tk.Label(
            frame3,
            text="ETA (minutes):",
            font=("Helvetica", 11, "bold"),
            bg=self.app.SECONDARY,
            width=15,
            anchor=tk.W
        ).pack(side=tk.LEFT)
        
        eta_entry = tk.Entry(frame3, font=("Helvetica", 11), width=10)
        eta_entry.insert(0, str(train.eta_minutes if train.eta_minutes else 0))
        eta_entry.pack(side=tk.LEFT, padx=10)
        
        def save_location():
            current_name = current_var.get()
            next_name = next_var.get()
            
            current_station = None
            next_station = None
            
            if current_name != "None (In Transit)":
                for s in stations:
                    if s.name == current_name:
                        current_station = s
                        break
            
            if next_name != "None (In Transit)":
                for s in stations:
                    if s.name == next_name:
                        next_station = s
                        break
            
            try:
                eta = int(eta_entry.get()) if eta_entry.get() else None
            except ValueError:
                eta = None
            
            train.update_location(current_station, next_station, eta)
            self.update_trains()
            dialog.destroy()
            messagebox.showinfo("Success", f"Train {train_id} location updated!")
        
        # Buttons
        btn_frame = tk.Frame(dialog, bg=self.app.SECONDARY)
        btn_frame.pack(pady=20)
        
        ModernButton(
            btn_frame,
            text="Save",
            bg=self.app.SUCCESS,
            fg="white",
            padx=20,
            pady=8,
            command=save_location
        ).pack(side=tk.LEFT, padx=10)
        
        ModernButton(
            btn_frame,
            text="Cancel",
            bg=self.app.DANGER,
            fg="white",
            padx=20,
            pady=8,
            command=dialog.destroy
        ).pack(side=tk.LEFT, padx=10)
    
    def _create_fare_tab(self):
        """Fare rules management (Super Admin only)"""
        frame = tk.Frame(self.fare_tab, bg=self.app.SECONDARY)
        frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        tk.Label(
            frame,
            text="💰 Fare Configuration",
            font=("Helvetica", 18, "bold"),
            bg=self.app.SECONDARY,
            fg=self.app.PRIMARY
        ).pack(pady=20)
        
        tk.Label(
            frame,
            text="🔒 Super Admin Only - Changes affect all fare calculations",
            font=("Helvetica", 10),
            bg=self.app.SECONDARY,
            fg=self.app.DANGER
        ).pack(pady=(0, 20))
        
        # Current values
        from models import FareCalculator
        
        settings_frame = tk.Frame(frame, bg=self.app.BG_LIGHT, relief=tk.SOLID, bd=1)
        settings_frame.pack(fill=tk.X, padx=50, pady=10)
        
        # Base fare
        row1 = tk.Frame(settings_frame, bg=self.app.BG_LIGHT)
        row1.pack(fill=tk.X, padx=20, pady=15)
        
        tk.Label(
            row1,
            text="Base Fare ($):",
            font=("Helvetica", 12, "bold"),
            bg=self.app.BG_LIGHT
        ).pack(side=tk.LEFT)
        
        self.base_fare_entry = tk.Entry(row1, font=("Helvetica", 12), width=10)
        self.base_fare_entry.insert(0, f"{FareCalculator.BASE_FARE:.2f}")
        self.base_fare_entry.pack(side=tk.LEFT, padx=10)
        
        ModernButton(
            row1,
            text="Update",
            bg=self.app.SUCCESS,
            fg=self.app.SECONDARY,
            padx=10,
            pady=5,
            command=self.update_base_fare
        ).pack(side=tk.LEFT, padx=5)
        
        # Zone rate
        row2 = tk.Frame(settings_frame, bg=self.app.BG_LIGHT)
        row2.pack(fill=tk.X, padx=20, pady=15)
        
        tk.Label(
            row2,
            text="Per Zone Rate ($):",
            font=("Helvetica", 12, "bold"),
            bg=self.app.BG_LIGHT
        ).pack(side=tk.LEFT)
        
        self.zone_rate_entry = tk.Entry(row2, font=("Helvetica", 12), width=10)
        self.zone_rate_entry.insert(0, f"{FareCalculator.ZONE_RATE:.2f}")
        self.zone_rate_entry.pack(side=tk.LEFT, padx=10)
        
        ModernButton(
            row2,
            text="Update",
            bg=self.app.SUCCESS,
            fg=self.app.SECONDARY,
            padx=10,
            pady=5,
            command=self.update_zone_rate
        ).pack(side=tk.LEFT, padx=5)
        
        # Discount info
        discount_frame = tk.LabelFrame(
            frame,
            text="  Discount Rates  ",
            font=("Helvetica", 12, "bold"),
            bg=self.app.BG_LIGHT
        )
        discount_frame.pack(fill=tk.X, padx=50, pady=20)
        
        for ptype, discount in [("Student", "20%"), ("Senior", "35%"), ("Disabled", "50%")]:
            tk.Label(
                discount_frame,
                text=f"  {ptype}: {discount} discount",
                font=("Helvetica", 11),
                bg=self.app.BG_LIGHT,
                fg=self.app.TEXT_DARK
            ).pack(anchor=tk.W, pady=5, padx=10)
    
    def _create_admin_tab(self):
        """Admin account management (Super Admin only)"""
        frame = tk.Frame(self.admin_tab, bg=self.app.SECONDARY)
        frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        tk.Label(
            frame,
            text="👥 Admin Account Management",
            font=("Helvetica", 18, "bold"),
            bg=self.app.SECONDARY,
            fg=self.app.PRIMARY
        ).pack(pady=20)
        
        tk.Label(
            frame,
            text="🔒 Super Admin Only - Manage operator accounts",
            font=("Helvetica", 10),
            bg=self.app.SECONDARY,
            fg=self.app.DANGER
        ).pack(pady=(0, 20))
        
        # Admin list
        tree_frame = tk.Frame(frame, bg=self.app.SECONDARY)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=20)
        
        self.admin_tree = ttk.Treeview(
            tree_frame,
            columns=("ID", "Username", "Name", "Role", "Department"),
            show="headings",
            height=10
        )
        
        for col, width in [("ID", 80), ("Username", 120), ("Name", 150), ("Role", 100), ("Department", 150)]:
            self.admin_tree.heading(col, text=col)
            self.admin_tree.column(col, width=width, anchor=tk.CENTER)
        
        self.admin_tree.pack(fill=tk.BOTH, expand=True)
        
        # Buttons
        btn_frame = tk.Frame(frame, bg=self.app.SECONDARY)
        btn_frame.pack(fill=tk.X, padx=20, pady=15)
        
        ModernButton(
            btn_frame,
            text="+ Create Admin Account",
            font=("Helvetica", 11, "bold"),
            bg=self.app.SUCCESS,
            fg=self.app.SECONDARY,
            padx=20,
            pady=10,
            command=self.create_admin_dialog
        ).pack(side=tk.LEFT, padx=5)
    
    def _create_alerts_tab(self):
        """Service alerts management"""
        # Active alerts list
        tree_frame = tk.Frame(self.alerts_tab, bg=self.app.BG_LIGHT)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        tk.Label(
            tree_frame,
            text="Active Service Alerts",
            font=("Helvetica", 14, "bold"),
            bg=self.app.BG_LIGHT,
            fg=self.app.PRIMARY
        ).pack(anchor=tk.W, pady=(0, 10))
        
        self.alert_tree = ttk.Treeview(
            tree_frame,
            columns=("ID", "Type", "Title", "Created", "Status"),
            show="headings",
            height=12
        )
        
        for col, width in [("ID", 80), ("Type", 100), ("Title", 250), ("Created", 150), ("Status", 80)]:
            self.alert_tree.heading(col, text=col)
            self.alert_tree.column(col, width=width, anchor=tk.CENTER)
        
        self.alert_tree.pack(fill=tk.BOTH, expand=True)
        
        # Buttons
        btn_frame = tk.Frame(self.alerts_tab, bg=self.app.BG_LIGHT)
        btn_frame.pack(fill=tk.X, padx=15, pady=(0, 15))
        
        ModernButton(
            btn_frame,
            text="+ Create New Alert",
            font=("Helvetica", 10, "bold"),
            bg=self.app.WARNING,
            fg=self.app.TEXT_DARK,
            padx=15,
            pady=8,
            command=self.create_alert
        ).pack(side=tk.LEFT, padx=5)
        
        ModernButton(
            btn_frame,
            text="Close Selected Alert",
            font=("Helvetica", 10),
            bg=self.app.DANGER,
            fg=self.app.SECONDARY,
            padx=15,
            pady=8,
            command=self.close_selected_alert
        ).pack(side=tk.LEFT, padx=5)
    
    def _create_footer(self):
        """Create footer"""
        footer = tk.Frame(self.root, bg="#1a1a2e", height=35)
        footer.pack(fill=tk.X)
        footer.pack_propagate(False)
        
        tk.Label(
            footer,
            text="© 2026 BART Super Admin Control Panel | Full System Access",
            font=("Helvetica", 9),
            bg="#1a1a2e",
            fg="#888"
        ).pack(pady=8)
    
    def update_displays(self):
        """Update all displays"""
        self.update_stats()
        self.update_stations()
        self.update_trains()
        self.update_admins()
        self.update_alerts()
    
    def update_stats(self):
        """Update statistics"""
        stats = self.bart_system.get_system_stats()
        self.stats_labels["total_users"].config(text=str(stats["total_users"]))
        self.stats_labels["total_trips"].config(text=str(stats["total_trips"]))
        self.stats_labels["active_trips"].config(text=str(stats["active_trips"]))
        self.stats_labels["total_revenue"].config(text=f"${stats['total_revenue']:.2f}")
        self.stats_labels["total_stations"].config(text=str(stats["total_stations"]))
        self.stats_labels["total_trains"].config(text=str(stats["total_trains"]))
    
    def update_stations(self):
        """Update station list"""
        for item in self.station_tree.get_children():
            self.station_tree.delete(item)
        
        for station in self.bart_system.get_all_stations():
            self.station_tree.insert("", tk.END, values=(
                station.station_id, station.name, station.zone, station.status.value
            ), tags=(station.station_id,))
    
    def update_trains(self):
        """Update train list"""
        for item in self.train_tree.get_children():
            self.train_tree.delete(item)
        
        for train in self.bart_system.get_all_trains():
            current = train.current_station.name if train.current_station else "In Transit"
            next_st = train.next_station.name if train.next_station else "-"
            eta = f"{train.eta_minutes} min" if train.eta_minutes else "-"
            self.train_tree.insert("", tk.END, values=(
                train.train_id, train.line, train.capacity, train.status.value, current, next_st, eta
            ), tags=(train.train_id,))
    
    def update_admins(self):
        """Update admin list"""
        for item in self.admin_tree.get_children():
            self.admin_tree.delete(item)
        
        for user in self.bart_system.auth_service.users.values():
            if isinstance(user, (Admin, SuperAdmin)):
                role = "Super Admin" if isinstance(user, SuperAdmin) else "Admin"
                dept = getattr(user, 'department', 'N/A')
                self.admin_tree.insert("", tk.END, values=(
                    user.user_id, user.username, user.name, role, dept
                ))
    
    def update_alerts(self):
        """Update alerts list"""
        for item in self.alert_tree.get_children():
            self.alert_tree.delete(item)
        
        for alert in self.bart_system.alerts.values():
            status = "Active" if alert.is_active else "Closed"
            self.alert_tree.insert("", tk.END, values=(
                alert.alert_id, alert.alert_type.value, alert.title,
                alert.start_time.strftime("%Y-%m-%d %H:%M"), status
            ), tags=(alert.alert_id,))
    
    def close_selected_station(self):
        """Close selected station"""
        selection = self.station_tree.selection()
        if not selection:
            messagebox.showerror("Error", "Please select a station")
            return
        
        station_id = self.station_tree.item(selection[0])["tags"][0]
        station = self.bart_system.get_station(station_id)
        
        if station is None:
            messagebox.showerror("Error", "Station not found")
            return
        
        try:
            self.bart_system.admin_close_station(self.admin, station)
            messagebox.showinfo("Success", f"Station {station.name} closed")
            self.update_displays()
        except Exception as e:
            messagebox.showerror("Error", str(e))
    
    def open_selected_station(self):
        """Open selected station"""
        selection = self.station_tree.selection()
        if not selection:
            messagebox.showerror("Error", "Please select a station")
            return
        
        station_id = self.station_tree.item(selection[0])["tags"][0]
        station = self.bart_system.get_station(station_id)
        
        if station is None:
            messagebox.showerror("Error", "Station not found")
            return
        
        try:
            self.bart_system.admin_open_station(self.admin, station)
            messagebox.showinfo("Success", f"Station {station.name} opened")
            self.update_displays()
        except Exception as e:
            messagebox.showerror("Error", str(e))
    
    def emergency_close_all(self):
        """Emergency close all stations"""
        if messagebox.askyesno("Confirm", "Close ALL stations? This is an emergency action."):
            for station in self.bart_system.get_all_stations():
                try:
                    self.bart_system.admin_close_station(self.admin, station)
                except:
                    pass
            messagebox.showinfo("Emergency", "All stations have been closed!")
            self.update_displays()
    
    def open_all_stations(self):
        """Open all stations"""
        if messagebox.askyesno("Confirm", "Open ALL stations?"):
            for station in self.bart_system.get_all_stations():
                try:
                    self.bart_system.admin_open_station(self.admin, station)
                except:
                    pass
            messagebox.showinfo("Success", "All stations are now open!")
            self.update_displays()
    
    def add_station_dialog(self):
        """Add new station dialog"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Add New Station")
        dialog.geometry("400x300")
        dialog.configure(bg=self.app.SECONDARY)
        dialog.transient(self.root)
        dialog.grab_set()
        
        tk.Label(dialog, text="Add New Station", font=("Helvetica", 14, "bold"), bg=self.app.SECONDARY).pack(pady=20)
        
        fields = {}
        for label, key in [("Station ID", "id"), ("Station Name", "name"), ("Zone", "zone")]:
            tk.Label(dialog, text=label, bg=self.app.SECONDARY).pack(anchor=tk.W, padx=30)
            entry = tk.Entry(dialog, width=30)
            entry.pack(padx=30, pady=5)
            fields[key] = entry
        
        def add():
            try:
                station = self.bart_system.admin_add_station(
                    self.admin, fields["id"].get(), fields["name"].get(), 
                    int(fields["zone"].get()), 0.0, 0.0  # Default lat/lon
                )
                messagebox.showinfo("Success", f"Station {station.name} added!")
                dialog.destroy()
                self.update_displays()
            except Exception as e:
                messagebox.showerror("Error", str(e))
        
        ModernButton(dialog, text="Add Station", bg=self.app.PRIMARY, fg=self.app.SECONDARY, command=add).pack(pady=20)
    
    def add_train_dialog(self):
        """Add new train dialog"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Add New Train")
        dialog.geometry("400x350")
        dialog.configure(bg=self.app.SECONDARY)
        dialog.transient(self.root)
        dialog.grab_set()
        
        tk.Label(dialog, text="Add New Train", font=("Helvetica", 14, "bold"), bg=self.app.SECONDARY).pack(pady=20)
        
        fields = {}
        for label, key in [("Train ID", "id"), ("Line", "line"), ("Capacity", "capacity")]:
            tk.Label(dialog, text=label, bg=self.app.SECONDARY).pack(anchor=tk.W, padx=30)
            entry = tk.Entry(dialog, width=30)
            entry.pack(padx=30, pady=5)
            fields[key] = entry
        
        def add():
            try:
                train = self.bart_system.admin_add_train(
                    self.admin, fields["id"].get(), fields["line"].get(), int(fields["capacity"].get())
                )
                messagebox.showinfo("Success", f"Train {train.train_id} added!")
                dialog.destroy()
                self.update_displays()
            except Exception as e:
                messagebox.showerror("Error", str(e))
        
        ModernButton(dialog, text="Add Train", bg=self.app.PRIMARY, fg=self.app.SECONDARY, command=add).pack(pady=20)
    
    def update_train_status(self, status: TrainStatus):
        """Update train status"""
        selection = self.train_tree.selection()
        if not selection:
            messagebox.showerror("Error", "Please select a train")
            return
        
        train_id = self.train_tree.item(selection[0])["tags"][0]
        train = self.bart_system.get_train(train_id)
        
        if train is None:
            messagebox.showerror("Error", "Train not found")
            return
        
        try:
            self.bart_system.admin_update_train_status(self.admin, train, status)
            messagebox.showinfo("Success", f"Train {train_id} status updated to {status.value}")
            self.update_displays()
        except Exception as e:
            messagebox.showerror("Error", str(e))
    
    def update_base_fare(self):
        """Update base fare"""
        try:
            new_fare = float(self.base_fare_entry.get())
            self.bart_system.admin_update_base_fare(self.admin, new_fare)
            messagebox.showinfo("Success", f"Base fare updated to ${new_fare:.2f}")
        except Exception as e:
            messagebox.showerror("Error", str(e))
    
    def update_zone_rate(self):
        """Update zone rate"""
        try:
            new_rate = float(self.zone_rate_entry.get())
            self.bart_system.admin_update_zone_rate(self.admin, new_rate)
            messagebox.showinfo("Success", f"Zone rate updated to ${new_rate:.2f}")
        except Exception as e:
            messagebox.showerror("Error", str(e))
    
    def create_admin_dialog(self):
        """Create admin account"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Create Admin Account")
        dialog.geometry("450x450")
        dialog.configure(bg=self.app.SECONDARY)
        dialog.transient(self.root)
        dialog.grab_set()
        
        tk.Label(dialog, text="Create Admin Account", font=("Helvetica", 14, "bold"), bg=self.app.SECONDARY).pack(pady=20)
        
        fields = {}
        for label, key in [("Username", "username"), ("Password", "password"), ("Name", "name"), ("Email", "email"), ("Department", "department")]:
            tk.Label(dialog, text=label, bg=self.app.SECONDARY).pack(anchor=tk.W, padx=30)
            if key == "password":
                entry = tk.Entry(dialog, width=35, show="●")
            else:
                entry = tk.Entry(dialog, width=35)
            entry.pack(padx=30, pady=3)
            fields[key] = entry
        
        def create():
            try:
                admin = self.bart_system.auth_service.register_user(
                    fields["username"].get(),
                    fields["password"].get(),
                    fields["email"].get(),
                    "admin",
                    name=fields["name"].get(),
                    department=fields["department"].get()
                )
                messagebox.showinfo("Success", f"Admin {admin.username} created!")
                dialog.destroy()
                self.update_displays()
            except Exception as e:
                messagebox.showerror("Error", str(e))
        
        ModernButton(dialog, text="Create Admin", bg=self.app.SUCCESS, fg=self.app.SECONDARY, command=create).pack(pady=20)
    
    def create_alert(self):
        """Create service alert"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Create Service Alert")
        dialog.geometry("500x450")
        dialog.configure(bg=self.app.SECONDARY)
        dialog.transient(self.root)
        dialog.grab_set()
        
        tk.Label(dialog, text="Create Service Alert", font=("Helvetica", 14, "bold"), bg=self.app.SECONDARY).pack(pady=20)
        
        tk.Label(dialog, text="Alert Title:", bg=self.app.SECONDARY).pack(anchor=tk.W, padx=30)
        title_entry = tk.Entry(dialog, width=50)
        title_entry.pack(padx=30, pady=5)
        
        tk.Label(dialog, text="Message:", bg=self.app.SECONDARY).pack(anchor=tk.W, padx=30, pady=(10, 0))
        message_text = tk.Text(dialog, height=5, width=50)
        message_text.pack(padx=30, pady=5)
        
        tk.Label(dialog, text="Alert Type:", bg=self.app.SECONDARY).pack(anchor=tk.W, padx=30, pady=(10, 0))
        type_var = tk.StringVar(value="DELAY")
        type_frame = tk.Frame(dialog, bg=self.app.SECONDARY)
        type_frame.pack(pady=5)
        
        for atype in ["DELAY", "CLOSURE", "MAINTENANCE"]:
            tk.Radiobutton(type_frame, text=atype, variable=type_var, value=atype, bg=self.app.SECONDARY).pack(side=tk.LEFT, padx=10)
        
        def create():
            title = title_entry.get().strip()
            message = message_text.get(1.0, tk.END).strip()
            
            if not title or not message:
                messagebox.showerror("Error", "Please fill all fields")
                return
            
            try:
                alert_type = AlertType[type_var.get()]
                affected = list(self.bart_system.stations.values())[:3]
                alert = self.bart_system.admin_create_alert(self.admin, alert_type, title, message, affected)
                messagebox.showinfo("Success", f"Alert {alert.alert_id} created!")
                dialog.destroy()
                self.update_displays()
            except Exception as e:
                messagebox.showerror("Error", str(e))
        
        ModernButton(dialog, text="Create Alert", bg=self.app.WARNING, fg=self.app.TEXT_DARK, command=create).pack(pady=20)
    
    def close_selected_alert(self):
        """Close selected alert"""
        selection = self.alert_tree.selection()
        if not selection:
            messagebox.showerror("Error", "Please select an alert")
            return
        
        alert_id = self.alert_tree.item(selection[0])["values"][0]
        alert = self.bart_system.alerts.get(alert_id)
        
        if alert:
            try:
                self.bart_system.admin_close_alert(self.admin, alert)
                messagebox.showinfo("Success", "Alert closed")
                self.update_displays()
            except Exception as e:
                messagebox.showerror("Error", str(e))
    
    def generate_report(self):
        """Generate ridership report"""
        try:
            stats = self.bart_system.admin_get_ridership_stats(self.admin)
            
            report = (
                f"{'='*50}\n"
                f"       BART SYSTEM RIDERSHIP REPORT\n"
                f"{'='*50}\n"
                f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
                f"Report By: {self.admin.name} (Super Admin)\n\n"
                f"SUMMARY:\n"
                f"  Total Trips: {stats['total_trips']}\n"
                f"  Closed Trips: {stats['closed_trips']}\n"
                f"  Active Trips: {stats['active_trips']}\n"
                f"  Total Revenue: ${stats['total_revenue']:.2f}\n"
                f"  Average Fare: ${stats['average_fare']:.2f}\n\n"
                f"BUSIEST STATIONS:\n"
            )
            
            for i, (station, count) in enumerate(stats['busiest_stations'][:5], 1):
                report += f"  {i}. {station}: {count} trips\n"
            
            report += f"\n{'='*50}"
            
            messagebox.showinfo("System Report", report)
        except Exception as e:
            messagebox.showerror("Error", str(e))
    
    def logout(self):
        """Logout"""
        self.app.current_user = None
        self.app.show_login_screen()


def main():
    """Main entry point"""
    root = tk.Tk()
    app = BARTLoginApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
