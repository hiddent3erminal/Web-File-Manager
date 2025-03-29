from flask import Flask, render_template, send_from_directory, request, redirect, url_for, flash, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os
import logging
import uuid

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = os.getenv('UPLOAD_FOLDER', 'uploads')
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default_secret_key')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URI', 'sqlite:///web_file_manager.db')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB limit

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ensure the uploads folder exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Models
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default='user')  # 'admin' or 'user'

class File(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(200), nullable=False)
    filepath = db.Column(db.String(300), nullable=False)
    uploaded_by = db.Column(db.String(80), nullable=False)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    size = db.Column(db.Integer, nullable=False)
    download_count = db.Column(db.Integer, default=0)
    password = db.Column(db.String(200), nullable=True)  # Optional password for file access

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
@login_required
def home():
    files = os.listdir(app.config['UPLOAD_FOLDER'])
    return render_template('index.html', files=files)

@app.route('/uploads/<filename>')
@login_required
def download(filename):
    try:
        filename = secure_filename(filename)  # Sanitize filename
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
    except FileNotFoundError:
        return "File not found", 404

@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'POST':
        try:
            if 'file' not in request.files:
                flash('No file part')
                return redirect(request.url)
            file = request.files['file']
            if file.filename == '':
                flash('No selected file')
                return redirect(request.url)
            if file:
                filename = secure_filename(file.filename)
                password = request.form.get('password')  # Get password from form
                hashed_password = generate_password_hash(password, method='pbkdf2:sha256') if password else None
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                new_file = File(
                    filename=filename,
                    filepath=filepath,
                    uploaded_by=current_user.username,
                    size=os.path.getsize(filepath),
                    password=hashed_password
                )
                db.session.add(new_file)
                db.session.commit()
                logger.info(f"User {current_user.username} uploaded file {filename}")
                flash('File successfully uploaded')
                return redirect(url_for('home'))
        except Exception as e:
            logger.error(f"Error uploading file: {e}")
            flash('An error occurred while uploading the file')
            return redirect(request.url)
    return render_template('upload.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash('Logged in successfully')
            return redirect(url_for('home'))
        else:
            flash('Invalid username or password')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully')
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Check if the username already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists. Please choose a different one.')
            return redirect(request.url)
        
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash('User registered successfully')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/files')
@login_required
def files():
    user_files = File.query.filter_by(uploaded_by=current_user.username).all()
    return render_template('files.html', files=user_files)

@app.route('/files/sort/<criteria>')
@login_required
def sort_files(criteria):
    if criteria == 'date':
        sorted_files = File.query.filter_by(uploaded_by=current_user.username).order_by(File.upload_date.desc()).all()
    elif criteria == 'size':
        sorted_files = File.query.filter_by(uploaded_by=current_user.username).order_by(File.size.desc()).all()
    elif criteria == 'name':
        sorted_files = File.query.filter_by(uploaded_by=current_user.username).order_by(File.filename.asc()).all()
    else:
        sorted_files = File.query.filter_by(uploaded_by=current_user.username).all()
    return render_template('files.html', files=sorted_files)

@app.route('/files/share/<file_id>')
@login_required
def share_file(file_id):
    file = File.query.get(file_id)
    if file and file.uploaded_by == current_user.username:
        local_ip = request.host.split(':')[0]  # Get local IP address
        shareable_link = f"http://{local_ip}:5000/files/download/{file.id}"  # Generate local network link
        return jsonify({'link': shareable_link})
    else:
        abort(403)

@app.route('/files/download/<file_id>', methods=['GET', 'POST'])
def download_file(file_id):
    file = File.query.get(file_id)
    if file:
        if request.method == 'POST':
            password = request.form.get('password')
            if file.password and not check_password_hash(file.password, password):
                flash('Incorrect password')
                return redirect(request.url)
        file.download_count += 1
        db.session.commit()
        logger.info(f"User {current_user.username} downloaded file {file.filename}")
        return send_from_directory(app.config['UPLOAD_FOLDER'], file.filename)
    else:
        abort(404)

@app.route('/files/delete/<file_id>', methods=['POST'])
@login_required
def delete_file(file_id):
    file = File.query.get(file_id)
    if file and file.uploaded_by == current_user.username:
        try:
            os.remove(file.filepath)  # Delete the file from the filesystem
            db.session.delete(file)  # Remove the file record from the database
            db.session.commit()
            flash('File deleted successfully')
        except Exception as e:
            logger.error(f"Error deleting file: {e}")
            flash('An error occurred while deleting the file')
    else:
        abort(403)
    return redirect(url_for('files'))

@app.route('/files/preview/<file_id>')
@login_required
def preview_file(file_id):
    file = File.query.get(file_id)
    if file and file.uploaded_by == current_user.username:
        if file.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
            return render_template('preview_image.html', file_url=url_for('download', filename=file.filename))
        elif file.filename.lower().endswith('.txt'):
            with open(file.filepath, 'r') as f:
                content = f.read()
            return render_template('preview_text.html', content=content)
        else:
            flash('Preview not supported for this file type')
            return redirect(url_for('files'))
    else:
        abort(403)

@app.route('/files/search', methods=['GET'])
@login_required
def search_files():
    query = request.args.get('q', '').strip()
    user_files = File.query.filter(File.uploaded_by == current_user.username, File.filename.contains(query)).all()
    return render_template('files.html', files=user_files, query=query)

@app.route('/files/page/<int:page>')
@login_required
def paginated_files(page=1):
    per_page = 10  # Number of files per page
    user_files = File.query.filter_by(uploaded_by=current_user.username).paginate(page=page, per_page=per_page)
    return render_template('files_paginated.html', files=user_files.items, pagination=user_files)

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        abort(403)
    users = User.query.all()
    files = File.query.all()
    return render_template('admin_dashboard.html', users=users, files=files)

@app.route('/admin/delete_user/<user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    if current_user.role != 'admin':
        abort(403)
    user = User.query.get(user_id)
    if user:
        db.session.delete(user)
        db.session.commit()
        flash('User deleted successfully')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete_file/<file_id>', methods=['POST'])
@login_required
def admin_delete_file(file_id):
    if current_user.role != 'admin':
        abort(403)
    file = File.query.get(file_id)
    if file:
        try:
            os.remove(file.filepath)  # Delete the file from the filesystem
            db.session.delete(file)  # Remove the file record from the database
            db.session.commit()
            flash('File deleted successfully')
        except Exception as e:
            logger.error(f"Error deleting file: {e}")
            flash('An error occurred while deleting the file')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/activity')
@login_required
def admin_activity():
    if current_user.role != 'admin':
        abort(403)
    activities = File.query.all()  # Fetch all file activities
    return render_template('admin_activity.html', activities=activities)

@app.errorhandler(404)
def not_found_error(error):
    logger.warning(f"404 error: {error}")
    return render_template('404.html'), 404

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Ensure database tables are created
        # Add predefined admin user if not exists
        if not User.query.filter_by(username='admin').first():
            admin_user = User(
                username='admin',
                password=generate_password_hash('admin123', method='pbkdf2:sha256'),
                role='admin'
            )
            db.session.add(admin_user)
            db.session.commit()
            logger.info("Admin user created with username: 'admin' and password: 'admin123'")

    app.run(debug=True)