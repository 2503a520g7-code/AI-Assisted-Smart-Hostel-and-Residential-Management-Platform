"""
database.py - Database connection, schema definition, and initialization for AIAC.
Ensures SQLite foreign-key enforcement, parameterized queries, and persistence across restarts.
"""

import sqlite3
import os
from werkzeug.security import generate_password_hash

DATABASE_PATH = os.environ.get('DATABASE_PATH', 'aiac_hostel.db')


def get_db(db_path=None):
    """Obtain a database connection with row factory and foreign keys enabled."""
    target_path = db_path or DATABASE_PATH
    conn = sqlite3.connect(target_path, timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys = ON;')
    return conn


def init_db(db_path=None):
    """Initialize database tables without destroying existing data."""
    conn = get_db(db_path)
    cursor = conn.cursor()

    cursor.executescript('''
    -- Users Table
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'student',
        hostel_block TEXT,
        academic_year TEXT,
        student_id TEXT,
        department TEXT,
        guardian_name TEXT,
        guardian_phone TEXT,
        room_id INTEGER,
        room_number TEXT,
        room_type TEXT,
        phone TEXT,
        status TEXT DEFAULT 'active',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (room_id) REFERENCES rooms(id) ON DELETE SET NULL
    );

    -- Hostel Blocks Table
    CREATE TABLE IF NOT EXISTS hostel_blocks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        gender_type TEXT DEFAULT 'Co-ed',
        total_floors INTEGER DEFAULT 4,
        description TEXT
    );

    -- Rooms Table
    CREATE TABLE IF NOT EXISTS rooms (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        block_id INTEGER NOT NULL,
        room_number TEXT NOT NULL,
        room_type TEXT DEFAULT 'Double Sharing Standard',
        floor INTEGER DEFAULT 1,
        capacity INTEGER NOT NULL DEFAULT 2,
        occupancy INTEGER NOT NULL DEFAULT 0,
        status TEXT DEFAULT 'available',
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (block_id) REFERENCES hostel_blocks(id) ON DELETE CASCADE,
        UNIQUE (block_id, room_number)
    );

    -- Room Allocations Table
    CREATE TABLE IF NOT EXISTS room_allocations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        room_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        allocated_date DATE NOT NULL,
        vacated_date DATE,
        status TEXT DEFAULT 'active',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (room_id) REFERENCES rooms(id) ON DELETE CASCADE,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );

    -- Leave Requests Table
    CREATE TABLE IF NOT EXISTS leave_requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        leave_type TEXT NOT NULL,
        start_datetime TEXT NOT NULL,
        return_datetime TEXT NOT NULL,
        destination TEXT NOT NULL,
        reason TEXT NOT NULL,
        emergency_contact TEXT NOT NULL,
        parent_phone TEXT,
        additional_notes TEXT,
        status TEXT DEFAULT 'Pending',
        decision_note TEXT,
        warden_id INTEGER,
        decision_datetime TEXT,
        outpass_ref TEXT UNIQUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (warden_id) REFERENCES users(id) ON DELETE SET NULL
    );

    -- Outpasses Table
    CREATE TABLE IF NOT EXISTS outpasses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        leave_request_id INTEGER NOT NULL UNIQUE,
        user_id INTEGER NOT NULL,
        outpass_ref TEXT NOT NULL UNIQUE,
        issued_datetime TEXT NOT NULL,
        departure_datetime TEXT NOT NULL,
        expected_return_datetime TEXT NOT NULL,
        destination TEXT NOT NULL,
        leave_type TEXT NOT NULL,
        warden_id INTEGER,
        warden_name TEXT,
        status TEXT DEFAULT 'Valid',
        verification_code TEXT NOT NULL UNIQUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (leave_request_id) REFERENCES leave_requests(id) ON DELETE CASCADE,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (warden_id) REFERENCES users(id) ON DELETE SET NULL
    );

    -- Emergency Alerts Table
    CREATE TABLE IF NOT EXISTS emergency_alerts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        category TEXT NOT NULL,
        location_or_room TEXT NOT NULL,
        priority TEXT DEFAULT 'Critical',
        description TEXT NOT NULL,
        contact_number TEXT,
        status TEXT DEFAULT 'New',
        acknowledged_by INTEGER,
        resolution_notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (acknowledged_by) REFERENCES users(id) ON DELETE SET NULL
    );

    -- Complaints Table
    CREATE TABLE IF NOT EXISTS complaints (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        complaint_code TEXT NOT NULL UNIQUE,
        user_id INTEGER NOT NULL,
        category TEXT NOT NULL,
        subject TEXT NOT NULL,
        description TEXT NOT NULL,
        location_or_room TEXT NOT NULL,
        priority TEXT DEFAULT 'Medium',
        ai_suggested_priority TEXT,
        ai_suggested_category TEXT,
        ai_confidence REAL DEFAULT 0.0,
        status TEXT DEFAULT 'Submitted',
        assigned_to TEXT,
        resolution_notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );

    -- Complaint Responses Table
    CREATE TABLE IF NOT EXISTS complaint_responses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        complaint_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        message TEXT NOT NULL,
        is_warden INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (complaint_id) REFERENCES complaints(id) ON DELETE CASCADE,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );

    -- Mess Menu Table
    CREATE TABLE IF NOT EXISTS mess_menus (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        day_of_week TEXT NOT NULL,
        meal_type TEXT NOT NULL,
        timing TEXT,
        items TEXT NOT NULL,
        is_special INTEGER DEFAULT 0,
        special_note TEXT,
        published_by INTEGER,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (published_by) REFERENCES users(id) ON DELETE SET NULL,
        UNIQUE (day_of_week, meal_type)
    );

    -- Hostel Fee Records Table
    CREATE TABLE IF NOT EXISTS hostel_fee_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        academic_term TEXT NOT NULL,
        total_amount REAL NOT NULL DEFAULT 45000.0,
        amount_paid REAL NOT NULL DEFAULT 0.0,
        due_date DATE NOT NULL,
        status TEXT DEFAULT 'Pending',
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );

    -- Dhobi Fee Records Table
    CREATE TABLE IF NOT EXISTS dhobi_fee_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        month_year TEXT NOT NULL,
        total_amount REAL NOT NULL DEFAULT 1200.0,
        amount_paid REAL NOT NULL DEFAULT 0.0,
        due_date DATE NOT NULL,
        status TEXT DEFAULT 'Pending',
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );

    -- Payment Transactions Table
    CREATE TABLE IF NOT EXISTS payment_transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fee_type TEXT NOT NULL,
        record_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        amount REAL NOT NULL,
        payment_method TEXT NOT NULL,
        transaction_ref TEXT NOT NULL UNIQUE,
        payment_status TEXT DEFAULT 'Completed',
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );

    -- Laundry Schedules Table
    CREATE TABLE IF NOT EXISTS laundry_schedules (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        collection_date DATE NOT NULL,
        collection_time_start TEXT NOT NULL,
        collection_time_end TEXT NOT NULL,
        expected_delivery_date DATE NOT NULL,
        is_available INTEGER DEFAULT 1,
        holiday_note TEXT,
        max_clothes_per_student INTEGER DEFAULT 15,
        created_by INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
    );

    -- Laundry Requests Table
    CREATE TABLE IF NOT EXISTS laundry_requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        request_code TEXT NOT NULL UNIQUE,
        user_id INTEGER NOT NULL,
        schedule_id INTEGER,
        cloth_count INTEGER NOT NULL,
        service_category TEXT NOT NULL,
        notes TEXT,
        status TEXT DEFAULT 'Request Submitted',
        pickup_date DATE,
        delivery_date DATE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (schedule_id) REFERENCES laundry_schedules(id) ON DELETE SET NULL
    );

    -- Notifications Table
    CREATE TABLE IF NOT EXISTS notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        title TEXT NOT NULL,
        message TEXT NOT NULL,
        link TEXT,
        type TEXT DEFAULT 'general',
        is_read INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );

    -- Announcements Table
    CREATE TABLE IF NOT EXISTS announcements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        target_audience TEXT DEFAULT 'all',
        hostel_block TEXT,
        priority TEXT DEFAULT 'normal',
        warden_id INTEGER,
        is_active INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (warden_id) REFERENCES users(id) ON DELETE SET NULL
    );

    -- System Settings Table
    CREATE TABLE IF NOT EXISTS system_settings (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL,
        description TEXT
    );

    -- Holiday Calendar Table
    CREATE TABLE IF NOT EXISTS holiday_calendar (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        holiday_date DATE NOT NULL,
        end_date DATE,
        holiday_type TEXT DEFAULT 'Public Holiday',
        description TEXT,
        mess_service_status TEXT DEFAULT 'Open (Standard Hours)',
        is_outing_allowed INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    ''')

    conn.commit()
    seed_default_data(conn)
    migrate_db(conn)
    conn.close()


def migrate_db(conn):
    """Safely apply schema migrations to preserve existing data across restarts."""
    cursor = conn.cursor()

    # 1. Ensure new student profile columns exist in users table
    cursor.execute("PRAGMA table_info(users)")
    existing_user_cols = [c[1] for c in cursor.fetchall()]
    new_user_cols = [
        ('student_id', 'TEXT'),
        ('department', 'TEXT'),
        ('guardian_name', 'TEXT'),
        ('guardian_phone', 'TEXT'),
        ('room_number', 'TEXT'),
        ('room_type', 'TEXT')
    ]
    for col_name, col_type in new_user_cols:
        if col_name not in existing_user_cols:
            cursor.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}")

    # Unique index for student_id (when provided)
    cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_users_student_id ON users(student_id) WHERE student_id IS NOT NULL AND student_id != ''")

    # Sync room_number for existing records if room_id is set
    cursor.execute("""
        UPDATE users 
        SET room_number = (SELECT room_number FROM rooms WHERE rooms.id = users.room_id)
        WHERE room_id IS NOT NULL AND (room_number IS NULL OR room_number = '')
    """)

    # 2. Ensure room_type exists in rooms table
    cursor.execute("PRAGMA table_info(rooms)")
    existing_room_cols = [c[1] for c in cursor.fetchall()]
    if 'room_type' not in existing_room_cols:
        cursor.execute("ALTER TABLE rooms ADD COLUMN room_type TEXT DEFAULT 'Double Sharing Standard'")
        cursor.execute("UPDATE rooms SET room_type = 'Single Occupancy Deluxe' WHERE capacity = 1")
        cursor.execute("UPDATE rooms SET room_type = 'Double Sharing Standard' WHERE capacity = 2")
        cursor.execute("UPDATE rooms SET room_type = 'Triple Sharing Standard' WHERE capacity = 3")

    # 3. Seed default holidays in holiday_calendar if empty
    cursor.execute("SELECT COUNT(*) FROM holiday_calendar")
    if cursor.fetchone()[0] == 0:
        default_holidays = [
            ('Diwali & Deepavali Break', '2026-11-08', '2026-11-12', 'Festival Holiday', 'Official campus festival break. Special festive sweets, feast and celebration dinners served in mess.', 'Festive Special Feast', 1),
            ('Guru Nanak Jayanti', '2026-11-24', '2026-11-24', 'Public Holiday', 'College holiday. Mess open with standard lunch and dinner timings.', 'Open (Standard Hours)', 1),
            ('Winter Semester Vacation', '2026-12-20', '2026-12-31', 'Semester Break', 'Term end vacation. Vacation leaves up to 10 days permitted with guardian consent.', 'Open (Limited Staff)', 1),
            ('New Year Campus Day', '2027-01-01', '2027-01-01', 'College Holiday', 'Welcome 2027! Special holiday brunch served from 10:00 AM to 1:00 PM.', 'Special Holiday Brunch', 1),
            ('Republic Day', '2027-01-26', '2027-01-26', 'National Holiday', 'National flag hoisting at 08:30 AM in Central Quadrangle. Special breakfast.', 'Flag Hoisting Special Breakfast', 1),
            ('Maha Shivratri', '2027-02-15', '2027-02-15', 'Festival Holiday', 'Special fasting fruits, sabudana khichdi, and milk served in mess.', 'Fasting & Regular Options', 1),
            ('Holi Spring Festival', '2027-03-24', '2027-03-25', 'Festival Holiday', 'Hostel color celebrations in campus ground. Thandai & Gujiya feast.', 'Celebration Buffet & Thandai', 1)
        ]
        for title, h_date, e_date, h_type, desc, mess_st, outing_ok in default_holidays:
            cursor.execute('''
                INSERT INTO holiday_calendar (title, holiday_date, end_date, holiday_type, description, mess_service_status, is_outing_allowed)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (title, h_date, e_date, h_type, desc, mess_st, outing_ok))

    conn.commit()


def seed_default_data(conn):
    """Seed base configuration, default warden, blocks, mess menu, and schedules if empty."""
    cursor = conn.cursor()

    # 1. System Settings
    default_settings = [
        ('college_email_domain', 'college.edu', 'Configurable email domain requirement for student registration. Set to * for any.'),
        ('hostel_name', 'AIAC Central Residential Complex', 'Official name of the hostel/residential campus'),
        ('emergency_phone_medical', '+91 98765 00108', '24/7 Campus Medical Center & Ambulance Line'),
        ('emergency_phone_security', '+91 98765 00100', 'Hostel Main Gate & Chief Security Control Desk'),
        ('emergency_phone_warden', '+91 98765 00101', 'Chief Warden Emergency Hotline'),
        ('emergency_phone_electrician', '+91 98765 00102', 'Resident Electrician & Maintenance Team'),
        ('warden_office_hours', '9:00 AM - 6:00 PM (Mon-Sat)', 'Hostel Administration Office Timings'),
        ('curfew_time', '09:30 PM', 'Mandatory in-campus hostel curfew time'),
        ('default_hostel_fee', '45000', 'Standard semester hostel fee per student in INR'),
        ('default_dhobi_fee', '1200', 'Monthly laundry/dhobi service fee per student in INR')
    ]
    for key, val, desc in default_settings:
        cursor.execute(
            'INSERT OR IGNORE INTO system_settings (key, value, description) VALUES (?, ?, ?)',
            (key, val, desc)
        )

    # 2. Initial Warden Account
    # Check if a warden already exists
    cursor.execute("SELECT id FROM users WHERE role = 'warden' LIMIT 1")
    warden = cursor.fetchone()
    if not warden:
        warden_email = 'warden@college.edu'
        warden_pass = generate_password_hash('WardenPassword123!')
        cursor.execute('''
            INSERT INTO users (name, email, password_hash, role, hostel_block, academic_year, phone, status)
            VALUES (?, ?, ?, 'warden', 'All Blocks', 'Staff', '+91 98765 00101', 'active')
        ''', ('Dr. Ramesh Sharma (Chief Warden)', warden_email, warden_pass))
        warden_id = cursor.lastrowid
    else:
        warden_id = warden['id']

    # 3. Hostel Blocks
    default_blocks = [
        ('Block A - Aryabhatta', 'Boys', 4, 'Senior Undergraduate & Postgraduate Boys Wing with High-Speed LAN'),
        ('Block B - Bhaskara', 'Boys', 4, 'Junior & Sophomore Boys Wing with Common Study Lounges'),
        ('Block C - Gargi', 'Girls', 4, 'Undergraduate Girls Wing with 24x7 Security Desk & Badminton Court'),
        ('Block D - Maitreyi', 'Girls', 4, 'Postgraduate & Research Scholar Girls Wing with Quiet Study Floors')
    ]
    for name, gender, floors, desc in default_blocks:
        cursor.execute('''
            INSERT OR IGNORE INTO hostel_blocks (name, gender_type, total_floors, description)
            VALUES (?, ?, ?, ?)
        ''', (name, gender, floors, desc))

    # 4. Rooms (Seed sample rooms if table is empty)
    cursor.execute('SELECT COUNT(*) as count FROM rooms')
    if cursor.fetchone()['count'] == 0:
        cursor.execute('SELECT id, name FROM hostel_blocks')
        blocks = cursor.fetchall()
        for b in blocks:
            b_id = b['id']
            # Create a variety of rooms across floors 1-3
            for floor in [1, 2, 3]:
                for room_idx in range(1, 6):
                    r_num = f'{floor}0{room_idx}'
                    cap = 2 if floor < 3 else 3
                    cursor.execute('''
                        INSERT OR IGNORE INTO rooms (block_id, room_number, floor, capacity, occupancy, status, notes)
                        VALUES (?, ?, ?, ?, 0, 'available', ?)
                    ''', (b_id, r_num, floor, cap, f'Floor {floor} Standard {cap}-Sharing Room'))

    # 5. Weekly Mess Menu (Monday to Sunday, all 4 meal slots)
    cursor.execute('SELECT COUNT(*) as count FROM mess_menus')
    if cursor.fetchone()['count'] == 0:
        weekly_menu = [
            # Monday
            ('Monday', 'Breakfast', '07:30 - 09:00 AM', 'Idli, Sambar, Coconut Chutney, Bread Butter, Banana, Tea/Coffee', 0, ''),
            ('Monday', 'Lunch', '12:30 - 02:00 PM', 'Jeera Rice, Yellow Dal Tadka, Aloo Gobhi, Phulka, Curd, Salad', 0, ''),
            ('Monday', 'Evening Snacks', '05:00 - 06:00 PM', 'Veg Cutlet, Mint Chutney, Tea / Masala Chai', 0, ''),
            ('Monday', 'Dinner', '07:30 - 09:30 PM', 'Chapati, Paneer Butter Masala, Mixed Veg Khichdi, Papad, Rice Kheer', 0, ''),

            # Tuesday
            ('Tuesday', 'Breakfast', '07:30 - 09:00 AM', 'Poha with Peanuts, Sev, Boiled Eggs / Sprouts, Toast, Fresh Milk, Tea', 0, ''),
            ('Tuesday', 'Lunch', '12:30 - 02:00 PM', 'Steamed Rice, Rajma Masala, Bhindi Fry, Tawa Roti, Boondi Raita, Pickle', 0, ''),
            ('Tuesday', 'Evening Snacks', '05:00 - 06:00 PM', 'Samosa, Tamarind Chutney, Ginger Tea', 0, ''),
            ('Tuesday', 'Dinner', '07:30 - 09:30 PM', 'Phulka, Dal Makhani, Dum Aloo, Steamed Basmati Rice, Fruit Custard', 0, ''),

            # Wednesday (Special Dinner!)
            ('Wednesday', 'Breakfast', '07:30 - 09:00 AM', 'Masala Dosa, Tomato Chutney, Sambar, Boiled Egg / Fruit, Coffee', 0, ''),
            ('Wednesday', 'Lunch', '12:30 - 02:00 PM', 'Lemon Rice, Curd Rice, Sambar, Potato Roast, Appalam, Cucumber Salad', 0, ''),
            ('Wednesday', 'Evening Snacks', '05:00 - 06:00 PM', 'Pav Bhaji / Bun Maska, Filter Coffee', 0, ''),
            ('Wednesday', 'Dinner', '07:30 - 09:30 PM', 'Shahi Paneer, Butter Naan, Veg Pulao / Chicken Biryani (Special), Dal Tadka, Gulab Jamun, Ice Cream', 1, 'SPECIAL MIDWEEK FEAST: Chef Special Biryani, Butter Naan & Hot Gulab Jamun'),

            # Thursday
            ('Thursday', 'Breakfast', '07:30 - 09:00 AM', 'Aloo Paratha with White Butter, Curd, Pickle, Boiled Egg, Tea', 0, ''),
            ('Thursday', 'Lunch', '12:30 - 02:00 PM', 'Steamed Rice, Chana Dal Palak, Baingan Bharta, Tawa Roti, Buttermilk', 0, ''),
            ('Thursday', 'Evening Snacks', '05:00 - 06:00 PM', 'Onion Pakoda, Green Chutney, Cardamom Tea', 0, ''),
            ('Thursday', 'Dinner', '07:30 - 09:30 PM', 'Tawa Roti, Kadai Vegetable, Dal Fry, Jeera Rice, Moong Dal Halwa', 0, ''),

            # Friday
            ('Friday', 'Breakfast', '07:30 - 09:00 AM', 'Medu Vada, Upma, Coconut Chutney, Sambar, Seasonal Fruit, Tea/Coffee', 0, ''),
            ('Friday', 'Lunch', '12:30 - 02:00 PM', 'Basmati Rice, Chole Masala, Bhature / Bhatura, Onion Salad, Boondi Raita', 0, ''),
            ('Friday', 'Evening Snacks', '05:00 - 06:00 PM', 'Corn Chat, Biscuits, Hot Tea', 0, ''),
            ('Friday', 'Dinner', '07:30 - 09:30 PM', 'Chapati, Matar Paneer, Dal Palak, Steamed Rice, Semiya Payasam', 0, ''),

            # Saturday
            ('Saturday', 'Breakfast', '08:00 - 09:30 AM', 'Puri Bhaji, Halwa, Boiled Eggs / Sprouted Moong, Tea/Coffee', 0, ''),
            ('Saturday', 'Lunch', '12:30 - 02:00 PM', 'Khichdi, Kadhi, Batata Vada, Papad, Pickle, Kachumber Salad', 0, ''),
            ('Saturday', 'Evening Snacks', '05:00 - 06:00 PM', 'Bhel Puri / Dhokla, Mint Chutney, Masala Tea', 0, ''),
            ('Saturday', 'Dinner', '07:30 - 09:30 PM', 'Tandoori Roti, Veg Kofta Curry, Dal Tadka, Fried Rice, Sweet Jalebi', 0, ''),

            # Sunday (Special Afternoon Lunch!)
            ('Sunday', 'Breakfast', '08:00 - 10:00 AM', 'Mysore Masala Dosa, Uttapam, Coconut & Tomato Chutney, Sambar, Filter Coffee', 0, ''),
            ('Sunday', 'Lunch', '12:30 - 02:30 PM', 'Hyderabadi Dum Biryani (Special), Mirchi Ka Salan, Paneer Tikka Masala, Tandoori Roti, Mixed Raita, Rasgulla & Mango Kulfi', 1, 'GRAND SUNDAY SPECIAL LUNCH: Royal Dum Biryani, Paneer Tikka & Artisanal Kulfi'),
            ('Sunday', 'Evening Snacks', '05:00 - 06:00 PM', 'French Fries, Sweet Corn, Hot Chocolate / Chai', 0, ''),
            ('Sunday', 'Dinner', '07:30 - 09:30 PM', 'Light Phulka, Moong Dal Tadka, Aloo Jeera, Steamed Rice, Curd, Seasonal Fresh Fruits', 0, 'Light comfort dinner after grand lunch')
        ]
        for day, meal, timing, items, is_spec, note in weekly_menu:
            cursor.execute('''
                INSERT OR IGNORE INTO mess_menus (day_of_week, meal_type, timing, items, is_special, special_note, published_by)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (day, meal, timing, items, is_spec, note, warden_id))

    # 6. Laundry Schedules
    cursor.execute('SELECT COUNT(*) as count FROM laundry_schedules')
    if cursor.fetchone()['count'] == 0:
        import datetime
        today = datetime.date.today()
        # Create schedules for upcoming collection slots
        slot1 = today + datetime.timedelta(days=(1 if today.weekday() != 0 else 0))
        deliv1 = slot1 + datetime.timedelta(days=2)
        slot2 = slot1 + datetime.timedelta(days=3)
        deliv2 = slot2 + datetime.timedelta(days=2)

        schedules = [
            ('Weekday Regular Laundry Collection', slot1.isoformat(), '08:00 AM', '11:30 AM', deliv1.isoformat(), 1, '', 15),
            ('Weekend Laundry Collection Drive', slot2.isoformat(), '09:00 AM', '01:00 PM', deliv2.isoformat(), 1, '', 20)
        ]
        for title, c_date, c_start, c_end, d_date, avail, note, max_c in schedules:
            cursor.execute('''
                INSERT INTO laundry_schedules (title, collection_date, collection_time_start, collection_time_end, expected_delivery_date, is_available, holiday_note, max_clothes_per_student, created_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (title, c_date, c_start, c_end, d_date, avail, note, max_c, warden_id))

    # 7. Announcements
    cursor.execute('SELECT COUNT(*) as count FROM announcements')
    if cursor.fetchone()['count'] == 0:
        announcements = [
            ('Welcome to AIAC Hostel Platform for Academic Year 2026-27',
             'Welcome to all residents! Please make sure your room profile is updated, review your mess schedule, and test your emergency alert protocol in your dashboard.',
             'all', None, 'normal', warden_id),
            ('Strict Curfew & Outpass Submission Reminder',
             'All outpass requests for weekend leave must be applied at least 6 hours in advance through the platform. Security checks will scan your digital outpass at the gate.',
             'all', None, 'urgent', warden_id),
            ('Dhobi Service Registration Open',
             'Dhobi services for this month are operational. You may submit your batch requests on scheduled pickup days with a maximum of 15 garments.',
             'all', None, 'normal', warden_id)
        ]
        for title, content, aud, block, prio, w_id in announcements:
            cursor.execute('''
                INSERT INTO announcements (title, content, target_audience, hostel_block, priority, warden_id)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (title, content, aud, block, prio, w_id))

    conn.commit()


def get_setting(key, default=None):
    """Fetch setting value from system_settings table."""
    conn = get_db()
    row = conn.execute('SELECT value FROM system_settings WHERE key = ?', (key,)).fetchone()
    conn.close()
    if row:
        return row['value']
    return default


def set_setting(key, value, description=None):
    """Set or update setting in system_settings table."""
    conn = get_db()
    conn.execute('''
        INSERT INTO system_settings (key, value, description)
        VALUES (?, ?, ?)
        ON CONFLICT(key) DO UPDATE SET value = excluded.value
    ''', (key, value, description or ''))
    conn.commit()
    conn.close()


def add_notification(user_id, title, message, link='', type='general', conn=None):
    """Helper to insert notification for a student, warden (user_id=0 or warden id), or all."""
    close_at_end = False
    if conn is None:
        conn = get_db()
        close_at_end = True
    conn.execute('''
        INSERT INTO notifications (user_id, title, message, link, type)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, title, message, link, type))
    if close_at_end:
        conn.commit()
        conn.close()


def notify_all_wardens(title, message, link='', type='general', conn=None):
    """Helper to insert notification for all warden accounts."""
    close_at_end = False
    if conn is None:
        conn = get_db()
        close_at_end = True
    wardens = conn.execute("SELECT id FROM users WHERE role = 'warden'").fetchall()
    for w in wardens:
        conn.execute('''
            INSERT INTO notifications (user_id, title, message, link, type)
            VALUES (?, ?, ?, ?, ?)
        ''', (w['id'], title, message, link, type))
    if close_at_end:
        conn.commit()
        conn.close()
