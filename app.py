import datetime
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash

class BankAccount:
    def __init__(self, initial_balance=0):
        self.balance = float(initial_balance)
        self.history = []
        if self.balance > 0:
            self.add_transaction("Initial deposit", self.balance)

    def get_balance(self):
        return self.balance

    def deposit(self, amount):
        if amount > 0:
            self.balance += amount
            self.add_transaction("Deposit", amount)
            return True
        return False

    def withdraw(self, amount):
        if 0 < amount <= self.balance:
            self.balance -= amount
            self.add_transaction("Withdrawal", -amount)
            return True
        return False

    def get_history(self):
        return self.history

    def add_transaction(self, description, amount):
        transaction = {
            "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "description": description,
            "amount": f"{amount:.2f}"
        }
        self.history.append(transaction)

class User:
    def __init__(self, username, pin, initial_balance=0):
        self.username = username
        self.pin = pin
        self.account = BankAccount(initial_balance)

class ATM:
    def __init__(self):
        self.users = {}

    def add_user(self, username, pin, initial_balance=0):
        if username in self.users:
            return None  # User already exists
        if len(pin) != 4 or not pin.isdigit():
            return False # Invalid PIN
        
        user = User(username, pin, initial_balance)
        self.users[username] = user
        return user

    def authenticate_user(self, username, pin):
        user = self.users.get(username)
        if user and user.pin == pin:
            return user
        return None

app = Flask(__name__)
app.secret_key = 'supersecretkey'
atm = ATM()

# Pre-populate with a user for demonstration
atm.add_user("user1", "1234", 1000)

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        pin = request.form['pin']
        initial_deposit = request.form.get('initial_deposit', 0)

        if not username or not pin:
            flash('Username and PIN are required.', 'danger')
            return redirect(url_for('signup'))
        
        try:
            initial_deposit = float(initial_deposit)
            if initial_deposit < 0:
                flash('Initial deposit cannot be negative.', 'danger')
                return redirect(url_for('signup'))
        except ValueError:
            flash('Invalid initial deposit amount.', 'danger')
            return redirect(url_for('signup'))

        result = atm.add_user(username, pin, initial_deposit)
        if result is None:
            flash('Username already exists.', 'danger')
            return redirect(url_for('signup'))
        elif not result:
            flash('PIN must be 4 digits.', 'danger')
            return redirect(url_for('signup'))
        else:
            flash('Account created successfully! Please log in.', 'success')
            return redirect(url_for('login'))
            
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        pin = request.form['pin']
        user = atm.authenticate_user(username, pin)
        if user:
            session['username'] = user.username
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials.', 'danger')
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))
    user = atm.users.get(session['username'])
    if not user:
        session.pop('username', None)
        return redirect(url_for('login'))
    return render_template('dashboard.html', username=user.username, balance=f"{user.account.get_balance():.2f}")

@app.route('/deposit', methods=['POST'])
def deposit():
    if 'username' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'}), 401
    
    user = atm.users.get(session['username'])
    if not user:
        return jsonify({'success': False, 'message': 'User not found'}), 401

    try:
        amount = float(request.json['amount'])
    except (ValueError, KeyError):
        return jsonify({'success': False, 'message': 'Invalid amount'}), 400

    if user.account.deposit(amount):
        return jsonify({'success': True, 'balance': f"{user.account.get_balance():.2f}", 'message': 'Deposit successful.'})
    else:
        return jsonify({'success': False, 'message': 'Deposit amount must be positive.'}), 400

@app.route('/withdraw', methods=['POST'])
def withdraw():
    if 'username' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'}), 401

    user = atm.users.get(session['username'])
    if not user:
        return jsonify({'success': False, 'message': 'User not found'}), 401

    try:
        amount = float(request.json['amount'])
    except (ValueError, KeyError):
        return jsonify({'success': False, 'message': 'Invalid amount'}), 400

    if user.account.withdraw(amount):
        return jsonify({'success': True, 'balance': f"{user.account.get_balance():.2f}", 'message': 'Withdrawal successful.'})
    else:
        return jsonify({'success': False, 'message': 'Insufficient funds or invalid amount.'}), 400

@app.route('/history')
def history():
    if 'username' not in session:
        return redirect(url_for('login'))
    user = atm.users.get(session['username'])
    if not user:
        session.pop('username', None)
        return redirect(url_for('login'))
    return render_template('history.html', history=user.account.get_history())

@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)
