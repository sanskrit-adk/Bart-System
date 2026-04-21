"""
BART Transportation System - Enhanced System Controller
Step 2: Authentication, Admin Management, and Business Logic
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Union, cast
from .models import (
    User, Passenger, Admin, SuperAdmin,
    Station, Train, Card, Trip, Gate, ServiceAlert,
    FareCalculator, TapEvent, InputValidator,
    UserRole, PassengerType, StationStatus, TrainStatus,
    CardStatus, TapType, TripStatus, AlertType
)
from .database import Database

# Type alias for admin users
AdminUser = Union[Admin, SuperAdmin]


class AuthenticationService:
    """
    Handles user authentication and session management
    """
    
    def __init__(self):
        self.users: Dict[str, User] = {}
        self.sessions: Dict[str, User] = {}  # session_token -> User
        self.username_index: Dict[str, User] = {}  # username -> User
    
    def register_user(self, username: str, password: str, email: str, 
                     user_type: str, **kwargs) -> User:
        """
        Register a new user
        
        Args:
            username: Username
            password: Password
            email: Email
            user_type: "passenger", "admin", "super_admin"
            **kwargs: Additional user-specific fields
            
        Returns:
            Created User object
            
        Raises:
            ValueError: If username already exists
        """
        username = username.strip().lower()
        InputValidator.validate_username(username)
        InputValidator.validate_password(password)
        InputValidator.validate_email(email)
        if 'name' in kwargs and kwargs['name']:
            kwargs['name'] = InputValidator.validate_name(kwargs['name'])

        if username in self.username_index:
            raise ValueError(f"Username '{username}' is already taken.")

        user_id = f"U{len(self.users)+1:04d}"
        
        if user_type == "passenger":
            name = kwargs.get("name", username)
            passenger_type = kwargs.get("passenger_type", PassengerType.REGULAR)
            user = Passenger(user_id, username, password, email, name, passenger_type)
        elif user_type == "admin":
            name = kwargs.get("name", username)
            department = kwargs.get("department", "Operations")
            user = Admin(user_id, username, password, email, name, department)
        elif user_type == "super_admin":
            name = kwargs.get("name", username)
            user = SuperAdmin(user_id, username, password, email, name)
        else:
            raise ValueError(f"Invalid user type: {user_type}")
        
        self.users[user_id] = user
        self.username_index[username] = user
        return user
    
    def login(self, username: str, password: str) -> Tuple[bool, Optional[User], str]:
        """
        Authenticate user and create session
        
        Args:
            username: Username
            password: Password
            
        Returns:
            Tuple of (success, user, message)
        """
        user = self.username_index.get(username.strip().lower())

        if not user:
            return False, None, "Username not found"
        
        if not user.verify_password(password):
            return False, None, "Incorrect password"
        
        # Create session
        session_token = f"S{user.user_id}_{datetime.now().timestamp()}"
        self.sessions[session_token] = user
        user.login()
        
        return True, user, "Login successful"
    
    def logout(self, session_token: str):
        """Logout user by removing session"""
        if session_token in self.sessions:
            del self.sessions[session_token]
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        return self.username_index.get(username)
    
    def get_all_users(self) -> List[User]:
        """Get all users"""
        return list(self.users.values())


class BARTSystem:
    """
    Enhanced BART system controller with role-based access
    
    Manages:
    - Authentication
    - Stations, trains, schedules
    - Trips and fares
    - Service alerts
    - Admin operations
    """
    
    def __init__(self, _test_mode: bool = False):
        # Core collections
        self.db = Database(in_memory=_test_mode)
        self.auth_service = AuthenticationService()
        self.stations: Dict[str, Station] = {}
        self.trains: Dict[str, Train] = {}
        self.cards: Dict[str, Card] = {}
        self.trips: Dict[str, Trip] = {}
        self.gates: Dict[str, Gate] = {}
        self.alerts: Dict[str, ServiceAlert] = {}
        self.active_trips: Dict[str, Trip] = {}  # card_id -> active trip

        # Initialize system
        self._initialize_stations()
        self._initialize_trains()
        self._load_persisted_data()   # load DB users/cards/trips first
        self._create_default_users()  # create defaults only if missing
    
    def _initialize_stations(self):
        """Initialize BART stations with GPS coordinates"""
        stations_data = [
            # Zone 1 - Downtown San Francisco
            ("S001", "Embarcadero", 1, 37.7929, -122.3972),
            ("S002", "Montgomery", 1, 37.7894, -122.4013),
            ("S003", "Powell", 1, 37.7844, -122.4079),
            ("S004", "Civic Center", 1, 37.7798, -122.4134),
            
            # Zone 2 - Mid-City & Inner East Bay
            ("S005", "16th Street", 2, 37.7649, -122.4194),
            ("S006", "24th Street", 2, 37.7524, -122.4183),
            ("S007", "Glen Park", 2, 37.7329, -122.4339),
            ("S008", "Berkeley", 2, 37.8703, -122.2678),
            ("S009", "Oakland", 2, 37.8044, -122.2712),
            
            # Zone 3 - Outer San Francisco
            ("S010", "Balboa Park", 3, 37.7213, -122.4469),
            ("S011", "Daly City", 3, 37.7059, -122.4692),
            
            # Zone 4 - Peninsula North
            ("S012", "Colma", 4, 37.6846, -122.4661),
            ("S013", "South San Francisco", 4, 37.6640, -122.4444),
            
            # Zone 5 - Peninsula South
            ("S014", "San Bruno", 5, 37.6371, -122.4160),
            ("S015", "Millbrae", 5, 37.5996, -122.3869),
        ]
        
        for station_id, name, zone, lat, lon in stations_data:
            station = Station(station_id, name, zone, lat, lon)
            self.stations[station_id] = station
            
            # Create gates
            entry_gate = Gate(f"G{station_id}E", TapType.ENTRY, station)
            exit_gate = Gate(f"G{station_id}X", TapType.EXIT, station)
            self.gates[entry_gate.gate_id] = entry_gate
            self.gates[exit_gate.gate_id] = exit_gate
    
    def _initialize_trains(self):
        """Initialize BART trains with initial locations"""
        trains_data = [
            ("T001", "Red Line", 200),
            ("T002", "Red Line", 200),
            ("T003", "Blue Line", 180),
            ("T004", "Blue Line", 180),
            ("T005", "Green Line", 180),
            ("T006", "Yellow Line", 200),
        ]
        
        for train_id, line, capacity in trains_data:
            train = Train(train_id, line, capacity)
            self.trains[train_id] = train
        
        # Assign initial locations to trains
        stations = list(self.stations.values())
        if len(stations) >= 6:
            # T001: Red Line - Embarcadero -> Montgomery
            self.trains["T001"].update_location(stations[0], stations[1], 3)
            self.trains["T001"].status = TrainStatus.DELAYED
            # T002: Red Line - Powell -> Civic Center
            self.trains["T002"].update_location(stations[2], stations[3], 5)
            # T003: Blue Line - 16th St -> 24th St
            self.trains["T003"].update_location(stations[4], stations[5], 4)
            # T004: Blue Line - Glen Park -> Balboa Park
            self.trains["T004"].update_location(stations[6] if len(stations) > 6 else stations[5], 
                                                 stations[7] if len(stations) > 7 else stations[0], 6)
            # T005: Green Line - Daly City -> Colma  
            self.trains["T005"].update_location(stations[8] if len(stations) > 8 else stations[0],
                                                 stations[9] if len(stations) > 9 else stations[1], 8)
            # T006: Yellow Line - South SF -> San Bruno
            self.trains["T006"].update_location(stations[10] if len(stations) > 10 else stations[2],
                                                 stations[11] if len(stations) > 11 else stations[3], 7)
    
    def _create_default_users(self):
        """Create default system users if they don't already exist in the DB."""
        defaults = [
            ("superadmin", "admin123", "super@bart.gov",
             "super_admin", {"name": "System Administrator"}),
            ("admin", "admin123", "admin@bart.gov",
             "admin", {"name": "John Admin", "department": "Operations"}),
            ("alice", "password123", "alice@example.com",
             "passenger", {"name": "Alice Johnson",
                           "passenger_type": PassengerType.STUDENT}),
        ]
        for username, password, email, utype, kwargs in defaults:
            if username not in self.auth_service.username_index:
                user = self.auth_service.register_user(
                    username, password, email, utype, **kwargs)
                self.db.save_user(user)
                # Give alice a starter card
                if utype == "passenger":
                    self.create_card_for_passenger(
                        cast(Passenger, user), 50.00)

    def _load_persisted_data(self):
        """Load users, cards and trips saved in previous sessions."""
        # ── Users ──
        for row in self.db.load_users():
            if row["username"] in self.auth_service.username_index:
                continue  # already in memory (shouldn't happen, but guard)
            role = row["role"]
            if role == "PASSENGER":
                pt = PassengerType[row["passenger_type"]] \
                     if row["passenger_type"] else PassengerType.REGULAR
                user = Passenger(row["user_id"], row["username"],
                                 "__hashed__", row["email"],
                                 row["name"], pt)
            elif role == "ADMIN":
                user = Admin(row["user_id"], row["username"],
                             "__hashed__", row["email"],
                             row["name"],
                             row["department"] or "Operations")
            elif role == "SUPER_ADMIN":
                user = SuperAdmin(row["user_id"], row["username"],
                                  "__hashed__", row["email"],
                                  row["name"])
            else:
                continue
            # Restore the real hash (bypass normal hashing)
            user.password_hash = row["password_hash"]
            user.created_at = datetime.fromisoformat(row["created_at"])
            self.auth_service.users[user.user_id] = user
            self.auth_service.username_index[user.username] = user

        # ── Cards ──
        for row in self.db.load_cards():
            owner = self.auth_service.users.get(row["owner_id"])
            if not owner or not isinstance(owner, Passenger):
                continue
            card = Card(row["card_id"], row["balance"])
            card.status = CardStatus[row["status"]]
            card.owner = owner
            owner.link_card(card)
            self.cards[card.card_id] = card

        # ── Trips ──
        for row in self.db.load_trips():
            card = self.cards.get(row["card_id"])
            passenger = self.auth_service.users.get(row["passenger_id"])
            entry_st = self.stations.get(row["entry_station"])
            if not card or not passenger or not entry_st:
                continue
            trip = Trip(row["trip_id"], card,
                        datetime.fromisoformat(row["start_time"]), entry_st)
            if row["exit_station"]:
                trip.exit_station = self.stations.get(row["exit_station"])
            if row["end_time"]:
                trip.end_time = datetime.fromisoformat(row["end_time"])
            if row["fare"] is not None:
                trip.fare = row["fare"]
            trip.status = TripStatus[row["status"]]
            self.trips[trip.trip_id] = trip
            if trip.status == TripStatus.ACTIVE:
                self.active_trips[card.card_id] = trip
    
    # ========================================================================
    # AUTHENTICATION METHODS
    # ========================================================================
    
    def login(self, username: str, password: str) -> Tuple[bool, Optional[User], str]:
        """Login user"""
        return self.auth_service.login(username, password)
    
    def register(self, username: str, password: str, email: str,
                name: str, passenger_type: PassengerType = PassengerType.REGULAR) -> Passenger:
        """Register new passenger and persist to database."""
        passenger = cast(Passenger, self.auth_service.register_user(
            username, password, email, "passenger",
            name=name, passenger_type=passenger_type
        ))
        self.db.save_user(passenger)
        return passenger
    
    def get_current_user(self, username: str) -> Optional[User]:
        """Get user by username"""
        return self.auth_service.get_user_by_username(username)
    
    # ========================================================================
    # PASSENGER OPERATIONS
    # ========================================================================
    
    def create_card_for_passenger(self, passenger: Passenger, initial_balance: float = 0.0) -> Card:
        """Create, link, and persist a card for a passenger."""
        card_id = f"C{len(self.cards)+1:04d}"
        card = Card(card_id, initial_balance)
        card.owner = passenger
        passenger.link_card(card)
        self.cards[card_id] = card
        self.db.save_card(card, passenger.user_id)
        if initial_balance > 0:
            self.db.save_transaction(
                card_id, "TOPUP", initial_balance, initial_balance,
                "Initial card load")
        return card
    
    def get_passenger_card(self, passenger: Passenger) -> Optional[Card]:
        """Get passenger's card"""
        return passenger.card
    
    def top_up_card(self, card: Card, amount: float):
        """Top up a card and persist the new balance."""
        card.top_up(amount)
        self.db.update_card(card)
        self.db.save_transaction(
            card.card_id, "TOPUP", amount, card.balance,
            f"Top-up ${amount:.2f}")
    
    def get_card_transactions(self, card: Card) -> List:
        """Get card transaction history"""
        return card.transactions
    
    # ========================================================================
    # TRIP OPERATIONS
    # ========================================================================
    
    # ========================================================================
    # SERVICE HOURS
    # ========================================================================

    @staticmethod
    def is_service_hours() -> bool:
        """BART operates 5:00 AM – 12:30 AM daily."""
        mins = datetime.now().hour * 60 + datetime.now().minute
        return not (30 <= mins < 300)   # suspended 12:30 AM – 4:59 AM

    def _get_system_admin(self) -> Optional["SuperAdmin"]:
        for u in self.auth_service.users.values():
            if isinstance(u, SuperAdmin):
                return u
        return None

    def run_service_hours_check(self) -> str:
        """
        Enforce nightly train suspension / morning resumption.
        Returns 'suspended', 'resumed', or 'no_change'.
        """
        sa = self._get_system_admin()
        if not sa:
            return 'no_change'
        in_service = self.is_service_hours()
        if not in_service:
            running = [t for t in self.trains.values()
                       if t.status == TrainStatus.RUNNING]
            if running:
                for t in running:
                    t.update_status(TrainStatus.OUT_OF_SERVICE)
                self.admin_create_alert(
                    sa, AlertType.CLOSURE,
                    "Night Service Suspended",
                    "All BART trains suspended 12:30 AM – 5:00 AM. "
                    "Regular service resumes at 5:00 AM.",
                    list(self.stations.values())
                )
                return 'suspended'
        else:
            suspended = [t for t in self.trains.values()
                         if t.status == TrainStatus.OUT_OF_SERVICE]
            if suspended:
                for t in suspended:
                    t.update_status(TrainStatus.RUNNING)
                for a in self.alerts.values():
                    if a.is_active and "Night Service" in a.title:
                        a.close_alert()
                self.admin_create_alert(
                    sa, AlertType.MAINTENANCE,
                    "Morning Service Active",
                    "All BART trains are back in service.",
                    list(self.stations.values())
                )
                return 'resumed'
        return 'no_change'

    def tap_entry(self, card: Card, station: Station) -> Trip:
        """
        Handle entry tap (Passenger operation)

        Validates:
        - Service hours (5:00 AM – 12:30 AM)
        - Card is active
        - Station is open
        - No existing active trip
        """
        if not self.is_service_hours():
            raise ValueError(
                "BART is not in service (12:30 AM – 5:00 AM). "
                "Service resumes at 5:00 AM.")
        if not card.is_active():
            raise ValueError("Card is frozen or expired")
        
        if not station.is_operational():
            raise ValueError(f"Station {station.name} is currently closed")
        
        if card.card_id in self.active_trips:
            active = self.active_trips[card.card_id]
            raise ValueError(f"Active trip exists from {active.entry_station.name}. Please tap out first.")
        
        # Create trip
        trip_id = f"TR{len(self.trips)+1:04d}"
        trip = Trip(trip_id, card, datetime.now(), station)
        
        # Create tap event
        gate = self.gates.get(f"G{station.station_id}E")
        if gate:
            trip.entry_tap = gate.create_tap_event()
        
        self.trips[trip_id] = trip
        self.active_trips[card.card_id] = trip
        self.db.save_trip(trip)

        return trip
    
    def tap_exit(self, card: Card, station: Station) -> Tuple[Trip, float]:
        """
        Handle exit tap (Passenger operation)
        
        Validates:
        - Card is active
        - Station is open
        - Active trip exists
        - Sufficient balance
        """
        if not card.is_active():
            raise ValueError("Card is frozen or expired")
        
        if not station.is_operational():
            raise ValueError(f"Station {station.name} is currently closed")
        
        if card.card_id not in self.active_trips:
            raise ValueError("No active trip found. Please tap in first.")
        
        trip = self.active_trips[card.card_id]
        
        # Calculate fare with discount
        passenger = card.owner
        fare = FareCalculator.calculate_fare(trip.entry_station, station, passenger)
        
        # Check balance
        if card.balance < fare:
            raise ValueError(f"Insufficient balance. Fare: ${fare:.2f}, Balance: ${card.balance:.2f}")
        
        # Deduct fare
        card.debit(fare)
        
        # Create exit tap event
        gate = self.gates.get(f"G{station.station_id}X")
        if gate:
            trip.exit_tap = gate.create_tap_event()
        
        # Close trip
        trip.close_trip(station, datetime.now(), fare)
        
        # Remove from active trips
        del self.active_trips[card.card_id]

        # Persist updated card balance and closed trip
        self.db.update_card(card)
        self.db.save_transaction(
            card.card_id, "FARE", -fare, card.balance,
            f"Fare {trip.entry_station.name} → {station.name}")
        self.db.save_trip(trip)

        return trip, fare
    
    def get_passenger_trips(self, passenger: Passenger) -> List[Trip]:
        """Get all trips for a passenger"""
        trips = [t for t in self.trips.values() if t.passenger == passenger]
        return sorted(trips, key=lambda t: t.start_time, reverse=True)
    
    def get_active_trip(self, card: Card) -> Optional[Trip]:
        """Get active trip for a card"""
        return self.active_trips.get(card.card_id)
    
    # ========================================================================
    # TRIP PLANNING (Passenger feature)
    # ========================================================================
    
    def plan_trip(self, start_station: Station, end_station: Station, 
                  passenger: Optional[Passenger] = None) -> dict:
        """
        Plan a trip and estimate fare/time
        
        Args:
            start_station: Starting station
            end_station: Destination station
            passenger: Passenger (for discount)
            
        Returns:
            Dictionary with trip details
        """
        fare = FareCalculator.calculate_fare(start_station, end_station, passenger)
        zone_diff = abs(start_station.zone - end_station.zone)
        
        # Estimate time (5 minutes per zone + 2 minutes base)
        estimated_time = 2 + (zone_diff * 5)
        
        return {
            "start": start_station.name,
            "end": end_station.name,
            "fare": fare,
            "estimated_time": estimated_time,
            "zones": zone_diff,
            "discount_applied": passenger is not None and passenger.get_discount_rate() > 0
        }
    
    # ========================================================================
    # REAL-TIME INFO (Passenger feature)
    # ========================================================================
    
    def get_next_trains(self, station: Station, limit: int = 3) -> List[Train]:
        """Get next arriving trains at a station"""
        # In real system, this would query actual train locations
        # For now, return trains with simulated ETAs
        available_trains = []
        for train in self.trains.values():
            if train.status == TrainStatus.RUNNING:
                # Simulate ETA
                train.update_location(station, eta_minutes=5)
                available_trains.append(train)
                if len(available_trains) >= limit:
                    break
        return available_trains
    
    def get_station_alerts(self, station: Station) -> List[ServiceAlert]:
        """Get active alerts for a station"""
        return [alert for alert in self.alerts.values() 
                if alert.is_active and station in alert.affected_stations]
    
    # ========================================================================
    # ADMIN OPERATIONS - Station Management
    # ========================================================================
    
    def admin_add_station(self, admin: AdminUser, station_id: str, name: str, 
                         zone: int, lat: float, lon: float) -> Station:
        """Add new station (Admin only)"""
        if not admin.has_permission(UserRole.ADMIN):
            raise PermissionError("Admin access required")
        
        if station_id in self.stations:
            raise ValueError(f"Station {station_id} already exists")
        
        station = Station(station_id, name, zone, lat, lon)
        self.stations[station_id] = station
        
        # Create gates
        entry_gate = Gate(f"G{station_id}E", TapType.ENTRY, station)
        exit_gate = Gate(f"G{station_id}X", TapType.EXIT, station)
        self.gates[entry_gate.gate_id] = entry_gate
        self.gates[exit_gate.gate_id] = exit_gate
        
        return station
    
    def admin_update_station_status(self, admin: AdminUser, station: Station, 
                                    status: StationStatus):
        """Update station status (Admin only)"""
        if not admin.has_permission(UserRole.ADMIN):
            raise PermissionError("Admin access required")
        
        station.status = status
    
    def admin_close_station(self, admin: AdminUser, station: Station,
                            reason: str = "") -> Optional[ServiceAlert]:
        """Close station (Admin only) and optionally create a closure alert."""
        self.admin_update_station_status(admin, station, StationStatus.CLOSED)
        if reason:
            return self.admin_create_alert(
                admin, AlertType.CLOSURE,
                f"{station.name} Station Closed",
                reason, [station])
        return None

    def admin_open_station(self, admin: AdminUser, station: Station):
        """Open station and close any active closure alerts for it."""
        self.admin_update_station_status(admin, station, StationStatus.OPEN)
        for a in self.alerts.values():
            if a.is_active and station in a.affected_stations:
                a.close_alert()
    
    # ========================================================================
    # ADMIN OPERATIONS - Train Management
    # ========================================================================
    
    def admin_add_train(self, admin: AdminUser, train_id: str, line: str, 
                       capacity: int = 200) -> Train:
        """Add new train (Admin only)"""
        if not admin.has_permission(UserRole.ADMIN):
            raise PermissionError("Admin access required")
        
        if train_id in self.trains:
            raise ValueError(f"Train {train_id} already exists")
        
        train = Train(train_id, line, capacity)
        self.trains[train_id] = train
        return train
    
    def admin_update_train_status(self, admin: AdminUser, train: Train, 
                                  status: TrainStatus):
        """Update train status (Admin only)"""
        if not admin.has_permission(UserRole.ADMIN):
            raise PermissionError("Admin access required")
        
        train.update_status(status)
    
    def admin_update_train_location(self, admin: AdminUser, train: Train, 
                                   current_station: Station, 
                                   next_station: Optional[Station] = None,
                                   eta_minutes: Optional[int] = None):
        """Update train location (Admin only)"""
        if not admin.has_permission(UserRole.ADMIN):
            raise PermissionError("Admin access required")
        
        train.update_location(current_station, next_station, eta_minutes)
    
    # ========================================================================
    # ADMIN OPERATIONS - Service Alerts
    # ========================================================================
    
    def admin_create_alert(self, admin: AdminUser, alert_type: AlertType, 
                          title: str, message: str, 
                          affected_stations: List[Station]) -> ServiceAlert:
        """Create service alert (Admin only)"""
        if not admin.has_permission(UserRole.ADMIN):
            raise PermissionError("Admin access required")
        
        alert_id = f"AL{len(self.alerts)+1:04d}"
        alert = ServiceAlert(alert_id, alert_type, title, message, affected_stations)
        alert.created_by = admin
        
        self.alerts[alert_id] = alert
        
        # Add alert to affected stations
        for station in affected_stations:
            station.alerts.append(alert)
        
        return alert
    
    def admin_close_alert(self, admin: AdminUser, alert: ServiceAlert):
        """Close service alert (Admin only)"""
        if not admin.has_permission(UserRole.ADMIN):
            raise PermissionError("Admin access required")
        
        alert.close_alert()
    
    def admin_update_train_status_with_alert(
            self, admin: AdminUser, train: "Train",
            status: TrainStatus, reason: str = "") -> Optional[ServiceAlert]:
        """Update train status and, for DELAYED, auto-create a service alert."""
        if not admin.has_permission(UserRole.ADMIN):
            raise PermissionError("Admin access required")
        train.update_status(status)
        alert = None
        if status == TrainStatus.DELAYED and reason:
            affected = [s for s in self.stations.values() if s.is_operational()][:5]
            alert = self.admin_create_alert(
                admin, AlertType.DELAY,
                f"Train {train.train_id} Delayed — {train.line}",
                reason, affected)
        return alert

    def admin_get_all_alerts(self, admin: AdminUser) -> List[ServiceAlert]:
        """Get all alerts (Admin only)"""
        if not admin.has_permission(UserRole.ADMIN):
            raise PermissionError("Admin access required")
        
        return list(self.alerts.values())
    
    # ========================================================================
    # ADMIN OPERATIONS - Fare Management (Super Admin only)
    # ========================================================================
    
    def admin_update_base_fare(self, super_admin: SuperAdmin, new_fare: float):
        """Update base fare (Super Admin only)"""
        if not super_admin.has_permission(UserRole.SUPER_ADMIN):
            raise PermissionError("Super Admin access required")
        
        FareCalculator.BASE_FARE = new_fare
    
    def admin_update_zone_rate(self, super_admin: SuperAdmin, new_rate: float):
        """Update zone rate (Super Admin only)"""
        if not super_admin.has_permission(UserRole.SUPER_ADMIN):
            raise PermissionError("Super Admin access required")
        
        FareCalculator.ZONE_RATE = new_rate
    
    # ========================================================================
    # ADMIN OPERATIONS - Monitoring & Reports
    # ========================================================================
    
    def admin_get_ridership_stats(self, admin: AdminUser, 
                                  start_date: Optional[datetime] = None,
                                  end_date: Optional[datetime] = None) -> dict:
        """Get ridership statistics (Admin only)"""
        if not admin.has_permission(UserRole.ADMIN):
            raise PermissionError("Admin access required")
        
        trips = list(self.trips.values())
        
        # Filter by date if provided
        if start_date:
            trips = [t for t in trips if t.start_time >= start_date]
        if end_date:
            trips = [t for t in trips if t.start_time <= end_date]
        
        total_trips = len(trips)
        closed_trips = [t for t in trips if t.status == TripStatus.CLOSED]
        total_revenue = sum(t.fare for t in closed_trips if t.fare)
        
        # Busiest stations
        station_counts = {}
        for trip in closed_trips:
            station_counts[trip.entry_station.name] = station_counts.get(trip.entry_station.name, 0) + 1
            if trip.exit_station:
                station_counts[trip.exit_station.name] = station_counts.get(trip.exit_station.name, 0) + 1
        
        busiest_stations = sorted(station_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            "total_trips": total_trips,
            "closed_trips": len(closed_trips),
            "active_trips": total_trips - len(closed_trips),
            "total_revenue": total_revenue,
            "busiest_stations": busiest_stations,
            "average_fare": total_revenue / len(closed_trips) if closed_trips else 0
        }
    
    # ========================================================================
    # QUERY METHODS
    # ========================================================================
    
    def get_station(self, station_id: str) -> Optional[Station]:
        """Get station by ID"""
        return self.stations.get(station_id)
    
    def get_all_stations(self) -> List[Station]:
        """Get all stations"""
        return sorted(self.stations.values(), key=lambda s: (s.zone, s.name))
    
    def get_stations_by_zone(self, zone: int) -> List[Station]:
        """Get stations in a specific zone"""
        return [s for s in self.stations.values() if s.zone == zone]
    
    def get_train(self, train_id: str) -> Optional[Train]:
        """Get train by ID"""
        return self.trains.get(train_id)
    
    def get_all_trains(self) -> List[Train]:
        """Get all trains"""
        return list(self.trains.values())
    
    def get_card(self, card_id: str) -> Optional[Card]:
        """Get card by ID"""
        return self.cards.get(card_id)
    
    def get_all_trips(self) -> List[Trip]:
        """Get all trips"""
        return sorted(self.trips.values(), key=lambda t: t.start_time, reverse=True)
    
    def get_system_stats(self) -> dict:
        """Get system statistics"""
        total_trips = len(self.trips)
        active_trips = len(self.active_trips)
        closed_trips = sum(1 for t in self.trips.values() if t.status == TripStatus.CLOSED)
        total_revenue = sum(t.fare for t in self.trips.values() if t.fare)
        
        return {
            "total_stations": len(self.stations),
            "total_trains": len(self.trains),
            "total_cards": len(self.cards),
            "total_users": len(self.auth_service.users),
            "total_trips": total_trips,
            "active_trips": active_trips,
            "closed_trips": closed_trips,
            "total_revenue": total_revenue,
            "active_alerts": sum(1 for a in self.alerts.values() if a.is_active)
        }


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("ENHANCED STEP 2: Testing BART System with Authentication & Admin")
    print("=" * 70)
    
    bart = BARTSystem()
    
    # Test Authentication
    print("\n1. Testing Authentication...")
    success, user, msg = bart.login("alice", "password123")
    alice: Optional[Passenger] = None
    if success and isinstance(user, Passenger):
        print(f"   ✓ Login successful: {user}")
        alice = user
    
    assert alice is not None, "Alice login failed"
    
    # Test Card Creation for Passenger
    print("\n2. Testing Card Creation for Passenger...")
    card = bart.create_card_for_passenger(alice, 100.00)
    print(f"   ✓ Card created: {card}")
    
    # Test Trip Planning
    print("\n3. Testing Trip Planning...")
    embarcadero = bart.get_station("S001")
    millbrae = bart.get_station("S015")
    assert embarcadero is not None, "Embarcadero station not found"
    assert millbrae is not None, "Millbrae station not found"
    plan = bart.plan_trip(embarcadero, millbrae, alice)
    print(f"   ✓ Trip plan: {plan['start']} → {plan['end']}")
    print(f"   ✓ Fare: ${plan['fare']:.2f} (Student discount applied)")
    print(f"   ✓ Estimated time: {plan['estimated_time']} minutes")
    
    # Test Trip Execution
    print("\n4. Testing Trip Execution...")
    trip = bart.tap_entry(card, embarcadero)
    print(f"   ✓ Tapped in: {trip.trip_id}")
    trip, fare = bart.tap_exit(card, millbrae)
    print(f"   ✓ Tapped out: Fare ${fare:.2f}, Balance ${card.balance:.2f}")
    
    # Test Admin Login
    print("\n5. Testing Admin Operations...")
    success, admin_user, msg = bart.login("admin", "admin123")
    admin: Optional[Admin] = None
    if success and isinstance(admin_user, Admin):
        print(f"   ✓ Admin login: {admin_user}")
        admin = admin_user
    
    assert admin is not None, "Admin login failed"
    
    # Test Station Management
    print("\n6. Testing Station Management...")
    powell = bart.get_station("S003")
    assert powell is not None, "Powell station not found"
    bart.admin_close_station(admin, powell)
    print(f"   ✓ Closed station: {powell.name} - {powell.status.value}")
    bart.admin_open_station(admin, powell)
    print(f"   ✓ Reopened station: {powell.name} - {powell.status.value}")
    
    # Test Service Alert
    print("\n7. Testing Service Alert Creation...")
    alert = bart.admin_create_alert(
        admin, AlertType.DELAY, "Red Line Delays",
        "Delays of 10-15 minutes on Red Line", [embarcadero, powell]
    )
    print(f"   ✓ Alert created: {alert}")
    
    # Test Train Management
    print("\n8. Testing Train Management...")
    train = bart.get_train("T001")
    assert train is not None, "Train T001 not found"
    bart.admin_update_train_location(admin, train, embarcadero, millbrae, 5)
    print(f"   ✓ Train location updated: {train}")
    
    # Test Admin Reports
    print("\n9. Testing Admin Reports...")
    stats = bart.admin_get_ridership_stats(admin)
    print(f"   ✓ Total trips: {stats['total_trips']}")
    print(f"   ✓ Total revenue: ${stats['total_revenue']:.2f}")
    print(f"   ✓ Busiest stations: {stats['busiest_stations'][:3]}")
    
    # Test Permission System
    print("\n10. Testing Permission System...")
    try:
        # Passenger trying admin operation (intentionally wrong type)
        bart.admin_close_station(alice, powell)  # type: ignore[arg-type]
        print("   ✗ Should have raised PermissionError!")
    except PermissionError as e:
        print(f"   ✓ Permission denied (expected): {e}")
    
    # System Stats
    print("\n11. System Statistics...")
    stats = bart.get_system_stats()
    print(f"   ✓ Total users: {stats['total_users']}")
    print(f"   ✓ Total stations: {stats['total_stations']}")
    print(f"   ✓ Total trains: {stats['total_trains']}")
    print(f"   ✓ Active alerts: {stats['active_alerts']}")
    
    print("\n" + "=" * 70)
    print("✓ All Enhanced Step 2 tests passed!")
    print("=" * 70)