import os
from flask import Flask, render_template, request, session, redirect, url_for, jsonify

from backend.bart_system import BARTSystem
from backend.models import (
    PassengerType, StationStatus, TrainStatus, AlertType, UserRole, FareCalculator
)

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'bart-system-dev-key-change-in-prod')

bart = BARTSystem()


def get_user():
    username = session.get('username')
    if not username:
        return None
    return bart.get_current_user(username)


def require_role(*roles):
    user = get_user()
    if not user or user.role not in roles:
        return None
    return user


# ─── Auth ────────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    user = get_user()
    if not user:
        return redirect(url_for('login'))
    role_map = {
        UserRole.PASSENGER: 'passenger',
        UserRole.ADMIN: 'admin',
        UserRole.SUPER_ADMIN: 'superadmin',
    }
    return redirect(url_for(role_map.get(user.role, 'login')))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        success, user, message = bart.login(username, password)
        if success:
            session['username'] = username
            return redirect(url_for('index'))
        return render_template('login.html', error=message)
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = request.form
        type_map = {
            'regular': PassengerType.REGULAR,
            'student': PassengerType.STUDENT,
            'senior': PassengerType.SENIOR,
        }
        ptype = type_map.get(data.get('passenger_type', 'regular'), PassengerType.REGULAR)
        try:
            bart.register(
                data.get('username', '').strip(),
                data.get('password', ''),
                data.get('email', '').strip(),
                data.get('name', '').strip(),
                ptype,
            )
            session['username'] = data.get('username', '').strip()
            return redirect(url_for('passenger'))
        except Exception as e:
            return render_template('register.html', error=str(e))
    return render_template('register.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


# ─── Passenger ───────────────────────────────────────────────────────────────

@app.route('/passenger')
def passenger():
    user = require_role(UserRole.PASSENGER)
    if not user:
        return redirect(url_for('login'))
    card = bart.get_passenger_card(user)
    active_trip = bart.get_active_trip(card) if card else None
    transactions = bart.get_card_transactions(card)[:15] if card else []
    trips = bart.get_passenger_trips(user)[:15]
    stations = bart.get_all_stations()
    return render_template('passenger.html',
        user=user, card=card, active_trip=active_trip,
        transactions=transactions, trips=trips,
        stations=stations, service_active=bart.is_service_hours(),
    )


@app.route('/api/card/create', methods=['POST'])
def api_card_create():
    user = require_role(UserRole.PASSENGER)
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    if bart.get_passenger_card(user):
        return jsonify({'error': 'Card already exists'}), 400
    try:
        card = bart.create_card_for_passenger(user, 0.0)
        return jsonify({'success': True, 'card_id': card.card_id, 'balance': card.balance})
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/api/card/topup', methods=['POST'])
def api_card_topup():
    user = require_role(UserRole.PASSENGER)
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    card = bart.get_passenger_card(user)
    if not card:
        return jsonify({'error': 'No card found'}), 400
    try:
        amount = float(request.json.get('amount', 0))
        if amount <= 0:
            return jsonify({'error': 'Amount must be positive'}), 400
        bart.top_up_card(card, amount)
        return jsonify({'success': True, 'balance': card.balance})
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/api/trip/entry', methods=['POST'])
def api_trip_entry():
    user = require_role(UserRole.PASSENGER)
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    card = bart.get_passenger_card(user)
    if not card:
        return jsonify({'error': 'No card found'}), 400
    station_id = request.json.get('station_id')
    station = bart.get_station(station_id)
    if not station:
        return jsonify({'error': 'Station not found'}), 400
    try:
        trip = bart.tap_entry(card, station)
        return jsonify({'success': True, 'trip_id': trip.trip_id, 'station': station.name})
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/api/trip/exit', methods=['POST'])
def api_trip_exit():
    user = require_role(UserRole.PASSENGER)
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    card = bart.get_passenger_card(user)
    if not card:
        return jsonify({'error': 'No card found'}), 400
    station_id = request.json.get('station_id')
    station = bart.get_station(station_id)
    if not station:
        return jsonify({'error': 'Station not found'}), 400
    try:
        trip, fare = bart.tap_exit(card, station)
        return jsonify({'success': True, 'fare': fare, 'balance': card.balance,
                        'from': trip.entry_station.name, 'to': station.name})
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/api/trip/plan', methods=['POST'])
def api_trip_plan():
    user = get_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.json
    start = bart.get_station(data.get('start_station_id'))
    end = bart.get_station(data.get('end_station_id'))
    if not start or not end:
        return jsonify({'error': 'Invalid stations'}), 400
    passenger = user if user.role == UserRole.PASSENGER else None
    try:
        result = bart.plan_trip(start, end, passenger)
        return jsonify({'success': True, 'result': {
            'start': result['start'].name,
            'end': result['end'].name,
            'fare': result['fare'],
            'estimated_time': result['estimated_time'],
            'zones': result['zones'],
            'discount_applied': result.get('discount_applied', False),
        }})
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/api/stations')
def api_stations():
    return jsonify([{
        'station_id': s.station_id,
        'name': s.name,
        'zone': s.zone,
        'status': s.status.value,
    } for s in bart.get_all_stations()])


@app.route('/api/trains/next')
def api_trains_next():
    station_id = request.args.get('station_id')
    station = bart.get_station(station_id)
    if not station:
        return jsonify({'error': 'Station not found'}), 400
    trains = bart.get_next_trains(station, 5)
    return jsonify([{
        'train_id': t.train_id,
        'line': t.line,
        'status': t.status.value,
        'eta_minutes': t.eta_minutes,
    } for t in trains])


# ─── Admin ───────────────────────────────────────────────────────────────────

@app.route('/admin')
def admin():
    user = require_role(UserRole.ADMIN, UserRole.SUPER_ADMIN)
    if not user:
        return redirect(url_for('login'))
    stations = bart.get_all_stations()
    trains = bart.get_all_trains()
    try:
        alerts = bart.admin_get_all_alerts(user)
        stats = bart.admin_get_ridership_stats(user)
    except Exception:
        alerts = []
        stats = {'total_trips': 0, 'active_trips': 0, 'closed_trips': 0,
                 'total_revenue': 0.0, 'average_fare': 0.0, 'busiest_stations': []}
    return render_template('admin.html',
        user=user, stations=stations, trains=trains,
        alerts=alerts, stats=stats,
    )


@app.route('/api/admin/station/status', methods=['POST'])
def api_admin_station_status():
    user = require_role(UserRole.ADMIN, UserRole.SUPER_ADMIN)
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.json
    station = bart.get_station(data.get('station_id'))
    if not station:
        return jsonify({'error': 'Station not found'}), 400
    status_map = {
        'open': StationStatus.OPEN,
        'closed': StationStatus.CLOSED,
        'maintenance': StationStatus.MAINTENANCE,
    }
    status = status_map.get(data.get('status', '').lower())
    if not status:
        return jsonify({'error': 'Invalid status'}), 400
    try:
        if status == StationStatus.CLOSED:
            bart.admin_close_station(user, station, data.get('reason', ''))
        elif status == StationStatus.OPEN:
            bart.admin_open_station(user, station)
        else:
            bart.admin_update_station_status(user, station, status)
        return jsonify({'success': True, 'status': station.status.value})
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/api/admin/train/status', methods=['POST'])
def api_admin_train_status():
    user = require_role(UserRole.ADMIN, UserRole.SUPER_ADMIN)
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.json
    train = bart.get_train(data.get('train_id'))
    if not train:
        return jsonify({'error': 'Train not found'}), 400
    status_map = {
        'running': TrainStatus.RUNNING,
        'delayed': TrainStatus.DELAYED,
        'out_of_service': TrainStatus.OUT_OF_SERVICE,
    }
    status = status_map.get(data.get('status', '').lower())
    if not status:
        return jsonify({'error': 'Invalid status'}), 400
    try:
        bart.admin_update_train_status_with_alert(user, train, status, data.get('reason', ''))
        return jsonify({'success': True, 'status': train.status.value})
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/api/admin/alert/create', methods=['POST'])
def api_admin_alert_create():
    user = require_role(UserRole.ADMIN, UserRole.SUPER_ADMIN)
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.json
    type_map = {
        'delay': AlertType.DELAY,
        'closure': AlertType.CLOSURE,
        'route_change': AlertType.ROUTE_CHANGE,
        'maintenance': AlertType.MAINTENANCE,
    }
    alert_type = type_map.get(data.get('alert_type', '').lower())
    if not alert_type:
        return jsonify({'error': 'Invalid alert type'}), 400
    station_ids = data.get('station_ids', [])
    stations = [s for sid in station_ids if (s := bart.get_station(sid))]
    try:
        alert = bart.admin_create_alert(user, alert_type, data.get('title', ''), data.get('message', ''), stations)
        return jsonify({'success': True, 'alert_id': alert.alert_id})
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/api/admin/alert/close', methods=['POST'])
def api_admin_alert_close():
    user = require_role(UserRole.ADMIN, UserRole.SUPER_ADMIN)
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.json
    try:
        alerts = bart.admin_get_all_alerts(user)
    except Exception:
        return jsonify({'error': 'Could not fetch alerts'}), 500
    alert = next((a for a in alerts if a.alert_id == data.get('alert_id')), None)
    if not alert:
        return jsonify({'error': 'Alert not found'}), 400
    try:
        bart.admin_close_alert(user, alert)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 400


# ─── Super Admin ──────────────────────────────────────────────────────────────

@app.route('/superadmin')
def superadmin():
    user = require_role(UserRole.SUPER_ADMIN)
    if not user:
        return redirect(url_for('login'))
    stats = bart.get_system_stats()
    stations = bart.get_all_stations()
    trains = bart.get_all_trains()
    try:
        alerts = bart.admin_get_all_alerts(user)
        ridership = bart.admin_get_ridership_stats(user)
    except Exception:
        alerts = []
        ridership = {'total_trips': 0, 'total_revenue': 0.0, 'average_fare': 0.0}
    return render_template('superadmin.html',
        user=user, stats=stats, fare_calculator=FareCalculator,
        stations=stations, trains=trains, alerts=alerts, ridership=ridership,
    )


@app.route('/api/superadmin/fare/base', methods=['POST'])
def api_fare_base():
    user = require_role(UserRole.SUPER_ADMIN)
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    try:
        fare = float(request.json.get('base_fare', 0))
        bart.admin_update_base_fare(user, fare)
        return jsonify({'success': True, 'base_fare': FareCalculator.BASE_FARE})
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/api/superadmin/fare/zone', methods=['POST'])
def api_fare_zone():
    user = require_role(UserRole.SUPER_ADMIN)
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    try:
        rate = float(request.json.get('zone_rate', 0))
        bart.admin_update_zone_rate(user, rate)
        return jsonify({'success': True, 'zone_rate': FareCalculator.ZONE_RATE})
    except Exception as e:
        return jsonify({'error': str(e)}), 400


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
