import random
from datetime import datetime, timedelta
from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user
from extensions import db, bcrypt
from models.user import User

auth_bp = Blueprint('auth', __name__)


# ── Helpers ────────────────────────────────────────────────────────────────────
def _admin_required():
    if not current_user.is_admin:
        flash('Access denied. Admin rights required.', 'danger')
        return False
    return True

import resend
from flask import current_app

def _send_otp_email(user_email, otp, username):
    try:
        resend.api_key = current_app.config.get('RESEND_API_KEY')
        sender_email = current_app.config.get('MAIL_DEFAULT_SENDER', 'onboarding@resend.dev')
        
        html_body = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2>Optical ERP - Password Reset</h2>
            <p>Hello {username},</p>
            <p>Your OTP for password reset is:</p>
            <h1 style="background: #f4f4f4; padding: 10px; border-radius: 5px; text-align: center; letter-spacing: 5px;">{otp}</h1>
            <p>This OTP is valid for 10 minutes.</p>
            <p style="color: #888; font-size: 12px; margin-top: 20px;">If you did not request this, you can safely ignore this email.</p>
        </div>
        """
        
        params = {
            "from": f"Optical ERP <{sender_email}>",
            "to": [user_email],
            "subject": "Optical ERP — Your OTP for Password Reset",
            "html": html_body
        }
        
        email = resend.Emails.send(params)
        print(f"Resend accepted email: {email}")
        return True
        
    except Exception as e:
        print(f"Resend API error: {e}")
        return False


# ── Index ──────────────────────────────────────────────────────────────────────
@auth_bp.route('/', methods=['GET'])
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    return redirect(url_for('auth.login'))


# ── Login ──────────────────────────────────────────────────────────────────────
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        user = User.query.filter_by(username=username).first()
        if user and bcrypt.check_password_hash(user.password_hash, password):
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(request.args.get('next') or url_for('dashboard.index'))
        flash('Invalid username or password.', 'danger')
    return render_template('auth/login.html')


# ── Logout ─────────────────────────────────────────────────────────────────────
@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))


# ══════════════════════════════════════════════════════════════════════════════
#  FORGOT PASSWORD — OTP Flow
#  Step 1: Enter username → OTP sent to registered email
#  Step 2: Enter OTP + new password → done
# ══════════════════════════════════════════════════════════════════════════════

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        user = User.query.filter_by(username=username).first()

        if not user:
            flash('No account found with that username.', 'danger')
            return redirect(url_for('auth.forgot_password'))

        if not user.email:
            flash('No email is registered for this account. Ask your admin to set one.', 'warning')
            return redirect(url_for('auth.forgot_password'))

        # Generate 6-digit OTP
        otp = str(random.randint(100000, 999999))
        user.otp = otp
        user.otp_expiry = datetime.utcnow() + timedelta(minutes=10)
        db.session.commit()

        sent = _send_otp_email(user.email, otp, user.username)

        if not sent:
            flash('Could not send OTP email. Check MAIL_* environment variables.', 'warning')
            return redirect(url_for('auth.forgot_password'))

        # Store username in session to carry to verify page
        session['otp_username'] = username
        flash(f'OTP sent to your registered email. Valid for 10 minutes.', 'info')
        return redirect(url_for('auth.verify_otp'))

    return render_template('auth/forgot_password.html')


@auth_bp.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    username = session.get('otp_username')
    if not username:
        flash('Session expired. Please start again.', 'warning')
        return redirect(url_for('auth.forgot_password'))

    user = User.query.filter_by(username=username).first()
    if not user:
        flash('Invalid session. Please start again.', 'danger')
        return redirect(url_for('auth.forgot_password'))

    if request.method == 'POST':
        entered_otp = request.form.get('otp', '').strip()
        new_password = request.form.get('new_password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()

        # Validate OTP
        if not user.otp or not user.otp_expiry:
            flash('No OTP found. Please request again.', 'danger')
            return redirect(url_for('auth.forgot_password'))

        if datetime.utcnow() > user.otp_expiry:
            flash('OTP has expired. Please request a new one.', 'danger')
            user.otp = None
            user.otp_expiry = None
            db.session.commit()
            return redirect(url_for('auth.forgot_password'))

        if entered_otp != user.otp:
            flash('Incorrect OTP. Please try again.', 'danger')
            return render_template('auth/verify_otp.html', username=username)

        # Validate new password
        if len(new_password) < 6:
            flash('Password must be at least 6 characters.', 'warning')
            return render_template('auth/verify_otp.html', username=username)

        if new_password != confirm_password:
            flash('Passwords do not match.', 'warning')
            return render_template('auth/verify_otp.html', username=username)

        # All good — update password
        user.password_hash = bcrypt.generate_password_hash(new_password).decode('utf-8')
        user.otp = None
        user.otp_expiry = None
        db.session.commit()
        session.pop('otp_username', None)

        flash('Password updated successfully! Please log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/verify_otp.html', username=username)


# ══════════════════════════════════════════════════════════════════════════════
#  ADMIN — USER MANAGEMENT
# ══════════════════════════════════════════════════════════════════════════════

@auth_bp.route('/users')
@login_required
def manage_users():
    if not _admin_required():
        return redirect(url_for('dashboard.index'))
    page = request.args.get('page', 1, type=int)
    users = User.query.order_by(User.created_at.desc()).paginate(page=page, per_page=20)
    return render_template('auth/manage_users.html', users=users)


@auth_bp.route('/users/add', methods=['POST'])
@login_required
def add_user():
    if not _admin_required():
        return redirect(url_for('dashboard.index'))

    username = request.form.get('username', '').strip()
    email = request.form.get('email', '').strip() or None
    password = request.form.get('password', '')
    role = request.form.get('role', 'staff')

    if User.query.filter_by(username=username).first():
        flash('Username already exists.', 'warning')
        return redirect(url_for('auth.manage_users'))

    if email and User.query.filter_by(email=email).first():
        flash('Email already registered.', 'warning')
        return redirect(url_for('auth.manage_users'))

    hashed = bcrypt.generate_password_hash(password).decode('utf-8')
    new_user = User(username=username, email=email, password_hash=hashed, role=role)
    db.session.add(new_user)
    db.session.commit()
    flash(f'User "{username}" created successfully!', 'success')
    return redirect(url_for('auth.manage_users'))


@auth_bp.route('/users/edit/<int:id>', methods=['POST'])
@login_required
def edit_user(id):
    if not _admin_required():
        return redirect(url_for('dashboard.index'))

    user = User.query.get_or_404(id)
    new_username = request.form.get('username', '').strip()
    new_email = request.form.get('email', '').strip() or None
    new_role = request.form.get('role', user.role)
    new_password = request.form.get('new_password', '').strip()

    # Check username conflict (ignore self)
    existing = User.query.filter_by(username=new_username).first()
    if existing and existing.id != user.id:
        flash('Username already taken by another user.', 'warning')
        return redirect(url_for('auth.manage_users'))

    # Check email conflict (ignore self)
    if new_email:
        existing_email = User.query.filter_by(email=new_email).first()
        if existing_email and existing_email.id != user.id:
            flash('Email already in use by another user.', 'warning')
            return redirect(url_for('auth.manage_users'))

    user.username = new_username
    user.email = new_email
    user.role = new_role

    if new_password:
        if len(new_password) < 6:
            flash('Password must be at least 6 characters.', 'warning')
            return redirect(url_for('auth.manage_users'))
        user.password_hash = bcrypt.generate_password_hash(new_password).decode('utf-8')

    db.session.commit()
    flash(f'User "{user.username}" updated successfully!', 'success')
    return redirect(url_for('auth.manage_users'))


@auth_bp.route('/users/delete/<int:id>', methods=['POST'])
@login_required
def delete_user(id):
    if not _admin_required():
        return redirect(url_for('dashboard.index'))

    user = User.query.get_or_404(id)
    if user.id == current_user.id:
        flash('You cannot delete your own account.', 'warning')
        return redirect(url_for('auth.manage_users'))

    username = user.username
    db.session.delete(user)
    db.session.commit()
    flash(f'User "{username}" deleted.', 'success')
    return redirect(url_for('auth.manage_users'))
