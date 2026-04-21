"""
Basic test cases for the BART Transportation System
"""

import unittest
from backend.models import (
    Passenger, Admin, SuperAdmin, Station, Train, Card,
    FareCalculator, PassengerType, StationStatus, TrainStatus,
    CardStatus, UserRole, AlertType
)
from backend.bart_system import BARTSystem, AuthenticationService


class TestAuthentication(unittest.TestCase):

    def setUp(self):
        self.auth = AuthenticationService()
        self.auth.register_user("alice", "pass123", "alice@test.com", "passenger", name="Alice")

    def test_register_new_user(self):
        user = self.auth.register_user("bob", "pass456", "bob@test.com", "passenger", name="Bob")
        self.assertEqual(user.username, "bob")

    def test_register_duplicate_username_raises(self):
        with self.assertRaises(ValueError):
            self.auth.register_user("alice", "other", "other@test.com", "passenger", name="Other")

    def test_login_success(self):
        success, user, msg = self.auth.login("alice", "pass123")
        self.assertTrue(success)
        self.assertIsNotNone(user)

    def test_login_wrong_password(self):
        success, user, msg = self.auth.login("alice", "wrongpass")
        self.assertFalse(success)
        self.assertIsNone(user)

    def test_login_unknown_user(self):
        success, user, msg = self.auth.login("nobody", "pass")
        self.assertFalse(success)

    def test_register_invalid_user_type_raises(self):
        with self.assertRaises(ValueError):
            self.auth.register_user("x", "x", "x@x.com", "robot")


class TestUserPermissions(unittest.TestCase):

    def test_passenger_cannot_admin(self):
        p = Passenger("U001", "alice", "pass", "a@b.com", "Alice")
        self.assertFalse(p.has_permission(UserRole.ADMIN))

    def test_admin_can_admin(self):
        a = Admin("U002", "admin", "pass", "a@b.com", "Admin", "Ops")
        self.assertTrue(a.has_permission(UserRole.ADMIN))

    def test_super_admin_can_all(self):
        sa = SuperAdmin("U003", "super", "pass", "s@b.com", "Super")
        self.assertTrue(sa.has_permission(UserRole.SUPER_ADMIN))
        self.assertTrue(sa.has_permission(UserRole.ADMIN))

    def test_password_verification(self):
        p = Passenger("U001", "alice", "mypassword", "a@b.com", "Alice")
        self.assertTrue(p.verify_password("mypassword"))
        self.assertFalse(p.verify_password("wrongpassword"))

    def test_password_update(self):
        p = Passenger("U001", "alice", "oldpass", "a@b.com", "Alice")
        result = p.update_password("oldpass", "newpass")
        self.assertTrue(result)
        self.assertTrue(p.verify_password("newpass"))


class TestStation(unittest.TestCase):

    def setUp(self):
        self.station = Station("S001", "Embarcadero", 1, 37.79, -122.39)

    def test_station_starts_open(self):
        self.assertTrue(self.station.is_operational())

    def test_close_station(self):
        self.station.close()
        self.assertFalse(self.station.is_operational())
        self.assertEqual(self.station.status, StationStatus.CLOSED)

    def test_reopen_station(self):
        self.station.close()
        self.station.open()
        self.assertTrue(self.station.is_operational())


class TestCard(unittest.TestCase):

    def setUp(self):
        self.card = Card("C001", 50.00)

    def test_initial_balance(self):
        self.assertEqual(self.card.balance, 50.00)

    def test_top_up(self):
        self.card.top_up(20.00)
        self.assertEqual(self.card.balance, 70.00)

    def test_top_up_negative_raises(self):
        with self.assertRaises(ValueError):
            self.card.top_up(-10)

    def test_debit(self):
        self.card.debit(10.00)
        self.assertEqual(self.card.balance, 40.00)

    def test_debit_insufficient_raises(self):
        with self.assertRaises(ValueError):
            self.card.debit(100.00)

    def test_freeze_and_unfreeze(self):
        self.card.freeze()
        self.assertFalse(self.card.is_active())
        self.card.unfreeze()
        self.assertTrue(self.card.is_active())

    def test_transaction_recorded(self):
        self.card.top_up(10.00)
        self.assertEqual(len(self.card.transactions), 1)


class TestFareCalculator(unittest.TestCase):

    def setUp(self):
        self.zone1 = Station("S001", "Embarcadero", 1)
        self.zone5 = Station("S015", "Millbrae", 5)
        self.zone1b = Station("S002", "Montgomery", 1)

    def test_same_zone_fare(self):
        fare = FareCalculator.calculate_fare(self.zone1, self.zone1b)
        self.assertEqual(fare, FareCalculator.BASE_FARE)

    def test_cross_zone_fare_higher(self):
        fare = FareCalculator.calculate_fare(self.zone1, self.zone5)
        self.assertGreater(fare, FareCalculator.BASE_FARE)

    def test_student_discount(self):
        student = Passenger("U001", "alice", "pass", "a@b.com", "Alice", PassengerType.STUDENT)
        regular_fare = FareCalculator.calculate_fare(self.zone1, self.zone5)
        student_fare = FareCalculator.calculate_fare(self.zone1, self.zone5, student)
        self.assertLess(student_fare, regular_fare)

    def test_senior_discount(self):
        senior = Passenger("U002", "bob", "pass", "b@b.com", "Bob", PassengerType.SENIOR)
        regular_fare = FareCalculator.calculate_fare(self.zone1, self.zone5)
        senior_fare = FareCalculator.calculate_fare(self.zone1, self.zone5, senior)
        self.assertLess(senior_fare, regular_fare)

    def test_regular_no_discount(self):
        regular = Passenger("U003", "carol", "pass", "c@b.com", "Carol", PassengerType.REGULAR)
        fare_no_passenger = FareCalculator.calculate_fare(self.zone1, self.zone5)
        fare_regular = FareCalculator.calculate_fare(self.zone1, self.zone5, regular)
        self.assertEqual(fare_no_passenger, fare_regular)


class TestBARTSystemTrips(unittest.TestCase):

    def setUp(self):
        self.bart = BARTSystem(_test_mode=True)
        success, user, _ = self.bart.login("alice", "password123")
        self.passenger = user
        self.card = self.bart.create_card_for_passenger(self.passenger, 100.00)
        self.entry = self.bart.get_station("S001")   # Zone 1
        self.exit = self.bart.get_station("S002")    # Zone 1

    def test_tap_entry_creates_active_trip(self):
        trip = self.bart.tap_entry(self.card, self.entry)
        self.assertIsNotNone(trip)
        active = self.bart.get_active_trip(self.card)
        self.assertIsNotNone(active)

    def test_tap_exit_closes_trip(self):
        self.bart.tap_entry(self.card, self.entry)
        trip, fare = self.bart.tap_exit(self.card, self.exit)
        self.assertIsNone(self.bart.get_active_trip(self.card))
        self.assertGreater(fare, 0)

    def test_tap_exit_deducts_balance(self):
        self.bart.tap_entry(self.card, self.entry)
        _, fare = self.bart.tap_exit(self.card, self.exit)
        self.assertAlmostEqual(self.card.balance, 100.00 - fare, places=2)

    def test_double_tap_entry_raises(self):
        self.bart.tap_entry(self.card, self.entry)
        with self.assertRaises(ValueError):
            self.bart.tap_entry(self.card, self.entry)

    def test_tap_exit_without_entry_raises(self):
        with self.assertRaises(ValueError):
            self.bart.tap_exit(self.card, self.exit)

    def test_tap_frozen_card_raises(self):
        self.card.freeze()
        with self.assertRaises(ValueError):
            self.bart.tap_entry(self.card, self.entry)

    def test_tap_closed_station_raises(self):
        self.entry.close()
        with self.assertRaises(ValueError):
            self.bart.tap_entry(self.card, self.entry)

    def test_insufficient_balance_raises(self):
        poor_card = self.bart.create_card_for_passenger(self.passenger, 0.01)
        # Need a new passenger to avoid card conflict
        new_passenger = self.bart.register("testuser2", "pass123", "t2@test.com", "Test Two")
        poor_card2 = self.bart.create_card_for_passenger(new_passenger, 0.01)
        far_exit = self.bart.get_station("S015")  # Zone 5 - expensive
        self.bart.tap_entry(poor_card2, self.entry)
        with self.assertRaises(ValueError):
            self.bart.tap_exit(poor_card2, far_exit)


class TestAdminOperations(unittest.TestCase):

    def setUp(self):
        self.bart = BARTSystem(_test_mode=True)
        _, self.admin, _ = self.bart.login("admin", "admin123")
        _, self.super_admin, _ = self.bart.login("superadmin", "admin123")
        _, self.passenger, _ = self.bart.login("alice", "password123")
        self.station = self.bart.get_station("S001")

    def test_admin_close_station(self):
        self.bart.admin_close_station(self.admin, self.station)
        self.assertEqual(self.station.status, StationStatus.CLOSED)

    def test_admin_open_station(self):
        self.bart.admin_close_station(self.admin, self.station)
        self.bart.admin_open_station(self.admin, self.station)
        self.assertEqual(self.station.status, StationStatus.OPEN)

    def test_admin_add_train(self):
        train = self.bart.admin_add_train(self.admin, "T999", "Purple Line", 150)
        self.assertIsNotNone(self.bart.get_train("T999"))

    def test_admin_create_alert(self):
        alert = self.bart.admin_create_alert(
            self.admin, AlertType.DELAY, "Test Alert", "Test message", [self.station]
        )
        self.assertTrue(alert.is_active)

    def test_admin_close_alert(self):
        alert = self.bart.admin_create_alert(
            self.admin, AlertType.DELAY, "Test", "Msg", [self.station]
        )
        self.bart.admin_close_alert(self.admin, alert)
        self.assertFalse(alert.is_active)

    def test_passenger_cannot_close_station(self):
        with self.assertRaises((PermissionError, AttributeError)):
            self.bart.admin_close_station(self.passenger, self.station)

    def test_super_admin_update_base_fare(self):
        self.bart.admin_update_base_fare(self.super_admin, 3.00)
        self.assertEqual(FareCalculator.BASE_FARE, 3.00)
        FareCalculator.BASE_FARE = 2.50  # reset

    def test_admin_cannot_update_base_fare(self):
        with self.assertRaises(PermissionError):
            self.bart.admin_update_base_fare(self.admin, 3.00)


class TestTripPlanning(unittest.TestCase):

    def setUp(self):
        self.bart = BARTSystem(_test_mode=True)
        _, self.passenger, _ = self.bart.login("alice", "password123")
        self.start = self.bart.get_station("S001")
        self.end = self.bart.get_station("S015")

    def test_plan_trip_returns_dict(self):
        plan = self.bart.plan_trip(self.start, self.end)
        self.assertIn("fare", plan)
        self.assertIn("estimated_time", plan)

    def test_plan_trip_with_discount(self):
        plan_no_discount = self.bart.plan_trip(self.start, self.end)
        plan_with_discount = self.bart.plan_trip(self.start, self.end, self.passenger)
        self.assertLess(plan_with_discount["fare"], plan_no_discount["fare"])
        self.assertTrue(plan_with_discount["discount_applied"])

    def test_plan_same_station_no_zone_diff(self):
        plan = self.bart.plan_trip(self.start, self.start)
        self.assertEqual(plan["zones"], 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
