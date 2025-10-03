from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-fallback-secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///messages.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

#Admin credentials
ADMIN_USERNAME = 'Andile'
ADMIN_PASSWORD = '2010'

#Database Model
class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Message {self.id} from {self.name}>'

#Create tables
with app.app_context():
    db.create_all()

# Routes
@app.route('/')
@app.route('/home')
def home():
    return render_template('home.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/certificates')
def certificates():
    return render_template('certificates.html')

@app.route('/testimonials')
def testimonials():
    return render_template('testimonials.html')

@app.route('/feedback', methods=['GET', 'POST'])
def feedback():
    if request.method == 'POST':
        try:
            name = request.form.get('name', '').strip()
            email = request.form.get('email', '').strip()
            subject = request.form.get('subject', '').strip()
            message = request.form.get('message', '').strip()

            if not all([name, email, subject, message]):
                flash('All fields are required', 'error')
                return redirect(url_for('fail'))

            new_message = Message(
                name=name, 
                email=email, 
                subject=subject, 
                message=message
            )
            db.session.add(new_message)
            db.session.commit()
            
            return redirect(url_for('sent'))
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred: {str(e)}', 'error')
            return redirect(url_for('fail'))
    
    return render_template('feedback.html')

@app.route('/sent')
def sent():
    return render_template('sent.html')

@app.route('/fail')
def fail():
    return render_template('fail.html')

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if session.get('admin_logged_in'):
        return redirect(url_for('admin_dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            flash('Login successful', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid username or password', 'error')
            return redirect(url_for('admin_login'))
    
    return render_template('login.html')

@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('admin_logged_in'):
        flash('Please login to access the admin dashboard', 'error')
        return redirect(url_for('admin_login'))
    
    # Get all messages ordered by newest first
    messages = Message.query.order_by(Message.created_at.desc()).all()
    
    # Count unread messages
    unread_count = Message.query.filter_by(is_read=False).count()
    
    return render_template('admin.html', messages=messages, unread_count=unread_count)

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    flash('You have been logged out', 'success')
    return redirect(url_for('home'))

@app.route('/admin/delete/<int:id>')
def delete_message(id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    try:
        message = Message.query.get_or_404(id)
        db.session.delete(message)
        db.session.commit()
        flash('Message deleted successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting message: {str(e)}', 'error')
    
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/mark-read/<int:id>')
def mark_read(id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    try:
        message = Message.query.get_or_404(id)
        message.is_read = True
        db.session.commit()
        flash('Message marked as read', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error: {str(e)}', 'error')
    
    return redirect(url_for('admin_dashboard'))

@app.route('/api/unread-count')
def unread_count():
    count = Message.query.filter_by(is_read=False).count()
    return {'unread': count}

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)