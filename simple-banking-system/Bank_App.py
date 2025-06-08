import pymysql
import datetime
import streamlit as st

# --- Database connection ---
def connect_db():
    return pymysql.connect(
        host="localhost",
        user="root",
        password="12345678",
        database="Python_Force"
    )

# --- Core logic functions ---

def generate_unique_account_number(cursor):
    import random
    while True:
        acc_num = random.randint(1000000000, 99999999999)
        cursor.execute("SELECT account_number FROM bank_accounts WHERE account_number = %s", (acc_num,))
        if not cursor.fetchone():
            return acc_num

def create_account(name, pin):
    db = connect_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM bank_accounts WHERE owner_name = %s", (name,))
    if cursor.fetchone():
        cursor.close()
        db.close()
        return "Account already exists for this name."
    else:
        account_number = generate_unique_account_number(cursor)
        cursor.execute("""
            INSERT INTO bank_accounts (owner_name, account_number, balance, total_credited, total_withdrawn, pin)
            VALUES (%s, %s, 0.0, 0.0, 0.0, %s)
        """, (name, account_number, pin))
        db.commit()
        cursor.close()
        db.close()
        return f"Account created successfully! Your Account Number is: {account_number}"

def authenticate(acc_num, pin):
    db = connect_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM bank_accounts WHERE account_number = %s AND pin = %s", (acc_num, pin))
    result = cursor.fetchone()
    cursor.close()
    db.close()
    return result is not None

def deposit(acc_num, amount):
    db = connect_db()
    cursor = db.cursor()
    cursor.execute("SELECT balance, total_credited FROM bank_accounts WHERE account_number = %s", (acc_num,))
    result = cursor.fetchone()
    if not result:
        cursor.close()
        db.close()
        return "Account not found."

    new_balance = result[0] + amount
    new_total_credit = result[1] + amount

    cursor.execute("UPDATE bank_accounts SET balance = %s, total_credited = %s WHERE account_number = %s",
                   (new_balance, new_total_credit, acc_num))
    db.commit()
    log_transaction(acc_num, "deposit", amount)
    cursor.close()
    db.close()
    return f"Deposited ₹{amount}. New balance: ₹{new_balance}"

def withdraw(acc_num, amount):
    db = connect_db()
    cursor = db.cursor()
    cursor.execute("SELECT balance, total_withdrawn FROM bank_accounts WHERE account_number = %s", (acc_num,))
    result = cursor.fetchone()
    if not result:
        cursor.close()
        db.close()
        return "Account not found."

    if result[0] >= amount:
        new_balance = result[0] - amount
        new_total_withdraw = result[1] + amount
        cursor.execute("UPDATE bank_accounts SET balance = %s, total_withdrawn = %s WHERE account_number = %s",
                       (new_balance, new_total_withdraw, acc_num))
        db.commit()
        log_transaction(acc_num, "withdraw", amount)
        cursor.close()
        db.close()
        return f"Withdrew ₹{amount}. New balance: ₹{new_balance}"
    else:
        cursor.close()
        db.close()
        return "Insufficient funds."

def transfer(from_acc, to_acc, amount):
    db = connect_db()
    cursor = db.cursor()

    cursor.execute("SELECT balance, owner_name FROM bank_accounts WHERE account_number = %s", (from_acc,))
    sender = cursor.fetchone()
    if not sender:
        cursor.close()
        db.close()
        return "Sender account not found."

    cursor.execute("SELECT balance, owner_name FROM bank_accounts WHERE account_number = %s", (to_acc,))
    receiver = cursor.fetchone()
    if not receiver:
        cursor.close()
        db.close()
        return "Recipient account does not exist."

    if sender[0] < amount:
        cursor.close()
        db.close()
        return "Insufficient funds."

    try:
        cursor.execute(
            "UPDATE bank_accounts SET balance = balance - %s, total_withdrawn = total_withdrawn + %s WHERE account_number = %s",
            (amount, amount, from_acc)
        )
        cursor.execute(
            "UPDATE bank_accounts SET balance = balance + %s, total_credited = total_credited + %s WHERE account_number = %s",
            (amount, amount, to_acc)
        )

        log_transaction(from_acc, "transfer_out", amount, cursor=cursor, db=db)
        log_transaction(to_acc, "transfer_in", amount, cursor=cursor, db=db)

        db.commit()
        cursor.close()
        db.close()
        return f"Transferred ₹{amount} from {sender[1]} - {from_acc} to {receiver[1]} - {to_acc}."

    except Exception as e:
        db.rollback()
        cursor.close()
        db.close()
        return f"Error during transfer: {e}"

def view_account_summary(acc_num):
    db = connect_db()
    cursor = db.cursor()
    cursor.execute("SELECT owner_name, account_number, balance, total_credited, total_withdrawn FROM bank_accounts WHERE account_number = %s", (acc_num,))
    account = cursor.fetchone()
    if not account:
        cursor.close()
        db.close()
        return None, None

    cursor.execute("SELECT transaction_type, amount, transaction_time FROM transactions WHERE account_number = %s ORDER BY transaction_time DESC", (acc_num,))
    transactions = cursor.fetchall()
    cursor.close()
    db.close()
    return account, transactions

def generate_reports():
    db = connect_db()
    cursor = db.cursor()
    cursor.execute("SELECT owner_name, balance FROM bank_accounts ORDER BY balance DESC LIMIT 5")
    top_depositors = cursor.fetchall()
    cursor.execute("SELECT SUM(balance) FROM bank_accounts")
    total_balance = cursor.fetchone()[0]
    cursor.close()
    db.close()
    return top_depositors, total_balance

def check_balance(acc_num):
    db = connect_db()
    cursor = db.cursor()
    cursor.execute("SELECT balance FROM bank_accounts WHERE account_number = %s", (acc_num,))
    result = cursor.fetchone()
    cursor.close()
    db.close()
    if result:
        return result[0]
    else:
        return None

def log_transaction(acc_num, trans_type, amount, cursor=None, db=None):
    need_close = False
    if cursor is None or db is None:
        db = connect_db()
        cursor = db.cursor()
        need_close = True

    cursor.execute("""
        INSERT INTO transactions (account_number, transaction_type, amount, transaction_time)
        VALUES (%s, %s, %s, %s)
    """, (acc_num, trans_type, amount, datetime.datetime.now()))

    if need_close:
        db.commit()
        cursor.close()
        db.close()

# --- Streamlit UI ---

st.set_page_config(page_title="Banking System", layout="centered")
st.title("🏦 Simple Banking System")

menu = [
    "Create Account",
    "Deposit",
    "Withdraw",
    "Transfer Money",
    "Check Balance",
    "View Account Summary",
    "Generate Reports"
]

choice = st.sidebar.selectbox("Choose an Option", menu)

if choice == "Create Account":
    st.header("Create Account")
    name = st.text_input("Owner Name")
    pin = st.text_input("Set 4-digit PIN", type="password")
    if st.button("Create Account"):
        if not name or not pin:
            st.error("Please enter both name and PIN.")
        elif len(pin) != 4 or not pin.isdigit():
            st.error("PIN must be exactly 4 digits.")
        else:
            msg = create_account(name, pin)
            st.success(msg)

elif choice == "Deposit":
    st.header("Deposit Money")
    acc_num = st.text_input("Account Number")
    pin = st.text_input("PIN", type="password")
    amount = st.number_input("Deposit Amount", min_value=0.01, format="%.2f")
    if st.button("Deposit"):
        if not acc_num or not pin:
            st.error("Enter account number and PIN.")
        elif not authenticate(acc_num, pin):
            st.error("Authentication failed.")
        else:
            msg = deposit(acc_num, amount)
            st.success(msg)

elif choice == "Withdraw":
    st.header("Withdraw Money")
    acc_num = st.text_input("Account Number")
    pin = st.text_input("PIN", type="password")
    amount = st.number_input("Withdrawal Amount", min_value=0.01, format="%.2f")
    if st.button("Withdraw"):
        if not acc_num or not pin:
            st.error("Enter account number and PIN.")
        elif not authenticate(acc_num, pin):
            st.error("Authentication failed.")
        else:
            msg = withdraw(acc_num, amount)
            if "Insufficient" in msg:
                st.error(msg)
            else:
                st.success(msg)

elif choice == "Transfer Money":
    st.header("Transfer Money")
    from_acc = st.text_input("Your Account Number (Sender)")
    pin = st.text_input("Your PIN", type="password")
    to_acc = st.text_input("Recipient Account Number")
    amount = st.number_input("Amount to Transfer", min_value=0.01, format="%.2f")
    if st.button("Transfer"):
        if not from_acc or not pin or not to_acc:
            st.error("Please enter all required fields.")
        elif not authenticate(from_acc, pin):
            st.error("Authentication failed.")
        else:
            msg = transfer(from_acc, to_acc, amount)
            if "Error" in msg or "Insufficient" in msg or "not found" in msg:
                st.error(msg)
            else:
                st.success(msg)

elif choice == "Check Balance":
    st.header("Check Balance")
    acc_num = st.text_input("Account Number")
    pin = st.text_input("PIN", type="password")
    if st.button("Check Balance"):
        if not acc_num or not pin:
            st.error("Enter account number and PIN.")
        elif not authenticate(acc_num, pin):
            st.error("Authentication failed.")
        else:
            bal = check_balance(acc_num)
            if bal is None:
                st.error("Account not found.")
            else:
                st.success(f"Your current balance is: ₹{bal}")

elif choice == "View Account Summary":
    st.header("Account Summary")
    acc_num = st.text_input("Account Number")
    pin = st.text_input("PIN", type="password")
    if st.button("View Summary"):
        if not acc_num or not pin:
            st.error("Enter account number and PIN.")
        elif not authenticate(acc_num, pin):
            st.error("Authentication failed.")
        else:
            account, transactions = view_account_summary(acc_num)
            if not account:
                st.error("Account not found.")
            else:
                st.subheader("Account Details")
                st.write(f"Name: {account[0]}")
                st.write(f"Account Number: {account[1]}")
                st.write(f"Balance: ₹{account[2]:.2f}")
                st.write(f"Total Credited: ₹{account[3]:.2f}")
                st.write(f"Total Withdrawn: ₹{account[4]:.2f}")
                st.subheader("Transaction History")
                if transactions:
                    for trans in transactions:
                        st.write(f"{trans[2]} - {trans[0].title()} of ₹{trans[1]:.2f}")
                else:
                    st.write("No transactions found.")

elif choice == "Generate Reports":
    st.header("Bank Reports")
    if st.button("Generate Reports"):
        top_depositors, total_balance = generate_reports()
        st.subheader("Top 5 Depositors")
        for depositor in top_depositors:
            st.write(f"{depositor[0]}: ₹{depositor[1]:.2f}")
        st.write(f"Total Bank Balance: ₹{total_balance:.2f}")
