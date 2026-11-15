"""
app.py - AIAC (AI-Assisted Smart Hostel and Residential Management Platform)
Main Flask Application with Student & Warden portals, authentication,
database operations, PDF generation, and AI assistance.
"""

import os
import uuid
import datetime
from functools import wraps
from flask import (
    Flask, render_template, request, redirect, url_for, flash,
    session, jsonify, send_file, abort
)
from werkzeug.security import generate_password_hash, check_password_hash

import database
import ai_engine
import pdf_generator

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'aiac-secret-key-development-2026')
app.config['PERMANENT_SESSION_LIFETIME'] = datetime.timedelta(days=7)
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Initialize database schema on startup
database.init_db()


# ==========================================
# AUTHENTICATION & ROLE-BASED ACCESS HELPERS
# ==========================================

def get_current_user():
    """Fetch current user record from database if logged in."""
    user_id = session.get('user_id')
    if not user_id:
        return None
    conn = database.get_db()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    return user


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login', next=request.path))
        return f(*args, **kwargs)
    return decorated_function


def student_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to continue.', 'warning')
            return redirect(url_for('login'))
        if session.get('role') != 'student':
            flash('Access restricted to registered students.', 'danger')
            return redirect(url_for('warden_dashboard'))
        return f(*args, **kwargs)
    return decorated_function


def warden_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Warden login required to access this portal.', 'warning')
            return redirect(url_for('login'))
        if session.get('role') not in ('warden', 'admin'):
            flash('Unauthorized access. Only authorized wardens may access this page.', 'danger')
            return redirect(url_for('student_dashboard'))
        return f(*args, **kwargs)
    return decorated_function


@app.context_processor
def inject_global_data():
    """Make common data available across all templates."""
    user = get_current_user()
    unread_count = 0
    if user:
        conn = database.get_db()
        if user['role'] == 'warden':
            # Wardens see notifications targeted to them or general
            row = conn.execute(
                'SELECT COUNT(*) as count FROM notifications WHERE (user_id = ? OR user_id = 0 OR user_id IS NULL) AND is_read = 0',
                (user['id'],)
            ).fetchone()
        else:
            row = conn.execute(
                'SELECT COUNT(*) as count FROM notifications WHERE user_id = ? AND is_read = 0',
                (user['id'],)
            ).fetchone()
        conn.close()
        unread_count = row['count'] if row else 0

    return {
        'current_user': user,
        'unread_notifications_count': unread_count,
        'current_year': datetime.datetime.now().year,
        'hostel_name': database.get_setting('hostel_name', 'AIAC Smart Residential Platform'),
        'college_email_domain': database.get_setting('college_email_domain', 'college.edu'),
        'emergency_medical': database.get_setting('emergency_phone_medical', '+91 98765 00108'),
        'emergency_security': database.get_setting('emergency_phone_security', '+91 98765 00100')
    }


# ==========================================
# PUBLIC ROUTES & AUTHENTICATION
# ==========================================

@app.route('/')
def index():
    """Landing route: display welcome portal for unauthenticated guests, or redirect to dashboard."""
    if 'user_id' in session:
        if session.get('role') == 'warden':
            return redirect(url_for('warden_dashboard'))
        return redirect(url_for('student_dashboard'))
    return render_template('welcome.html')


@app.route('/warden/login', methods=['GET', 'POST'])
def warden_login():
    """Dedicated Warden Administration Desk login."""
    if 'user_id' in session:
        if session.get('role') == 'warden':
            return redirect(url_for('warden_dashboard'))
        flash('You are currently logged in as a student. Please log out first to access the Warden portal.', 'warning')
        return redirect(url_for('student_dashboard'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        if not email or not password:
            flash('Please enter your authorized warden email and password.', 'danger')
            return render_template('warden_login.html', email=email)

        conn = database.get_db()
        user = conn.execute('SELECT * FROM users WHERE LOWER(email) = ?', (email,)).fetchone()
        conn.close()

        if not user or not check_password_hash(user['password_hash'], password):
            flash('Invalid warden credentials. Access restricted to authorized personnel.', 'danger')
            return render_template('warden_login.html', email=email)

        if user['role'] not in ('warden', 'admin'):
            flash('Access restricted: This portal is for authorized hostel wardens and administrators only. Please use the Student Portal to log in.', 'danger')
            return render_template('warden_login.html', email=email)

        if user['status'] != 'active':
            flash('Your account has been deactivated. Please contact the Chief Administrator.', 'danger')
            return render_template('warden_login.html', email=email)

        session.clear()
        session['user_id'] = user['id']
        session['role'] = user['role']
        session['name'] = user['name']
        session['email'] = user['email']
        session.permanent = True

        flash(f'Welcome back, Warden {user["name"]}!', 'success')
        return redirect(url_for('warden_dashboard'))

    return render_template('warden_login.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Student Portal login (accepts College Email or Student ID)."""
    if 'user_id' in session:
        if session.get('role') == 'warden':
            return redirect(url_for('warden_dashboard'))
        return redirect(url_for('student_dashboard'))

    if request.method == 'POST':
        identifier = request.form.get('identifier', request.form.get('email', '')).strip()
        password = request.form.get('password', '')

        if not identifier or not password:
            flash('Please enter your college email or Student ID, and your password.', 'danger')
            return render_template('login.html', identifier=identifier)

        conn = database.get_db()
        user = conn.execute('''
            SELECT * FROM users
            WHERE LOWER(email) = LOWER(?) OR LOWER(student_id) = LOWER(?)
        ''', (identifier, identifier)).fetchone()
        conn.close()

        if not user or not check_password_hash(user['password_hash'], password):
            flash('Invalid email or password. Please verify your credentials.', 'danger')
            return render_template('login.html', identifier=identifier)

        if user['status'] != 'active':
            flash('Your account has been deactivated. Please contact the Chief Warden.', 'danger')
            return render_template('login.html', identifier=identifier)

        # Successful authentication
        session.clear()
        session['user_id'] = user['id']
        session['role'] = user['role']
        session['name'] = user['name']
        session['email'] = user['email']
        session.permanent = True

        flash(f'Welcome back, {user["name"]}!', 'success')
        if user['role'] == 'warden':
            return redirect(url_for('warden_dashboard'))
        return redirect(url_for('student_dashboard'))

    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    """Student registration with room allocation & validation against configurable college domain."""
    if 'user_id' in session:
        return redirect(url_for('index'))

    conn = database.get_db()
    blocks = conn.execute('SELECT * FROM hostel_blocks ORDER BY name').fetchall()
    rooms_rows = conn.execute('''
        SELECT b.name as block_name, r.room_number, r.capacity, r.occupancy
        FROM rooms r
        JOIN hostel_blocks b ON r.block_id = b.id
        ORDER BY b.name, r.room_number
    ''').fetchall()
    conn.close()

    rooms_by_block = {}
    for r in rooms_rows:
        rooms_by_block.setdefault(r['block_name'], []).append(r['room_number'])

    configured_domain = database.get_setting('college_email_domain', 'college.edu').strip().lower()

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        hostel_block = request.form.get('hostel_block', '').strip()
        room_number = request.form.get('room_number', '').strip()
        academic_year = request.form.get('academic_year', '').strip()
        room_type = request.form.get('room_type', '').strip() or 'Double Sharing Standard'
        phone = request.form.get('phone', '').strip()
        student_id_val = request.form.get('student_id', '').strip() or None
        department_val = request.form.get('department', '').strip() or None

        # Validations
        errors = []
        if not name or len(name) < 2:
            errors.append('Please provide your full legal name.')

        if not email:
            errors.append('College email address is required.')
        elif configured_domain and configured_domain != '*':
            if not email.endswith(f'@{configured_domain}'):
                errors.append(f'Email must be an official college email ending with @{configured_domain}.')

        if len(password) < 8:
            errors.append('Password must be at least 8 characters long.')
        elif not any(c.isalpha() for c in password) or not any(c.isdigit() or not c.isalnum() for c in password):
            errors.append('Password must contain at least one letter and one number or symbol.')

        if password != confirm_password:
            errors.append('Password and confirmation password do not match.')

        if not hostel_block:
            errors.append('Please select your assigned or preferred hostel block.')

        if not academic_year:
            errors.append('Please specify your academic year.')

        if errors:
            for err in errors:
                flash(err, 'danger')
            return render_template('register.html', blocks=blocks, rooms_by_block=rooms_by_block,
                                   name=name, email=email, hostel_block=hostel_block,
                                   academic_year=academic_year, phone=phone,
                                   student_id=student_id_val, department=department_val,
                                   room_number=room_number, room_type=room_type)

        conn = database.get_db()
        existing_email = conn.execute('SELECT id FROM users WHERE LOWER(email) = ?', (email,)).fetchone()
        if existing_email:
            conn.close()
            flash('An account with this college email already exists. Please log in or reset your password.', 'danger')
            return render_template('register.html', blocks=blocks, rooms_by_block=rooms_by_block,
                                   name=name, email=email, hostel_block=hostel_block,
                                   academic_year=academic_year, phone=phone,
                                   student_id=student_id_val, department=department_val,
                                   room_number=room_number, room_type=room_type)

        if student_id_val:
            existing_id = conn.execute('SELECT id FROM users WHERE LOWER(student_id) = ?', (student_id_val.lower(),)).fetchone()
            if existing_id:
                conn.close()
                flash(f'Student ID / Roll Number "{student_id_val}" is already registered. Please use your existing account.', 'danger')
                return render_template('register.html', blocks=blocks, rooms_by_block=rooms_by_block,
                                       name=name, email=email, hostel_block=hostel_block,
                                       academic_year=academic_year, phone=phone,
                                       student_id=student_id_val, department=department_val,
                                       room_number=room_number, room_type=room_type)

        allocated_room = None
        if room_number:
            allocated_room = conn.execute('''
                SELECT r.*, b.name as block_name
                FROM rooms r
                JOIN hostel_blocks b ON r.block_id = b.id
                WHERE b.name = ? AND LOWER(r.room_number) = LOWER(?)
            ''', (hostel_block, room_number)).fetchone()

            if not allocated_room:
                valid_rooms = [r['room_number'] for r in conn.execute('''
                    SELECT r.room_number FROM rooms r
                    JOIN hostel_blocks b ON r.block_id = b.id
                    WHERE b.name = ? ORDER BY r.room_number
                ''', (hostel_block,)).fetchall()]
                conn.close()
                room_list_str = ', '.join(valid_rooms[:8]) if valid_rooms else 'None'
                flash(f'Room "{room_number}" does not exist in {hostel_block}. Available rooms include: {room_list_str}...', 'danger')
                return render_template('register.html', blocks=blocks, rooms_by_block=rooms_by_block,
                                       name=name, email=email, hostel_block=hostel_block,
                                       academic_year=academic_year, phone=phone,
                                       student_id=student_id_val, department=department_val,
                                       room_number=room_number, room_type=room_type)

            if allocated_room['occupancy'] >= allocated_room['capacity']:
                conn.close()
                flash(f'Room {allocated_room["room_number"]} in {hostel_block} is already at full capacity ({allocated_room["occupancy"]}/{allocated_room["capacity"]}). Please select another room.', 'danger')
                return render_template('register.html', blocks=blocks, rooms_by_block=rooms_by_block,
                                       name=name, email=email, hostel_block=hostel_block,
                                       academic_year=academic_year, phone=phone,
                                       student_id=student_id_val, department=department_val,
                                       room_number=room_number, room_type=room_type)

        # Hash password and insert student record
        pw_hash = generate_password_hash(password)
        cursor = conn.cursor()
        room_id_to_save = allocated_room['id'] if allocated_room else None
        room_num_to_save = allocated_room['room_number'] if allocated_room else (room_number or None)
        room_type_to_save = room_type or (allocated_room['room_type'] if allocated_room else None)

        cursor.execute('''
            INSERT INTO users (name, email, password_hash, role, hostel_block, room_id, room_number, room_type, academic_year, phone, student_id, department, status)
            VALUES (?, ?, ?, 'student', ?, ?, ?, ?, ?, ?, ?, ?, 'active')
        ''', (name, email, pw_hash, hostel_block, room_id_to_save, room_num_to_save, room_type_to_save, academic_year, phone, student_id_val, department_val))
        new_user_id = cursor.lastrowid

        # Update room occupancy and record allocation if room was assigned
        if allocated_room:
            cursor.execute('UPDATE rooms SET occupancy = occupancy + 1 WHERE id = ?', (allocated_room['id'],))
            cursor.execute('''
                INSERT INTO room_allocations (room_id, user_id, allocated_date, status)
                VALUES (?, ?, CURRENT_DATE, 'active')
            ''', (allocated_room['id'], new_user_id))

        # Initialize student default fee records (Hostel Fee & Dhobi Fee)
        default_hostel_fee = float(database.get_setting('default_hostel_fee', '45000'))
        default_dhobi_fee = float(database.get_setting('default_dhobi_fee', '1200'))
        today = datetime.date.today()
        due_hostel = (today + datetime.timedelta(days=30)).isoformat()
        due_dhobi = (today + datetime.timedelta(days=15)).isoformat()

        cursor.execute('''
            INSERT INTO hostel_fee_records (user_id, academic_term, total_amount, amount_paid, due_date, status, notes)
            VALUES (?, 'Academic Term 2026-27', ?, 0.0, ?, 'Pending', 'Standard semester accommodation charges')
        ''', (new_user_id, default_hostel_fee, due_hostel))

        cursor.execute('''
            INSERT INTO dhobi_fee_records (user_id, month_year, total_amount, amount_paid, due_date, status, notes)
            VALUES (?, 'October 2026', ?, 0.0, ?, 'Pending', 'Monthly unlimited laundry service charges')
        ''', (new_user_id, default_dhobi_fee, due_dhobi))

        # Welcome notification
        cursor.execute('''
            INSERT INTO notifications (user_id, title, message, link, type)
            VALUES (?, 'Welcome to AIAC!', 'Your student registration was successful. Explore your dashboard to view rooms, outpasses, mess menus, and emergency features.', '/dashboard', 'system')
        ''', (new_user_id,))

        # Notify wardens of new student registration
        cursor.execute("SELECT id FROM users WHERE role = 'warden'")
        wardens = cursor.fetchall()
        for w in wardens:
            cursor.execute('''
                INSERT INTO notifications (user_id, title, message, link, type)
                VALUES (?, 'New Student Registered', ?, '/warden/students', 'system')
            ''', (w['id'], f'{name} ({email}) registered in {hostel_block}' + (f', Room {room_num_to_save}' if room_num_to_save else '')))

        conn.commit()
        conn.close()

        if room_num_to_save:
            flash(f'Registration successful! Room {room_num_to_save} has been allocated. Please sign in to continue.', 'success')
        else:
            flash('Registration successful! You may now log in with your college credentials.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html', blocks=blocks, rooms_by_block=rooms_by_block)


@app.route('/logout')
def logout():
    """Clear session and redirect to welcome portal."""
    session.clear()
    flash('You have been safely logged out.', 'info')
    return redirect(url_for('index'))


@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Safe password-reset workflow."""
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')

        if not email or not new_password:
            flash('Please enter your registered email and a new password.', 'danger')
            return render_template('forgot_password.html')

        if len(new_password) < 8:
            flash('Password must be at least 8 characters.', 'danger')
            return render_template('forgot_password.html')

        if new_password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('forgot_password.html')

        conn = database.get_db()
        user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        if not user:
            conn.close()
            # Security practice: avoid user enumeration while giving safe response
            flash('If an account exists with this email, your password has been reset. Please log in.', 'info')
            return redirect(url_for('login'))

        # Update password
        new_hash = generate_password_hash(new_password)
        conn.execute('UPDATE users SET password_hash = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?', (new_hash, user['id']))

        # Add notification
        conn.execute('''
            INSERT INTO notifications (user_id, title, message, link, type)
            VALUES (?, 'Password Reset Successful', 'Your account password was updated. If you did not initiate this change, contact the warden immediately.', '/profile', 'system')
        ''', (user['id'],))

        conn.commit()
        conn.close()

        flash('Your password has been successfully reset. Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('forgot_password.html')


# ==========================================
# STUDENT PORTAL & DASHBOARD
# ==========================================

@app.route('/dashboard')
@login_required
def student_dashboard():
    """Student personalized dashboard with summary metrics, room info, leaves, complaints, fees."""
    if session.get('role') == 'warden':
        return redirect(url_for('warden_dashboard'))

    user_id = session['user_id']
    conn = database.get_db()

    # User profile with room allocation
    student = conn.execute('''
        SELECT u.*, 
               COALESCE(r.room_number, u.room_number) as room_number,
               COALESCE(r.room_type, u.room_type) as room_type,
               r.floor, r.capacity,
               COALESCE(b.name, u.hostel_block) as block_name
        FROM users u
        LEFT JOIN rooms r ON u.room_id = r.id
        LEFT JOIN hostel_blocks b ON r.block_id = b.id
        WHERE u.id = ?
    ''', (user_id,)).fetchone()

    # Pending leave requests
    pending_leaves = conn.execute('''
        SELECT * FROM leave_requests WHERE user_id = ? AND status = 'Pending' ORDER BY created_at DESC
    ''', (user_id,)).fetchall()

    # Approved outpasses
    approved_outpasses = conn.execute('''
        SELECT o.*, l.reason, l.destination, l.start_datetime, l.return_datetime
        FROM outpasses o
        JOIN leave_requests l ON o.leave_request_id = l.id
        WHERE o.user_id = ?
        ORDER BY o.created_at DESC LIMIT 5
    ''', (user_id,)).fetchall()

    # Unresolved complaints
    active_complaints = conn.execute('''
        SELECT * FROM complaints WHERE user_id = ? AND status NOT IN ('Resolved', 'Rejected') ORDER BY created_at DESC
    ''', (user_id,)).fetchall()

    # Upcoming laundry requests
    active_laundry = conn.execute('''
        SELECT lr.*, ls.collection_date, ls.collection_time_start
        FROM laundry_requests lr
        LEFT JOIN laundry_schedules ls ON lr.schedule_id = ls.id
        WHERE lr.user_id = ? AND lr.status NOT IN ('Delivered', 'Cancelled')
        ORDER BY lr.created_at DESC
    ''', (user_id,)).fetchall()

    # Fee summary
    hostel_fee = conn.execute('''
        SELECT * FROM hostel_fee_records WHERE user_id = ? ORDER BY id DESC LIMIT 1
    ''', (user_id,)).fetchone()

    dhobi_fee = conn.execute('''
        SELECT * FROM dhobi_fee_records WHERE user_id = ? ORDER BY id DESC LIMIT 1
    ''', (user_id,)).fetchone()

    # Recent notifications
    notifications = conn.execute('''
        SELECT * FROM notifications WHERE user_id = ? ORDER BY created_at DESC LIMIT 5
    ''', (user_id,)).fetchall()

    # Active announcements
    announcements = conn.execute('''
        SELECT * FROM announcements WHERE is_active = 1 ORDER BY created_at DESC LIMIT 3
    ''', ()).fetchall()

    conn.close()

    return render_template(
        'student_dashboard.html',
        student=student,
        pending_leaves=pending_leaves,
        approved_outpasses=approved_outpasses,
        active_complaints=active_complaints,
        active_laundry=active_laundry,
        hostel_fee=hostel_fee,
        dhobi_fee=dhobi_fee,
        notifications=notifications,
        announcements=announcements
    )


@app.route('/profile', methods=['GET', 'POST'])
@login_required
@student_required
def profile():
    """Student profile view and allowed edits (phone, bio/details, password)."""
    user_id = session['user_id']
    conn = database.get_db()

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'update_info':
            phone = request.form.get('phone', '').strip()
            student_id_val = request.form.get('student_id', '').strip()
            department_val = request.form.get('department', '').strip()
            guardian_name_val = request.form.get('guardian_name', '').strip()
            guardian_phone_val = request.form.get('guardian_phone', '').strip()

            conn.execute('''
                UPDATE users 
                SET phone = ?, student_id = ?, department = ?, guardian_name = ?, guardian_phone = ?, updated_at = CURRENT_TIMESTAMP 
                WHERE id = ?
            ''', (phone, student_id_val, department_val, guardian_name_val, guardian_phone_val, user_id))
            conn.commit()
            flash('Profile details updated successfully.', 'success')

        elif action == 'change_password':
            current_pw = request.form.get('current_password', '')
            new_pw = request.form.get('new_password', '')
            confirm_pw = request.form.get('confirm_password', '')

            user = conn.execute('SELECT password_hash FROM users WHERE id = ?', (user_id,)).fetchone()

            if not check_password_hash(user['password_hash'], current_pw):
                flash('Current password is incorrect.', 'danger')
            elif len(new_pw) < 8:
                flash('New password must be at least 8 characters.', 'danger')
            elif new_pw != confirm_pw:
                flash('New passwords do not match.', 'danger')
            else:
                new_hash = generate_password_hash(new_pw)
                conn.execute('UPDATE users SET password_hash = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?', (new_hash, user_id))
                conn.commit()
                flash('Password changed successfully!', 'success')

        return redirect(url_for('profile'))

    student = conn.execute('''
        SELECT u.*, r.room_number, r.floor, r.capacity, b.name as block_name
        FROM users u
        LEFT JOIN rooms r ON u.room_id = r.id
        LEFT JOIN hostel_blocks b ON r.block_id = b.id
        WHERE u.id = ?
    ''', (user_id,)).fetchone()
    conn.close()

    return render_template('profile.html', student=student)


@app.route('/room-details')
@login_required
@student_required
def room_details():
    """View assigned room details, roommates, capacity, or unallocated state."""
    user_id = session['user_id']
    conn = database.get_db()

    student = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()

    room = None
    roommates = []
    allocation_record = None
    if student['room_id']:
        room = conn.execute('''
            SELECT r.*, b.name as block_name, b.description as block_desc
            FROM rooms r
            JOIN hostel_blocks b ON r.block_id = b.id
            WHERE r.id = ?
        ''', (student['room_id'],)).fetchone()

        if room:
            roommates = conn.execute('''
                SELECT id, name, email, academic_year, phone, student_id, department
                FROM users
                WHERE room_id = ? AND id != ? AND role = 'student'
            ''', (student['room_id'], user_id)).fetchall()

            allocation_record = conn.execute('''
                SELECT * FROM room_allocations 
                WHERE room_id = ? AND user_id = ? 
                ORDER BY allocated_date DESC LIMIT 1
            ''', (student['room_id'], user_id)).fetchone()

    # Active outpass / leave for this resident
    active_outpasses = conn.execute('''
        SELECT o.*, l.destination, l.leave_type, l.start_datetime, l.return_datetime
        FROM outpasses o
        JOIN leave_requests l ON o.leave_request_id = l.id
        WHERE o.user_id = ? AND o.status = 'Valid'
        ORDER BY o.created_at DESC LIMIT 3
    ''', (user_id,)).fetchall()

    conn.close()
    return render_template(
        'room_details.html',
        student=student,
        room=room,
        roommates=roommates,
        allocation_record=allocation_record,
        active_outpasses=active_outpasses
    )


# ==========================================
# LEAVE MANAGEMENT & OUTPASS
# ==========================================

@app.route('/leave', methods=['GET', 'POST'])
@login_required
@student_required
def leave_management():
    """Leave requests submission and history."""
    user_id = session['user_id']
    conn = database.get_db()

    if request.method == 'POST':
        leave_type = request.form.get('leave_type', '').strip()
        start_datetime = request.form.get('start_datetime', '').strip()
        return_datetime = request.form.get('return_datetime', '').strip()
        destination = request.form.get('destination', '').strip()
        reason = request.form.get('reason', '').strip()
        emergency_contact = request.form.get('emergency_contact', '').strip()
        parent_phone = request.form.get('parent_phone', '').strip()
        additional_notes = request.form.get('additional_notes', '').strip()

        # Validation
        if not all([leave_type, start_datetime, return_datetime, destination, reason, emergency_contact]):
            flash('Please fill in all mandatory leave details.', 'danger')
        elif return_datetime <= start_datetime:
            flash('Expected return date and time must be after the departure time.', 'danger')
        else:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO leave_requests (user_id, leave_type, start_datetime, return_datetime,
                                           destination, reason, emergency_contact, parent_phone, additional_notes, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'Pending')
            ''', (user_id, leave_type, start_datetime, return_datetime, destination, reason, emergency_contact, parent_phone, additional_notes))
            conn.commit()

            # Notify wardens
            database.notify_all_wardens(
                'New Leave Request Submitted',
                f'{session["name"]} submitted a request for {leave_type} to {destination}.',
                '/warden/leave-requests',
                'leave',
                conn=conn
            )
            conn.commit()

            flash('Leave request submitted successfully! Awaiting warden review.', 'success')
            conn.close()
            return redirect(url_for('leave_management'))

    # Fetch leave history
    leaves = conn.execute('''
        SELECT l.*, o.id as outpass_id, o.outpass_ref as approved_outpass_ref
        FROM leave_requests l
        LEFT JOIN outpasses o ON l.id = o.leave_request_id
        WHERE l.user_id = ?
        ORDER BY l.created_at DESC
    ''', (user_id,)).fetchall()
    conn.close()

    return render_template('leave_management.html', leaves=leaves)


@app.route('/leave/cancel/<int:leave_id>', methods=['POST'])
@login_required
@student_required
def cancel_leave(leave_id):
    """Cancel eligible pending leave request."""
    user_id = session['user_id']
    conn = database.get_db()
    leave = conn.execute('SELECT * FROM leave_requests WHERE id = ? AND user_id = ?', (leave_id, user_id)).fetchone()

    if not leave:
        flash('Leave request not found.', 'danger')
    elif leave['status'] != 'Pending':
        flash('Only Pending leave requests can be cancelled.', 'warning')
    else:
        conn.execute("UPDATE leave_requests SET status = 'Cancelled', updated_at = CURRENT_TIMESTAMP WHERE id = ?", (leave_id,))
        conn.commit()
        flash('Leave request cancelled successfully.', 'info')

    conn.close()
    return redirect(url_for('leave_management'))


@app.route('/leave/outing', methods=['GET', 'POST'])
@login_required
@student_required
def leave_outing():
    """Dedicated One-Day Outing Permit module."""
    user_id = session['user_id']
    conn = database.get_db()
    student = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()

    if request.method == 'POST':
        start_datetime = request.form.get('start_datetime', '').strip()
        return_datetime = request.form.get('return_datetime', '').strip()
        destination = request.form.get('destination', '').strip()
        reason = request.form.get('reason', '').strip()
        emergency_contact = request.form.get('emergency_contact', '').strip()
        parent_phone = request.form.get('parent_phone', '').strip()
        additional_notes = request.form.get('additional_notes', '').strip()

        if not all([start_datetime, return_datetime, destination, reason, emergency_contact]):
            flash('Please fill in all mandatory outing details.', 'danger')
        elif return_datetime <= start_datetime:
            flash('Expected return time must be after the departure time.', 'danger')
        else:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO leave_requests (user_id, leave_type, start_datetime, return_datetime,
                                           destination, reason, emergency_contact, parent_phone, additional_notes, status)
                VALUES (?, 'One-day outing', ?, ?, ?, ?, ?, ?, ?, 'Pending')
            ''', (user_id, start_datetime, return_datetime, destination, reason, emergency_contact, parent_phone, additional_notes))
            conn.commit()

            database.notify_all_wardens(
                'New One-Day Outing Request',
                f'{session["name"]} requested a one-day outing to {destination}.',
                '/warden/leave-requests',
                'leave',
                conn=conn
            )
            conn.commit()
            flash('One-day outing request submitted successfully! Awaiting warden review.', 'success')
            conn.close()
            return redirect(url_for('leave_outing'))

    outings = conn.execute('''
        SELECT l.*, o.id as outpass_id, o.outpass_ref as approved_outpass_ref
        FROM leave_requests l
        LEFT JOIN outpasses o ON l.id = o.leave_request_id
        WHERE l.user_id = ? AND l.leave_type = 'One-day outing'
        ORDER BY l.created_at DESC
    ''', (user_id,)).fetchall()
    conn.close()

    return render_template('one_day_outing.html', student=student, outings=outings)


@app.route('/leave/vacation', methods=['GET', 'POST'])
@login_required
@student_required
def leave_vacation():
    """Dedicated Vacation Request module (strictly validated up to 10 days)."""
    user_id = session['user_id']
    conn = database.get_db()
    student = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()

    if request.method == 'POST':
        start_datetime = request.form.get('start_datetime', '').strip()
        return_datetime = request.form.get('return_datetime', '').strip()
        destination = request.form.get('destination', '').strip()
        reason = request.form.get('reason', '').strip()
        emergency_contact = request.form.get('emergency_contact', '').strip()
        parent_phone = request.form.get('parent_phone', '').strip()
        additional_notes = request.form.get('additional_notes', '').strip()

        if not all([start_datetime, return_datetime, destination, reason, emergency_contact, parent_phone]):
            flash('Please provide all vacation details including mandatory parent phone number.', 'danger')
        elif return_datetime <= start_datetime:
            flash('Expected return date and time must be after the departure time.', 'danger')
        else:
            # Validate max 10 days
            try:
                start_dt = datetime.datetime.fromisoformat(start_datetime)
                return_dt = datetime.datetime.fromisoformat(return_datetime)
                duration = return_dt - start_dt
                if duration.total_seconds() > 10 * 86400:
                    flash('Vacation requests via student portal are limited to a maximum of 10 days. For longer leaves, consult the Chief Warden.', 'danger')
                    conn.close()
                    return redirect(url_for('leave_vacation'))
            except Exception:
                pass

            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO leave_requests (user_id, leave_type, start_datetime, return_datetime,
                                           destination, reason, emergency_contact, parent_phone, additional_notes, status)
                VALUES (?, 'Vacation leave (up to 10 days)', ?, ?, ?, ?, ?, ?, ?, 'Pending')
            ''', (user_id, start_datetime, return_datetime, destination, reason, emergency_contact, parent_phone, additional_notes))
            conn.commit()

            database.notify_all_wardens(
                'New Vacation Request (Up to 10 Days)',
                f'{session["name"]} requested vacation leave to {destination} ({start_datetime[:10]} to {return_datetime[:10]}).',
                '/warden/leave-requests',
                'leave',
                conn=conn
            )
            conn.commit()
            flash('Vacation request submitted successfully! Awaiting warden review.', 'success')
            conn.close()
            return redirect(url_for('leave_vacation'))

    vacations = conn.execute('''
        SELECT l.*, o.id as outpass_id, o.outpass_ref as approved_outpass_ref
        FROM leave_requests l
        LEFT JOIN outpasses o ON l.id = o.leave_request_id
        WHERE l.user_id = ? AND l.leave_type LIKE '%Vacation%'
        ORDER BY l.created_at DESC
    ''', (user_id,)).fetchall()
    conn.close()

    return render_template('vacation_request.html', student=student, vacations=vacations)


@app.route('/outpass-status')
@login_required
@student_required
def outpass_status():
    """Digital Movement Outpass Status module."""
    user_id = session['user_id']
    conn = database.get_db()

    approved_outpasses = conn.execute('''
        SELECT o.*, l.destination, l.leave_type, l.start_datetime, l.return_datetime, l.reason
        FROM outpasses o
        JOIN leave_requests l ON o.leave_request_id = l.id
        WHERE o.user_id = ?
        ORDER BY o.created_at DESC
    ''', (user_id,)).fetchall()

    pending_requests = conn.execute('''
        SELECT * FROM leave_requests 
        WHERE user_id = ? AND status = 'Pending'
        ORDER BY created_at DESC
    ''', (user_id,)).fetchall()

    conn.close()
    return render_template('outpass_status.html',
                           approved_outpasses=approved_outpasses,
                           pending_requests=pending_requests)


@app.route('/holiday-calendar')
@login_required
def holiday_calendar():
    """Academic and hostel holiday calendar for students and wardens."""
    conn = database.get_db()
    holidays = conn.execute('SELECT * FROM holiday_calendar ORDER BY holiday_date ASC').fetchall()
    conn.close()
    return render_template('holiday_calendar.html', holidays=holidays)


@app.route('/warden/holiday/add', methods=['POST'])
@login_required
@warden_required
def warden_add_holiday():
    """Warden publishes an official campus holiday."""
    title = request.form.get('title', '').strip()
    holiday_date = request.form.get('holiday_date', '').strip()
    end_date = request.form.get('end_date', '').strip() or holiday_date
    holiday_type = request.form.get('holiday_type', 'Public Holiday')
    mess_service_status = request.form.get('mess_service_status', 'Open (Standard Hours)').strip()
    description = request.form.get('description', '').strip()

    if not title or not holiday_date:
        flash('Holiday Title and Date are required.', 'danger')
        return redirect(url_for('holiday_calendar'))

    conn = database.get_db()
    conn.execute('''
        INSERT INTO holiday_calendar (title, holiday_date, end_date, holiday_type, description, mess_service_status, is_outing_allowed)
        VALUES (?, ?, ?, ?, ?, ?, 1)
    ''', (title, holiday_date, end_date, holiday_type, description, mess_service_status))
    conn.commit()

    # Announce holiday to all students
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE role = 'student'")
    students = cursor.fetchall()
    for s in students:
        cursor.execute('''
            INSERT INTO notifications (user_id, title, message, link, type)
            VALUES (?, 'Holiday Notice Published', ?, '/holiday-calendar', 'system')
        ''', (s['id'], f'Official holiday "{title}" scheduled for {holiday_date}. Check calendar.'))

    conn.commit()
    conn.close()

    flash(f'Holiday "{title}" published to the campus calendar!', 'success')
    return redirect(url_for('holiday_calendar'))


@app.route('/outpass/<int:outpass_id>')
@login_required
def view_outpass(outpass_id):
    """View approved outpass. Pending or rejected requests cannot display outpass."""
    user_id = session['user_id']
    role = session.get('role')
    conn = database.get_db()

    query = '''
        SELECT o.*, l.destination, l.reason, l.emergency_contact, l.parent_phone, l.decision_note,
               u.name as student_name, u.email as student_email, u.hostel_block, u.academic_year,
               r.room_number, w.name as warden_full_name
        FROM outpasses o
        JOIN leave_requests l ON o.leave_request_id = l.id
        JOIN users u ON o.user_id = u.id
        LEFT JOIN rooms r ON u.room_id = r.id
        LEFT JOIN users w ON o.warden_id = w.id
        WHERE o.id = ?
    '''
    outpass = conn.execute(query, (outpass_id,)).fetchone()
    conn.close()

    if not outpass:
        abort(404, description='Outpass not found or not approved.')

    # Access control: only the student who owns the outpass or wardens can view it
    if role != 'warden' and outpass['user_id'] != user_id:
        abort(403, description='Unauthorized access to outpass.')

    return render_template('outpass.html', outpass=outpass)


@app.route('/outpass/<int:outpass_id>/pdf')
@login_required
def download_outpass_pdf(outpass_id):
    """Download approved Outpass as binary PDF."""
    user_id = session['user_id']
    role = session.get('role')
    conn = database.get_db()

    outpass = conn.execute('''
        SELECT o.*, l.destination, l.reason, l.emergency_contact, l.decision_note,
               u.name, u.email, u.hostel_block, u.academic_year, r.room_number
        FROM outpasses o
        JOIN leave_requests l ON o.leave_request_id = l.id
        JOIN users u ON o.user_id = u.id
        LEFT JOIN rooms r ON u.room_id = r.id
        WHERE o.id = ?
    ''', (outpass_id,)).fetchone()
    conn.close()

    if not outpass:
        abort(404)

    if role != 'warden' and outpass['user_id'] != user_id:
        abort(403)

    student_data = {
        'name': outpass['name'],
        'email': outpass['email'],
        'hostel_block': outpass['hostel_block'],
        'room_number': outpass['room_number'],
        'academic_year': outpass['academic_year']
    }
    pdf_buffer = pdf_generator.generate_outpass_pdf(dict(outpass), student_data)
    filename = f"AIAC_Outpass_{outpass['outpass_ref']}.pdf"

    return send_file(pdf_buffer, mimetype='application/pdf', as_attachment=True, download_name=filename)


@app.route('/outpass/<int:outpass_id>/print')
@login_required
def print_outpass(outpass_id):
    """Printable web layout for approved outpass."""
    return view_outpass(outpass_id)


# ==========================================
# EMERGENCY SUPPORT MODULE
# ==========================================

@app.route('/emergency', methods=['GET', 'POST'])
@login_required
def emergency_support():
    """Emergency support module for immediate alerts and helpline access."""
    user_id = session['user_id']
    conn = database.get_db()

    if request.method == 'POST':
        category = request.form.get('category', '').strip()
        location_or_room = request.form.get('location_or_room', '').strip()
        priority = request.form.get('priority', 'Critical').strip()
        description = request.form.get('description', '').strip()
        contact_number = request.form.get('contact_number', '').strip()

        if not category or not location_or_room or not description:
            flash('Please provide the emergency category, exact location, and description.', 'danger')
        else:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO emergency_alerts (user_id, category, location_or_room, priority, description, contact_number, status)
                VALUES (?, ?, ?, ?, ?, ?, 'New')
            ''', (user_id, category, location_or_room, priority, description, contact_number))
            alert_id = cursor.lastrowid
            conn.commit()

            # Broadcast alert notification to all wardens
            database.notify_all_wardens(
                f'🚨 EMERGENCY ALERT: {category} ({priority})',
                f'Urgent alert at {location_or_room} by {session["name"]}. Check dashboard immediately!',
                '/warden/emergencies',
                'emergency',
                conn=conn
            )
            conn.commit()

            # Confirm to student with explicit safety notice
            flash('Emergency Alert successfully logged and dispatched to the Warden Control Desk! Our residential team has been notified.', 'danger')
            conn.close()
            return redirect(url_for('emergency_support'))

    # Retrieve user's emergency alerts
    user_alerts = conn.execute('''
        SELECT * FROM emergency_alerts WHERE user_id = ? ORDER BY created_at DESC
    ''', (user_id,)).fetchall()

    # Emergency contacts
    contacts = {
        'medical': database.get_setting('emergency_phone_medical', '+91 98765 00108'),
        'security': database.get_setting('emergency_phone_security', '+91 98765 00100'),
        'warden': database.get_setting('emergency_phone_warden', '+91 98765 00101'),
        'electrician': database.get_setting('emergency_phone_electrician', '+91 98765 00102')
    }

    conn.close()
    return render_template('emergency.html', alerts=user_alerts, contacts=contacts)


# ==========================================
# COMPLAINT MANAGEMENT MODULE
# ==========================================

@app.route('/complaints', methods=['GET', 'POST'])
@login_required
@student_required
def complaints():
    """Complaints submission with AI auto-categorization & priority suggestion, and tracking."""
    user_id = session['user_id']
    conn = database.get_db()

    if request.method == 'POST':
        category = request.form.get('category', '').strip()
        subject = request.form.get('subject', '').strip()
        description = request.form.get('description', '').strip()
        location_or_room = request.form.get('location_or_room', '').strip()
        priority = request.form.get('priority', 'Medium').strip()

        if not subject or not description or not location_or_room:
            flash('Please complete all mandatory complaint fields.', 'danger')
        else:
            # Run AI analysis for smart insights & categorization
            ai_res = ai_engine.analyze_complaint(subject, description)
            final_cat = category or ai_res['suggested_category']
            final_prio = priority or ai_res['suggested_priority']

            complaint_code = f"CMP-{datetime.datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:4].upper()}"

            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO complaints (complaint_code, user_id, category, subject, description,
                                       location_or_room, priority, ai_suggested_priority,
                                       ai_suggested_category, ai_confidence, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Submitted')
            ''', (complaint_code, user_id, final_cat, subject, description,
                  location_or_room, final_prio, ai_res['suggested_priority'],
                  ai_res['suggested_category'], ai_res['confidence']))
            conn.commit()

            # Notify wardens
            database.notify_all_wardens(
                f'New Complaint: {complaint_code}',
                f'{session["name"]} reported a {final_cat} issue ({final_prio} priority) at {location_or_room}.',
                '/warden/complaints',
                'complaint',
                conn=conn
            )
            conn.commit()

            flash(f'Complaint {complaint_code} submitted successfully! AI identified this as {final_cat} ({final_prio}).', 'success')
            conn.close()
            return redirect(url_for('complaints'))

    # Fetch student's complaints with latest responses
    user_complaints = conn.execute('''
        SELECT * FROM complaints WHERE user_id = ? ORDER BY created_at DESC
    ''', (user_id,)).fetchall()

    # Fetch responses dictionary
    complaint_ids = [c['id'] for c in user_complaints]
    responses_map = {}
    if complaint_ids:
        placeholders = ','.join('?' for _ in complaint_ids)
        res_rows = conn.execute(f'''
            SELECT cr.*, u.name as responder_name
            FROM complaint_responses cr
            JOIN users u ON cr.user_id = u.id
            WHERE cr.complaint_id IN ({placeholders})
            ORDER BY cr.created_at ASC
        ''', complaint_ids).fetchall()
        for r in res_rows:
            responses_map.setdefault(r['complaint_id'], []).append(r)

    conn.close()
    return render_template('complaints.html', complaints=user_complaints, responses_map=responses_map)


@app.route('/complaints/<int:complaint_id>/reply', methods=['POST'])
@login_required
def reply_complaint(complaint_id):
    """Add a response message to a complaint thread."""
    user_id = session['user_id']
    role = session.get('role')
    message = request.form.get('message', '').strip()

    if not message:
        flash('Reply message cannot be empty.', 'danger')
        return redirect(request.referrer or url_for('complaints'))

    conn = database.get_db()
    complaint = conn.execute('SELECT * FROM complaints WHERE id = ?', (complaint_id,)).fetchone()

    if not complaint:
        abort(404)

    # Permission check: student owner or warden
    if role != 'warden' and complaint['user_id'] != user_id:
        abort(403)

    is_warden = 1 if role == 'warden' else 0
    conn.execute('''
        INSERT INTO complaint_responses (complaint_id, user_id, message, is_warden)
        VALUES (?, ?, ?, ?)
    ''', (complaint_id, user_id, message, is_warden))

    conn.commit()

    # Send notification to student or warden
    if role == 'warden':
        database.add_notification(
            complaint['user_id'],
            f'Response to Complaint {complaint["complaint_code"]}',
            f'The hostel management has responded to your complaint: "{message[:60]}..."',
            '/complaints',
            'complaint',
            conn=conn
        )
    else:
        database.notify_all_wardens(
            f'Student Reply on {complaint["complaint_code"]}',
            f'{session["name"]} added a comment to their complaint.',
            '/warden/complaints',
            'complaint',
            conn=conn
        )

    conn.commit()
    conn.close()
    flash('Response recorded.', 'success')
    return redirect(request.referrer or url_for('complaints'))


# ==========================================
# WEEKLY MESS MENU
# ==========================================

@app.route('/mess-menu')
@login_required
def mess_menu():
    """Weekly mess menu with highlighted Sunday special lunch & Wednesday special dinner."""
    conn = database.get_db()
    menu_items = conn.execute('''
        SELECT * FROM mess_menus ORDER BY
        CASE day_of_week
            WHEN 'Monday' THEN 1
            WHEN 'Tuesday' THEN 2
            WHEN 'Wednesday' THEN 3
            WHEN 'Thursday' THEN 4
            WHEN 'Friday' THEN 5
            WHEN 'Saturday' THEN 6
            WHEN 'Sunday' THEN 7
        END,
        CASE meal_type
            WHEN 'Breakfast' THEN 1
            WHEN 'Lunch' THEN 2
            WHEN 'Evening Snacks' THEN 3
            WHEN 'Dinner' THEN 4
        END
    ''').fetchall()
    conn.close()

    # Structure menu by day and meal
    structured_menu = {
        'Monday': {}, 'Tuesday': {}, 'Wednesday': {}, 'Thursday': {},
        'Friday': {}, 'Saturday': {}, 'Sunday': {}
    }
    for item in menu_items:
        day = item['day_of_week']
        meal = item['meal_type']
        if day in structured_menu:
            structured_menu[day][meal] = item

    current_day = datetime.datetime.now().strftime('%A')

    return render_template('mess_menu.html', menu=structured_menu, current_day=current_day)


# ==========================================
# HOSTEL & DHOBI FEE MANAGEMENT
# ==========================================

@app.route('/hostel-fees')
@login_required
@student_required
def hostel_fees():
    """Hostel accommodation fee status, payment history, and receipt downloads."""
    user_id = session['user_id']
    conn = database.get_db()

    fee_records = conn.execute('''
        SELECT * FROM hostel_fee_records WHERE user_id = ? ORDER BY id DESC
    ''', (user_id,)).fetchall()

    payments = conn.execute('''
        SELECT * FROM payment_transactions WHERE user_id = ? AND fee_type = 'hostel' ORDER BY created_at DESC
    ''', (user_id,)).fetchall()

    conn.close()
    return render_template('hostel_fees.html', fee_records=fee_records, payments=payments)


@app.route('/hostel-fees/pay', methods=['POST'])
@login_required
@student_required
def pay_hostel_fee():
    """Demo online payment workflow for Hostel Fees."""
    user_id = session['user_id']
    record_id = request.form.get('record_id')
    amount_to_pay = float(request.form.get('amount', 0.0))
    payment_mode = request.form.get('payment_method', 'Demo Online Gateway')

    if amount_to_pay <= 0:
        flash('Invalid payment amount.', 'danger')
        return redirect(url_for('hostel_fees'))

    conn = database.get_db()
    fee_rec = conn.execute('SELECT * FROM hostel_fee_records WHERE id = ? AND user_id = ?', (record_id, user_id)).fetchone()

    if not fee_rec:
        flash('Fee record not found.', 'danger')
        conn.close()
        return redirect(url_for('hostel_fees'))

    new_amount_paid = fee_rec['amount_paid'] + amount_to_pay
    total_due = fee_rec['total_amount']

    new_status = 'Paid' if new_amount_paid >= total_due else 'Partially Paid'
    txn_ref = f"HST-TXN-{datetime.datetime.now().strftime('%Y%m%d%H%M')}-{uuid.uuid4().hex[:4].upper()}"

    # Record payment transaction
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO payment_transactions (fee_type, record_id, user_id, amount, payment_method, transaction_ref, payment_status, notes)
        VALUES ('hostel', ?, ?, ?, ?, ?, 'Completed', 'Demo Payment Gateway Verified')
    ''', (record_id, user_id, amount_to_pay, payment_mode, txn_ref))

    # Update fee record
    cursor.execute('''
        UPDATE hostel_fee_records
        SET amount_paid = ?, status = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    ''', (new_amount_paid, new_status, record_id))

    # Confirmation notification
    cursor.execute('''
        INSERT INTO notifications (user_id, title, message, link, type)
        VALUES (?, 'Hostel Fee Payment Confirmed', ?, '/hostel-fees', 'fee')
    ''', (user_id, f'Payment of ₹{amount_to_pay:,.2f} recorded (Ref: {txn_ref}). Status: {new_status}.'))

    conn.commit()
    conn.close()

    flash(f'Payment of ₹{amount_to_pay:,.2f} processed successfully! Reference ID: {txn_ref}', 'success')
    return redirect(url_for('hostel_fees'))


@app.route('/dhobi-fees')
@login_required
@student_required
def dhobi_fees():
    """Separate Dhobi & laundry fees section."""
    user_id = session['user_id']
    conn = database.get_db()

    fee_records = conn.execute('''
        SELECT * FROM dhobi_fee_records WHERE user_id = ? ORDER BY id DESC
    ''', (user_id,)).fetchall()

    payments = conn.execute('''
        SELECT * FROM payment_transactions WHERE user_id = ? AND fee_type = 'dhobi' ORDER BY created_at DESC
    ''', (user_id,)).fetchall()

    conn.close()
    return render_template('dhobi_fees.html', fee_records=fee_records, payments=payments)


@app.route('/dhobi-fees/pay', methods=['POST'])
@login_required
@student_required
def pay_dhobi_fee():
    """Demo payment workflow for Dhobi / Laundry fees."""
    user_id = session['user_id']
    record_id = request.form.get('record_id')
    amount_to_pay = float(request.form.get('amount', 0.0))
    payment_mode = request.form.get('payment_method', 'Demo UPI / Online')

    if amount_to_pay <= 0:
        flash('Invalid payment amount.', 'danger')
        return redirect(url_for('dhobi_fees'))

    conn = database.get_db()
    fee_rec = conn.execute('SELECT * FROM dhobi_fee_records WHERE id = ? AND user_id = ?', (record_id, user_id)).fetchone()

    if not fee_rec:
        flash('Dhobi fee record not found.', 'danger')
        conn.close()
        return redirect(url_for('dhobi_fees'))

    new_amount_paid = fee_rec['amount_paid'] + amount_to_pay
    total_due = fee_rec['total_amount']

    new_status = 'Paid' if new_amount_paid >= total_due else 'Partially Paid'
    txn_ref = f"DHB-TXN-{datetime.datetime.now().strftime('%Y%m%d%H%M')}-{uuid.uuid4().hex[:4].upper()}"

    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO payment_transactions (fee_type, record_id, user_id, amount, payment_method, transaction_ref, payment_status, notes)
        VALUES ('dhobi', ?, ?, ?, ?, ?, 'Completed', 'Demo Dhobi Gateway Verified')
    ''', (record_id, user_id, amount_to_pay, payment_mode, txn_ref))

    cursor.execute('''
        UPDATE dhobi_fee_records
        SET amount_paid = ?, status = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    ''', (new_amount_paid, new_status, record_id))

    cursor.execute('''
        INSERT INTO notifications (user_id, title, message, link, type)
        VALUES (?, 'Dhobi Fee Payment Confirmed', ?, '/dhobi-fees', 'fee')
    ''', (user_id, f'Dhobi service fee payment of ₹{amount_to_pay:,.2f} recorded (Ref: {txn_ref}).'))

    conn.commit()
    conn.close()

    flash(f'Dhobi payment of ₹{amount_to_pay:,.2f} recorded successfully! Reference ID: {txn_ref}', 'success')
    return redirect(url_for('dhobi_fees'))


@app.route('/receipt/<string:fee_type>/<int:payment_id>/pdf')
@login_required
def download_receipt_pdf(fee_type, payment_id):
    """Download verified binary PDF receipt for hostel or dhobi payment."""
    user_id = session['user_id']
    role = session.get('role')

    conn = database.get_db()
    payment = conn.execute('SELECT * FROM payment_transactions WHERE id = ?', (payment_id,)).fetchone()

    if not payment:
        conn.close()
        abort(404, description='Payment transaction not found.')

    if role != 'warden' and payment['user_id'] != user_id:
        conn.close()
        abort(403, description='Unauthorized access to receipt.')

    student = conn.execute('''
        SELECT u.*, r.room_number
        FROM users u
        LEFT JOIN rooms r ON u.room_id = r.id
        WHERE u.id = ?
    ''', (payment['user_id'],)).fetchone()

    if fee_type == 'hostel':
        fee_rec = conn.execute('SELECT * FROM hostel_fee_records WHERE id = ?', (payment['record_id'],)).fetchone()
    else:
        fee_rec = conn.execute('SELECT * FROM dhobi_fee_records WHERE id = ?', (payment['record_id'],)).fetchone()

    conn.close()

    if not fee_rec:
        abort(404)

    pdf_buffer = pdf_generator.generate_receipt_pdf(dict(payment), dict(student), dict(fee_rec), fee_type)
    filename = f"AIAC_Receipt_{payment['transaction_ref']}.pdf"
    return send_file(pdf_buffer, mimetype='application/pdf', as_attachment=True, download_name=filename)


# ==========================================
# DHOBI AND LAUNDRY MANAGEMENT
# ==========================================

@app.route('/laundry', methods=['GET', 'POST'])
@login_required
@student_required
def laundry():
    """Laundry schedules, availability, requests submission, and live tracking."""
    user_id = session['user_id']
    conn = database.get_db()

    if request.method == 'POST':
        schedule_id = request.form.get('schedule_id')
        cloth_count = int(request.form.get('cloth_count', 0))
        service_category = request.form.get('service_category', 'Regular Wash & Iron')
        notes = request.form.get('notes', '').strip()

        if cloth_count <= 0 or cloth_count > 25:
            flash('Garment count must be between 1 and 25 clothes.', 'danger')
        else:
            request_code = f"LND-{datetime.datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:4].upper()}"
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO laundry_requests (request_code, user_id, schedule_id, cloth_count, service_category, notes, status)
                VALUES (?, ?, ?, ?, ?, ?, 'Request Submitted')
            ''', (request_code, user_id, schedule_id, cloth_count, service_category, notes))
            conn.commit()

            database.notify_all_wardens(
                f'New Laundry Request: {request_code}',
                f'{session["name"]} submitted {cloth_count} garments for {service_category}.',
                '/warden/laundry',
                'laundry',
                conn=conn
            )
            conn.commit()

            flash(f'Laundry request {request_code} submitted successfully! Hand over garments at the laundry desk.', 'success')
            conn.close()
            return redirect(url_for('laundry'))

    # Available schedules
    schedules = conn.execute('''
        SELECT * FROM laundry_schedules WHERE collection_date >= date('now') ORDER BY collection_date ASC
    ''').fetchall()

    # User laundry history
    requests_history = conn.execute('''
        SELECT lr.*, ls.collection_date, ls.collection_time_start, ls.collection_time_end, ls.expected_delivery_date
        FROM laundry_requests lr
        LEFT JOIN laundry_schedules ls ON lr.schedule_id = ls.id
        WHERE lr.user_id = ?
        ORDER BY lr.created_at DESC
    ''', (user_id,)).fetchall()

    conn.close()
    return render_template('laundry.html', schedules=schedules, requests_history=requests_history)


@app.route('/laundry/cancel/<int:request_id>', methods=['POST'])
@login_required
@student_required
def cancel_laundry(request_id):
    """Cancel laundry request if not yet collected."""
    user_id = session['user_id']
    conn = database.get_db()
    req = conn.execute('SELECT * FROM laundry_requests WHERE id = ? AND user_id = ?', (request_id, user_id)).fetchone()

    if not req:
        flash('Request not found.', 'danger')
    elif req['status'] not in ('Request Submitted', 'Scheduled'):
        flash('Cannot cancel request once clothes are collected or in wash cycle.', 'warning')
    else:
        conn.execute("UPDATE laundry_requests SET status = 'Cancelled', updated_at = CURRENT_TIMESTAMP WHERE id = ?", (request_id,))
        conn.commit()
        flash('Laundry request cancelled successfully.', 'info')

    conn.close()
    return redirect(url_for('laundry'))


# ==========================================
# NOTIFICATIONS & SETTINGS
# ==========================================

@app.route('/notifications')
@login_required
def notifications():
    """Central notifications hub."""
    user_id = session['user_id']
    role = session.get('role')
    conn = database.get_db()

    if role == 'warden':
        items = conn.execute('''
            SELECT * FROM notifications
            WHERE user_id = ? OR user_id = 0 OR user_id IS NULL
            ORDER BY created_at DESC
        ''', (user_id,)).fetchall()
    else:
        items = conn.execute('''
            SELECT * FROM notifications WHERE user_id = ? ORDER BY created_at DESC
        ''', (user_id,)).fetchall()

    conn.close()
    return render_template('notifications.html', notifications=items)


@app.route('/notifications/read/<int:notif_id>', methods=['POST'])
@login_required
def mark_notification_read(notif_id):
    """Mark single notification as read."""
    user_id = session['user_id']
    conn = database.get_db()
    conn.execute('UPDATE notifications SET is_read = 1 WHERE id = ?', (notif_id,))
    conn.commit()
    conn.close()
    return jsonify({'status': 'success'})


@app.route('/notifications/read-all', methods=['POST'])
@login_required
def mark_all_notifications_read():
    """Mark all notifications as read for current user."""
    user_id = session['user_id']
    role = session.get('role')
    conn = database.get_db()
    if role == 'warden':
        conn.execute('UPDATE notifications SET is_read = 1 WHERE user_id = ? OR user_id = 0 OR user_id IS NULL', (user_id,))
    else:
        conn.execute('UPDATE notifications SET is_read = 1 WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()
    flash('All notifications marked as read.', 'info')
    return redirect(url_for('notifications'))


@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    """Settings page for student preferences."""
    if session.get('role') == 'warden':
        return redirect(url_for('warden_settings'))

    user_id = session['user_id']
    conn = database.get_db()
    student = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    conn.close()

    return render_template('settings.html', student=student)


# ==========================================
# WARDEN / ADMIN PORTAL & DASHBOARD
# ==========================================

@app.route('/warden/dashboard')
@login_required
@warden_required
def warden_dashboard():
    """Warden main overview with live database counts and operational metrics."""
    conn = database.get_db()

    stats = {
        'total_students': conn.execute("SELECT COUNT(*) FROM users WHERE role = 'student'").fetchone()[0],
        'total_rooms': conn.execute("SELECT COUNT(*) FROM rooms").fetchone()[0],
        'occupied_rooms': conn.execute("SELECT COUNT(*) FROM rooms WHERE occupancy > 0").fetchone()[0],
        'vacant_rooms': conn.execute("SELECT COUNT(*) FROM rooms WHERE occupancy < capacity AND status = 'available'").fetchone()[0],
        'pending_leaves': conn.execute("SELECT COUNT(*) FROM leave_requests WHERE status = 'Pending'").fetchone()[0],
        'new_emergencies': conn.execute("SELECT COUNT(*) FROM emergency_alerts WHERE status = 'New'").fetchone()[0],
        'unresolved_complaints': conn.execute("SELECT COUNT(*) FROM complaints WHERE status NOT IN ('Resolved', 'Rejected')").fetchone()[0],
        'pending_fees_count': conn.execute("SELECT COUNT(*) FROM hostel_fee_records WHERE status IN ('Pending', 'Overdue')").fetchone()[0],
        'active_laundry_count': conn.execute("SELECT COUNT(*) FROM laundry_requests WHERE status NOT IN ('Delivered', 'Cancelled')").fetchone()[0],
    }

    recent_emergencies = conn.execute('''
        SELECT e.*, u.name as student_name, u.phone as student_phone, u.hostel_block
        FROM emergency_alerts e
        JOIN users u ON e.user_id = u.id
        ORDER BY CASE e.status WHEN 'New' THEN 1 WHEN 'Acknowledged' THEN 2 ELSE 3 END, e.created_at DESC
        LIMIT 5
    ''').fetchall()

    recent_leaves = conn.execute('''
        SELECT l.*, u.name as student_name, u.email as student_email, u.hostel_block
        FROM leave_requests l
        JOIN users u ON l.user_id = u.id
        WHERE l.status = 'Pending'
        ORDER BY l.created_at ASC
        LIMIT 5
    ''').fetchall()

    recent_complaints = conn.execute('''
        SELECT c.*, u.name as student_name, u.hostel_block
        FROM complaints c
        JOIN users u ON c.user_id = u.id
        WHERE c.status NOT IN ('Resolved', 'Rejected')
        ORDER BY CASE c.priority WHEN 'Urgent' THEN 1 WHEN 'High' THEN 2 ELSE 3 END, c.created_at DESC
        LIMIT 5
    ''').fetchall()

    conn.close()

    return render_template(
        'warden_dashboard.html',
        stats=stats,
        emergencies=recent_emergencies,
        leaves=recent_leaves,
        complaints=recent_complaints
    )


@app.route('/warden/students', methods=['GET'])
@login_required
@warden_required
def warden_students():
    """Student management: view, search, filter students."""
    search = request.args.get('search', '').strip()
    block_filter = request.args.get('block', '').strip()
    year_filter = request.args.get('year', '').strip()

    conn = database.get_db()
    query = '''
        SELECT u.*, r.room_number, b.name as block_name
        FROM users u
        LEFT JOIN rooms r ON u.room_id = r.id
        LEFT JOIN hostel_blocks b ON r.block_id = b.id
        WHERE u.role = 'student'
    '''
    params = []

    if search:
        query += ' AND (u.name LIKE ? OR u.email LIKE ? OR u.phone LIKE ? OR u.student_id LIKE ?)'
        wildcard = f'%{search}%'
        params.extend([wildcard, wildcard, wildcard, wildcard])

    if block_filter:
        query += ' AND u.hostel_block = ?'
        params.append(block_filter)

    if year_filter:
        query += ' AND u.academic_year = ?'
        params.append(year_filter)

    query += ' ORDER BY u.created_at DESC'
    students = conn.execute(query, params).fetchall()
    blocks = conn.execute('SELECT * FROM hostel_blocks ORDER BY name').fetchall()
    conn.close()

    return render_template('student_management.html', students=students, blocks=blocks,
                           search=search, selected_block=block_filter, selected_year=year_filter)


@app.route('/warden/rooms', methods=['GET'])
@login_required
@warden_required
def warden_rooms():
    """Room management: view rooms, capacity, allocations."""
    block_filter = request.args.get('block', '')
    status_filter = request.args.get('status', '')

    conn = database.get_db()
    query = '''
        SELECT r.*, b.name as block_name,
               (SELECT COUNT(*) FROM users u WHERE u.room_id = r.id) as actual_occupants
        FROM rooms r
        JOIN hostel_blocks b ON r.block_id = b.id
        WHERE 1=1
    '''
    params = []

    if block_filter:
        query += ' AND r.block_id = ?'
        params.append(block_filter)

    if status_filter:
        query += ' AND r.status = ?'
        params.append(status_filter)

    query += ' ORDER BY b.name, r.room_number ASC'
    rooms = conn.execute(query, params).fetchall()

    blocks = conn.execute('SELECT * FROM hostel_blocks ORDER BY name').fetchall()
    unallocated_students = conn.execute("SELECT id, name, email, hostel_block FROM users WHERE role = 'student' AND (room_id IS NULL OR room_id = 0)").fetchall()

    conn.close()
    return render_template('room_management.html', rooms=rooms, blocks=blocks,
                           unallocated_students=unallocated_students,
                           selected_block=block_filter, selected_status=status_filter)


@app.route('/warden/rooms/add', methods=['POST'])
@login_required
@warden_required
def warden_add_room():
    """Add a new hostel room."""
    block_id = request.form.get('block_id')
    room_number = request.form.get('room_number', '').strip()
    floor = int(request.form.get('floor', 1))
    capacity = int(request.form.get('capacity', 2))
    notes = request.form.get('notes', '').strip()

    if not block_id or not room_number:
        flash('Block and Room number are required.', 'danger')
        return redirect(url_for('warden_rooms'))

    conn = database.get_db()
    try:
        conn.execute('''
            INSERT INTO rooms (block_id, room_number, floor, capacity, occupancy, status, notes)
            VALUES (?, ?, ?, ?, 0, 'available', ?)
        ''', (block_id, room_number, floor, capacity, notes))
        conn.commit()
        flash(f'Room {room_number} added successfully.', 'success')
    except Exception as e:
        flash(f'Failed to add room: Room {room_number} may already exist in this block.', 'danger')
    finally:
        conn.close()

    return redirect(url_for('warden_rooms'))


@app.route('/warden/rooms/allocate', methods=['POST'])
@login_required
@warden_required
def warden_allocate_room():
    """Allocate or change room for a student. Prevents assigning beyond capacity."""
    student_id = request.form.get('student_id')
    room_id = request.form.get('room_id')

    if not student_id or not room_id:
        flash('Please select both a student and a room.', 'danger')
        return redirect(url_for('warden_rooms'))

    conn = database.get_db()
    room = conn.execute('SELECT * FROM rooms WHERE id = ?', (room_id,)).fetchone()
    if not room:
        flash('Selected room does not exist.', 'danger')
        conn.close()
        return redirect(url_for('warden_rooms'))

    # Check capacity constraint
    current_occupants = conn.execute('SELECT COUNT(*) FROM users WHERE room_id = ? AND role = "student"', (room_id,)).fetchone()[0]
    if current_occupants >= room['capacity']:
        flash(f'Room {room["room_number"]} is at full capacity ({room["capacity"]}/{room["capacity"]}). Cannot assign additional students.', 'danger')
        conn.close()
        return redirect(url_for('warden_rooms'))

    # Allocate room
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET room_id = ? WHERE id = ?', (room_id, student_id))
    new_occ = current_occupants + 1
    new_status = 'full' if new_occ >= room['capacity'] else 'available'
    cursor.execute('UPDATE rooms SET occupancy = ?, status = ? WHERE id = ?', (new_occ, new_status, room_id))

    # Record allocation history
    today = datetime.date.today().isoformat()
    cursor.execute('''
        INSERT INTO room_allocations (room_id, user_id, allocated_date, status)
        VALUES (?, ?, ?, 'active')
    ''', (room_id, student_id, today))

    conn.commit()

    # Notify student
    database.add_notification(
        student_id,
        'Hostel Room Assigned',
        f'You have been allocated Room {room["room_number"]}. View your room details in your dashboard.',
        '/room-details',
        'system',
        conn=conn
    )

    conn.commit()
    conn.close()

    flash('Student room assigned successfully.', 'success')
    return redirect(url_for('warden_rooms'))


@app.route('/warden/rooms/vacate/<int:student_id>', methods=['POST'])
@login_required
@warden_required
def warden_vacate_room(student_id):
    """De-allocate student from their room."""
    conn = database.get_db()
    student = conn.execute('SELECT * FROM users WHERE id = ?', (student_id,)).fetchone()

    if student and student['room_id']:
        old_room_id = student['room_id']
        conn.execute('UPDATE users SET room_id = NULL WHERE id = ?', (student_id,))
        # Update room occupancy
        occ = conn.execute('SELECT COUNT(*) FROM users WHERE room_id = ? AND role = "student"', (old_room_id,)).fetchone()[0]
        conn.execute('UPDATE rooms SET occupancy = ?, status = "available" WHERE id = ?', (occ, old_room_id))
        conn.commit()
        flash('Student unallocated from room.', 'info')

    conn.close()
    return redirect(url_for('warden_rooms'))


@app.route('/warden/leave-requests', methods=['GET'])
@login_required
@warden_required
def warden_leave_requests():
    """Warden leave requests review, approval, and rejection."""
    status_filter = request.args.get('status', 'Pending')

    conn = database.get_db()
    query = '''
        SELECT l.*, u.name as student_name, u.email as student_email, u.hostel_block, u.phone as student_phone,
               r.room_number, o.outpass_ref
        FROM leave_requests l
        JOIN users u ON l.user_id = u.id
        LEFT JOIN rooms r ON u.room_id = r.id
        LEFT JOIN outpasses o ON l.id = o.leave_request_id
    '''
    params = []
    if status_filter and status_filter != 'all':
        query += ' WHERE l.status = ?'
        params.append(status_filter)

    query += ' ORDER BY l.created_at DESC'
    requests_list = conn.execute(query, params).fetchall()
    conn.close()

    return render_template('warden_leave_requests.html', requests=requests_list, selected_status=status_filter)


@app.route('/warden/leave-requests/<int:leave_id>/action', methods=['POST'])
@login_required
@warden_required
def warden_leave_action(leave_id):
    """Approve or reject student leave request with decision note."""
    decision = request.form.get('decision')  # 'Approved' or 'Rejected'
    decision_note = request.form.get('decision_note', '').strip()
    warden_id = session['user_id']
    now_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    if decision not in ('Approved', 'Rejected'):
        flash('Invalid leave decision.', 'danger')
        return redirect(url_for('warden_leave_requests'))

    conn = database.get_db()
    leave = conn.execute('SELECT * FROM leave_requests WHERE id = ?', (leave_id,)).fetchone()

    if not leave:
        flash('Leave request not found.', 'danger')
        conn.close()
        return redirect(url_for('warden_leave_requests'))

    cursor = conn.cursor()

    if decision == 'Approved':
        outpass_ref = f"OUT-{datetime.datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:4].upper()}"
        verification_code = f"VRF-{uuid.uuid4().hex[:8].upper()}"

        cursor.execute('''
            UPDATE leave_requests
            SET status = 'Approved', decision_note = ?, warden_id = ?, decision_datetime = ?, outpass_ref = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (decision_note, warden_id, now_str, outpass_ref, leave_id))

        cursor.execute('''
            INSERT INTO outpasses (leave_request_id, user_id, outpass_ref, issued_datetime,
                                  departure_datetime, expected_return_datetime, destination, leave_type,
                                  warden_id, warden_name, status, verification_code)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Valid', ?)
        ''', (leave_id, leave['user_id'], outpass_ref, now_str,
              leave['start_datetime'], leave['return_datetime'], leave['destination'],
              leave['leave_type'], warden_id, session['name'], verification_code))

        conn.commit()

        # Notify student with outpass link
        database.add_notification(
            leave['user_id'],
            'Leave Request Approved - Outpass Issued!',
            f'Your {leave["leave_type"]} request to {leave["destination"]} was approved. Reference: {outpass_ref}. Download your outpass.',
            f'/outpass/{cursor.lastrowid}',
            'outpass',
            conn=conn
        )
        flash(f'Leave request approved! Outpass {outpass_ref} generated.', 'success')

    else:
        cursor.execute('''
            UPDATE leave_requests
            SET status = 'Rejected', decision_note = ?, warden_id = ?, decision_datetime = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (decision_note, warden_id, now_str, leave_id))

        conn.commit()

        database.add_notification(
            leave['user_id'],
            'Leave Request Rejected',
            f'Your leave request was rejected by the warden. Reason: {decision_note or "Not permitted by hostel guidelines."}',
            '/leave',
            'leave',
            conn=conn
        )
        flash('Leave request rejected.', 'warning')

    conn.commit()
    conn.close()
    return redirect(url_for('warden_leave_requests'))


@app.route('/warden/outpasses')
@login_required
@warden_required
def warden_outpasses():
    """View all student outpasses issued by the system."""
    conn = database.get_db()
    outpasses = conn.execute('''
        SELECT o.*, u.name as student_name, u.email as student_email, u.hostel_block, r.room_number
        FROM outpasses o
        JOIN users u ON o.user_id = u.id
        LEFT JOIN rooms r ON u.room_id = r.id
        ORDER BY o.issued_datetime DESC
    ''').fetchall()
    conn.close()
    return render_template('outpass.html', all_outpasses=outpasses, is_warden_view=True)


@app.route('/warden/emergencies', methods=['GET'])
@login_required
@warden_required
def warden_emergencies():
    """Warden Emergency management desk."""
    status_filter = request.args.get('status', '')

    conn = database.get_db()
    query = '''
        SELECT e.*, u.name as student_name, u.email as student_email, u.phone as student_phone, u.hostel_block,
               w.name as ack_warden_name
        FROM emergency_alerts e
        JOIN users u ON e.user_id = u.id
        LEFT JOIN users w ON e.acknowledged_by = w.id
    '''
    params = []
    if status_filter:
        query += ' WHERE e.status = ?'
        params.append(status_filter)

    query += ' ORDER BY CASE e.status WHEN "New" THEN 1 WHEN "Acknowledged" THEN 2 WHEN "In Progress" THEN 3 ELSE 4 END, e.created_at DESC'
    alerts = conn.execute(query, params).fetchall()
    conn.close()

    return render_template('warden_emergencies.html', alerts=alerts, selected_status=status_filter)


@app.route('/warden/emergencies/<int:alert_id>/action', methods=['POST'])
@login_required
@warden_required
def warden_emergency_action(alert_id):
    """Update emergency alert status and resolution notes."""
    new_status = request.form.get('status')
    resolution_notes = request.form.get('resolution_notes', '').strip()
    warden_id = session['user_id']

    conn = database.get_db()
    alert = conn.execute('SELECT * FROM emergency_alerts WHERE id = ?', (alert_id,)).fetchone()

    if not alert:
        flash('Emergency alert not found.', 'danger')
        conn.close()
        return redirect(url_for('warden_emergencies'))

    conn.execute('''
        UPDATE emergency_alerts
        SET status = ?, acknowledged_by = ?, resolution_notes = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    ''', (new_status, warden_id, resolution_notes, alert_id))

    conn.commit()

    database.add_notification(
        alert['user_id'],
        f'Emergency Alert Status: {new_status}',
        f'Your emergency report ({alert["category"]}) has been marked as {new_status}. Warden Note: {resolution_notes or "Under response."}',
        '/emergency',
        'emergency',
        conn=conn
    )

    conn.commit()
    conn.close()
    flash(f'Emergency alert updated to {new_status}.', 'success')
    return redirect(url_for('warden_emergencies'))


@app.route('/warden/complaints', methods=['GET'])
@login_required
@warden_required
def warden_complaints():
    """Warden complaints review, staff assignment, and resolution."""
    status_filter = request.args.get('status', '')
    cat_filter = request.args.get('category', '')
    prio_filter = request.args.get('priority', '')

    conn = database.get_db()
    query = '''
        SELECT c.*, u.name as student_name, u.email as student_email, u.hostel_block, r.room_number
        FROM complaints c
        JOIN users u ON c.user_id = u.id
        LEFT JOIN rooms r ON u.room_id = r.id
        WHERE 1=1
    '''
    params = []
    if status_filter:
        query += ' AND c.status = ?'
        params.append(status_filter)
    if cat_filter:
        query += ' AND c.category = ?'
        params.append(cat_filter)
    if prio_filter:
        query += ' AND c.priority = ?'
        params.append(prio_filter)

    query += ' ORDER BY CASE c.priority WHEN "Urgent" THEN 1 WHEN "High" THEN 2 ELSE 3 END, c.created_at DESC'
    complaints_list = conn.execute(query, params).fetchall()

    # Load responses map
    comp_ids = [c['id'] for c in complaints_list]
    res_map = {}
    if comp_ids:
        placeholders = ','.join('?' for _ in comp_ids)
        res_rows = conn.execute(f'''
            SELECT cr.*, u.name as responder_name
            FROM complaint_responses cr
            JOIN users u ON cr.user_id = u.id
            WHERE cr.complaint_id IN ({placeholders})
            ORDER BY cr.created_at ASC
        ''', comp_ids).fetchall()
        for r in res_rows:
            res_map.setdefault(r['complaint_id'], []).append(r)

    conn.close()
    return render_template('warden_complaints.html', complaints=complaints_list, responses_map=res_map,
                           selected_status=status_filter, selected_cat=cat_filter, selected_prio=prio_filter)


@app.route('/warden/complaints/<int:complaint_id>/action', methods=['POST'])
@login_required
@warden_required
def warden_complaint_action(complaint_id):
    """Update complaint status, assign staff, and add resolution notes."""
    new_status = request.form.get('status')
    assigned_to = request.form.get('assigned_to', '').strip()
    resolution_notes = request.form.get('resolution_notes', '').strip()

    conn = database.get_db()
    complaint = conn.execute('SELECT * FROM complaints WHERE id = ?', (complaint_id,)).fetchone()

    if not complaint:
        flash('Complaint not found.', 'danger')
        conn.close()
        return redirect(url_for('warden_complaints'))

    conn.execute('''
        UPDATE complaints
        SET status = ?, assigned_to = ?, resolution_notes = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    ''', (new_status, assigned_to, resolution_notes, complaint_id))

    conn.commit()

    database.add_notification(
        complaint['user_id'],
        f'Complaint Status Updated: {complaint["complaint_code"]}',
        f'Your complaint status is now "{new_status}". Assigned: {assigned_to or "Maintenance Team"}.',
        '/complaints',
        'complaint',
        conn=conn
    )

    conn.commit()
    conn.close()
    flash(f'Complaint {complaint["complaint_code"]} updated to {new_status}.', 'success')
    return redirect(url_for('warden_complaints'))


@app.route('/warden/mess-menu', methods=['GET', 'POST'])
@login_required
@warden_required
def warden_mess_menu():
    """Warden menu management: edit items, mark special meals, publish."""
    conn = database.get_db()

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'save_item':
            day = request.form.get('day_of_week')
            meal = request.form.get('meal_type')
            timing = request.form.get('timing', '')
            items = request.form.get('items', '').strip()
            is_special = 1 if request.form.get('is_special') == '1' else 0
            special_note = request.form.get('special_note', '').strip()

            conn.execute('''
                INSERT INTO mess_menus (day_of_week, meal_type, timing, items, is_special, special_note, published_by, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(day_of_week, meal_type) DO UPDATE SET
                    timing = excluded.timing,
                    items = excluded.items,
                    is_special = excluded.is_special,
                    special_note = excluded.special_note,
                    published_by = excluded.published_by,
                    updated_at = CURRENT_TIMESTAMP
            ''', (day, meal, timing, items, is_special, special_note, session['user_id']))
            conn.commit()
            flash(f'Updated {day} {meal} menu.', 'success')

        elif action == 'publish_all':
            # Notify all registered students of mess menu publication
            students = conn.execute("SELECT id FROM users WHERE role = 'student'").fetchall()
            for s in students:
                conn.execute('''
                    INSERT INTO notifications (user_id, title, message, link, type)
                    VALUES (?, 'Updated Weekly Mess Menu Published', 'Hostel Warden has updated and published the weekly mess timetable. Check out the special meals!', '/mess-menu', 'mess')
                ''', (s['id'],))
            conn.commit()
            flash('Weekly Mess Menu published and in-app notifications sent to all students!', 'success')

        conn.close()
        return redirect(url_for('warden_mess_menu'))

    menu_rows = conn.execute('''
        SELECT * FROM mess_menus ORDER BY
        CASE day_of_week
            WHEN 'Monday' THEN 1 WHEN 'Tuesday' THEN 2 WHEN 'Wednesday' THEN 3
            WHEN 'Thursday' THEN 4 WHEN 'Friday' THEN 5 WHEN 'Saturday' THEN 6 WHEN 'Sunday' THEN 7
        END,
        CASE meal_type
            WHEN 'Breakfast' THEN 1 WHEN 'Lunch' THEN 2 WHEN 'Evening Snacks' THEN 3 WHEN 'Dinner' THEN 4
        END
    ''').fetchall()
    conn.close()

    return render_template('warden_mess_menu.html', menu_rows=menu_rows)


@app.route('/warden/fees', methods=['GET', 'POST'])
@login_required
@warden_required
def warden_fees():
    """Warden fee management: create fee records, record verified offline payments."""
    conn = database.get_db()

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'record_payment':
            fee_type = request.form.get('fee_type')
            record_id = int(request.form.get('record_id'))
            amount = float(request.form.get('amount', 0.0))
            method = request.form.get('payment_method', 'Bank Transfer (Verified)')
            notes = request.form.get('notes', 'Verified by Hostel Accounts Office')

            if amount <= 0:
                flash('Please enter a valid amount.', 'danger')
            else:
                table = 'hostel_fee_records' if fee_type == 'hostel' else 'dhobi_fee_records'
                rec = conn.execute(f'SELECT * FROM {table} WHERE id = ?', (record_id,)).fetchone()
                if rec:
                    new_paid = rec['amount_paid'] + amount
                    new_status = 'Paid' if new_paid >= rec['total_amount'] else 'Partially Paid'
                    prefix = 'HST' if fee_type == 'hostel' else 'DHB'
                    txn_ref = f"{prefix}-VERIF-{datetime.datetime.now().strftime('%Y%m%d%H%M')}-{uuid.uuid4().hex[:4].upper()}"

                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO payment_transactions (fee_type, record_id, user_id, amount, payment_method, transaction_ref, payment_status, notes)
                        VALUES (?, ?, ?, ?, ?, ?, 'Completed', ?)
                    ''', (fee_type, record_id, rec['user_id'], amount, method, txn_ref, notes))

                    cursor.execute(f'''
                        UPDATE {table} SET amount_paid = ?, status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?
                    ''', (new_paid, new_status, record_id))

                    conn.commit()

                    database.add_notification(
                        rec['user_id'],
                        f'{fee_type.capitalize()} Fee Payment Verified',
                        f'Hostel Accounts Office verified your payment of ₹{amount:,.2f} (Ref: {txn_ref}).',
                        f'/{fee_type}-fees',
                        'fee',
                        conn=conn
                    )

                    conn.commit()
                    flash(f'Payment of ₹{amount:,.2f} successfully recorded. Ref: {txn_ref}', 'success')

        conn.close()
        return redirect(url_for('warden_fees'))

    # Retrieve hostel and dhobi fee ledgers
    hostel_records = conn.execute('''
        SELECT f.*, u.name as student_name, u.email as student_email, u.hostel_block, r.room_number
        FROM hostel_fee_records f
        JOIN users u ON f.user_id = u.id
        LEFT JOIN rooms r ON u.room_id = r.id
        ORDER BY f.created_at DESC
    ''').fetchall()

    dhobi_records = conn.execute('''
        SELECT d.*, u.name as student_name, u.email as student_email, u.hostel_block
        FROM dhobi_fee_records d
        JOIN users u ON d.user_id = u.id
        ORDER BY d.created_at DESC
    ''').fetchall()

    conn.close()
    return render_template('warden_fees.html', hostel_records=hostel_records, dhobi_records=dhobi_records)


@app.route('/warden/laundry', methods=['GET', 'POST'])
@login_required
@warden_required
def warden_laundry():
    """Warden / staff laundry management: configure schedules and update request statuses."""
    conn = database.get_db()

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'add_schedule':
            title = request.form.get('title', '').strip()
            c_date = request.form.get('collection_date')
            c_start = request.form.get('collection_time_start', '08:00 AM')
            c_end = request.form.get('collection_time_end', '11:00 AM')
            d_date = request.form.get('expected_delivery_date')
            max_c = int(request.form.get('max_clothes', 15))

            conn.execute('''
                INSERT INTO laundry_schedules (title, collection_date, collection_time_start, collection_time_end,
                                              expected_delivery_date, is_available, max_clothes_per_student, created_by)
                VALUES (?, ?, ?, ?, ?, 1, ?, ?)
            ''', (title, c_date, c_start, c_end, d_date, max_c, session['user_id']))

            # Broadcast laundry availability notification to students
            students = conn.execute("SELECT id FROM users WHERE role = 'student'").fetchall()
            for s in students:
                conn.execute('''
                    INSERT INTO notifications (user_id, title, message, link, type)
                    VALUES (?, 'New Laundry Collection Schedule Announced', ?, '/laundry', 'laundry')
                ''', (s['id'], f'Laundry pickup on {c_date} ({c_start} - {c_end}). Deliveries on {d_date}.'))

            conn.commit()
            flash('Laundry schedule created and students notified.', 'success')

        elif action == 'update_status':
            req_id = int(request.form.get('request_id'))
            new_status = request.form.get('status')

            req = conn.execute('SELECT * FROM laundry_requests WHERE id = ?', (req_id,)).fetchone()
            if req:
                conn.execute('UPDATE laundry_requests SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?', (new_status, req_id))
                conn.commit()

                database.add_notification(
                    req['user_id'],
                    f'Laundry Status Update: {req["request_code"]}',
                    f'Your laundry bundle is now: {new_status}.',
                    '/laundry',
                    'laundry',
                    conn=conn
                )
                conn.commit()
                flash(f'Request {req["request_code"]} updated to {new_status}.', 'success')

        elif action == 'toggle_schedule':
            sched_id = int(request.form.get('schedule_id'))
            avail = int(request.form.get('is_available', 1))
            note = request.form.get('holiday_note', '')
            conn.execute('UPDATE laundry_schedules SET is_available = ?, holiday_note = ? WHERE id = ?', (avail, note, sched_id))
            conn.commit()
            flash('Schedule status updated.', 'info')

        conn.close()
        return redirect(url_for('warden_laundry'))

    schedules = conn.execute('SELECT * FROM laundry_schedules ORDER BY collection_date DESC').fetchall()
    requests_list = conn.execute('''
        SELECT lr.*, u.name as student_name, u.email as student_email, u.hostel_block, r.room_number,
               ls.collection_date
        FROM laundry_requests lr
        JOIN users u ON lr.user_id = u.id
        LEFT JOIN rooms r ON u.room_id = r.id
        LEFT JOIN laundry_schedules ls ON lr.schedule_id = ls.id
        ORDER BY lr.created_at DESC
    ''').fetchall()

    conn.close()
    return render_template('warden_laundry.html', schedules=schedules, requests=requests_list)


@app.route('/warden/announcements', methods=['GET', 'POST'])
@login_required
@warden_required
def warden_announcements():
    """Hostel announcements broadcast module."""
    conn = database.get_db()

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'create':
            title = request.form.get('title', '').strip()
            content = request.form.get('content', '').strip()
            audience = request.form.get('target_audience', 'all')
            block = request.form.get('hostel_block', '')
            priority = request.form.get('priority', 'normal')

            conn.execute('''
                INSERT INTO announcements (title, content, target_audience, hostel_block, priority, warden_id)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (title, content, audience, block or None, priority, session['user_id']))

            # Broadcast in-app notification
            students = conn.execute("SELECT id FROM users WHERE role = 'student'").fetchall()
            for s in students:
                conn.execute('''
                    INSERT INTO notifications (user_id, title, message, link, type)
                    VALUES (?, ?, ?, '/dashboard', 'announcement')
                ''', (s['id'], f'📢 Announcement: {title}', content[:100] + '...'))

            conn.commit()
            flash('Announcement published and sent to residents.', 'success')

        elif action == 'delete':
            ann_id = int(request.form.get('announcement_id'))
            conn.execute('DELETE FROM announcements WHERE id = ?', (ann_id,))
            conn.commit()
            flash('Announcement removed.', 'info')

        conn.close()
        return redirect(url_for('warden_announcements'))

    announcements_list = conn.execute('SELECT * FROM announcements ORDER BY created_at DESC').fetchall()
    blocks = conn.execute('SELECT * FROM hostel_blocks ORDER BY name').fetchall()
    conn.close()

    return render_template('warden_announcements.html', announcements=announcements_list, blocks=blocks)


@app.route('/warden/reports')
@login_required
@warden_required
def warden_reports():
    """Comprehensive Reports & Analytics dashboard based on real database records."""
    conn = database.get_db()

    # 1. Registration totals
    total_students = conn.execute("SELECT COUNT(*) FROM users WHERE role = 'student'").fetchone()[0]

    # 2. Room occupancy
    total_rooms = conn.execute("SELECT COUNT(*) FROM rooms").fetchone()[0]
    total_capacity = conn.execute("SELECT COALESCE(SUM(capacity), 0) FROM rooms").fetchone()[0]
    total_occupied_beds = conn.execute("SELECT COUNT(*) FROM users WHERE room_id IS NOT NULL AND role = 'student'").fetchone()[0]
    occupancy_pct = round((total_occupied_beds / total_capacity * 100), 1) if total_capacity > 0 else 0

    # 3. Leave statistics
    leave_stats = {
        'total': conn.execute("SELECT COUNT(*) FROM leave_requests").fetchone()[0],
        'approved': conn.execute("SELECT COUNT(*) FROM leave_requests WHERE status = 'Approved'").fetchone()[0],
        'rejected': conn.execute("SELECT COUNT(*) FROM leave_requests WHERE status = 'Rejected'").fetchone()[0],
        'pending': conn.execute("SELECT COUNT(*) FROM leave_requests WHERE status = 'Pending'").fetchone()[0]
    }

    # 4. Complaints breakdown
    complaints_raw = conn.execute("SELECT * FROM complaints").fetchall()
    complaints_data = [dict(c) for c in complaints_raw]
    ai_summary = ai_engine.generate_complaint_summary(complaints_data)

    cat_counts = conn.execute('''
        SELECT category, COUNT(*) as count FROM complaints GROUP BY category ORDER BY count DESC
    ''').fetchall()

    status_counts = conn.execute('''
        SELECT status, COUNT(*) as count FROM complaints GROUP BY status
    ''').fetchall()

    # 5. Emergency statistics
    emergency_stats = {
        'total': conn.execute("SELECT COUNT(*) FROM emergency_alerts").fetchone()[0],
        'new': conn.execute("SELECT COUNT(*) FROM emergency_alerts WHERE status = 'New'").fetchone()[0],
        'in_progress': conn.execute("SELECT COUNT(*) FROM emergency_alerts WHERE status IN ('Acknowledged', 'In Progress')").fetchone()[0],
        'resolved': conn.execute("SELECT COUNT(*) FROM emergency_alerts WHERE status = 'Resolved'").fetchone()[0],
    }

    # 6. Fees collection metrics
    hostel_fees_coll = {
        'billed': conn.execute("SELECT COALESCE(SUM(total_amount), 0) FROM hostel_fee_records").fetchone()[0],
        'collected': conn.execute("SELECT COALESCE(SUM(amount_paid), 0) FROM hostel_fee_records").fetchone()[0]
    }
    hostel_fees_coll['pending'] = max(0.0, hostel_fees_coll['billed'] - hostel_fees_coll['collected'])

    dhobi_fees_coll = {
        'billed': conn.execute("SELECT COALESCE(SUM(total_amount), 0) FROM dhobi_fee_records").fetchone()[0],
        'collected': conn.execute("SELECT COALESCE(SUM(amount_paid), 0) FROM dhobi_fee_records").fetchone()[0]
    }
    dhobi_fees_coll['pending'] = max(0.0, dhobi_fees_coll['billed'] - dhobi_fees_coll['collected'])

    # 7. Laundry stats
    laundry_stats = {
        'total_requests': conn.execute("SELECT COUNT(*) FROM laundry_requests").fetchone()[0],
        'delivered': conn.execute("SELECT COUNT(*) FROM laundry_requests WHERE status = 'Delivered'").fetchone()[0],
        'active': conn.execute("SELECT COUNT(*) FROM laundry_requests WHERE status NOT IN ('Delivered', 'Cancelled')").fetchone()[0]
    }

    conn.close()

    return render_template(
        'reports.html',
        total_students=total_students,
        total_rooms=total_rooms,
        total_capacity=total_capacity,
        total_occupied_beds=total_occupied_beds,
        occupancy_pct=occupancy_pct,
        leave_stats=leave_stats,
        complaints_summary=ai_summary,
        category_breakdown=cat_counts,
        status_breakdown=status_counts,
        emergency_stats=emergency_stats,
        hostel_fees=hostel_fees_coll,
        dhobi_fees=dhobi_fees_coll,
        laundry_stats=laundry_stats
    )


@app.route('/warden/settings', methods=['GET', 'POST'])
@login_required
@warden_required
def warden_settings():
    """Warden platform settings: college email domain, contacts, hostel configuration."""
    if request.method == 'POST':
        domain = request.form.get('college_email_domain', '').strip().lower()
        hostel_name = request.form.get('hostel_name', '').strip()
        med_phone = request.form.get('emergency_medical', '').strip()
        sec_phone = request.form.get('emergency_security', '').strip()
        warden_phone = request.form.get('emergency_warden', '').strip()
        elec_phone = request.form.get('emergency_electrician', '').strip()
        curfew = request.form.get('curfew_time', '').strip()

        database.set_setting('college_email_domain', domain, 'Allowed college email domain for registrations')
        if hostel_name:
            database.set_setting('hostel_name', hostel_name)
        if med_phone:
            database.set_setting('emergency_phone_medical', med_phone)
        if sec_phone:
            database.set_setting('emergency_phone_security', sec_phone)
        if warden_phone:
            database.set_setting('emergency_phone_warden', warden_phone)
        if elec_phone:
            database.set_setting('emergency_phone_electrician', elec_phone)
        if curfew:
            database.set_setting('curfew_time', curfew)

        flash('Hostel platform configuration updated successfully.', 'success')
        return redirect(url_for('warden_settings'))

    settings_dict = {
        'college_email_domain': database.get_setting('college_email_domain', 'college.edu'),
        'hostel_name': database.get_setting('hostel_name', 'AIAC Central Residential Complex'),
        'emergency_medical': database.get_setting('emergency_phone_medical', '+91 98765 00108'),
        'emergency_security': database.get_setting('emergency_phone_security', '+91 98765 00100'),
        'emergency_warden': database.get_setting('emergency_phone_warden', '+91 98765 00101'),
        'emergency_electrician': database.get_setting('emergency_phone_electrician', '+91 98765 00102'),
        'curfew_time': database.get_setting('curfew_time', '09:30 PM')
    }

    return render_template('settings.html', settings=settings_dict, is_warden=True)


# ==========================================
# REST / JSON API ENDPOINTS
# ==========================================

@app.route('/api/ai/suggest-complaint', methods=['POST'])
@login_required
def api_ai_suggest_complaint():
    """Live AI Complaint Categorization & Urgency Suggestion API."""
    data = request.get_json() or {}
    subject = data.get('subject', '')
    description = data.get('description', '')

    result = ai_engine.analyze_complaint(subject, description)
    return jsonify(result)


@app.route('/api/ai/chatbot', methods=['POST'])
@login_required
def api_ai_chatbot():
    """AIAC 24/7 Virtual Concierge / FAQ Chatbot API."""
    data = request.get_json() or {}
    message = data.get('message', '')
    user_name = session.get('name', 'Resident')

    response = ai_engine.faq_bot_reply(message, user_name)
    return jsonify(response)


@app.route('/api/notifications/unread-count')
@login_required
def api_unread_count():
    """Returns real-time unread notifications count for badge update."""
    user_id = session['user_id']
    role = session.get('role')
    conn = database.get_db()
    if role == 'warden':
        row = conn.execute(
            'SELECT COUNT(*) as count FROM notifications WHERE (user_id = ? OR user_id = 0 OR user_id IS NULL) AND is_read = 0',
            (user_id,)
        ).fetchone()
    else:
        row = conn.execute(
            'SELECT COUNT(*) as count FROM notifications WHERE user_id = ? AND is_read = 0',
            (user_id,)
        ).fetchone()
    conn.close()
    return jsonify({'unread_count': row['count'] if row else 0})


# ==========================================
# ERROR HANDLERS
# ==========================================

@app.errorhandler(404)
def not_found_error(error):
    return render_template('error.html', code=404, title="Page Not Found",
                           message=getattr(error, 'description', "The page or record you requested does not exist.")), 404


@app.errorhandler(403)
def forbidden_error(error):
    return render_template('error.html', code=403, title="Access Forbidden",
                           message=getattr(error, 'description', "You do not have permission to view or manage this record.")), 403


@app.errorhandler(500)
def internal_error(error):
    return render_template('error.html', code=500, title="System Error",
                           message="An internal error occurred. Our engineering team has been notified."), 500


if __name__ == '__main__':
    # Run development server
    port = int(os.environ.get('PORT', 5000))
    print(f"Starting AIAC Hostel Platform on http://127.0.0.1:{port}")
    app.run(host='0.0.0.0', port=port, debug=False)
