import os, csv, io, json, pymysql, hashlib, smtplib, ssl, sys, random, uuid
from email.message import EmailMessage
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_from_directory, make_response
from datetime import timedelta, datetime
from werkzeug.utils import secure_filename
from fpdf import FPDF, XPos, YPos
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'ml'))
from classifier import auto_categorize, categorize, predict_top3, detect_anomaly, clean_and_tokenize
import model_registry
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'ml'))
from sentiment import analyze_sentiment
from priority import compute_priority
from model_stats import model_cards, correlation_matrix

app = Flask(
    __name__,
    template_folder=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend', 'templates'),
    static_folder=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend', 'static')
)
app.secret_key = os.environ.get('SECRET_KEY', 'supersecretkey')
app.permanent_session_lifetime = timedelta(days=1)

SMTP_CONFIG = dict(
    host=os.environ.get('SMTP_HOST', 'smtp.gmail.com'),
    port=int(os.environ.get('SMTP_PORT', 587)),
    user=os.environ.get('SMTP_USER', 'brooskings661@gmail.com'),
    password=os.environ.get('SMTP_PASS', 'vksq mrdy qnqd zbut')
)

DEPARTMENT_EMAILS_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'department_emails.json')

DEPARTMENT_EMAILS = {
    'IT Support': os.environ.get('EMAIL_IT', 'brooskings661@gmail.com'),
    'Library': os.environ.get('EMAIL_LIBRARY', 'brooskings661@gmail.com'),
    'Hostels': os.environ.get('EMAIL_HOSTELS', 'brooskings661@gmail.com'),
    'Academics': os.environ.get('EMAIL_ACADEMICS', 'brooskings661@gmail.com'),
    'Canteen': os.environ.get('EMAIL_CANTEEN', 'brooskings661@gmail.com'),
    'Maintenance': os.environ.get('EMAIL_MAINTENANCE', 'brooskings661@gmail.com'),
    'Security': os.environ.get('EMAIL_SECURITY', 'brooskings661@gmail.com'),
    'Transport': os.environ.get('EMAIL_TRANSPORT', 'brooskings661@gmail.com'),
    'Financial Services': os.environ.get('EMAIL_FINANCE', 'brooskings661@gmail.com'),
    'Administrative': os.environ.get('EMAIL_ADMIN', 'brooskings661@gmail.com'),
    'Other': os.environ.get('EMAIL_OTHER', 'brooskings661@gmail.com'),
}

if os.path.isfile(DEPARTMENT_EMAILS_PATH):
    try:
        with open(DEPARTMENT_EMAILS_PATH) as f:
            saved = json.load(f)
            DEPARTMENT_EMAILS.update(saved)
    except Exception as e:
        print(f"[DEPARTMENT EMAILS] {e}")

DB_CONFIG = dict(
    host=os.environ.get('DB_HOST', '127.0.0.1'),
    port=int(os.environ.get('DB_PORT', 3306)),
    user=os.environ.get('DB_USER', 'root'),
    password=os.environ.get('DB_PASSWORD', ''),
    database=os.environ.get('DB_NAME', 'complainify'),
    charset='utf8mb4'
)
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'uploads')
ALLOWED_EXTENSIONS = {'pdf', 'svg', 'png', 'jpg', 'jpeg', 'doc', 'docx', 'xls', 'xlsx', 'csv', 'txt', 'zip'}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def get_db():
    return pymysql.connect(**DB_CONFIG, cursorclass=pymysql.cursors.DictCursor)

def hash_pw(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

def gen_ticket():
    return 'CMP-' + os.urandom(2).hex().upper()

ANON_EMAIL_DOMAIN = '@anonymous.complainify'

def is_anon_email(email):
    """Anonymous (incognito) complaints carry a placeholder address.
    No mail must ever go to it — department routing is the only mail allowed."""
    return bool(email) and email.lower().endswith(ANON_EMAIL_DOMAIN)

CATEGORIES = ['Academics', 'Hostels', 'IT Support', 'Infrastructure', 'Financial Services',
              'Administrative', 'Security', 'Maintenance', 'Transport', 'Canteen', 'Library', 'Other']

DEFAULT_COLLEGES = ['College of Science & Technology', 'School of Business & Management',
                    'College of Engineering', 'Faculty of Health Sciences',
                    'Faculty of Humanities & Social Sciences', 'College of Education',
                    'Faculty of Law', 'Other']

def get_colleges():
    """Colleges/faculties within the university (fallback to defaults if table missing)."""
    try:
        conn = get_db(); cur = conn.cursor()
        cur.execute("SELECT name FROM colleges ORDER BY id")
        rows = cur.fetchall()
        cur.close(); conn.close()
        return [r['name'] for r in rows] or DEFAULT_COLLEGES
    except Exception as e:
        print(f"[COLLEGES] {e}")
        return DEFAULT_COLLEGES

def create_notification(user_id, message, link=None):
    try:
        conn = get_db(); cur = conn.cursor()
        cur.execute("INSERT INTO notifications (user_id, message, link) VALUES (%s, %s, %s)", (user_id, message, link))
        conn.commit()
        cur.close(); conn.close()
    except Exception as e:
        print(f"[NOTIFICATION ERROR] {e}")

def log_action(user_id, action, target_type=None, target_id=None, details=None):
    try:
        conn = get_db(); cur = conn.cursor()
        cur.execute("INSERT INTO audit_logs (user_id, action, target_type, target_id, details) VALUES (%s, %s, %s, %s, %s)",
            (user_id, action, target_type, target_id, details))
        conn.commit()
        cur.close(); conn.close()
    except Exception as e:
        print(f"[LOG_ACTION ERROR] {e} — retrying with table init")
        try:
            conn = get_db(); cur = conn.cursor()
            for tbl in ['audit_logs', 'notifications', 'complaint_comments']:
                cur.execute(f"DROP TABLE IF EXISTS {tbl}")
            cur.execute("""CREATE TABLE audit_logs (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT DEFAULT NULL,
                action VARCHAR(100) NOT NULL,
                target_type VARCHAR(50) DEFAULT NULL,
                target_id VARCHAR(50) DEFAULT NULL,
                details TEXT DEFAULT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""")
            cur.execute("""CREATE TABLE notifications (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                message TEXT NOT NULL,
                link VARCHAR(255) DEFAULT NULL,
                is_read TINYINT(1) DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""")
            cur.execute("""CREATE TABLE complaint_comments (
                id INT AUTO_INCREMENT PRIMARY KEY,
                complaint_id INT NOT NULL,
                user_id INT NOT NULL,
                message TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""")
            conn.commit()
            cur.execute("INSERT INTO audit_logs (user_id, action, target_type, target_id, details) VALUES (%s, %s, %s, %s, %s)",
                (user_id, action, target_type, target_id, details))
            conn.commit()
            cur.close(); conn.close()
            print(f"[LOG_ACTION] Recovered — tables recreated, log inserted")
        except Exception as e2:
            print(f"[LOG_ACTION] Fatal: {e2}")

def send_email_notification(to_email, subject, body):
    if not SMTP_CONFIG['user'] or not SMTP_CONFIG['password']:
        print(f"[EMAIL SKIPPED] No SMTP config: to={to_email}, subject={subject}")
        return False
    try:
        msg = EmailMessage()
        msg['Subject'] = subject
        msg['From'] = SMTP_CONFIG['user']
        msg['To'] = to_email
        msg.set_content(body)
        context = ssl.create_default_context()
        with smtplib.SMTP(SMTP_CONFIG['host'], SMTP_CONFIG['port'], timeout=30) as server:
            server.starttls(context=context)
            server.login(SMTP_CONFIG['user'], SMTP_CONFIG['password'])
            server.send_message(msg)
        return True
    except Exception as e:
        print(f"[EMAIL ERROR] {e}")
        return False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit-complaint', methods=['GET', 'POST'])
def submit_complaint():
    if request.method == 'POST':
        conn = get_db(); cur = conn.cursor()
        try:
            tid = gen_ticket()
            uid = session.get('user_id')
            anon = request.args.get('anonymous') == '1'
            if anon and not uid:
                anon_id = 'ANON-' + hashlib.md5((str(random.random()) + str(datetime.now())).encode()).hexdigest()[:8].upper()
                fullname = anon_id
                email = anon_id.lower() + '@anonymous.complainify'
            else:
                fullname = request.form.get('fullname', session.get('fullname', 'Anonymous'))
                email = request.form.get('email', session.get('email', ''))
            college = request.form.get('college', session.get('college', '')).strip()
            description = request.form.get('description', '')
            subject = request.form.get('subject', '')
            full_text = subject + ' ' + description
            manual_cat = request.form.get('category', '').strip()

            if manual_cat and manual_cat != 'auto':
                category = manual_cat
                confidence = 1.0
                tier = 'auto'
            else:
                result = categorize(full_text)
                category = result['category']
                confidence = result['confidence']
                tier = result['tier']
                if tier == 'auto':
                    flash(f'AI auto-categorized: {category} ({confidence*100:.1f}%)', 'success')
                elif tier == 'suggest':
                    flash(f'AI suggests: {category} ({confidence*100:.1f}%) — please review', 'warning')
                else:
                    flash(f'Unclear complaint ({confidence*100:.1f}%) — category set to Other', 'warning')
                    category = 'Other'

            anomaly = detect_anomaly(full_text)
            if anomaly['is_anomaly']:
                flash('⚠️ This complaint looks unusual — will be flagged for manual review', 'warning')

            sentiment_result = analyze_sentiment(full_text)
            sentiment = sentiment_result['label']
            sentiment_score = sentiment_result['score']

            priority, priority_score, priority_reason = compute_priority(
                full_text, sentiment, sentiment_score, anomaly)
            flash(f'Priority set to {priority} (score {priority_score} — {priority_reason})', 'warning' if priority == 'High' else 'success')

            student_attachment = request.files.get('student_attachment')
            student_attachment_name = None
            if student_attachment and student_attachment.filename and '.' in student_attachment.filename:
                ext = student_attachment.filename.rsplit('.', 1)[1].lower()
                if ext in ALLOWED_EXTENSIONS:
                    unique_name = f"{tid}_{uuid.uuid4().hex[:8]}.{ext}"
                    student_attachment.save(os.path.join(UPLOAD_FOLDER, unique_name))
                    student_attachment_name = unique_name

            dept_name = DEPARTMENT_EMAILS.get(category)
            if dept_name and category != 'Other':
                assigned_to = category
                auto_status = 'In Progress'
            else:
                assigned_to = None
                auto_status = 'Pending'

            cur.execute("""INSERT INTO complaints
                (ticket_id,user_id,fullname,email,college,category,priority,priority_score,priority_reason,subject,description,sentiment,sentiment_score,student_attachment,assigned_to,status,assigned_at,model_version)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                (tid, uid, fullname, email, college or None,
                 category, priority, priority_score, priority_reason,
                 subject, description, sentiment, sentiment_score, student_attachment_name,
                 assigned_to, auto_status, datetime.now() if assigned_to else None,
                 model_registry.latest_version_id()))
            conn.commit()

            conn2 = get_db(); cur2 = conn2.cursor()
            cur2.execute("SELECT id FROM users WHERE role='admin'")
            for admin in cur2.fetchall():
                create_notification(admin['id'], f'New complaint #{tid} ({category})', url_for('admin_complaint_detail', ticket_id=tid))
            cur2.close(); conn2.close()
            log_action(uid, 'submit_complaint', 'complaint', tid, f'Category: {category}, Priority: {priority}')

            student_email_sent = False
            if SMTP_CONFIG['user'] and not anon:
                student_email = email
                if student_email:
                    body = f"""Dear Student,

Your complaint (Ticket: {tid}) has been received successfully.

Category: {category}
Subject: {subject}
Status: Pending

We will review and assign it shortly.

Regards,
Complainify Team"""
                    try:
                        if send_email_notification(student_email,
                                f'Complaint Received: {tid}', body):
                            student_email_sent = True
                            cur.execute("UPDATE complaints SET email_sent=1 WHERE ticket_id=%s", (tid,))
                            conn.commit()
                    except Exception as e:
                        print(f"[EMAIL BLOCK ERROR] {e}")

            dept_email = DEPARTMENT_EMAILS.get(category)
            if SMTP_CONFIG['user'] and dept_email:
                dept_body = f"""Dear Department,

A new complaint has been filed that falls under your department.

Ticket: {tid}
Category: {category}
Subject: {subject}
Priority: {priority}
Description: {description[:500]}

Please review and take necessary action.

Regards,
Complainify System"""
                try:
                    send_email_notification(dept_email, f'New Complaint #{tid} — {category}', dept_body)
                except Exception as e:
                    print(f"[EMAIL BLOCK ERROR] {e}")

            if anon:
                flash(f'Anonymous complaint submitted! Your tracking ID: {tid} — save this to check status.', 'success')
            elif student_email_sent:
                flash(f'Complaint submitted! Ticket: {tid} | Category: {category}', 'success')
            else:
                flash(f'Complaint submitted! Ticket: {tid} | Category: {category} — confirmation email could not be sent, you can still track it anytime.', 'warning')
        finally:
            cur.close(); conn.close()
        return redirect(url_for('track_complaint'))
    return render_template('submit_complaint.html', categories=CATEGORIES, colleges=get_colleges())

@app.route('/track', methods=['GET', 'POST'])
def track_complaint():
    result = None
    if request.method == 'POST':
        tid = request.form.get('ticket_id')
        conn = get_db(); cur = conn.cursor()
        cur.execute("""SELECT ticket_id,status,priority,priority_score,priority_reason,category,subject,description,student_attachment,college,
            date_format(created_at,'%%d %%b %%Y') date,
            date_format(assigned_at,'%%d %%b %%Y %%h:%%i %%p') assigned_date,
            date_format(resolved_at,'%%d %%b %%Y %%h:%%i %%p') resolved_date,
            assigned_to,admin_notes,validated
            FROM complaints WHERE ticket_id=%s""", (tid,))
        result = cur.fetchone()
        cur.close(); conn.close()
    return render_template('track.html', result=result)

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        conn = get_db(); cur = conn.cursor()
        cur.execute("SELECT id FROM users WHERE email=%s", (email,))
        user = cur.fetchone()
        if not user:
            flash('No account found with this email.', 'error')
            cur.close(); conn.close()
            return render_template('forgot_password.html')
        otp = str(random.randint(100000, 999999))
        expires = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cur.execute("INSERT INTO otps (email, otp, expires_at) VALUES (%s, %s, DATE_ADD(NOW(), INTERVAL 10 MINUTE))",
            (email, otp))
        conn.commit()
        sent = False
        if SMTP_CONFIG['user'] and SMTP_CONFIG['password']:
            sent = send_email_notification(email, f'Your OTP for Complainify Password Reset',
                f'Your OTP is: {otp}\n\nThis code expires in 10 minutes.\n\nIf you did not request this, ignore this email.')
        cur.close(); conn.close()
        if sent:
            flash(f'OTP sent to {email}. Check your inbox.', 'success')
        else:
            flash(f'OTP: {otp} (Email not configured — use this code)', 'info')
        session['reset_email'] = email
        return redirect(url_for('reset_password'))
    return render_template('forgot_password.html')

@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    email = session.get('reset_email')
    if not email:
        flash('Please request an OTP first.', 'error')
        return redirect(url_for('forgot_password'))
    if request.method == 'POST':
        otp = request.form.get('otp', '').strip()
        new_pw = request.form.get('new_password', '')
        confirm = request.form.get('confirm_password', '')
        if len(new_pw) < 6:
            flash('Password must be at least 6 characters.', 'error')
            return render_template('reset_password.html')
        if new_pw != confirm:
            flash('Passwords do not match.', 'error')
            return render_template('reset_password.html')
        conn = get_db(); cur = conn.cursor()
        cur.execute("SELECT id FROM otps WHERE email=%s AND otp=%s AND used=0 AND expires_at > NOW() ORDER BY id DESC LIMIT 1",
            (email, otp))
        record = cur.fetchone()
        if not record:
            flash('Invalid or expired OTP. Please request a new one.', 'error')
            cur.close(); conn.close()
            return render_template('reset_password.html')
        cur.execute("UPDATE users SET password=%s, plain_password=%s WHERE email=%s",
            (hash_pw(new_pw), new_pw, email))
        cur.execute("UPDATE otps SET used=1 WHERE email=%s AND otp=%s", (email, otp))
        conn.commit()
        cur.close(); conn.close()
        session.pop('reset_email', None)
        flash('Password reset successful! Please login.', 'success')
        return redirect(url_for('student_login'))
    return render_template('reset_password.html')

def login_required(role=None):
    if 'user_id' not in session:
        return False
    if role and session.get('role') != role:
        return False
    return True

# ── STUDENT ROUTES ──

@app.route('/student/login', methods=['GET', 'POST'])
def student_login():
    if 'user_id' in session and session.get('role') == 'student':
        return redirect(url_for('student_dashboard'))
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = hash_pw(request.form.get('password', ''))
        conn = get_db(); cur = conn.cursor()
        cur.execute("SELECT id,fullname,email,password,role,phone,college FROM users WHERE email=%s AND role='student'", (email,))
        user = cur.fetchone()
        if user:
            if user['password'] == password:
                session.permanent = True
                session['user_id'] = user['id']
                session['fullname'] = user['fullname']
                session['email'] = user['email']
                session['phone'] = user.get('phone', '')
                session['college'] = user.get('college') or ''
                session['role'] = 'student'
                cur.close(); conn.close()
                log_action(user['id'], 'login', 'session', '', 'Student login')
                return redirect(url_for('student_dashboard'))
            flash('Incorrect password. Please try again.', 'error')
        else:
            flash('Account not found with this email.', 'error')
        cur.close(); conn.close()
    return render_template('student/login.html')

@app.route('/student/register', methods=['GET', 'POST'])
def student_register():
    colleges = get_colleges()
    if request.method == 'POST':
        fullname = request.form.get('fullname', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        pw = request.form.get('password', '')
        confirm = request.form.get('confirm_password', '')
        college = request.form.get('college', '').strip()
        if not fullname or not email or not phone or not pw:
            flash('All fields are required.', 'error')
            return render_template('student/register.html', colleges=colleges, selected=college)
        if college and college not in colleges:
            flash('Please select a valid college.', 'error')
            return render_template('student/register.html', colleges=colleges, selected=college)
        if '@' not in email:
            flash('Please enter a valid email address.', 'error')
            return render_template('student/register.html', colleges=colleges, selected=college)
        if len(pw) < 6:
            flash('Password must be at least 6 characters.', 'error')
            return render_template('student/register.html', colleges=colleges, selected=college)
        if pw != confirm:
            flash('Passwords do not match.', 'error')
            return render_template('student/register.html', colleges=colleges, selected=college)
        conn = get_db(); cur = conn.cursor()
        try:
            cur.execute("INSERT INTO users (fullname,email,phone,plain_password,password,role,college) VALUES (%s,%s,%s,%s,%s,'student',%s)",
                (fullname, email, phone, pw, hash_pw(pw), college or None))
            conn.commit()
            flash('Registration successful! Please login.', 'success')
        except pymysql.err.IntegrityError:
            flash('Email already registered.', 'error')
            return render_template('student/register.html', colleges=colleges, selected=college)
        finally:
            cur.close(); conn.close()
        return redirect(url_for('student_login'))
    return render_template('student/register.html', colleges=colleges, selected='')

@app.route('/student/dashboard')
def student_dashboard():
    if not login_required('student'):
        return redirect(url_for('student_login'))
    conn = get_db(); cur = conn.cursor()
    cur.execute("""SELECT ticket_id,category,priority,status,subject,sentiment,college,
        date_format(created_at,'%%d %%b %%Y') date,
        assigned_to,validated
        FROM complaints WHERE user_id=%s ORDER BY created_at DESC""", (session['user_id'],))
    complaints = cur.fetchall()
    total = len(complaints)
    resolved = sum(1 for c in complaints if c['status'] == 'Resolved')
    in_progress = sum(1 for c in complaints if c['status'] == 'In Progress')
    pending = total - resolved - in_progress

    cur.execute("""SELECT category, COUNT(*) cnt FROM complaints WHERE user_id=%s GROUP BY category ORDER BY cnt DESC""", (session['user_id'],))
    cat_rows = cur.fetchall()
    student_cat_labels = [r['category'] for r in cat_rows]
    student_cat_values = [r['cnt'] for r in cat_rows]

    cur.execute("""SELECT DATE_FORMAT(created_at, '%%Y-%%m') month, COUNT(*) cnt FROM complaints WHERE user_id=%s GROUP BY month ORDER BY month""", (session['user_id'],))
    trend_rows = cur.fetchall()
    trend_labels = [r['month'] for r in trend_rows]
    trend_values = [r['cnt'] for r in trend_rows]
    cur.close(); conn.close()

    return render_template('student/dashboard.html',
        student_name=session.get('fullname', 'Student'),
        total=total, resolved=resolved, in_progress=in_progress, pending=pending, complaints=complaints,
        student_cat_labels=student_cat_labels, student_cat_values=student_cat_values,
        trend_labels=trend_labels, trend_values=trend_values)

@app.route('/student/complaint/<ticket_id>')
def student_complaint_detail(ticket_id):
    if not login_required('student'):
        return redirect(url_for('student_login'))
    conn = get_db(); cur = conn.cursor()
    cur.execute("""SELECT *,
        date_format(created_at,'%%d %%b %%Y %%h:%%i %%p') created,
        date_format(assigned_at,'%%d %%b %%Y %%h:%%i %%p') assigned_date,
        date_format(resolved_at,'%%d %%b %%Y %%h:%%i %%p') resolved_date
        FROM complaints WHERE ticket_id=%s AND user_id=%s""", (ticket_id, session['user_id']))
    complaint = cur.fetchone()
    if not complaint:
        cur.close(); conn.close()
        flash('Complaint not found.', 'error')
        return redirect(url_for('student_dashboard'))
    cur.execute("""SELECT complaint_comments.*, users.fullname, users.role FROM complaint_comments
        JOIN users ON complaint_comments.user_id=users.id
        WHERE complaint_id=%s ORDER BY complaint_comments.created_at ASC""", (complaint['id'],))
    comments = cur.fetchall()
    cur.close(); conn.close()
    return render_template('student/complaint_detail.html', c=complaint, comments=comments,
        student_name=session.get('fullname', 'Student'))

@app.route('/student/settings', methods=['GET', 'POST'])
def student_settings():
    if not login_required('student'):
        return redirect(url_for('student_login'))
    conn = get_db(); cur = conn.cursor()
    if request.method == 'POST':
        action = request.form.get('action', '')
        if action == 'profile':
            fullname = request.form.get('fullname', '').strip()
            phone = request.form.get('phone', '').strip()
            college = request.form.get('college', '').strip()
            if college and college not in get_colleges():
                college = ''
            if fullname:
                cur.execute("UPDATE users SET fullname=%s, phone=%s, college=%s WHERE id=%s",
                    (fullname, phone, college or None, session['user_id']))
                conn.commit()
                session['fullname'] = fullname
                session['phone'] = phone
                session['college'] = college
                flash('Profile updated!', 'success')
        elif action == 'password':
            current = hash_pw(request.form.get('current_password', ''))
            new_pw = request.form.get('new_password', '')
            confirm = request.form.get('confirm_password', '')
            cur.execute("SELECT password FROM users WHERE id=%s", (session['user_id'],))
            user = cur.fetchone()
            if user and user['password'] != current:
                flash('Current password is incorrect.', 'error')
            elif len(new_pw) < 6:
                flash('New password must be at least 6 characters.', 'error')
            elif new_pw != confirm:
                flash('Passwords do not match.', 'error')
            else:
                cur.execute("UPDATE users SET password=%s, plain_password=%s WHERE id=%s",
                    (hash_pw(new_pw), new_pw, session['user_id']))
                conn.commit()
                flash('Password changed!', 'success')
    cur.execute("SELECT fullname,email,phone,college FROM users WHERE id=%s", (session['user_id'],))
    user = cur.fetchone()
    cur.close(); conn.close()
    return render_template('student/settings.html', user=user, colleges=get_colleges(),
        student_name=session.get('fullname', 'Student'))

# ── ADMIN ROUTES ──

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if 'user_id' in session and session.get('role') == 'admin':
        return redirect(url_for('admin_dashboard'))
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = hash_pw(request.form.get('password', ''))
        conn = get_db(); cur = conn.cursor()
        cur.execute("SELECT id,fullname,email,password,role FROM users WHERE email=%s AND role='admin'", (email,))
        user = cur.fetchone()
        if user:
            if user['password'] == password:
                session.permanent = True
                session['user_id'] = user['id']
                session['fullname'] = user['fullname']
                session['email'] = user['email']
                session['role'] = 'admin'
                cur.close(); conn.close()
                log_action(user['id'], 'login', 'session', '', 'Admin login')
                return redirect(url_for('admin_dashboard'))
            flash('Incorrect password.', 'error')
        else:
            flash('Admin account not found.', 'error')
        cur.close(); conn.close()
    return render_template('admin/login.html')

@app.route('/admin/register', methods=['GET', 'POST'])
def admin_register():
    if request.method == 'POST':
        fullname = request.form.get('fullname', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        pw = request.form.get('password', '')
        confirm = request.form.get('confirm_password', '')
        if not fullname or not email or not phone or not pw:
            flash('All fields are required.', 'error')
            return render_template('admin/register.html')
        if '@' not in email:
            flash('Valid email required.', 'error')
            return render_template('admin/register.html')
        if len(pw) < 6:
            flash('Password must be at least 6 characters.', 'error')
            return render_template('admin/register.html')
        if pw != confirm:
            flash('Passwords do not match.', 'error')
            return render_template('admin/register.html')
        conn = get_db(); cur = conn.cursor()
        try:
            cur.execute("INSERT INTO users (fullname,email,phone,plain_password,password,role) VALUES (%s,%s,%s,%s,%s,'admin')",
                (fullname, email, phone, pw, hash_pw(pw)))
            conn.commit()
            flash('Admin registration successful! Please login.', 'success')
        except pymysql.err.IntegrityError:
            flash('Email already registered.', 'error')
        finally:
            cur.close(); conn.close()
        return redirect(url_for('admin_login'))
    return render_template('admin/register.html')

@app.route('/admin/dashboard')
def admin_dashboard():
    if not login_required('admin'):
        return redirect(url_for('admin_login'))
    conn = get_db(); cur = conn.cursor()
    cur.execute("""SELECT ticket_id,fullname student,category,priority,status,subject,sentiment,
        date_format(created_at,'%d %b %Y') date,
        assigned_to,validated
        FROM complaints ORDER BY created_at DESC""")
    all_complaints = cur.fetchall()
    total = len(all_complaints)
    resolved = sum(1 for c in all_complaints if c['status'] == 'Resolved')
    in_progress = sum(1 for c in all_complaints if c['status'] == 'In Progress')
    pending = total - resolved - in_progress

    cur.execute("SELECT COUNT(*) cnt FROM complaints WHERE status='Resolved' AND resolved_at IS NOT NULL AND TIMESTAMPDIFF(MINUTE, created_at, resolved_at) IS NOT NULL")
    resolved_cnt_row = cur.fetchone()
    resolved_cnt = resolved_cnt_row['cnt'] if resolved_cnt_row else 0
    cur.execute("SELECT COALESCE(AVG(TIMESTAMPDIFF(MINUTE, created_at, resolved_at) / 60.0), 0) avg_hrs FROM complaints WHERE status='Resolved' AND resolved_at IS NOT NULL")
    avg_row = cur.fetchone()
    avg_resolution = round(float(avg_row['avg_hrs']), 1) if avg_row else 0

    cur.execute("SELECT COUNT(*) cnt FROM complaints WHERE priority='High' AND status!='Resolved'")
    critical_row = cur.fetchone()
    critical = critical_row['cnt'] if critical_row else 0

    cur.execute("""SELECT category, COUNT(*) cnt FROM complaints GROUP BY category ORDER BY cnt DESC""")
    cat_rows = cur.fetchall()
    cat_labels = [r['category'] for r in cat_rows]
    cat_values = [r['cnt'] for r in cat_rows]
    cat_total = sum(cat_values) or 1
    cat_pcts = [round(v / cat_total * 100) for v in cat_values]

    cur.execute("""SELECT sentiment, COUNT(*) cnt FROM complaints GROUP BY sentiment""")
    sent_rows = cur.fetchall()
    sent_map = {r['sentiment']: r['cnt'] for r in sent_rows}
    sent_pos = sent_map.get('Positive', 0)
    sent_neg = sent_map.get('Negative', 0)
    sent_neu = sent_map.get('Neutral', 0)

    cur.close(); conn.close()

    train_log = {}
    if os.path.isfile(TRAIN_LOG_PATH):
        try:
            with open(TRAIN_LOG_PATH) as f:
                train_log = json.load(f)
        except Exception as e:
            print(f"[DASHBOARD TRAIN LOG] {e}")

    cards = model_cards()
    try:
        corr = correlation_matrix()
    except Exception as e:
        print(f"[DASHBOARD CORRELATION] {e}")
        corr = None

    return render_template('admin/dashboard.html', total=total, resolved=resolved,
        in_progress=in_progress, pending=pending, critical=critical,
        avg_resolution=avg_resolution,
        cat_labels=cat_labels, cat_values=cat_values, cat_pcts=cat_pcts,
        sent_pos=sent_pos, sent_neg=sent_neg, sent_neu=sent_neu,
        complaints=all_complaints, recent=all_complaints[:10],
        train_log=train_log,
        model_cards=cards, corr=corr,
        admin_name=session.get('fullname', 'Admin'))

@app.route('/admin/complaints')
def admin_complaints():
    if not login_required('admin'):
        return redirect(url_for('admin_login'))
    conn = get_db(); cur = conn.cursor()
    status_filter = request.args.get('status', '')
    category_filter = request.args.get('category', '')
    priority_filter = request.args.get('priority', '')
    sentiment_filter = request.args.get('sentiment', '')
    college_filter = request.args.get('college', '')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    page = int(request.args.get('page', 1))
    per_page = 20
    offset = (page - 1) * per_page
    base_query = "FROM complaints WHERE 1=1"
    params = []
    if status_filter:
        base_query += " AND status=%s"
        params.append(status_filter)
    if category_filter:
        base_query += " AND category=%s"
        params.append(category_filter)
    if priority_filter:
        base_query += " AND priority=%s"
        params.append(priority_filter)
    if sentiment_filter:
        base_query += " AND sentiment=%s"
        params.append(sentiment_filter)
    if college_filter:
        base_query += " AND college=%s"
        params.append(college_filter)
    if date_from:
        base_query += " AND created_at >= %s"
        params.append(date_from)
    if date_to:
        base_query += " AND created_at <= %s 23:59:59"
        params.append(date_to)
    cur.execute(f"SELECT COUNT(*) cnt {base_query}", params)
    total_row = cur.fetchone()
    total_count = total_row['cnt'] if total_row else 0
    total_pages = max(1, (total_count + per_page - 1) // per_page)
    query = f"""SELECT ticket_id,fullname student,category,priority,status,subject,sentiment,college,
        date_format(created_at,'%%d %%b %%Y') date,
        date_format(created_at,'%%Y-%%m-%%d') date_input,
        created_at, assigned_to, validated
        {base_query} ORDER BY created_at DESC LIMIT %s OFFSET %s"""
    cur.execute(query, params + [per_page, offset])
    complaints = cur.fetchall()
    cur.close(); conn.close()
    from datetime import datetime, timedelta
    today = datetime.now().strftime('%Y-%m-%d')
    week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    month_start = datetime.now().replace(day=1).strftime('%Y-%m-%d')
    return render_template('admin/complaints_list.html', complaints=complaints,
        admin_name=session.get('fullname', 'Admin'),
        status_filter=status_filter, category_filter=category_filter,
        priority_filter=priority_filter, sentiment_filter=sentiment_filter,
        college_filter=college_filter,
        date_from=date_from, date_to=date_to,
        today=today, week_ago=week_ago, month_start=month_start,
        page=page, total_pages=total_pages, total_count=total_count,
        colleges=get_colleges(),
        categories=[c for c in CATEGORIES if c != 'Other'])

@app.route('/admin/complaint/<ticket_id>')
def admin_complaint_detail(ticket_id):
    if not login_required('admin'):
        return redirect(url_for('admin_login'))
    conn = get_db(); cur = conn.cursor()
    cur.execute("""SELECT *,
        date_format(created_at,'%%d %%b %%Y %%h:%%i %%p') created,
        date_format(assigned_at,'%%d %%b %%Y %%h:%%i %%p') assigned_date,
        date_format(resolved_at,'%%d %%b %%Y %%h:%%i %%p') resolved_date
        FROM complaints WHERE ticket_id=%s""", (ticket_id,))
    complaint = cur.fetchone()
    if not complaint:
        cur.close(); conn.close()
        flash('Complaint not found.', 'error')
        return redirect(url_for('admin_dashboard'))
    cur.execute("""SELECT complaint_comments.*, users.fullname, users.role FROM complaint_comments
        JOIN users ON complaint_comments.user_id=users.id
        WHERE complaint_id=%s ORDER BY complaint_comments.created_at ASC""", (complaint['id'],))
    comments = cur.fetchall()
    cur.close(); conn.close()
    return render_template('admin/complaint_detail.html', c=complaint, comments=comments,
        admin_name=session.get('fullname', 'Admin'),
        departments=[d for d in CATEGORIES if d != 'Other'])

@app.route('/admin/assign/<ticket_id>', methods=['POST'])
def admin_assign(ticket_id):
    if not login_required('admin'):
        return jsonify({'error': 'Unauthorized'}), 403
    assigned_to = request.form.get('assigned_to', '').strip()
    conn = get_db(); cur = conn.cursor()
    cur.execute("UPDATE complaints SET assigned_to=%s, assigned_at=NOW(), status='In Progress' WHERE ticket_id=%s",
        (assigned_to, ticket_id))
    conn.commit()
    cur.execute("SELECT email, subject, user_id FROM complaints WHERE ticket_id=%s", (ticket_id,))
    c = cur.fetchone()
    cur.close(); conn.close()
    if c and c['email'] and not is_anon_email(c['email']) and SMTP_CONFIG['user']:
        send_email_notification(c['email'],
            f'Complaint {ticket_id} - Assigned to {assigned_to}',
            f'Dear Student,\n\nYour complaint ({ticket_id}) has been assigned to {assigned_to}.\n\nWe will resolve it shortly.\n\nRegards,\nComplainify Team')
    if c and c['user_id']:
        create_notification(c['user_id'], f'Your complaint #{ticket_id} was assigned to {assigned_to}', url_for('student_complaint_detail', ticket_id=ticket_id))
    log_action(session['user_id'], 'assign_complaint', 'complaint', ticket_id, f'Assigned to {assigned_to}')
    flash(f'Assigned to {assigned_to}', 'success')
    return redirect(url_for('admin_complaint_detail', ticket_id=ticket_id))

@app.route('/admin/status/<ticket_id>', methods=['POST'])
def admin_update_status(ticket_id):
    if not login_required('admin'):
        return jsonify({'error': 'Unauthorized'}), 403
    status = request.form.get('status', '')
    admin_notes = request.form.get('admin_notes', '')
    valid_statuses = ['Pending', 'In Progress', 'Resolved']
    if status not in valid_statuses:
        flash('Invalid status.', 'error')
        return redirect(url_for('admin_complaint_detail', ticket_id=ticket_id))
    attachment = request.files.get('attachment')
    attachment_name = None
    if attachment and attachment.filename and '.' in attachment.filename:
        ext = attachment.filename.rsplit('.', 1)[1].lower()
        if ext in ALLOWED_EXTENSIONS:
            unique_name = f"{ticket_id}_{uuid.uuid4().hex[:8]}.{ext}"
            attachment.save(os.path.join(UPLOAD_FOLDER, unique_name))
            attachment_name = unique_name
    conn = get_db(); cur = conn.cursor()
    if attachment_name:
        if status == 'Resolved':
            cur.execute("UPDATE complaints SET status=%s, admin_notes=%s, resolved_at=NOW(), attachment=%s WHERE ticket_id=%s",
                (status, admin_notes, attachment_name, ticket_id))
        else:
            cur.execute("UPDATE complaints SET status=%s, admin_notes=%s, attachment=%s WHERE ticket_id=%s",
                (status, admin_notes, attachment_name, ticket_id))
    else:
        if status == 'Resolved':
            cur.execute("UPDATE complaints SET status=%s, admin_notes=%s, resolved_at=NOW() WHERE ticket_id=%s",
                (status, admin_notes, ticket_id))
        else:
            cur.execute("UPDATE complaints SET status=%s, admin_notes=%s WHERE ticket_id=%s",
                (status, admin_notes, ticket_id))
    conn.commit()
    cur.execute("SELECT email, subject, user_id FROM complaints WHERE ticket_id=%s", (ticket_id,))
    c = cur.fetchone()
    cur.close(); conn.close()
    if c and c['email'] and not is_anon_email(c['email']) and SMTP_CONFIG['user']:
        send_email_notification(c['email'],
            f'Complaint {ticket_id} - Status Updated to {status}',
            f'Dear Student,\n\nYour complaint ({ticket_id}) status has been updated to: {status}.\n\nNotes: {admin_notes or "N/A"}\n\nRegards,\nComplainify Team')
    if c and c['user_id']:
        create_notification(c['user_id'], f'Your complaint #{ticket_id} status: {status}', url_for('student_complaint_detail', ticket_id=ticket_id))
    log_action(session['user_id'], 'update_status', 'complaint', ticket_id, f'Status: {status}')
    flash(f'Status updated to {status}', 'success')
    return redirect(url_for('admin_complaint_detail', ticket_id=ticket_id))

@app.route('/admin/validate/<ticket_id>', methods=['POST'])
def admin_validate(ticket_id):
    if not login_required('admin'):
        return jsonify({'error': 'Unauthorized'}), 403
    conn = get_db(); cur = conn.cursor()
    cur.execute("UPDATE complaints SET validated=1 WHERE ticket_id=%s", (ticket_id,))
    conn.commit()
    cur.execute("SELECT user_id FROM complaints WHERE ticket_id=%s", (ticket_id,))
    c = cur.fetchone()
    cur.close(); conn.close()
    if c and c['user_id']:
        create_notification(c['user_id'], f'Your complaint #{ticket_id} was validated as legitimate', url_for('student_complaint_detail', ticket_id=ticket_id))
    log_action(session['user_id'], 'validate_complaint', 'complaint', ticket_id, '')
    flash('Complaint validated as legitimate.', 'success')
    return redirect(url_for('admin_complaint_detail', ticket_id=ticket_id))

@app.route('/admin/confirm-label/<ticket_id>', methods=['POST'])
def admin_confirm_label(ticket_id):
    """Human confirms (and can correct) the true category.

    Only rows with category_confirmed=1 are eligible for the retraining
    pipeline, so the model never trains on its own auto-predicted labels.
    """
    if not login_required('admin'):
        return jsonify({'error': 'Unauthorized'}), 403
    category = request.form.get('category', '').strip()
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT category FROM complaints WHERE ticket_id=%s", (ticket_id,))
    existing = cur.fetchone()
    if category and existing and category in [d for d in CATEGORIES if d != 'Other']:
        cur.execute("""UPDATE complaints
            SET category=%s, category_confirmed=1, confirmed_by=%s, confirmed_at=NOW()
            WHERE ticket_id=%s""", (category, session.get('fullname', 'Admin'), ticket_id))
    elif existing:
        cur.execute("""UPDATE complaints
            SET category_confirmed=1, confirmed_by=%s, confirmed_at=NOW()
            WHERE ticket_id=%s""", (session.get('fullname', 'Admin'), ticket_id))
    conn.commit()
    cur.close(); conn.close()
    log_action(session['user_id'], 'confirm_label', 'complaint', ticket_id, f'Confirmed category: {category or "unchanged"}')
    flash('Category confirmed for training dataset.', 'success')
    return redirect(url_for('admin_complaint_detail', ticket_id=ticket_id))

@app.route('/admin/resend-email/<ticket_id>', methods=['POST'])
def admin_resend_email(ticket_id):
    if not login_required('admin'):
        return jsonify({'error': 'Unauthorized'}), 403
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT email, ticket_id, status, subject FROM complaints WHERE ticket_id=%s", (ticket_id,))
    c = cur.fetchone()
    if c and c['email'] and not is_anon_email(c['email']) and SMTP_CONFIG['user']:
        send_email_notification(c['email'],
            f'Complaint {ticket_id} - Status: {c["status"]}',
            f'Dear Student,\n\nYour complaint ({ticket_id}) is currently: {c["status"]}.\n\nRegards,\nComplainify Team')
        flash('Email resent.', 'success')
    elif c and c['email'] and is_anon_email(c['email']):
        flash('Anonymous complaint — no student email sent (department mail only).', 'warning')
    else:
        flash('Email not sent (no recipient or no SMTP config).', 'warning')
    cur.close(); conn.close()
    return redirect(url_for('admin_complaint_detail', ticket_id=ticket_id))

@app.route('/admin/settings', methods=['GET', 'POST'])
def admin_settings():
    if not login_required('admin'):
        return redirect(url_for('admin_login'))
    conn = get_db(); cur = conn.cursor()
    if request.method == 'POST':
        action = request.form.get('action', '')
        if action == 'profile':
            fullname = request.form.get('fullname', '').strip()
            phone = request.form.get('phone', '').strip()
            if fullname:
                cur.execute("UPDATE users SET fullname=%s, phone=%s WHERE id=%s",
                    (fullname, phone, session['user_id']))
                conn.commit()
                session['fullname'] = fullname
                flash('Profile updated!', 'success')
        elif action == 'password':
            current = hash_pw(request.form.get('current_password', ''))
            new_pw = request.form.get('new_password', '')
            confirm = request.form.get('confirm_password', '')
            cur.execute("SELECT password FROM users WHERE id=%s", (session['user_id'],))
            user = cur.fetchone()
            if user and user['password'] != current:
                flash('Current password is incorrect.', 'error')
            elif len(new_pw) < 6:
                flash('New password must be at least 6 characters.', 'error')
            elif new_pw != confirm:
                flash('Passwords do not match.', 'error')
            else:
                cur.execute("UPDATE users SET password=%s, plain_password=%s WHERE id=%s",
                    (hash_pw(new_pw), new_pw, session['user_id']))
                conn.commit()
                flash('Password changed!', 'success')
        elif action == 'department_emails':
            dept_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'department_emails.json')
            depts = {}
            for key in request.form:
                if key.startswith('dept_'):
                    cat = key[5:]
                    val = request.form.get(key, '').strip()
                    if val:
                        depts[cat] = val
            with open(dept_file, 'w') as f:
                json.dump(depts, f, indent=2)
            flash('Department emails updated!', 'success')
    cur.execute("SELECT fullname,email,phone FROM users WHERE id=%s", (session['user_id'],))
    user = cur.fetchone()
    cur.close(); conn.close()
    dept_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'department_emails.json')
    dept_emails = {}
    if os.path.isfile(dept_file):
        try:
            with open(dept_file) as f:
                dept_emails = json.load(f)
        except Exception as e:
            print(f"[SETTINGS DEPT EMAILS] {e}")
    for cat in DEPARTMENT_EMAILS:
        dept_emails.setdefault(cat, DEPARTMENT_EMAILS[cat])
    return render_template('admin/settings.html', user=user,
        admin_name=session.get('fullname', 'Admin'), dept_emails=dept_emails)

# ── REPORT & CSV EXPORT ──

@app.route('/admin/analysis')
def admin_analysis():
    if not login_required('admin'):
        return redirect(url_for('admin_login'))
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'ml'))
    import gen_analysis
    try:
        rows = gen_analysis.fetch_rows()
        analysis = gen_analysis.build_analysis(rows)
        analysis['rows'] = len(rows)
    except Exception as e:
        print(f"[ANALYSIS ERROR] {e}")
        cached = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'live_analysis.json')
        analysis = {}
        if os.path.isfile(cached):
            try:
                with open(cached) as f:
                    analysis = json.load(f)
            except Exception as e2:
                print(f"[ANALYSIS CACHE ERROR] {e2}")
        analysis['rows'] = None
        analysis['error'] = str(e)
    return render_template('admin/analysis.html', a=analysis,
        admin_name=session.get('fullname', 'Admin'))

@app.route('/admin/report')
def admin_report():
    if not login_required('admin'):
        return redirect(url_for('admin_login'))
    conn = get_db(); cur = conn.cursor()
    cur.execute("""SELECT ticket_id,fullname student,category,priority,status,subject,
        created_at, assigned_to, validated
        FROM complaints ORDER BY created_at DESC""")
    complaints = cur.fetchall()
    for c in complaints:
        c['date'] = c['created_at'].strftime('%d %b %Y') if c['created_at'] else '-'
    total = len(complaints)
    resolved = sum(1 for c in complaints if c['status'] == 'Resolved')
    in_progress = sum(1 for c in complaints if c['status'] == 'In Progress')
    pending = total - resolved - in_progress
    validated = sum(1 for c in complaints if c['validated'])
    cat_counts = {}
    for c in complaints:
        cat_counts[c['category']] = cat_counts.get(c['category'], 0) + 1
    cat_labels = list(cat_counts.keys())
    cat_values = list(cat_counts.values())

    # Date-based analysis
    from collections import defaultdict
    daily_counts = defaultdict(int)
    monthly_counts = defaultdict(int)
    for c in complaints:
        if c['created_at']:
            day_key = c['created_at'].strftime('%Y-%m-%d')
            month_key = c['created_at'].strftime('%b %Y')
            daily_counts[day_key] += 1
            monthly_counts[month_key] += 1
    daily_labels = sorted(daily_counts.keys())[-30:]
    daily_data = [daily_counts[d] for d in daily_labels]
    month_labels = list(monthly_counts.keys())
    month_data = [monthly_counts[m] for m in month_labels]

    # Resolution time stats
    cur.execute("""SELECT TIMESTAMPDIFF(HOUR, created_at, resolved_at) hrs
        FROM complaints WHERE status='Resolved' AND resolved_at IS NOT NULL""")
    res_times = [r['hrs'] for r in cur.fetchall()]
    avg_res = round(sum(res_times)/len(res_times), 1) if res_times else 0
    max_res = max(res_times) if res_times else 0
    min_res = min(res_times) if res_times else 0

    # Sentiment breakdown
    cur.execute("""SELECT sentiment, COUNT(*) cnt FROM complaints
        WHERE sentiment IN ('Positive','Neutral','Negative') GROUP BY sentiment""")
    sent_data = {r['sentiment']: r['cnt'] for r in cur.fetchall()}
    cur.close(); conn.close()

    # Training dataset analysis
    train_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'train_dataset.csv')
    train_cats = {}
    train_total = 0
    train_lens = []
    train_unique = 0
    try:
        with open(train_path, encoding='utf-8') as f:
            rows = list(csv.DictReader(f))
        train_total = len(rows)
        unique_texts = set()
        for r in rows:
            c = r['category']
            train_cats[c] = train_cats.get(c, 0) + 1
            train_lens.append(len(r['text']))
            unique_texts.add(r['text'])
        train_unique = len(unique_texts)
    except Exception as e:
        print(f"[TRAIN ANALYSIS] {e}")
    train_avg_len = round(sum(train_lens) / len(train_lens)) if train_lens else 0
    train_min_len = min(train_lens) if train_lens else 0
    train_max_len = max(train_lens) if train_lens else 0
    sorted_lens = sorted(train_lens)
    train_median_len = sorted_lens[len(sorted_lens)//2] if sorted_lens else 0
    train_cat_labels = list(train_cats.keys())
    train_cat_values = list(train_cats.values())

    # Training log data for accuracy graph
    train_log_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'ml', 'training_log.json')
    train_log = {}
    if os.path.isfile(train_log_path):
        try:
            with open(train_log_path) as f:
                train_log = json.load(f)
        except Exception as e:
            print(f"[REPORT TRAIN LOG] {e}")

    return render_template('admin/report.html', complaints=complaints,
        total=total, resolved=resolved, in_progress=in_progress, pending=pending, validated=validated,
        cat_labels=cat_labels, cat_values=cat_values,
        train_log=train_log,
        daily_labels=daily_labels, daily_data=daily_data,
        month_labels=month_labels, month_data=month_data,
        avg_res=avg_res, max_res=max_res, min_res=min_res,
        sent_data=sent_data,
        train_total=train_total, train_unique=train_unique,
        train_avg_len=train_avg_len, train_min_len=train_min_len,
        train_max_len=train_max_len, train_median_len=train_median_len,
        train_cat_labels=train_cat_labels, train_cat_values=train_cat_values,
        admin_name=session.get('fullname', 'Admin'))

def _chart_png(kind, **data):
    """Render one chart to PNG bytes (matplotlib Agg, no GUI).

    Supported kinds:
      category   -> bar,  data: labels, values
      sentiment  -> pie,  data: labels, values
      status     -> pie,  data: labels, values
      daily      -> line, data: labels, values
      monthly    -> bar,  data: labels, values
      resolution -> bar,  data: labels, values  (e.g. Avg/Min/Max hours)
      accuracy   -> line, data: labels, values  (accuracy % over time)
    """
    import io
    import matplotlib
    matplotlib.use('Agg')
    from matplotlib import pyplot as plt

    labels = data.get('labels') or []
    values = data.get('values') or []
    if not labels or not values:
        return None
    values = [v if v is not None else 0 for v in values]
    if kind in ('sentiment', 'status') and sum(values) == 0:
        return None

    bar_colors = ['#3b82f6', '#6366f1', '#8b5cf6', '#ec4899', '#f43f5e',
                  '#f59e0b', '#10b981', '#06b6d4', '#94a3b8', '#f97316']
    pie_colors = {
        'Positive': '#10b981', 'Neutral': '#94a3b8', 'Negative': '#ef4444',
        'Pending': '#f59e0b', 'In Progress': '#3b82f6', 'Resolved': '#10b981',
    }

    buf = io.BytesIO()
    fig, ax = plt.subplots(figsize=(10, 4.4), dpi=120)

    if kind in ('category', 'monthly', 'resolution'):
        if len(labels) > len(bar_colors):
            bar_colors = bar_colors * (len(labels) // len(bar_colors) + 1)
        fill = data.get('colors') or bar_colors[:len(labels)]
        bars = ax.bar(labels, values,
                      color=fill,
                      edgecolor='#1e3a8a', linewidth=0.6)
        for b, v in zip(bars, values):
            ax.text(b.get_x() + b.get_width()/2, v + max(values) * 0.01, str(v),
                    ha='center', va='bottom', fontsize=8)
        ax.set_ylabel('Count', fontsize=9)
        ax.tick_params(axis='x', rotation=35, labelsize=8)
        ax.tick_params(axis='y', labelsize=8)
        ax.grid(axis='y', alpha=0.3)
    elif kind in ('sentiment', 'status'):
        c = [pie_colors.get(l.split(' (')[0], '#6366f1') for l in labels]
        wedges, _, autotexts = ax.pie(values, labels=labels, autopct='%1.0f%%',
                                      startangle=90, colors=c,
                                      wedgeprops=dict(width=0.35),
                                      textprops={'fontsize': 9})
        for at in autotexts:
            at.set_color('white'); at.set_fontsize(8); at.set_fontweight('bold')
    else:  # daily / accuracy -> line
        ax.plot(labels, values, marker='o', color='#d32f2f', linewidth=2, markersize=5)
        ax.set_ylabel('Value', fontsize=9)
        ax.tick_params(axis='x', rotation=35, labelsize=8)
        ax.tick_params(axis='y', labelsize=8)
        ax.grid(axis='y', alpha=0.3)
        if kind == 'accuracy':
            ax.set_ylim(0, 100)
            ax.set_ylabel('Accuracy %', fontsize=9)
            if data.get('current') is not None:
                ax.axhline(y=data['current'], color='#0a1628', linestyle='--', linewidth=1)

    ax.set_title(data.get('title', ''), fontsize=12, fontweight='bold', color='#0a1628')
    fig.tight_layout()
    fig.savefig(buf, format='png')
    plt.close(fig)
    buf.seek(0)
    return buf.read()


def _pdf_text(value, maxlen=None):
    """PDF-safe string for fpdf core fonts (latin-1 range).
    Non-latin-1 chars (emoji, CJK, Devanagari, curly quotes...) are replaced with '?'
    so the report always exports instead of crashing with UnicodeEncodeError."""
    if value is None:
        return ''
    s = str(value)
    if maxlen is not None and len(s) > maxlen:
        s = s[:maxlen]
    try:
        s.encode('latin-1')
        return s
    except UnicodeEncodeError:
        return s.encode('latin-1', 'replace').decode('latin-1')


@app.route('/admin/export/pdf')
def admin_export_pdf():
    if not login_required('admin'):
        return redirect(url_for('admin_login'))
    conn = get_db(); cur = conn.cursor()
    status_filter = request.args.get('status', '')
    category_filter = request.args.get('category', '')
    college_filter = request.args.get('college', '')
    base = "FROM complaints WHERE 1=1"
    params = []
    if status_filter:
        base += " AND status=%s"
        params.append(status_filter)
    if category_filter:
        base += " AND category=%s"
        params.append(category_filter)
    if college_filter:
        base += " AND college=%s"
        params.append(college_filter)
    cur.execute(f"SELECT ticket_id,fullname,category,priority,status,subject,sentiment,assigned_to,college,date_format(created_at,'%%d %%b %%Y') created_at {base} ORDER BY created_at DESC", params)
    complaints = cur.fetchall()
    cur.execute(f"SELECT COUNT(*) total, SUM(status='Resolved') resolved, SUM(status='In Progress') in_progress, SUM(status='Pending') pending {base}", params)
    stats = cur.fetchone()
    cur.execute(f"SELECT category, COUNT(*) cnt {base} GROUP BY category", params if params else None)
    cat_rows = cur.fetchall()
    cur.execute("SELECT sentiment, COUNT(*) cnt FROM complaints WHERE sentiment IN ('Positive','Neutral','Negative') GROUP BY sentiment")
    sent_rows = cur.fetchall()
    cur.execute(f"SELECT status, COUNT(*) cnt {base} GROUP BY status", params if params else None)
    status_rows = cur.fetchall()

    # Date-based analysis
    from collections import defaultdict
    cur.execute(f"SELECT created_at {base}", params if params else None)
    date_rows = cur.fetchall()
    daily_counts = defaultdict(int)
    monthly_counts = defaultdict(int)
    for r in date_rows:
        if r['created_at']:
            daily_counts[r['created_at'].strftime('%Y-%m-%d')] += 1
            monthly_counts[r['created_at'].strftime('%b %Y')] += 1
    daily_labels = sorted(daily_counts.keys())[-30:]
    daily_data = [daily_counts[d] for d in daily_labels]
    month_labels = list(monthly_counts.keys())
    month_data = [monthly_counts[m] for m in month_labels]

    # Resolution time stats
    cur.execute("""SELECT TIMESTAMPDIFF(HOUR, created_at, resolved_at) hrs
        FROM complaints WHERE status='Resolved' AND resolved_at IS NOT NULL""")
    res_times = [r['hrs'] for r in cur.fetchall()]
    avg_res = round(sum(res_times)/len(res_times), 1) if res_times else 0
    max_res = max(res_times) if res_times else 0
    min_res = min(res_times) if res_times else 0
    cur.close(); conn.close()

    # Training log for accuracy chart
    train_log = {}
    if os.path.isfile(TRAIN_LOG_PATH):
        try:
            with open(TRAIN_LOG_PATH) as f:
                train_log = json.load(f)
        except Exception as e:
            print(f"[PDF TRAIN LOG] {e}")

    # Build chart PNGs (each chart -> own page in the PDF)
    cat_labels = [r['category'] for r in cat_rows]
    cat_values = [r['cnt'] for r in cat_rows]

    acc_labels = [h['date'] for h in train_log.get('history', []) if h.get('accuracy') is not None]
    acc_values = [h['accuracy'] for h in train_log.get('history', []) if h.get('accuracy') is not None]

    # Match report page graph labels (slice names + counts, same order/colors)
    sent_map = {r['sentiment']: r['cnt'] for r in sent_rows}
    sent_lbl = [f'{s} ({sent_map.get(s, 0)})' for s in ['Positive', 'Neutral', 'Negative']]
    sent_vals = [sent_map.get(s, 0) for s in ['Positive', 'Neutral', 'Negative']]
    status_map = {r['status']: r['cnt'] for r in status_rows}
    status_lbl = [f'{s} ({status_map.get(s, 0)})' for s in ['Pending', 'In Progress', 'Resolved']]
    status_vals = [status_map.get(s, 0) for s in ['Pending', 'In Progress', 'Resolved']]

    # ML Training Dataset analysis (matches report page)
    train_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'train_dataset.csv')
    train_cats = {}
    train_lens = []
    try:
        with open(train_path, encoding='utf-8') as f:
            train_rows = list(csv.DictReader(f))
        for r in train_rows:
            train_cats[r['category']] = train_cats.get(r['category'], 0) + 1
            train_lens.append(len(r['text']))
    except Exception as e:
        print(f"[PDF TRAIN ANALYSIS] {e}")
    train_cat_labels = list(train_cats.keys())
    train_cat_values = list(train_cats.values())
    train_avg_len = round(sum(train_lens) / len(train_lens)) if train_lens else 0
    train_min_len = min(train_lens) if train_lens else 0
    train_max_len = max(train_lens) if train_lens else 0
    sorted_lens = sorted(train_lens)
    train_median_len = sorted_lens[len(sorted_lens)//2] if sorted_lens else 0

    charts = [
        ('category', cat_labels, cat_values, 'Complaint Category Distribution'),
        ('sentiment', sent_lbl, sent_vals, 'Complaint Sentiment Breakdown'),
        ('status', status_lbl, status_vals, 'Complaint Status Breakdown'),
        ('daily', daily_labels, daily_data, 'Daily Complaint Trend (Last 30 Days)'),
        ('monthly', month_labels, month_data, 'Monthly Complaint Trends',
         {'colors': ['#6366f1'] * len(month_labels)}),
        ('resolution', ['Average', 'Fastest', 'Slowest'], [avg_res, min_res, max_res], 'Resolution Time (Hours)'),
    ]
    if train_cat_labels:
        charts.append(('category', train_cat_labels, train_cat_values, 'ML Training Dataset - Category Distribution'))
    if train_lens:
        charts.append(('resolution', ['Min', 'Max', 'Avg', 'Median'],
                       [train_min_len, train_max_len, train_avg_len, train_median_len],
                       'ML Training Dataset - Text Length (Characters)',
                       {'colors': ['#f59e0b', '#ef4444', '#3b82f6', '#10b981']}))
    if len(acc_labels) >= 2:
        charts.append(('accuracy', acc_labels, acc_values, 'Classifier Accuracy Over Time',
                       {'current': train_log.get('accuracy')}))

    import tempfile, os as os_mod
    tmpdir = tempfile.mkdtemp(prefix='complainify_')
    chart_paths = []
    try:
        for idx, (kind, labels, values, title, *extra) in enumerate(charts, start=1):
            kw = dict(title=title)
            if extra:
                kw.update(extra[0])
            png = _chart_png(kind, labels=labels, values=values, **kw)
            if png is None:
                continue
            p = os_mod.path.join(tmpdir, f'chart_{idx}.png')
            with open(p, 'wb') as f:
                f.write(png)
            chart_paths.append((title, p))

        pdf = FPDF(orientation='L', unit='mm', format='A4')
        pdf.set_auto_page_break(auto=True, margin=10)
        pdf.add_page()
        pdf.set_font('Helvetica', 'B', 16)
        pdf.set_text_color(2, 36, 72)
        pdf.cell(0, 10, 'Complainify - Complaint Report', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_font('helvetica', 'I', 7)
        pdf.cell(0, 6, _pdf_text(f'Generated: {datetime.now().strftime("%d %b %Y %I:%M %p")} | Admin: {session.get("fullname", "Admin")}{" | Status: " + status_filter if status_filter else ""}{" | Category: " + category_filter if category_filter else ""}{" | College: " + college_filter if college_filter else ""}'), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(4)
        pdf.set_font('Helvetica', 'B', 10)
        pdf.set_fill_color(2, 36, 72)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(35, 8, 'Ticket', border=1, fill=True)
        pdf.cell(28, 8, 'Student', border=1, fill=True)
        pdf.cell(30, 8, 'Category', border=1, fill=True)
        pdf.cell(18, 8, 'Priority', border=1, fill=True)
        pdf.cell(18, 8, 'Status', border=1, fill=True)
        pdf.cell(22, 8, 'Sentiment', border=1, fill=True)
        pdf.cell(62, 8, 'Subject', border=1, fill=True)
        pdf.cell(35, 8, 'College', border=1, fill=True)
        pdf.cell(25, 8, 'Assigned To', border=1, fill=True)
        pdf.cell(22, 8, 'Date', border=1, fill=True)
        pdf.ln()
        pdf.set_font('Helvetica', '', 8)
        pdf.set_text_color(30, 41, 59)
        for c in complaints:
            row_h = 6
            if pdf.get_y() + row_h > 190:
                pdf.add_page()
                pdf.set_font('Helvetica', 'B', 10)
                pdf.set_fill_color(2, 36, 72)
                pdf.set_text_color(255, 255, 255)
                pdf.cell(35, 8, 'Ticket', border=1, fill=True)
                pdf.cell(28, 8, 'Student', border=1, fill=True)
                pdf.cell(30, 8, 'Category', border=1, fill=True)
                pdf.cell(18, 8, 'Priority', border=1, fill=True)
                pdf.cell(18, 8, 'Status', border=1, fill=True)
                pdf.cell(22, 8, 'Sentiment', border=1, fill=True)
                pdf.cell(62, 8, 'Subject', border=1, fill=True)
                pdf.cell(35, 8, 'College', border=1, fill=True)
                pdf.cell(25, 8, 'Assigned To', border=1, fill=True)
                pdf.cell(22, 8, 'Date', border=1, fill=True)
                pdf.ln()
                pdf.set_font('Helvetica', '', 8)
                pdf.set_text_color(30, 41, 59)
            if c['sentiment'] == 'Negative': pdf.set_text_color(185, 28, 28)
            else: pdf.set_text_color(30, 41, 59)
            pdf.cell(35, row_h, _pdf_text(c['ticket_id']), border=1)
            pdf.cell(28, row_h, _pdf_text(c['fullname'], 15), border=1)
            pdf.cell(30, row_h, _pdf_text(c['category'], 12), border=1)
            pdf.cell(18, row_h, _pdf_text(c['priority']), border=1)
            pdf.cell(18, row_h, _pdf_text(c['status']), border=1)
            pdf.cell(22, row_h, _pdf_text(c['sentiment'] or 'Neutral'), border=1)
            subj = _pdf_text(c['subject'])
            subj = subj[:32] + '...' if len(subj) > 32 else subj
            pdf.cell(62, row_h, subj, border=1)
            pdf.cell(35, row_h, _pdf_text(c['college'] or '-', 16), border=1)
            pdf.cell(25, row_h, _pdf_text(c['assigned_to'] or '-', 12), border=1)
            pdf.cell(22, row_h, _pdf_text(c['created_at']), border=1)
            pdf.ln()

        # ── Each chart on its OWN page ──
        page_w = 297
        margin = 15
        img_w = page_w - margin * 2
        for title, p in chart_paths:
            pdf.add_page()
            pdf.set_font('Helvetica', 'B', 14)
            pdf.set_text_color(2, 36, 72)
            pdf.cell(0, 10, title, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.set_font('helvetica', 'I', 8)
            pdf.set_text_color(100, 116, 139)
            pdf.cell(0, 6, f'Generated: {datetime.now().strftime("%d %b %Y")}', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.ln(3)
            pdf.set_text_color(30, 41, 59)
            pdf.set_font('Helvetica', '', 8)
            pdf.image(p, x=margin, w=img_w)

        # ── Summary statistics page ──
        pdf.add_page()
        pdf.set_font('Helvetica', 'B', 14)
        pdf.set_text_color(2, 36, 72)
        pdf.cell(0, 10, 'Summary Statistics', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(4)
        pdf.set_font('Helvetica', '', 11)
        pdf.set_text_color(30, 41, 59)
        for label, key in [('Total Complaints', 'total'), ('Resolved', 'resolved'), ('In Progress', 'in_progress'), ('Pending', 'pending')]:
            val = stats[key] if stats[key] is not None else 0
            pdf.cell(60, 8, f'{label}: {val}', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(3)
        pdf.cell(60, 8, f'Avg Resolution: {avg_res} hrs', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.cell(60, 8, f'Fastest Resolution: {min_res} hrs', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.cell(60, 8, f'Slowest Resolution: {max_res} hrs', new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        pdf_out = bytes(pdf.output())
        response = make_response(pdf_out)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = 'attachment; filename=complainify_report.pdf'
        return response
    finally:
        import shutil
        shutil.rmtree(tmpdir, ignore_errors=True)

@app.route('/admin/export/csv')
def admin_export_csv():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('admin_login'))
    conn = get_db(); cur = conn.cursor()
    cur.execute("""SELECT ticket_id,fullname,email,category,priority,status,subject,description,
        assigned_to,validated,date_format(created_at,'%%Y-%%m-%%d %%H:%%i:%%s') created_at,
        date_format(resolved_at,'%%Y-%%m-%%d %%H:%%i:%%s') resolved_at
        FROM complaints ORDER BY created_at DESC""")
    rows = cur.fetchall()
    cur.close(); conn.close()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Ticket ID', 'Student Name', 'Email', 'Category', 'Priority', 'Status',
        'Subject', 'Description', 'Assigned To', 'Validated', 'Submitted At', 'Resolved At'])
    for r in rows:
        writer.writerow([r['ticket_id'], r['fullname'], r['email'], r['category'], r['priority'],
            r['status'], r['subject'], r['description'], r['assigned_to'] or '',
            'Yes' if r['validated'] else 'No', r['created_at'], r['resolved_at'] or ''])
    response = app.response_class(
        response=output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=complainify_report.csv'}
    )
    return response

# ── API: Report data (for report.html) ──

@app.route('/admin/report/data')
def admin_report_data():
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT COUNT(*) total, SUM(status='Resolved') resolved, SUM(status='In Progress') in_progress, SUM(status='Pending') pending FROM complaints")
    row = cur.fetchone()
    cur.close(); conn.close()
    return jsonify({'total': row['total'], 'resolved': row['resolved'], 'in_progress': row['in_progress'], 'pending': row['pending']})

# ── API: Auto-categorize ──

@app.route('/api/predict', methods=['POST'])
def api_predict():
    data = request.get_json()
    if not data or 'text' not in data:
        return jsonify({'error': 'No text provided'}), 400
    result = categorize(data['text'])
    return jsonify({
        'category': result['category'],
        'confidence': round(result['confidence'], 4),
        'tier': result['tier'],
        'model_version': model_registry.latest_version_id()
    })

@app.route('/api/models/latest')
def api_model_latest():
    info = model_registry.get_version_info(model_registry.latest_version_id())
    if info is None:
        return jsonify({'error': 'No model registered yet'}), 404
    return jsonify(info)

@app.route('/api/models')
def api_list_models():
    return jsonify({'versions': model_registry.list_versions(),
                    'active': model_registry.latest_version_id()})

@app.route('/api/predict-top3', methods=['POST'])
def api_predict_top3():
    data = request.get_json()
    if not data or 'text' not in data:
        return jsonify({'error': 'No text provided'}), 400
    result = predict_top3(data['text'])
    return jsonify({'predictions': result})

@app.route('/api/analyze', methods=['POST'])
def api_analyze():
    data = request.get_json()
    if not data or 'text' not in data:
        return jsonify({'error': 'No text provided'}), 400
    text = data['text']
    category_result = categorize(text)
    anomaly = detect_anomaly(text)
    sentiment_result = analyze_sentiment(text)
    priority, priority_score, priority_reason = compute_priority(
        text, sentiment_result['label'], sentiment_result['score'], anomaly)
    return jsonify({
        'category': category_result['category'],
        'confidence': round(category_result['confidence'], 4),
        'sentiment': sentiment_result['label'],
        'sentiment_score': round(sentiment_result['score'], 4),
        'priority': priority,
        'priority_score': priority_score,
        'priority_reason': priority_reason,
        'is_anomaly': anomaly['is_anomaly'],
        'anomaly_flags': anomaly['flags']
    })

@app.route('/api/predict-resolution')
def api_predict_resolution():
    conn = get_db(); cur = conn.cursor()
    text = request.args.get('text', '')
    if text:
        result = categorize(text)
        category = result['category']
    else:
        category = request.args.get('category', '')
    priority = request.args.get('priority', 'Medium')
    sentiment = request.args.get('sentiment', 'Neutral')
    cur.execute("""SELECT AVG(TIMESTAMPDIFF(HOUR, created_at, resolved_at)) avg_hrs,
        COUNT(*) samples FROM complaints
        WHERE status='Resolved' AND category=%s AND priority=%s AND sentiment=%s
        AND resolved_at IS NOT NULL""", (category, priority, sentiment))
    row = cur.fetchone()
    if row and row['samples'] >= 3:
        result = {'hours': round(float(row['avg_hrs']), 1), 'samples': row['samples'], 'confidence': 'high'}
    else:
        cur.execute("""SELECT AVG(TIMESTAMPDIFF(HOUR, created_at, resolved_at)) avg_hrs,
            COUNT(*) samples FROM complaints
            WHERE status='Resolved' AND category=%s AND resolved_at IS NOT NULL""", (category,))
        row = cur.fetchone()
        if row and row['samples'] >= 3:
            result = {'hours': round(float(row['avg_hrs']), 1), 'samples': row['samples'], 'confidence': 'medium'}
        else:
            cur.execute("""SELECT AVG(TIMESTAMPDIFF(HOUR, created_at, resolved_at)) avg_hrs,
                COUNT(*) samples FROM complaints
                WHERE status='Resolved' AND resolved_at IS NOT NULL""")
            row = cur.fetchone()
            result = {'hours': round(float(row['avg_hrs'] or 48)), 'samples': row['samples'] if row else 0, 'confidence': 'low'}
    cur.close(); conn.close()
    return jsonify(result)

# ── COMMENTS ──

@app.route('/complaint/<ticket_id>/comment', methods=['POST'])
def add_comment(ticket_id):
    if 'user_id' not in session:
        return redirect(url_for('index'))
    message = request.form.get('message', '').strip()
    if not message:
        flash('Comment cannot be empty.', 'error')
        return redirect(request.referrer or url_for('index'))
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT id, user_id FROM complaints WHERE ticket_id=%s", (ticket_id,))
    complaint = cur.fetchone()
    if not complaint:
        cur.close(); conn.close()
        flash('Complaint not found.', 'error')
        return redirect(url_for('index'))
    cur.execute("INSERT INTO complaint_comments (complaint_id, user_id, message) VALUES (%s, %s, %s)",
        (complaint['id'], session['user_id'], message))
    conn.commit()
    # Notify the other party
    if session['user_id'] != complaint['user_id']:
        create_notification(complaint['user_id'], f'New comment on #{ticket_id}', url_for('student_complaint_detail', ticket_id=ticket_id))
    else:
        conn2 = get_db(); cur2 = conn2.cursor()
        cur2.execute("SELECT id FROM users WHERE role='admin'")
        for admin in cur2.fetchall():
            create_notification(admin['id'], f'New comment on #{ticket_id}', url_for('admin_complaint_detail', ticket_id=ticket_id))
        cur2.close(); conn2.close()
    log_action(session['user_id'], 'add_comment', 'complaint', ticket_id, message[:100])
    cur.close(); conn.close()
    flash('Comment added.', 'success')
    return redirect(request.referrer or url_for('index'))

# ── NOTIFICATIONS API ──

@app.route('/notifications/count')
def notifications_count():
    if 'user_id' not in session:
        return jsonify({'count': 0})
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT COUNT(*) cnt FROM notifications WHERE user_id=%s AND is_read=0", (session['user_id'],))
    row = cur.fetchone()
    cur.close(); conn.close()
    return jsonify({'count': row['cnt'] if row else 0})

@app.route('/notifications')
def notifications_list():
    if 'user_id' not in session:
        return jsonify({'notifications': []})
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT id, message, link, is_read, created_at FROM notifications WHERE user_id=%s ORDER BY created_at DESC LIMIT 20", (session['user_id'],))
    rows = cur.fetchall()
    cur.close(); conn.close()
    return jsonify({'notifications': [{
        'id': r['id'], 'message': r['message'], 'link': r['link'],
        'is_read': bool(r['is_read']),
        'created_at': r['created_at'].strftime('%d %b %Y %I:%M %p') if r['created_at'] else ''
    } for r in rows]})

@app.route('/notifications/mark-read/<int:nid>')
def notifications_mark_read(nid):
    if 'user_id' not in session:
        return jsonify({'ok': False})
    conn = get_db(); cur = conn.cursor()
    cur.execute("UPDATE notifications SET is_read=1 WHERE id=%s AND user_id=%s", (nid, session['user_id']))
    conn.commit(); cur.close(); conn.close()
    return jsonify({'ok': True})

@app.route('/notifications/mark-all-read')
def notifications_mark_all_read():
    if 'user_id' not in session:
        return jsonify({'ok': False})
    conn = get_db(); cur = conn.cursor()
    cur.execute("UPDATE notifications SET is_read=1 WHERE user_id=%s", (session['user_id'],))
    conn.commit(); cur.close(); conn.close()
    return jsonify({'ok': True})

# ── AUDIT LOGS (Admin) ──

@app.route('/admin/audit-logs')
def admin_audit_logs():
    if not login_required('admin'):
        return redirect(url_for('admin_login'))
    conn = get_db(); cur = conn.cursor()
    action_filter = request.args.get('action', '')
    page = int(request.args.get('page', 1))
    per_page = 50
    offset = (page - 1) * per_page
    base = "WHERE 1=1"
    params = []
    if action_filter:
        base += " AND action=%s"
        params.append(action_filter)
    cur.execute(f"SELECT COUNT(*) cnt FROM audit_logs {base}", params)
    total = cur.fetchone()['cnt']
    total_pages = max(1, (total + per_page - 1) // per_page)
    cur.execute(f"""SELECT audit_logs.*, users.fullname FROM audit_logs
        LEFT JOIN users ON audit_logs.user_id=users.id
        {base} ORDER BY created_at DESC LIMIT %s OFFSET %s""", params + [per_page, offset])
    logs = cur.fetchall()
    cur.execute("SELECT DISTINCT action FROM audit_logs ORDER BY action")
    actions = [r['action'] for r in cur.fetchall()]
    cur.close(); conn.close()
    return render_template('admin/audit_logs.html', logs=logs, actions=actions,
        action_filter=action_filter, page=page, total_pages=total_pages, total=total,
        admin_name=session.get('fullname', 'Admin'))

# ── USER MANAGEMENT (Admin) ──

@app.route('/admin/users')
def admin_users():
    if not login_required('admin'):
        return redirect(url_for('admin_login'))
    conn = get_db(); cur = conn.cursor()
    search = request.args.get('search', '')
    role_filter = request.args.get('role', '')
    query = "SELECT u.*, (SELECT COUNT(*) FROM complaints WHERE user_id=u.id) complaint_count FROM users u WHERE 1=1"
    params = []
    if search:
        query += " AND (u.fullname LIKE %s OR u.email LIKE %s OR u.phone LIKE %s)"
        s = f'%{search}%'
        params.extend([s, s, s])
    if role_filter:
        query += " AND u.role=%s"
        params.append(role_filter)
    query += " ORDER BY u.created_at DESC"
    cur.execute(query, params)
    users = cur.fetchall()
    cur.close(); conn.close()
    return render_template('admin/users.html', users=users, search=search, role_filter=role_filter,
        admin_name=session.get('fullname', 'Admin'))

@app.route('/admin/users/reset-password/<int:uid>', methods=['POST'])
def admin_reset_user_password(uid):
    if not login_required('admin'):
        return redirect(url_for('admin_login'))
    new_pw = request.form.get('new_password', '')
    if len(new_pw) < 6:
        flash('Password must be at least 6 characters.', 'error')
        return redirect(url_for('admin_users'))
    conn = get_db(); cur = conn.cursor()
    cur.execute("UPDATE users SET password=%s, plain_password=%s WHERE id=%s",
        (hash_pw(new_pw), new_pw, uid))
    conn.commit(); cur.close(); conn.close()
    log_action(session['user_id'], 'reset_user_password', 'user', str(uid), '')
    flash('Password reset successful.', 'success')
    return redirect(url_for('admin_users'))

@app.route('/admin/users/delete/<int:uid>', methods=['POST'])
def admin_delete_user(uid):
    if not login_required('admin'):
        return redirect(url_for('admin_login'))
    if uid == session['user_id']:
        flash('Cannot delete yourself.', 'error')
        return redirect(url_for('admin_users'))
    conn = get_db(); cur = conn.cursor()
    cur.execute("DELETE FROM users WHERE id=%s", (uid,))
    conn.commit(); cur.close(); conn.close()
    log_action(session['user_id'], 'delete_user', 'user', str(uid), '')
    flash('User deleted.', 'success')
    return redirect(url_for('admin_users'))

# ── RETRAIN & TRAINING LOGS ──

TRAIN_LOG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'ml', 'training_log.json')

@app.route('/admin/training-logs')
def admin_training_logs():
    if not login_required('admin'):
        return redirect(url_for('admin_login'))
    log_data = {}
    try:
        with open(TRAIN_LOG_PATH) as f:
            log_data = json.load(f)
    except Exception as e:
        print(f"[TRAIN LOG LOAD] {e}")
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT COUNT(*) cnt FROM complaints")
    total_complaints = cur.fetchone()['cnt']
    cur.execute("SELECT COUNT(*) cnt FROM complaints WHERE status='Resolved'")
    resolved = cur.fetchone()['cnt']
    cur.close(); conn.close()
    return render_template('admin/training_logs.html', log=log_data,
        total_complaints=total_complaints, resolved=resolved,
        models=model_registry.list_versions(),
        models_active=model_registry.latest_version_id(),
        admin_name=session.get('fullname', 'Admin'))

@app.route('/admin/retrain', methods=['POST'])
def admin_retrain():
    if not login_required('admin'):
        return redirect(url_for('admin_login'))
    import subprocess, sys as sys_mod
    train_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'ml')
    script_path = os.path.join(train_dir, 'retrain.py')
    try:
        result = subprocess.run([sys_mod.executable, script_path], capture_output=True, text=True, timeout=120)
        if result.returncode == 0:
            log_data = json.loads(result.stdout.strip())
            import classifier as clf
            clf._model = None
            acc = log_data.get('accuracy')
            acc_str = f'{acc}%' if acc is not None else 'N/A (too few test samples)'
            f1_str = log_data.get('macro_f1', 'N/A')
            flash(f'Retrain complete! Accuracy: {acc_str}, F1: {f1_str}', 'success')
        else:
            flash(f'Retrain failed: {result.stderr[:500]}', 'error')
    except Exception as e:
        flash(f'Retrain error: {str(e)[:200]}', 'error')
    log_action(session['user_id'], 'retrain_model', 'model', '', '')
    return redirect(url_for('admin_training_logs'))

@app.route('/api/retrain', methods=['POST'])
def api_retrain():
    """JSON endpoint to trigger the retraining pipeline."""
    import subprocess, sys as sys_mod
    train_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'ml')
    script_path = os.path.join(train_dir, 'retrain.py')
    try:
        result = subprocess.run([sys_mod.executable, script_path], capture_output=True, text=True, timeout=180)
        if result.returncode == 0:
            log_data = json.loads(result.stdout.strip())
            import classifier as clf
            clf._model = None
            return jsonify({'status': 'ok', 'log': log_data})
        return jsonify({'status': 'error', 'message': result.stderr[:500]}), 500
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)[:200]}), 500

# ── ANOMALY API ──

@app.route('/api/detect-anomaly', methods=['POST'])
def api_detect_anomaly():
    data = request.get_json()
    if not data or 'text' not in data:
        return jsonify({'error': 'No text provided'}), 400
    result = detect_anomaly(data['text'])
    return jsonify(result)

# ── SIMILAR COMPLAINTS ──

@app.route('/api/similar-complaints', methods=['POST'])
def api_similar_complaints():
    data = request.get_json()
    if not data or 'text' not in data:
        return jsonify({'error': 'No text provided'}), 400
    text = data['text']
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT ticket_id, subject, description, category, status FROM complaints WHERE status='Resolved' ORDER BY created_at DESC LIMIT 500")
    candidates = cur.fetchall()
    cur.close(); conn.close()
    if not candidates:
        return jsonify({'similar': []})
    query_tokens = set(clean_and_tokenize(text, add_bigrams=False))
    scored = []
    for c in candidates:
        candidate_text = (c['subject'] or '') + ' ' + (c['description'] or '')
        candidate_tokens = set(clean_and_tokenize(candidate_text, add_bigrams=False))
        intersection = query_tokens & candidate_tokens
        union = query_tokens | candidate_tokens
        if union:
            similarity = len(intersection) / len(union)
            scored.append((similarity, c))
    scored.sort(key=lambda x: x[0], reverse=True)
    top3 = scored[:3]
    return jsonify({'similar': [{
        'ticket_id': s[1]['ticket_id'],
        'subject': s[1]['subject'],
        'category': s[1]['category'],
        'similarity': round(s[0], 3)
    } for s in top3 if s[0] > 0.05]})

# ── FILE SERVING ──

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

@app.route('/dashboard-redirect')
def dashboard_redirect():
    if session.get('role') == 'admin':
        return redirect(url_for('admin_dashboard'))
    elif session.get('role') == 'student':
        return redirect(url_for('student_dashboard'))
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

def init_db():
    try:
        conn = get_db(); cur = conn.cursor()
        cur.execute("""CREATE TABLE IF NOT EXISTS audit_logs (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT DEFAULT NULL,
            action VARCHAR(100) NOT NULL,
            target_type VARCHAR(50) DEFAULT NULL,
            target_id VARCHAR(50) DEFAULT NULL,
            details TEXT DEFAULT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""")
        cur.execute("""CREATE TABLE IF NOT EXISTS notifications (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            message TEXT NOT NULL,
            link VARCHAR(255) DEFAULT NULL,
            is_read TINYINT(1) DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""")
        cur.execute("""CREATE TABLE IF NOT EXISTS complaint_comments (
            id INT AUTO_INCREMENT PRIMARY KEY,
            complaint_id INT NOT NULL,
            user_id INT NOT NULL,
            message TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""")
        conn.commit()
        cur.close(); conn.close()
    except Exception as e:
        print(f"[INIT DB] {e}")

init_db()

def _scheduled_retrain_worker():
    """Background thread: periodically retrains per RETRAIN_SCHEDULE_HOURS."""
    try:
        hours = int(os.environ.get('RETRAIN_SCHEDULE_HOURS', '0') or '0')
    except ValueError:
        hours = 0
    if hours <= 0:
        return
    import subprocess, sys as sys_mod, time, threading
    train_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'ml')
    script_path = os.path.join(train_dir, 'retrain.py')

    def run():
        while True:
            time.sleep(hours * 3600)
            try:
                subprocess.run([sys_mod.executable, script_path], capture_output=True, text=True, timeout=600)
            except Exception as e:
                print(f"[SCHEDULED RETRAIN] {e}")

    threading.Thread(target=run, daemon=True).start()


if __name__ == '__main__':
    _scheduled_retrain_worker()
    app.run(debug=True)
