"""
BART Transportation System - Enhanced Models with Authentication
Step 1: Core Models with User Roles and Authentication
"""

from datetime import datetime
from typing import Optional, List, Union, TYPE_CHECKING
from enum import Enum
import hashlib
import re


# ============================================================================
# ENUMERATIONS
# ============================================================================

class UserRole(Enum):
    """User role enumeration"""
    GUEST = "GUEST"
    PASSENGER = "PASSENGER"
    ADMIN = "ADMIN"
    SUPER_ADMIN = "SUPER_ADMIN"


class PassengerType(Enum):
    """Passenger type for fare calculation"""
    REGULAR = "REGULAR"
    STUDENT = "STUDENT"
    SENIOR = "SENIOR"


class CardStatus(Enum):
    """Card status enumeration"""
    ACTIVE = "ACTIVE"
    FROZEN = "FROZEN"
    EXPIRED = "EXPIRED"


class TapType(Enum):
    """Tap event type enumeration"""
    ENTRY = "ENTRY"
    EXIT = "EXIT"


class TripStatus(Enum):
    """Trip status enumeration"""
    ACTIVE = "ACTIVE"
    CLOSED = "CLOSED"


class TransactionType(Enum):
    """Transaction type enumeration"""
    TOPUP = "TOPUP"
    FARE = "FARE"
    REFUND = "REFUND"


class StationStatus(Enum):
    """Station operational status"""
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    MAINTENANCE = "MAINTENANCE"


class TrainStatus(Enum):
    """Train operational status"""
    RUNNING = "RUNNING"
    DELAYED = "DELAYED"
    OUT_OF_SERVICE = "OUT_OF_SERVICE"


class AlertType(Enum):
    """Service alert type"""
    DELAY = "DELAY"
    CLOSURE = "CLOSURE"
    ROUTE_CHANGE = "ROUTE_CHANGE"
    MAINTENANCE = "MAINTENANCE"


# ============================================================================
# INPUT VALIDATION
# ============================================================================

class InputValidator:
    """Centralised input validation for all user-facing registration fields."""

    _USERNAME = re.compile(r'^[A-Za-z][A-Za-z0-9_]{2,29}$')
    _NAME     = re.compile(r"^[A-Za-z][A-Za-z\s'\-]{1,49}$")

    # General email: starts with alphanumeric, allows letters/digits/._%-+ before @,
    # valid domain with at least 2-char TLD. Blocks ?, !, #, etc.
    _EMAIL = re.compile(
        r'^[a-zA-Z0-9][a-zA-Z0-9._%+\-]*@[a-zA-Z0-9][a-zA-Z0-9.\-]*\.[a-zA-Z]{2,}$'
    )
    # Gmail local part (before + or @): 6-30 chars, only a-z / 0-9 / dot,
    # must start and end with alphanumeric, no consecutive dots.
    _GMAIL_LOCAL = re.compile(r'^[a-z0-9](?:[a-z0-9.]{4,28})[a-z0-9]$')
    _GMAIL_DOMAINS = {'gmail.com', 'googlemail.com'}

    @classmethod
    def validate_username(cls, username: str) -> str:
        """3-30 chars, starts with letter, alphanumeric + underscore only."""
        if not username:
            raise ValueError("Username is required.")
        if not cls._USERNAME.match(username):
            raise ValueError(
                "Username must be 3–30 characters, start with a letter, "
                "and contain only letters, numbers, or underscores (no spaces)."
            )
        return username

    @classmethod
    def validate_password(cls, password: str) -> str:
        """Minimum 6 characters."""
        if not password:
            raise ValueError("Password is required.")
        if len(password) < 6:
            raise ValueError("Password must be at least 6 characters.")
        return password

    @classmethod
    def validate_email(cls, email: str) -> str:
        """Validate email with stricter rules for Gmail addresses."""
        email = (email or "").strip().lower()
        if not email:
            raise ValueError("Email is required.")

        # General format check (blocks ?, !, # and other invalid chars)
        if not cls._EMAIL.match(email):
            raise ValueError(
                "Enter a valid email address (e.g. user@example.com). "
                "Only letters, numbers, and . _ % + - are allowed before the @."
            )

        local, domain = email.split('@', 1)

        # Gmail-specific rules
        if domain in cls._GMAIL_DOMAINS:
            base = local.split('+')[0]  # strip optional +tag
            if '..' in base:
                raise ValueError(
                    "Gmail addresses cannot contain consecutive dots.")
            if base.startswith('.') or base.endswith('.'):
                raise ValueError(
                    "Gmail addresses cannot start or end with a dot.")
            # Only a-z, 0-9, dot allowed in Gmail usernames
            if not re.match(r'^[a-z0-9.]+$', base):
                raise ValueError(
                    "Gmail usernames can only contain letters (a–z), "
                    "numbers (0–9), and dots. Special characters are not allowed."
                )
            if len(base) < 6:
                raise ValueError(
                    "Gmail usernames must be at least 6 characters long.")
            if len(base) > 30:
                raise ValueError(
                    "Gmail usernames must be 30 characters or fewer.")

        return email

    @classmethod
    def validate_name(cls, name: str) -> str:
        """2-50 chars, letters/spaces/hyphens/apostrophes, starts with letter."""
        name = (name or "").strip()
        if not name:
            raise ValueError("Full name is required.")
        if len(name) < 2:
            raise ValueError("Name must be at least 2 characters.")
        if len(name) > 50:
            raise ValueError("Name must be 50 characters or fewer.")
        if not cls._NAME.match(name):
            raise ValueError(
                "Name must start with a letter and contain only "
                "letters, spaces, hyphens, or apostrophes."
            )
        return name


# ============================================================================
# USER AUTHENTICATION & MANAGEMENT
# ============================================================================

class User:
    """
    Base user class with authentication
    
    Attributes:
        user_id (str): Unique user identifier
        username (str): Login username
        password_hash (str): Hashed password
        email (str): User email
        role (UserRole): User role
        created_at (datetime): Account creation timestamp
        last_login (Optional[datetime]): Last login timestamp
    """
    
    def __init__(self, user_id: str, username: str, password: str, email: str, role: UserRole):
        self.user_id = user_id
        self.username = username
        self.password_hash = self._hash_password(password)
        self.email = email
        self.role = role
        self.created_at = datetime.now()
        self.last_login: Optional[datetime] = None
    
    @staticmethod
    def _hash_password(password: str) -> str:
        """Hash password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def verify_password(self, password: str) -> bool:
        """Verify password against stored hash"""
        return self.password_hash == self._hash_password(password)
    
    def update_password(self, old_password: str, new_password: str) -> bool:
        """Update password if old password is correct"""
        if self.verify_password(old_password):
            self.password_hash = self._hash_password(new_password)
            return True
        return False
    
    def login(self):
        """Record login timestamp"""
        self.last_login = datetime.now()
    
    def has_permission(self, required_role: UserRole) -> bool:
        """Check if user has required permission level"""
        role_hierarchy = {
            UserRole.GUEST: 0,
            UserRole.PASSENGER: 1,
            UserRole.ADMIN: 2,
            UserRole.SUPER_ADMIN: 3
        }
        return role_hierarchy[self.role] >= role_hierarchy[required_role]
    
    def __str__(self):
        return f"User {self.username} ({self.role.value})"


class Passenger(User):
    """
    Passenger user with profile and travel capabilities
    
    Attributes:
        name (str): Full name
        passenger_type (PassengerType): Regular/Student/Senior
        phone (Optional[str]): Phone number
        card (Optional[Card]): Linked Clipper card
    """
    
    def __init__(self, user_id: str, username: str, password: str, email: str, 
                 name: str, passenger_type: PassengerType = PassengerType.REGULAR):
        super().__init__(user_id, username, password, email, UserRole.PASSENGER)
        self.name = name
        self.passenger_type = passenger_type
        self.phone: Optional[str] = None
        self.card: Optional['Card'] = None
    
    def link_card(self, card: 'Card'):
        """Link a Clipper card to this passenger"""
        self.card = card
    
    def get_discount_rate(self) -> float:
        """Get fare discount rate based on passenger type"""
        discount_rates = {
            PassengerType.REGULAR: 0.0,
            PassengerType.STUDENT: 0.25,  # 25% discount
            PassengerType.SENIOR: 0.375   # 37.5% discount
        }
        return discount_rates[self.passenger_type]
    
    def __str__(self):
        return f"Passenger {self.name} ({self.passenger_type.value})"


class Admin(User):
    """
    Admin user with system management capabilities
    
    Attributes:
        name (str): Full name
        department (str): Admin department
    """
    
    def __init__(self, user_id: str, username: str, password: str, email: str, 
                 name: str, department: str = "Operations"):
        super().__init__(user_id, username, password, email, UserRole.ADMIN)
        self.name = name
        self.department = department
    
    def __str__(self):
        return f"Admin {self.name} ({self.department})"


class SuperAdmin(User):
    """
    Super Admin with full system control
    
    Attributes:
        name (str): Full name
    """
    
    def __init__(self, user_id: str, username: str, password: str, email: str, name: str):
        super().__init__(user_id, username, password, email, UserRole.SUPER_ADMIN)
        self.name = name
    
    def __str__(self):
        return f"Super Admin {self.name}"


# ============================================================================
# STATION & INFRASTRUCTURE
# ============================================================================

class Station:
    """
    Represents a BART station
    
    Attributes:
        station_id (str): Unique identifier
        name (str): Station name
        zone (int): Zone number (1-5)
        status (StationStatus): Operational status
        latitude (float): GPS latitude
        longitude (float): GPS longitude
        platforms (int): Number of platforms
    """
    
    def __init__(self, station_id: str, name: str, zone: int, 
                 latitude: float = 0.0, longitude: float = 0.0):
        self.station_id = station_id
        self.name = name
        self.zone = zone
        self.status = StationStatus.OPEN
        self.latitude = latitude
        self.longitude = longitude
        self.platforms = 2  # Default 2 platforms
        self.alerts: List['ServiceAlert'] = []
    
    def is_operational(self) -> bool:
        """Check if station is open for service"""
        return self.status == StationStatus.OPEN
    
    def close(self):
        """Close station"""
        self.status = StationStatus.CLOSED
    
    def open(self):
        """Open station"""
        self.status = StationStatus.OPEN
    
    def __str__(self):
        return f"{self.name} (Zone {self.zone}) - {self.status.value}"


class Train:
    """
    Represents a BART train
    
    Attributes:
        train_id (str): Unique train identifier
        line (str): Line name (e.g., "Red Line", "Blue Line")
        capacity (int): Maximum passenger capacity
        status (TrainStatus): Operational status
        current_station (Optional[Station]): Current location
    """
    
    def __init__(self, train_id: str, line: str, capacity: int = 200):
        self.train_id = train_id
        self.line = line
        self.capacity = capacity
        self.status = TrainStatus.RUNNING
        self.current_station: Optional[Station] = None
        self.next_station: Optional[Station] = None
        self.eta_minutes: Optional[int] = None
    
    def update_status(self, status: TrainStatus):
        """Update train operational status"""
        self.status = status
    
    def update_location(self, current_station: Optional[Station] = None, next_station: Optional[Station] = None, 
                       eta_minutes: Optional[int] = None):
        """Update train location and ETA"""
        self.current_station = current_station
        self.next_station = next_station
        self.eta_minutes = eta_minutes
    
    def __str__(self):
        location = f" at {self.current_station.name}" if self.current_station else ""
        return f"Train {self.train_id} ({self.line}){location} - {self.status.value}"


# ============================================================================
# CARD & TRANSACTIONS
# ============================================================================

class Card:
    """
    Clipper card with balance and transaction management
    
    Attributes:
        card_id (str): Unique card identifier
        balance (float): Current balance
        status (CardStatus): Card status
        transactions (List[Transaction]): Transaction history
        owner (Optional[Passenger]): Card owner
    """
    
    def __init__(self, card_id: str, initial_balance: float = 0.0):
        self.card_id = card_id
        self.balance = initial_balance
        self.status = CardStatus.ACTIVE
        self.transactions: List['Transaction'] = []
        self.owner: Optional[Passenger] = None
    
    def top_up(self, amount: float) -> bool:
        """Add money to the card"""
        if amount <= 0:
            raise ValueError("Top-up amount must be positive")
        
        self.balance += amount
        transaction = Transaction(
            txn_id=f"TX{len(self.transactions)+1:04d}",
            amount=amount,
            time=datetime.now(),
            txn_type=TransactionType.TOPUP
        )
        self.transactions.append(transaction)
        return True
    
    def debit(self, amount: float) -> bool:
        """Deduct money from the card"""
        if amount <= 0:
            raise ValueError("Debit amount must be positive")
        
        if self.balance < amount:
            raise ValueError(f"Insufficient balance. Required: ${amount:.2f}, Available: ${self.balance:.2f}")
        
        self.balance -= amount
        transaction = Transaction(
            txn_id=f"TX{len(self.transactions)+1:04d}",
            amount=-amount,
            time=datetime.now(),
            txn_type=TransactionType.FARE
        )
        self.transactions.append(transaction)
        return True
    
    def refund(self, amount: float, reason: str = ""):
        """Refund money to card"""
        self.balance += amount
        transaction = Transaction(
            txn_id=f"TX{len(self.transactions)+1:04d}",
            amount=amount,
            time=datetime.now(),
            txn_type=TransactionType.REFUND
        )
        self.transactions.append(transaction)
    
    def freeze(self):
        """Freeze the card"""
        self.status = CardStatus.FROZEN
    
    def unfreeze(self):
        """Unfreeze the card"""
        self.status = CardStatus.ACTIVE
    
    def is_active(self) -> bool:
        """Check if card is active"""
        return self.status == CardStatus.ACTIVE
    
    def __str__(self):
        owner_info = f" - Owner: {self.owner.name}" if self.owner else ""
        return f"Card {self.card_id}: ${self.balance:.2f} ({self.status.value}){owner_info}"


class Transaction:
    """
    Represents a financial transaction
    
    Attributes:
        txn_id (str): Unique transaction identifier
        amount (float): Transaction amount
        time (datetime): Transaction timestamp
        type (TransactionType): Transaction type
    """
    
    def __init__(self, txn_id: str, amount: float, time: datetime, txn_type: TransactionType):
        self.txn_id = txn_id
        self.amount = amount
        self.time = time
        self.type = txn_type
    
    def __str__(self):
        sign = "+" if self.amount > 0 else ""
        return f"{self.type.value}: {sign}${self.amount:.2f} at {self.time.strftime('%Y-%m-%d %H:%M')}"


# ============================================================================
# TRIP MANAGEMENT
# ============================================================================

class TapEvent:
    """Represents a tap event at a gate"""
    
    def __init__(self, tap_id: str, time: datetime, tap_type: TapType):
        self.tap_id = tap_id
        self.time = time
        self.type = tap_type
    
    def __str__(self):
        return f"{self.type.value} at {self.time.strftime('%H:%M:%S')}"


class Trip:
    """
    Represents a journey from entry to exit
    
    Attributes:
        trip_id (str): Unique trip identifier
        passenger (Optional[Passenger]): Passenger who took the trip
        card (Card): Card used for the trip
        start_time (datetime): Trip start time
        end_time (Optional[datetime]): Trip end time
        status (TripStatus): Trip status
        entry_station (Station): Entry station
        exit_station (Optional[Station]): Exit station
        fare (Optional[float]): Trip fare
    """
    
    def __init__(self, trip_id: str, card: Card, start_time: datetime, entry_station: Station):
        self.trip_id = trip_id
        self.passenger = card.owner
        self.card = card
        self.start_time = start_time
        self.end_time: Optional[datetime] = None
        self.status = TripStatus.ACTIVE
        self.entry_station = entry_station
        self.exit_station: Optional[Station] = None
        self.entry_tap: Optional[TapEvent] = None
        self.exit_tap: Optional[TapEvent] = None
        self.fare: Optional[float] = None
    
    def close_trip(self, exit_station: Station, exit_time: datetime, fare: float):
        """Close the trip with exit details"""
        self.exit_station = exit_station
        self.end_time = exit_time
        self.fare = fare
        self.status = TripStatus.CLOSED
    
    def get_duration(self) -> Optional[float]:
        """Get trip duration in minutes"""
        if self.end_time:
            delta = self.end_time - self.start_time
            return delta.total_seconds() / 60
        return None
    
    def __str__(self):
        passenger_name = self.passenger.name if self.passenger else "Guest"
        if self.status == TripStatus.ACTIVE:
            return f"Trip {self.trip_id} ({passenger_name}): {self.entry_station.name} → (In Progress)"
        else:
            duration = self.get_duration()
            exit_name = self.exit_station.name if self.exit_station else "Unknown"
            return f"Trip {self.trip_id} ({passenger_name}): {self.entry_station.name} → {exit_name} (${self.fare:.2f}, {duration:.0f}min)"


class Gate:
    """Represents an entry or exit gate at a station"""
    
    def __init__(self, gate_id: str, gate_type: TapType, station: Station):
        self.gate_id = gate_id
        self.type = gate_type
        self.station = station
    
    def create_tap_event(self) -> TapEvent:
        """Create a tap event when card is tapped"""
        tap_id = f"T{datetime.now().timestamp():.0f}"
        return TapEvent(tap_id, datetime.now(), self.type)
    
    def __str__(self):
        return f"Gate {self.gate_id} ({self.type.value}) at {self.station.name}"


# ============================================================================
# FARE CALCULATOR WITH DISCOUNTS
# ============================================================================

class FareCalculator:
    """
    Handles fare calculation with passenger type discounts
    """
    
    BASE_FARE = 2.50
    ZONE_RATE = 0.75
    
    @staticmethod
    def calculate_fare(entry_station: Station, exit_station: Station, 
                      passenger: Optional[Passenger] = None) -> float:
        """
        Calculate fare based on zones and passenger type
        
        Args:
            entry_station: Station where trip started
            exit_station: Station where trip ended
            passenger: Passenger (for discount calculation)
            
        Returns:
            Calculated fare amount
        """
        zone_diff = abs(entry_station.zone - exit_station.zone)
        base_fare = FareCalculator.BASE_FARE + (zone_diff * FareCalculator.ZONE_RATE)
        
        # Apply discount if passenger provided
        if passenger:
            discount = passenger.get_discount_rate()
            base_fare = base_fare * (1 - discount)
        
        return round(base_fare, 2)


# ============================================================================
# SERVICE ALERTS
# ============================================================================

class ServiceAlert:
    """
    Service alert for delays, closures, etc.
    
    Attributes:
        alert_id (str): Unique alert identifier
        alert_type (AlertType): Type of alert
        title (str): Alert title
        message (str): Detailed message
        affected_stations (List[Station]): Affected stations
        start_time (datetime): Alert start time
        end_time (Optional[datetime]): Alert end time
        created_by (Optional[Admin]): Admin who created the alert
    """
    
    def __init__(self, alert_id: str, alert_type: AlertType, title: str, 
                 message: str, affected_stations: List[Station]):
        self.alert_id = alert_id
        self.alert_type = alert_type
        self.title = title
        self.message = message
        self.affected_stations = affected_stations
        self.start_time = datetime.now()
        self.end_time: Optional[datetime] = None
        self.created_by: Optional[Union["Admin", "SuperAdmin"]] = None
        self.is_active = True
    
    def close_alert(self):
        """Close/resolve the alert"""
        self.end_time = datetime.now()
        self.is_active = False
    
    def __str__(self):
        stations = ", ".join([s.name for s in self.affected_stations[:3]])
        if len(self.affected_stations) > 3:
            stations += "..."
        return f"Alert {self.alert_id} ({self.alert_type.value}): {self.title} - Affects: {stations}"


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("ENHANCED STEP 1: Testing Models with Authentication & Roles")
    print("=" * 70)
    
    # Test User Authentication
    print("\n1. Testing User Authentication...")
    passenger = Passenger("U001", "alice", "password123", "alice@example.com", 
                         "Alice Johnson", PassengerType.STUDENT)
    print(f"   ✓ Created: {passenger}")
    print(f"   ✓ Role: {passenger.role.value}")
    print(f"   ✓ Discount rate: {passenger.get_discount_rate() * 100}%")
    
    # Test password verification
    print("\n2. Testing Password Verification...")
    if passenger.verify_password("password123"):
        print("   ✓ Password verified successfully")
    
    # Test Admin
    print("\n3. Testing Admin User...")
    admin = Admin("A001", "admin", "admin123", "admin@bart.gov", 
                  "John Admin", "Operations")
    print(f"   ✓ Created: {admin}")
    print(f"   ✓ Has admin permission: {admin.has_permission(UserRole.ADMIN)}")
    
    # Test Station with status
    print("\n4. Testing Station Management...")
    station = Station("S001", "Embarcadero", 1, 37.7929, -122.3972)
    print(f"   ✓ Created: {station}")
    station.close()
    print(f"   ✓ Closed station: {station.status.value}")
    station.open()
    print(f"   ✓ Reopened station: {station.status.value}")
    
    # Test Train
    print("\n5. Testing Train Management...")
    train = Train("T001", "Red Line", 200)
    print(f"   ✓ Created: {train}")
    train.update_location(station, eta_minutes=2)
    assert train.current_station is not None
    print(f"   ✓ Train location: {train.current_station.name}, ETA: {train.eta_minutes}min")
    
    # Test Card with Owner
    print("\n6. Testing Card with Owner...")
    card = Card("C001", 50.00)
    card.owner = passenger
    passenger.link_card(card)
    print(f"   ✓ Created: {card}")
    
    # Test Fare Calculation with Discount
    print("\n7. Testing Fare Calculation with Student Discount...")
    station2 = Station("S015", "Millbrae", 5)
    fare_regular = FareCalculator.calculate_fare(station, station2)
    fare_student = FareCalculator.calculate_fare(station, station2, passenger)
    print(f"   ✓ Regular fare: ${fare_regular:.2f}")
    print(f"   ✓ Student fare: ${fare_student:.2f}")
    print(f"   ✓ Savings: ${fare_regular - fare_student:.2f}")
    
    # Test Service Alert
    print("\n8. Testing Service Alert...")
    alert = ServiceAlert("AL001", AlertType.DELAY, "Train Delay", 
                        "Delays expected due to signal issues", [station])
    alert.created_by = admin
    print(f"   ✓ Created: {alert}")
    
    # Test Permission System
    print("\n9. Testing Permission System...")
    guest = User("G001", "guest", "guest123", "guest@example.com", UserRole.GUEST)
    print(f"   ✓ Guest can be passenger: {guest.has_permission(UserRole.PASSENGER)}")
    print(f"   ✓ Passenger can be admin: {passenger.has_permission(UserRole.ADMIN)}")
    print(f"   ✓ Admin can be admin: {admin.has_permission(UserRole.ADMIN)}")
    
    print("\n" + "=" * 70)
    print("✓ All Enhanced Step 1 tests passed!")
    print("=" * 70)