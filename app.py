import os
import random
import smtplib
import tkinter as tk
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from tkinter import messagebox, ttk

from email.message import EmailMessage

from config import (
    SHOP_NAME, CURRENCY,
    LOW_STOCK_LIMIT, EXPIRY_WARNING_DAYS, EMAIL_ADDRESS, EMAIL_PASSWORD
)
from database import fetch_all, fetch_one, execute, get_connection
from invoice import create_invoice

BG = "#f3f6f8"
NAVY = "#123b56"
BLUE = "#2563eb"
GREEN = "#16834f"
GRAY = "#64748b"
WHITE = "#ffffff"
RED = "#dc2626"
LIGHT_BLUE = "#e9f2ff"
LIGHT_GREEN = "#eaf8f0"


MAX_LOGIN_ATTEMPTS = 3
OTP_VALID_MINUTES = 5


class LoginFrame(tk.Frame):
    def __init__(self, master, on_login, on_forgot, on_otp_login):
        super().__init__(master, bg=BG)
        self.on_login = on_login
        self.on_forgot = on_forgot
        self.on_otp_login = on_otp_login
        self.attempts_left = MAX_LOGIN_ATTEMPTS
        self._build()

    def _build(self):
        card = tk.Frame(self, bg=WHITE, bd=1, relief="solid", padx=42, pady=30)
        card.place(relx=0.5, rely=0.5, anchor="center", width=460, height=560)

        tk.Label(card, text="💊", bg=WHITE, fg=GREEN,
                 font=("Segoe UI Emoji", 34)).pack(pady=(0, 4))
        tk.Label(card, text=SHOP_NAME, bg=WHITE, fg=NAVY,
                 font=("Segoe UI", 22, "bold")).pack()
        tk.Label(card, text="Owner Login System", bg=WHITE, fg=GRAY,
                 font=("Segoe UI", 11)).pack(pady=(3, 20))

        self.user_var = tk.StringVar()
        self.pass_var = tk.StringVar()
        self.status_var = tk.StringVar(
            value=f"Login attempts remaining: {self.attempts_left}"
        )

        tk.Label(card, text="Username", bg=WHITE, fg="#1f2937",
                 font=("Segoe UI", 10, "bold"), anchor="w").pack(fill="x")
        self.user_entry = ttk.Entry(card, textvariable=self.user_var,
                                    font=("Segoe UI", 11))
        self.user_entry.pack(fill="x", pady=(5, 12), ipady=5)

        tk.Label(card, text="Password", bg=WHITE, fg="#1f2937",
                 font=("Segoe UI", 10, "bold"), anchor="w").pack(fill="x")
        self.pass_entry = ttk.Entry(card, textvariable=self.pass_var, show="*",
                                    font=("Segoe UI", 11))
        self.pass_entry.pack(fill="x", pady=(5, 8), ipady=5)

        tk.Label(card, textvariable=self.status_var, bg=WHITE, fg=RED,
                 font=("Segoe UI", 9, "bold"), wraplength=360).pack(anchor="w", pady=(0, 10))

        self.login_button = tk.Button(
            card, text="LOGIN", command=self.login,
            bg=BLUE, fg=WHITE, activebackground=BLUE,
            activeforeground=WHITE, font=("Segoe UI", 11, "bold"),
            relief="flat", bd=0, cursor="hand2", height=2
        )
        self.login_button.pack(fill="x", pady=(0, 8))

        # This option becomes available only after all password attempts are used.
        self.otp_login_button = tk.Button(
            card, text="Login with OTP", command=self.on_otp_login,
            bg=LIGHT_GREEN, fg=GREEN, activebackground="#d8f3e5",
            activeforeground=GREEN, font=("Segoe UI", 10, "bold"),
            relief="flat", bd=0, cursor="hand2", height=2,
            state="disabled"
        )
        self.otp_login_button.pack(fill="x", pady=(0, 8))

        self.forgot_button = tk.Button(
            card, text="Forgot Password?", command=self.on_forgot,
            bg=WHITE, fg=BLUE, activebackground=LIGHT_BLUE,
            activeforeground=BLUE, font=("Segoe UI", 10, "bold"),
            relief="flat", bd=0, cursor="hand2"
        )
        self.forgot_button.pack(pady=(0, 12))

        tk.Label(card, text="Demo Login", bg=WHITE, fg=GRAY,
                 font=("Segoe UI", 9, "bold")).pack()
        tk.Label(card, text="Username: pushkar", bg=WHITE, fg=GRAY,
                 font=("Segoe UI", 9)).pack()
        tk.Label(card, text="Password: 1234", bg=WHITE, fg=GRAY,
                 font=("Segoe UI", 9)).pack()

        self.bind_all("<Return>", self._enter_login, add="+")

    def _enter_login(self, event=None):
        if self.winfo_exists():
            self.login()

    def login(self):
        if self.attempts_left <= 0:
            messagebox.showwarning(
                "Password Login Locked",
                "Password login attempts are exhausted.\n\n"
                "Use 'Login with OTP' to continue."
            )
            return

        username = self.user_var.get().strip()
        password = self.pass_var.get()

        if not username or not password:
            messagebox.showwarning("Missing Details", "Enter username and password.")
            return

        try:
            user = fetch_one(
                "SELECT * FROM owners WHERE username=%s AND password=%s",
                (username, password)
            )
        except Exception as exc:
            messagebox.showerror(
                "Database Error",
                f"Unable to access MySQL.\n\n{exc}"
            )
            return

        if user:
            self.attempts_left = MAX_LOGIN_ATTEMPTS
            self.on_login(user)
            return

        self.attempts_left -= 1
        self.status_var.set(
            f"Login attempts remaining: {self.attempts_left}"
        )

        if self.attempts_left == 0:
            self.login_button.config(state="disabled")
            self.otp_login_button.config(state="normal")
            self.status_var.set(
                "Password attempts exhausted. Use Login with OTP to continue."
            )
            messagebox.showwarning(
                "Password Login Locked",
                "You have used all 3 password attempts.\n\n"
                "The 'Login with OTP' option is now available."
            )
        else:
            # Automatically refresh the login inputs after an incorrect attempt.
            # The remaining-attempt counter is preserved.
            self.pass_var.set("")
            self.status_var.set(
                f"Incorrect username or password. Attempts remaining: {self.attempts_left}"
            )
            self.user_entry.focus_set()
            self.user_entry.selection_range(0, tk.END)
            messagebox.showerror(
                "Login Failed",
                "Invalid username or password.\n\n"
                "The login fields have been refreshed for your next attempt."
            )

    def destroy(self):
        try:
            self.unbind_all("<Return>")
        except Exception:
            pass
        super().destroy()


class OTPLoginFrame(tk.Frame):
    """OTP login screen used after the password-attempt limit is reached."""

    def __init__(self, master, on_login, on_back):
        super().__init__(master, bg=BG)
        self.on_login = on_login
        self.on_back = on_back
        self.otp = None
        self.otp_expires = None
        self.owner = None
        self._build()

    def _build(self):
        card = tk.Frame(self, bg=WHITE, bd=1, relief="solid", padx=42, pady=30)
        card.place(relx=0.5, rely=0.5, anchor="center", width=500, height=500)

        tk.Label(card, text="🔐", bg=WHITE, fg=GREEN,
                 font=("Segoe UI Emoji", 34)).pack(pady=(0, 4))
        tk.Label(card, text=SHOP_NAME, bg=WHITE, fg=NAVY,
                 font=("Segoe UI", 22, "bold")).pack()
        tk.Label(card, text="Login with OTP", bg=WHITE, fg=GRAY,
                 font=("Segoe UI", 11)).pack(pady=(3, 20))

        self.identity_var = tk.StringVar()
        self.otp_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Enter your username or registered email.")

        tk.Label(card, text="Username or Registered Email", bg=WHITE, fg="#1f2937",
                 font=("Segoe UI", 10, "bold"), anchor="w").pack(fill="x")
        ttk.Entry(card, textvariable=self.identity_var,
                  font=("Segoe UI", 11)).pack(fill="x", pady=(5, 14), ipady=5)

        ttk.Button(card, text="Send OTP", command=self.send_otp).pack(fill="x", ipady=6)

        tk.Label(card, text="OTP", bg=WHITE, fg="#1f2937",
                 font=("Segoe UI", 10, "bold"), anchor="w").pack(fill="x", pady=(16, 0))
        ttk.Entry(card, textvariable=self.otp_var,
                  font=("Segoe UI", 11)).pack(fill="x", pady=(5, 10), ipady=5)

        tk.Label(card, textvariable=self.status_var, bg=WHITE, fg=GRAY,
                 wraplength=390, justify="left", font=("Segoe UI", 9)).pack(anchor="w", pady=(2, 12))

        ttk.Button(card, text="Verify OTP & Login", command=self.verify_otp).pack(fill="x", ipady=6)
        ttk.Button(card, text="Back to Password Login", command=self.on_back).pack(fill="x", pady=10, ipady=4)

    def send_otp(self):
        identity = self.identity_var.get().strip()
        if not identity:
            messagebox.showwarning("Missing Details", "Enter username or registered email.")
            return

        try:
            owner = fetch_one(
                "SELECT * FROM owners WHERE username=%s OR LOWER(email)=LOWER(%s) LIMIT 1",
                (identity, identity)
            )
        except Exception as exc:
            messagebox.showerror("Database Error", f"Unable to access MySQL.\n\n{exc}")
            return

        if not owner:
            messagebox.showerror("Account Not Found", "No owner account matches that username or email.")
            return

        receiver_email = owner.get("email")
        if not receiver_email:
            messagebox.showerror("Email Error", "No registered email is available for this owner account.")
            return

        self.otp = str(random.randint(100000, 999999))
        self.owner = owner

        try:
            msg = EmailMessage()
            msg["Subject"] = f"{SHOP_NAME} - Login OTP"
            msg["From"] = EMAIL_ADDRESS
            msg["To"] = receiver_email
            msg.set_content(
                f"Hello {owner.get('name') or owner.get('username') or 'Owner'},\n\n"
                f"Your Medi-Track login OTP is: {self.otp}\n\n"
                f"This OTP is valid for {OTP_VALID_MINUTES} minutes.\n\n"
                "If you did not request this OTP, please ignore this email.\n\n"
                f"Regards,\n{SHOP_NAME}"
            )

            with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=20) as smtp:
                smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
                smtp.send_message(msg)

        except Exception as exc:
            self.otp = None
            messagebox.showerror(
                "OTP Email Failed",
                "The OTP could not be sent to the registered email.\n\n"
                f"Error: {exc}\n\n"
                "Check EMAIL_ADDRESS and your Gmail App Password in config.py."
            )
            return

        self.otp_expires = datetime.now() + timedelta(minutes=OTP_VALID_MINUTES)
        self.status_var.set(
            f"OTP sent to {receiver_email} | Valid for {OTP_VALID_MINUTES} minutes"
        )
        messagebox.showinfo(
            "OTP Sent",
            f"OTP has been sent to {receiver_email}.\n\n"
            f"It is valid for {OTP_VALID_MINUTES} minutes."
        )

    def verify_otp(self):
        entered = self.otp_var.get().strip()

        if not self.owner or not self.otp:
            messagebox.showwarning("OTP Required", "Click Send OTP first.")
            return

        if datetime.now() > self.otp_expires:
            self.otp = None
            self.otp_expires = None
            messagebox.showerror("OTP Expired", "This OTP has expired. Generate a new OTP.")
            return

        if entered != self.otp:
            messagebox.showerror("Invalid OTP", "The OTP is incorrect.")
            return

        messagebox.showinfo("OTP Login Successful", "OTP verified successfully.")
        self.otp = None
        self.otp_expires = None
        self.on_login(self.owner)


class ForgotPasswordFrame(tk.Frame):
    def __init__(self, master, on_back):
        super().__init__(master, bg=BG)
        self.on_back = on_back
        self.otp = None
        self.otp_expires = None
        self.verified_email = None
        self._build()

    def _build(self):
        card = tk.Frame(self, bg=WHITE, bd=1, relief="solid", padx=38, pady=30)
        card.place(relx=0.5, rely=0.5, anchor="center", width=500, height=500)
        tk.Label(card, text="Reset Password", bg=WHITE, fg=NAVY,
                 font=("Segoe UI", 22, "bold")).pack(anchor="w")
        tk.Label(card, text="Email verification", bg=WHITE, fg=GRAY,
                 font=("Segoe UI", 10)).pack(anchor="w", pady=(3, 22))

        self.email_var = tk.StringVar()
        self.otp_var = tk.StringVar()
        self.new_pass_var = tk.StringVar()
        self.confirm_var = tk.StringVar()
        self.otp_status = tk.StringVar(value="OTP not generated")

        for title, var in [("Registered Email", self.email_var), ("OTP", self.otp_var),
                           ("New Password", self.new_pass_var), ("Confirm Password", self.confirm_var)]:
            tk.Label(card, text=title, bg=WHITE, anchor="w").pack(fill="x")
            show = "*" if "Password" in title else None
            ttk.Entry(card, textvariable=var, show=show, font=("Segoe UI", 10)).pack(fill="x", pady=(5, 10), ipady=4)

        ttk.Button(card, text="Send OTP", command=self.send_otp).pack(fill="x", ipady=5)
        tk.Label(card, textvariable=self.otp_status, bg=WHITE, fg=GRAY,
                 font=("Segoe UI", 9)).pack(anchor="w", pady=8)
        ttk.Button(card, text="Verify OTP & Reset Password", command=self.reset_password).pack(fill="x", ipady=5)
        ttk.Button(card, text="Back to Login", command=self.on_back).pack(fill="x", pady=10, ipady=4)

    def send_otp(self):
        email = self.email_var.get().strip().lower()
        owner = fetch_one("SELECT owner_id, username, email FROM owners WHERE LOWER(email)=LOWER(%s)", (email,))
        if not owner:
            messagebox.showerror("Email Not Found", "No owner account is registered with this email.")
            return
        self.otp = str(random.randint(100000, 999999))
        receiver_email = owner["email"]

        try:
            msg = EmailMessage()
            msg["Subject"] = f"{SHOP_NAME} - Password Reset OTP"
            msg["From"] = EMAIL_ADDRESS
            msg["To"] = receiver_email
            msg.set_content(
                f"Hello {owner.get('username') or 'Owner'},\n\n"
                f"Your Medi-Track password reset OTP is: {self.otp}\n\n"
                f"This OTP is valid for {OTP_VALID_MINUTES} minutes.\n\n"
                "If you did not request a password reset, please ignore this email.\n\n"
                f"Regards,\n{SHOP_NAME}"
            )

            with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=20) as smtp:
                smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
                smtp.send_message(msg)

        except Exception as exc:
            self.otp = None
            messagebox.showerror(
                "OTP Email Failed",
                "The password-reset OTP could not be sent.\n\n"
                f"Error: {exc}\n\n"
                "Check EMAIL_ADDRESS and your Gmail App Password in config.py."
            )
            return

        self.otp_expires = datetime.now() + timedelta(minutes=OTP_VALID_MINUTES)
        self.verified_email = receiver_email
        self.otp_status.set(
            f"OTP sent to {receiver_email} | Valid for {OTP_VALID_MINUTES} minutes"
        )
        messagebox.showinfo(
            "OTP Sent",
            f"Password reset OTP has been sent to {receiver_email}.\n\n"
            f"It is valid for {OTP_VALID_MINUTES} minutes."
        )

    def reset_password(self):
        otp = self.otp_var.get().strip()
        new_pass = self.new_pass_var.get()
        confirm = self.confirm_var.get()
        if not self.otp or not self.verified_email:
            messagebox.showwarning("OTP Required", "Generate an OTP first.")
            return
        if datetime.now() > self.otp_expires:
            messagebox.showerror("OTP Expired", "Generate a new OTP.")
            return
        if otp != self.otp:
            messagebox.showerror("Invalid OTP", "The OTP is incorrect.")
            return
        if len(new_pass) < 4:
            messagebox.showerror("Invalid Password", "Password must contain at least 4 characters.")
            return
        if new_pass != confirm:
            messagebox.showerror("Password Mismatch", "New password and confirmation do not match.")
            return
        execute("UPDATE owners SET password=%s WHERE email=%s", (new_pass, self.verified_email))
        self.otp = None
        self.otp_expires = None
        messagebox.showinfo("Password Reset", "Password reset successfully. You can now log in.")
        self.on_back()


class PageBase(tk.Frame):
    def __init__(self, master, app, title, subtitle=""):
        super().__init__(master, bg=BG)
        self.app = app
        self.title = title
        self.subtitle = subtitle
        self.header = tk.Frame(self, bg=BG)
        self.header.pack(fill="x", padx=28, pady=(25, 14))
        tk.Label(self.header, text=title, bg=BG, fg=NAVY,
                 font=("Segoe UI", 21, "bold")).pack(anchor="w")
        if subtitle:
            tk.Label(self.header, text=subtitle, bg=BG, fg=GRAY,
                     font=("Segoe UI", 10)).pack(anchor="w", pady=(4, 0))
        self.body = tk.Frame(self, bg=BG)
        self.body.pack(fill="both", expand=True, padx=28, pady=(0, 25))

    def panel(self, parent=None, **kwargs):
        parent = parent or self.body
        return tk.Frame(parent, bg=WHITE, bd=1, relief="solid", **kwargs)


class DashboardPage(PageBase):
    def __init__(self, master, app):
        super().__init__(master, app, "Dashboard", "Overview of medicines, stock, expiry and sales")
        self.stats = {}
        self.build()
        self.refresh()

    def build(self):
        grid = tk.Frame(self.body, bg=BG)
        grid.pack(fill="x")
        cards = [
            ("meds", "Medicine Batches", "0"),
            ("units", "Total Stock Units", "0"),
            ("low", "Low Stock", "0"),
            ("expiry", "Expiry Alerts", "0"),
            ("sales", "Today's Sales", f"{CURRENCY}0.00"),
        ]
        for i, (key, label, default) in enumerate(cards):
            card = self.panel(grid, padx=18, pady=16)
            card.grid(row=0, column=i, padx=5, sticky="nsew")
            grid.grid_columnconfigure(i, weight=1)
            tk.Label(card, text=label, bg=WHITE, fg=GRAY,
                     font=("Segoe UI", 9, "bold")).pack(anchor="w")
            value = tk.Label(card, text=default, bg=WHITE, fg=NAVY,
                             font=("Segoe UI", 20, "bold"))
            value.pack(anchor="w", pady=(7, 0))
            self.stats[key] = value

        notice = self.panel(self.body, padx=22, pady=20)
        notice.pack(fill="x", pady=18)
        tk.Label(notice, text="Medi-Track Store Control Center", bg=WHITE, fg=NAVY,
                 font=("Segoe UI", 13, "bold")).pack(anchor="w")
        tk.Label(notice, text="Use the left menu to open every requested feature as a separate page. "
                              "Expired medicine is blocked from sale and stock is validated before billing.",
                 bg=WHITE, fg=GRAY, justify="left", wraplength=1100).pack(anchor="w", pady=(7, 0))

    def refresh(self):
        self.stats["meds"].config(text=str(fetch_one("SELECT COUNT(*) c FROM medicines")["c"]))
        self.stats["units"].config(text=str(fetch_one("SELECT COALESCE(SUM(quantity),0) c FROM medicines")["c"]))
        self.stats["low"].config(text=str(fetch_one("SELECT COUNT(*) c FROM medicines WHERE quantity <= %s", (LOW_STOCK_LIMIT,))["c"]))
        self.stats["expiry"].config(text=str(fetch_one(
            "SELECT COUNT(*) c FROM medicines WHERE expiry_date <= DATE_ADD(CURDATE(), INTERVAL %s DAY)",
            (EXPIRY_WARNING_DAYS,))["c"]))
        total = fetch_one("SELECT COALESCE(SUM(grand_total),0) c FROM sales WHERE DATE(sale_date)=CURDATE()")["c"]
        self.stats["sales"].config(text=f"{CURRENCY}{float(total):.2f}")


class AddMedicinePage(PageBase):
    def __init__(self, master, app):
        super().__init__(master, app, "Add Medicine", "Create a medicine batch. Batch number is the Primary Key.")
        self.vars = {k: tk.StringVar() for k in ["batch", "name", "category", "manufacturer", "purchase", "selling", "quantity", "expiry"]}
        self.build()

    def build(self):
        form = self.panel(self.body, padx=24, pady=20)
        form.pack(fill="x")
        fields = [
            ("Batch Number (Primary Key)", "batch"), ("Medicine Name", "name"),
            ("Category", "category"), ("Manufacturer", "manufacturer"),
            ("Purchase Price", "purchase"), ("Selling Price", "selling"),
            ("Quantity", "quantity"), ("Expiry Date (YYYY-MM-DD)", "expiry"),
        ]
        for i, (label, key) in enumerate(fields):
            r, c = divmod(i, 4)
            tk.Label(form, text=label, bg=WHITE, fg=GRAY, font=("Segoe UI", 9, "bold")).grid(row=r*2, column=c, sticky="w", padx=7, pady=(0, 3))
            ttk.Entry(form, textvariable=self.vars[key], width=26).grid(row=r*2+1, column=c, sticky="ew", padx=7, pady=(0, 14), ipady=4)
        for c in range(4):
            form.grid_columnconfigure(c, weight=1)
        buttons = tk.Frame(form, bg=WHITE)
        buttons.grid(row=4, column=0, columnspan=4, sticky="ew", padx=7, pady=4)
        ttk.Button(buttons, text="Save Medicine", command=self.save).pack(side="left", padx=(0, 8), ipadx=10, ipady=4)
        ttk.Button(buttons, text="Clear", command=self.clear).pack(side="left", ipadx=10, ipady=4)

    def clear(self):
        for v in self.vars.values():
            v.set("")

    def save(self):
        v = self.vars
        batch = v["batch"].get().strip()
        name = v["name"].get().strip()
        category = v["category"].get().strip()
        manufacturer = v["manufacturer"].get().strip()
        if not all([batch, name, category, manufacturer, v["purchase"].get(), v["selling"].get(), v["quantity"].get(), v["expiry"].get()]):
            messagebox.showwarning("Missing Data", "Fill every medicine field.")
            return
        try:
            purchase = Decimal(v["purchase"].get())
            selling = Decimal(v["selling"].get())
            qty = int(v["quantity"].get())
        except (InvalidOperation, ValueError):
            messagebox.showerror("Invalid Data", "Price and quantity must be valid numbers.")
            return
        if purchase < 0 or selling < 0 or qty < 0 or selling < purchase:
            messagebox.showerror("Validation Error", "Prices cannot be negative, quantity cannot be negative, and selling price must be >= purchase price.")
            return
        try:
            expiry = date.fromisoformat(v["expiry"].get())
        except ValueError:
            messagebox.showerror("Invalid Date", "Use YYYY-MM-DD.")
            return
        try:
            execute(
                """
                INSERT INTO medicines
                (batch_no, medicine_name, category, manufacturer, purchase_price, selling_price, quantity, expiry_date)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                medicine_name = VALUES(medicine_name),
                category = VALUES(category),
                manufacturer = VALUES(manufacturer),
                purchase_price = VALUES(purchase_price),
                selling_price = VALUES(selling_price),
                quantity = VALUES(quantity),
                expiry_date = VALUES(expiry_date)
                """,
                (batch, name, category, manufacturer, purchase, selling, qty, expiry)
            )
        except Exception as e:
            messagebox.showerror("Database Error", f"Medicine could not be saved.\n\n{e}")
            return
        messagebox.showinfo("Saved", "Medicine saved successfully.")
        self.clear()
        self.app.refresh_pages()


class ViewMedicinesPage(PageBase):
    def __init__(self, master, app):
        super().__init__(master, app, "View Medicines", "Complete list of medicine batches stored in MySQL.")
        self.build()
        self.refresh()

    def build(self):
        top = self.panel(self.body, padx=15, pady=13)
        top.pack(fill="x")
        tk.Label(top, text="All medicine batches", bg=WHITE, fg=GRAY).pack(side="left")
        ttk.Button(top, text="Refresh", command=self.refresh).pack(side="right")
        wrap = tk.Frame(self.body, bg=BG)
        wrap.pack(fill="both", expand=True, pady=12)
        cols = ("batch", "name", "category", "manufacturer", "purchase", "selling", "quantity", "expiry")
        self.tree = ttk.Treeview(wrap, columns=cols, show="headings")
        heads = ["Batch No.", "Medicine", "Category", "Manufacturer", "Purchase", "Selling", "Qty", "Expiry"]
        for c, h in zip(cols, heads):
            self.tree.heading(c, text=h)
            self.tree.column(c, width=135, anchor="center")
        self.tree.pack(side="left", fill="both", expand=True)
        sb = ttk.Scrollbar(wrap, orient="vertical", command=self.tree.yview)
        sb.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=sb.set)

    def refresh(self):
        if not hasattr(self, "tree"):
            return
        for i in self.tree.get_children():
            self.tree.delete(i)
        rows = fetch_all("SELECT * FROM medicines ORDER BY medicine_name")
        for m in rows:
            self.tree.insert("", "end", values=(m["batch_no"], m["medicine_name"], m["category"], m["manufacturer"],
                                                  f"{CURRENCY}{float(m['purchase_price']):.2f}", f"{CURRENCY}{float(m['selling_price']):.2f}",
                                                  m["quantity"], m["expiry_date"]))


class MedicineSearchPage(PageBase):
    def __init__(self, master, app):
        super().__init__(master, app, "Medicine Search", "Quickly find a batch using batch number, medicine name, category or manufacturer.")
        self.search_var = tk.StringVar()
        self.build()
        self.refresh()

    def build(self):
        bar = self.panel(self.body, padx=15, pady=13)
        bar.pack(fill="x")
        ttk.Entry(bar, textvariable=self.search_var, width=55).pack(side="left", ipady=5)
        ttk.Button(bar, text="Search", command=self.refresh).pack(side="left", padx=7)
        ttk.Button(bar, text="Clear", command=lambda: (self.search_var.set(""), self.refresh())).pack(side="left")
        wrap = tk.Frame(self.body, bg=BG)
        wrap.pack(fill="both", expand=True, pady=12)
        self.tree = ttk.Treeview(wrap, columns=("batch","name","category","manufacturer","qty","expiry","status"), show="headings")
        for c, h in zip(("batch","name","category","manufacturer","qty","expiry","status"),
                         ["Batch", "Medicine", "Category", "Manufacturer", "Qty", "Expiry", "Status"]):
            self.tree.heading(c, text=h)
            self.tree.column(c, width=160, anchor="center")
        self.tree.pack(side="left", fill="both", expand=True)
        sb = ttk.Scrollbar(wrap, orient="vertical", command=self.tree.yview)
        sb.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=sb.set)

    def refresh(self):
        if not hasattr(self, "tree"):
            return
        for i in self.tree.get_children():
            self.tree.delete(i)
        q = self.search_var.get().strip()
        if q:
            like = f"%{q}%"
            rows = fetch_all("SELECT * FROM medicines WHERE batch_no LIKE %s OR medicine_name LIKE %s OR category LIKE %s OR manufacturer LIKE %s ORDER BY medicine_name",
                             (like, like, like, like))
        else:
            rows = fetch_all("SELECT * FROM medicines ORDER BY medicine_name")
        today = date.today()
        for m in rows:
            exp = m["expiry_date"]
            if isinstance(exp, str): exp = date.fromisoformat(exp)
            elif hasattr(exp, "date"): exp = exp.date()
            status = "EXPIRED" if exp < today else "LOW STOCK" if m["quantity"] <= LOW_STOCK_LIMIT else "OK"
            self.tree.insert("", "end", values=(m["batch_no"], m["medicine_name"], m["category"], m["manufacturer"], m["quantity"], exp, status))


class SellMedicinePage(PageBase):
    def __init__(self, master, app):
        super().__init__(master, app, "Sell Medicine", "Enter batch number and medicine name, or select a medicine from the list.")
        self.cart = []
        self.last_invoice = None
        self.customer_var = tk.StringVar(value="Walk-in Customer")
        self.phone_var = tk.StringVar()
        self.batch_var = tk.StringVar()
        self.medicine_var = tk.StringVar()
        self.qty_var = tk.StringVar(value="1")
        self.discount_var = tk.StringVar(value="0")
        self.build()
        self.refresh_cart()

    def build(self):
        top = self.panel(self.body, padx=15, pady=14)
        top.pack(fill="x")
        values = [
            ("Customer Name", self.customer_var, 20),
            ("Phone", self.phone_var, 16),
            ("Batch Number", self.batch_var, 18),
            ("Medicine Name", self.medicine_var, 18),
            ("Quantity", self.qty_var, 8)
        ]
        for label, var, width in values:
            tk.Label(top, text=label, bg=WHITE, fg=GRAY, font=("Segoe UI", 9, "bold")).pack(side="left", padx=(0, 5))
            ttk.Entry(top, textvariable=var, width=width).pack(side="left", padx=(0, 12), ipady=4)
        ttk.Button(top, text="Add to Cart", command=self.add).pack(side="left", padx=4)
        ttk.Button(top, text="View Medicines", command=self.view_medicines).pack(side="left", padx=4)
        ttk.Button(top, text="Clear Cart", command=self.clear).pack(side="left")

        area = tk.Frame(self.body, bg=BG)
        area.pack(fill="both", expand=True, pady=12)
        left = self.panel(area, padx=12, pady=12)
        left.pack(side="left", fill="both", expand=True)
        cols = ("batch", "name", "qty", "rate", "amount")
        self.tree = ttk.Treeview(left, columns=cols, show="headings")
        for c, h in zip(cols, ["Batch", "Medicine", "Qty", "Rate", "Amount"]):
            self.tree.heading(c, text=h)
        self.tree.pack(fill="both", expand=True)

        right = self.panel(area, padx=16, pady=16, width=360)
        right.pack(side="right", fill="y", padx=(12, 0))
        tk.Label(right, text="Bill Summary", bg=WHITE, fg=NAVY, font=("Segoe UI", 13, "bold")).pack(anchor="w")
        self.summary_text = tk.Text(right, width=42, height=18, bg="#f8fafc", fg="#1f2937", relief="flat")
        self.summary_text.pack(fill="both", expand=True, pady=12)
        tk.Label(right, text="Discount", bg=WHITE, fg=GRAY, font=("Segoe UI", 9, "bold")).pack(anchor="w")
        ttk.Entry(right, textvariable=self.discount_var, width=18).pack(anchor="w", pady=5)
        self.total_label = tk.Label(right, text=f"Grand Total: {CURRENCY}0.00", bg=WHITE, fg=GREEN,
                                     font=("Segoe UI", 16, "bold"))
        self.total_label.pack(anchor="w", pady=8)
        ttk.Button(right, text="Generate Bill", command=self.checkout).pack(fill="x", ipady=6)
        ttk.Button(right, text="Print Last Bill", command=self.print_bill).pack(fill="x", pady=8, ipady=5)

    def view_medicines(self):
        window = tk.Toplevel(self)
        window.title("Available Medicines")
        window.geometry("800x500")
        window.configure(bg=BG)

        tk.Label(
            window, text="Available Medicines", bg=BG, fg=NAVY,
            font=("Segoe UI", 16, "bold")
        ).pack(anchor="w", padx=18, pady=15)

        wrap = tk.Frame(window, bg=BG)
        wrap.pack(fill="both", expand=True, padx=18, pady=(0, 18))

        cols = ("batch", "name", "quantity", "price", "expiry")
        tree = ttk.Treeview(wrap, columns=cols, show="headings")

        for col, heading in zip(
            cols,
            ["Batch Number", "Medicine Name", "Available Qty", "Selling Price", "Expiry"]
        ):
            tree.heading(col, text=heading)
            tree.column(col, width=150, anchor="center")

        tree.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(wrap, orient="vertical", command=tree.yview)
        scrollbar.pack(side="right", fill="y")
        tree.configure(yscrollcommand=scrollbar.set)

        medicines = fetch_all(
            "SELECT batch_no, medicine_name, quantity, selling_price, expiry_date "
            "FROM medicines WHERE quantity > 0 ORDER BY medicine_name"
        )

        for medicine in medicines:
            tree.insert(
                "", "end",
                values=(
                    medicine["batch_no"],
                    medicine["medicine_name"],
                    medicine["quantity"],
                    f"{CURRENCY}{float(medicine['selling_price']):.2f}",
                    medicine["expiry_date"]
                )
            )

        def select_medicine(event=None):
            selected = tree.selection()
            if not selected:
                return
            values = tree.item(selected[0], "values")
            self.batch_var.set(values[0])
            self.medicine_var.set(values[1])
            window.destroy()

        tree.bind("<Double-1>", select_medicine)

        ttk.Button(
            window, text="Select Medicine", command=select_medicine
        ).pack(pady=(0, 15), ipadx=10, ipady=4)

    def add(self):
        batch = self.batch_var.get().strip()
        medicine_name = self.medicine_var.get().strip()
        if not batch or not medicine_name:
            messagebox.showwarning("Missing Details", "Enter batch number and medicine name.")
            return
        try:
            qty = int(self.qty_var.get())
        except ValueError:
            messagebox.showerror("Stock Validation", "Quantity must be a whole number.")
            return
        if qty <= 0:
            messagebox.showerror("Stock Validation", "Quantity must be greater than 0.")
            return
        med = fetch_one("SELECT * FROM medicines WHERE batch_no=%s", (batch,))
        if not med:
            messagebox.showerror("Medicine Not Found", "No medicine exists for this batch number.")
            return
        if medicine_name.lower() != str(med["medicine_name"]).lower():
            messagebox.showerror("Medicine Mismatch", "Medicine name does not match the selected batch.")
            return
        exp = med["expiry_date"]
        if isinstance(exp, str): exp = date.fromisoformat(exp)
        elif hasattr(exp, "date"): exp = exp.date()
        if exp < date.today():
            messagebox.showerror("Stock Validation", "Expired medicine cannot be sold.")
            return
        if med["quantity"] <= 0:
            messagebox.showerror("Stock Validation", "This medicine is out of stock.")
            return
        existing = sum(i["quantity"] for i in self.cart if i["batch_no"] == batch)
        if existing + qty > med["quantity"]:
            messagebox.showerror("Stock Validation", f"Available quantity is {med['quantity']}. Cart quantity would exceed stock.")
            return
        self.cart.append({
            "batch_no": batch, "medicine_name": med["medicine_name"], "quantity": qty,
            "unit_price": float(med["selling_price"]), "line_total": round(float(med["selling_price"]) * qty, 2)
        })
        self.refresh_cart()

    def clear(self):
        self.cart.clear()
        self.medicine_var.set("")
        self.batch_var.set("")
        self.refresh_cart()

    def refresh_cart(self):
        if not hasattr(self, "tree"):
            return
        for i in self.tree.get_children():
            self.tree.delete(i)
        subtotal = 0
        for x in self.cart:
            subtotal += x["line_total"]
            self.tree.insert("", "end", values=(x["batch_no"], x["medicine_name"], x["quantity"],
                                                   f"{CURRENCY}{x['unit_price']:.2f}", f"{CURRENCY}{x['line_total']:.2f}"))
        try: discount = float(self.discount_var.get() or 0)
        except ValueError: discount = 0
        discount = max(0, min(discount, subtotal))
        total = subtotal - discount
        self.total_label.config(text=f"Grand Total: {CURRENCY}{total:.2f}")
        self.summary_text.delete("1.0", "end")
        self.summary_text.insert("end", f"{SHOP_NAME}\n")
        self.summary_text.insert("end", f"Customer: {self.customer_var.get() or 'Walk-in Customer'}\n")
        self.summary_text.insert("end", f"Phone: {self.phone_var.get() or '-'}\n")
        self.summary_text.insert("end", "-" * 34 + "\n")
        for x in self.cart:
            self.summary_text.insert("end", f"{x['medicine_name']} x{x['quantity']}\n{CURRENCY}{x['line_total']:.2f}\n")
        self.summary_text.insert("end", "-" * 34 + "\n")
        self.summary_text.insert("end", f"Subtotal: {CURRENCY}{subtotal:.2f}\nDiscount: {CURRENCY}{discount:.2f}\nTOTAL: {CURRENCY}{total:.2f}")

    def checkout(self):
        if not self.cart:
            messagebox.showwarning("Empty Cart", "Add a medicine before generating the bill.")
            return
        try: discount = float(self.discount_var.get() or 0)
        except ValueError:
            messagebox.showerror("Invalid Discount", "Discount must be a number.")
            return
        subtotal = round(sum(i["line_total"] for i in self.cart), 2)
        if discount < 0 or discount > subtotal:
            messagebox.showerror("Invalid Discount", "Discount must be between 0 and the subtotal.")
            return
        total = round(subtotal - discount, 2)
        customer = self.customer_var.get().strip() or "Walk-in Customer"
        phone = self.phone_var.get().strip()

        conn = get_connection()
        cur = conn.cursor()
        try:
            conn.start_transaction()
            # Validate live stock again immediately before committing sale.
            for item in self.cart:
                cur.execute("SELECT quantity, expiry_date FROM medicines WHERE batch_no=%s FOR UPDATE", (item["batch_no"],))
                row = cur.fetchone()
                if not row:
                    raise ValueError(f"Batch {item['batch_no']} no longer exists.")
                qty, exp = row
                if hasattr(exp, "date"): exp = exp.date()
                if exp < date.today():
                    raise ValueError(f"Batch {item['batch_no']} is expired.")
                if qty < item["quantity"]:
                    raise ValueError(f"Insufficient stock for batch {item['batch_no']}. Available: {qty}.")
            cur.execute("INSERT INTO customers(customer_name, phone) VALUES (%s,%s)", (customer, phone))
            customer_id = cur.lastrowid
            cur.execute("INSERT INTO sales(customer_id, customer_name, customer_phone, subtotal, discount, grand_total) VALUES (%s,%s,%s,%s,%s,%s)",
                        (customer_id, customer, phone, subtotal, discount, total))
            sale_id = cur.lastrowid
            for item in self.cart:
                cur.execute("INSERT INTO sale_items(sale_id,batch_no,medicine_name,quantity,unit_price,line_total) VALUES (%s,%s,%s,%s,%s,%s)",
                            (sale_id, item["batch_no"], item["medicine_name"], item["quantity"], item["unit_price"], item["line_total"]))
                cur.execute("UPDATE medicines SET quantity=quantity-%s WHERE batch_no=%s", (item["quantity"], item["batch_no"]))
            conn.commit()
        except Exception as exc:
            conn.rollback()
            messagebox.showerror("Sale Failed", str(exc))
            return
        finally:
            cur.close()
            conn.close()

        self.last_invoice = create_invoice(sale_id, customer, phone, self.cart, subtotal, discount, total)
        messagebox.showinfo("Sale Complete", f"Sale saved successfully.\nInvoice: {self.last_invoice}")
        self.clear()
        self.discount_var.set("0")
        self.app.refresh_pages()

    def print_bill(self):
        if not self.last_invoice or not os.path.exists(self.last_invoice):
            messagebox.showwarning("No Bill", "Generate a bill first.")
            return
        try:
            os.startfile(self.last_invoice, "print")
        except Exception:
            messagebox.showinfo("Print Bill", f"Invoice created at:\n{os.path.abspath(self.last_invoice)}\n\nOpen the file and print it manually on this system.")


class StockPage(PageBase):
    def __init__(self, master, app):
        super().__init__(master, app, "Stock Management & Validation", "Monitor stock, low-stock batches and out-of-stock medicines.")
        self.build()
        self.refresh()

    def build(self):
        top = self.panel(self.body, padx=18, pady=13)
        top.pack(fill="x")
        tk.Label(top, text=f"Low stock threshold: {LOW_STOCK_LIMIT} units", bg=WHITE, fg=GRAY).pack(side="left")
        ttk.Button(top, text="Refresh Stock", command=self.refresh).pack(side="right")
        wrap = tk.Frame(self.body, bg=BG)
        wrap.pack(fill="both", expand=True, pady=12)
        cols = ("batch", "name", "qty", "status", "expiry")
        self.tree = ttk.Treeview(wrap, columns=cols, show="headings")
        for c, h in zip(cols, ["Batch", "Medicine", "Quantity", "Stock Status", "Expiry"]):
            self.tree.heading(c, text=h)
            self.tree.column(c, width=180, anchor="center")
        self.tree.pack(side="left", fill="both", expand=True)
        sb = ttk.Scrollbar(wrap, orient="vertical", command=self.tree.yview)
        sb.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=sb.set)

    def refresh(self):
        if not hasattr(self, "tree"):
            return
        for i in self.tree.get_children():
            self.tree.delete(i)
        rows = fetch_all("SELECT batch_no, medicine_name, quantity, expiry_date FROM medicines ORDER BY quantity, medicine_name")
        for m in rows:
            q = m["quantity"]
            status = "OUT OF STOCK" if q == 0 else "LOW STOCK" if q <= LOW_STOCK_LIMIT else "OK"
            self.tree.insert("", "end", values=(m["batch_no"], m["medicine_name"], q, status, m["expiry_date"]))


class BillCalculatorPage(PageBase):
    def __init__(self, master, app):
        super().__init__(master, app, "Automatic Bill Calculation", "Standalone calculator for quantity, subtotal, discount and final amount.")
        self.vars = {"price":tk.StringVar(),"qty":tk.StringVar(value="1"),"discount":tk.StringVar(value="0")}
        self.result = tk.StringVar(value=f"Grand Total: {CURRENCY}0.00")
        self.build()

    def build(self):
        card=self.panel(self.body,padx=24,pady=24)
        card.pack(fill="x")
        fields=[("Unit Price", "price"),("Quantity","qty"),("Discount","discount")]
        for i,(label,key) in enumerate(fields):
            tk.Label(card,text=label,bg=WHITE,fg=GRAY,font=("Segoe UI",9,"bold")).grid(row=0,column=i,sticky="w",padx=7)
            ttk.Entry(card,textvariable=self.vars[key],width=22).grid(row=1,column=i,padx=7,pady=7,ipady=4)
        ttk.Button(card,text="Calculate Bill",command=self.calculate).grid(row=1,column=3,padx=10,pady=7,ipady=4)
        tk.Label(card,textvariable=self.result,bg=WHITE,fg=GREEN,font=("Segoe UI",18,"bold")).grid(row=2,column=0,columnspan=4,sticky="w",padx=7,pady=(18,0))

    def calculate(self):
        try:
            price=Decimal(self.vars["price"].get())
            qty=int(self.vars["qty"].get())
            discount=Decimal(self.vars["discount"].get() or "0")
        except (InvalidOperation,ValueError):
            messagebox.showerror("Invalid Data","Unit price, quantity and discount must be valid numbers.")
            return
        subtotal=price*qty
        if qty<=0 or price<0 or discount<0 or discount>subtotal:
            messagebox.showerror("Validation Error","Check the price, quantity and discount values.")
            return
        self.result.set(f"Subtotal: {CURRENCY}{subtotal:.2f}    Discount: {CURRENCY}{discount:.2f}    Grand Total: {CURRENCY}{subtotal-discount:.2f}")


class SalesRecordPage(PageBase):
    def __init__(self, master, app):
        super().__init__(master, app, "Sales Record", "View completed transactions and bill details.")
        self.build()
        self.refresh()

    def build(self):
        top = self.panel(self.body, padx=15, pady=12)
        top.pack(fill="x")
        ttk.Button(top, text="Refresh", command=self.refresh).pack(side="right")
        wrap = tk.Frame(self.body, bg=BG)
        wrap.pack(fill="both", expand=True, pady=12)
        cols = ("id", "date", "customer", "phone", "subtotal", "discount", "total")
        self.tree = ttk.Treeview(wrap, columns=cols, show="headings")
        heads = ["Sale ID", "Date", "Customer", "Phone", "Subtotal", "Discount", "Grand Total"]
        for c, h in zip(cols, heads): self.tree.heading(c, text=h)
        self.tree.column(c, width=140, anchor="center")
        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<Double-1>", self.show_items)

        tk.Label(self.body, text="Double-click a sale to view purchased medicines.", bg=BG, fg=GRAY).pack(anchor="w")

    def refresh(self):
        if not hasattr(self, "tree"):
            return
        for i in self.tree.get_children():
            self.tree.delete(i)
        rows = fetch_all("SELECT sale_id, sale_date, customer_name, customer_phone, subtotal, discount, grand_total FROM sales ORDER BY sale_id DESC")
        for s in rows:
            self.tree.insert("", "end", values=(s["sale_id"], s["sale_date"], s["customer_name"], s["customer_phone"] or "-",
                                                  f"{CURRENCY}{float(s['subtotal']):.2f}", f"{CURRENCY}{float(s['discount']):.2f}",
                                                  f"{CURRENCY}{float(s['grand_total']):.2f}"))

    def show_items(self, event=None):
        sel = self.tree.selection()
        if not sel: return
        sale_id = self.tree.item(sel[0], "values")[0]
        items = fetch_all("SELECT batch_no, medicine_name, quantity, unit_price, line_total FROM sale_items WHERE sale_id=%s", (sale_id,))
        win = tk.Toplevel(self)
        win.title(f"Sale #{sale_id} Details")
        win.geometry("650x400")
        win.configure(bg=BG)
        tk.Label(win, text=f"Sale #{sale_id}", bg=BG, fg=NAVY, font=("Segoe UI", 16, "bold")).pack(anchor="w", padx=18, pady=16)
        tree = ttk.Treeview(win, columns=("batch","name","qty","rate","amount"), show="headings")
        for c, h in zip(("batch","name","qty","rate","amount"), ["Batch","Medicine","Qty","Rate","Amount"]):
            tree.heading(c, text=h)
        tree.pack(fill="both", expand=True, padx=18, pady=(0, 18))
        for x in items:
            tree.insert("", "end", values=(x["batch_no"], x["medicine_name"], x["quantity"], f"{CURRENCY}{float(x['unit_price']):.2f}", f"{CURRENCY}{float(x['line_total']):.2f}"))


class ExpiryPage(PageBase):
    def __init__(self, master, app):
        super().__init__(master, app, "Expiry Alerts", f"Automatic date-based expiry checking. Alert window: {EXPIRY_WARNING_DAYS} days.")
        self.build()
        self.refresh()

    def build(self):
        top = self.panel(self.body, padx=18, pady=13)
        top.pack(fill="x")
        tk.Label(top, text="Expired and soon-to-expire batches are shown automatically.", bg=WHITE, fg=GRAY).pack(side="left")
        ttk.Button(top, text="Refresh Alerts", command=self.refresh).pack(side="right")
        wrap = tk.Frame(self.body, bg=BG)
        wrap.pack(fill="both", expand=True, pady=12)
        cols = ("batch","name","qty","expiry","days","status")
        self.tree = ttk.Treeview(wrap, columns=cols, show="headings")
        for c, h in zip(cols, ["Batch","Medicine","Qty","Expiry","Days Left","Status"]):
            self.tree.heading(c, text=h)
        self.tree.pack(fill="both", expand=True)
        sb = ttk.Scrollbar(wrap, orient="vertical", command=self.tree.yview)
        sb.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=sb.set)

    def refresh(self):
        if not hasattr(self, "tree"):
            return
        for i in self.tree.get_children():
            self.tree.delete(i)
        rows = fetch_all("SELECT batch_no, medicine_name, quantity, expiry_date FROM medicines ORDER BY expiry_date")
        today = date.today()
        for m in rows:
            exp = m["expiry_date"]
            if isinstance(exp, str): exp = date.fromisoformat(exp)
            elif hasattr(exp, "date"): exp = exp.date()
            days = (exp - today).days
            if days < 0: status = "EXPIRED"
            elif days <= EXPIRY_WARNING_DAYS: status = "EXPIRING SOON"
            else: status = "OK"
            if status != "OK":
                self.tree.insert("", "end", values=(m["batch_no"], m["medicine_name"], m["quantity"], exp, days, status))


class MainApp(tk.Frame):
    def __init__(self, master, user, on_logout):
        super().__init__(master, bg=BG)
        self.user = user
        self.on_logout = on_logout
        self.pages = {}
        self.page_classes = {
            "Dashboard": DashboardPage,
            "Add Medicine": AddMedicinePage,
            "View Medicines": ViewMedicinesPage,
            "Medicine Search": MedicineSearchPage,
            "Sell Medicine": SellMedicinePage,
            "Stock Management": StockPage,
            "Automatic Bill Calculation": BillCalculatorPage,
            "Sales Record": SalesRecordPage,
            "Expiry Alerts": ExpiryPage,
        }
        self.build_shell()
        self.show_page("Dashboard")

    def build_shell(self):
        top = tk.Frame(self, bg=NAVY, height=70)
        top.pack(fill="x")
        top.pack_propagate(False)
        tk.Label(top, text="💊", bg=NAVY, fg=WHITE, font=("Segoe UI Emoji", 25)).pack(side="left", padx=(20, 8))
        tk.Label(top, text=SHOP_NAME, bg=NAVY, fg=WHITE, font=("Segoe UI", 19, "bold")).pack(side="left")
        tk.Label(top, text=f" | Owner: {self.user['username']}", bg=NAVY, fg="#dbeafe", font=("Segoe UI", 10)).pack(side="left", padx=8)
        ttk.Button(top, text="Logout", command=self.on_logout).pack(side="right", padx=18, pady=18)

        self.body = tk.Frame(self, bg=BG)
        self.body.pack(fill="both", expand=True)
        nav = tk.Frame(self.body, bg="#0f3045", width=220)
        nav.pack(side="left", fill="y")
        nav.pack_propagate(False)
        content = tk.Frame(self.body, bg=BG)
        content.pack(side="left", fill="both", expand=True)
        self.content = content

        tk.Label(nav, text="MENU", bg="#0f3045", fg="#b8c8d4", font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=20, pady=(20, 9))
        for name in self.page_classes:
            b = tk.Button(nav, text=name, anchor="w", bd=0, relief="flat", bg="#0f3045", fg=WHITE,
                          activebackground="#1b5578", activeforeground=WHITE, padx=20, pady=9,
                          font=("Segoe UI", 9, "bold"), command=lambda n=name: self.show_page(n))
            b.pack(fill="x")
        tk.Label(nav, text="\nFeatures included:\n• Login attempt limit\n• OTP reset\n• Batch Primary Key\n• Stock validation\n• Auto billing\n• Expiry checking",
                 bg="#0f3045", fg="#b8c8d4", justify="left", font=("Segoe UI", 8), anchor="w").pack(side="bottom", fill="x", padx=18, pady=18)

    def show_page(self, name):
        for child in self.content.winfo_children():
            child.pack_forget()
        if name not in self.pages:
            self.pages[name] = self.page_classes[name](self.content, self)
        self.pages[name].pack(fill="both", expand=True)
        page = self.pages[name]
        if hasattr(page, "refresh"):
            try: page.refresh()
            except Exception: pass

    def refresh_pages(self):
        for page in self.pages.values():
            if hasattr(page, "refresh"):
                try: page.refresh()
                except Exception: pass


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Medi-Track | Medical Store Management")
        self.state("zoomed")
        self.minsize(1100, 700)
        self.configure(bg=BG)
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self.show_login()

    def clear(self):
        for child in self.winfo_children():
            child.destroy()

    def show_login(self):
        self.clear()
        LoginFrame(self, self.show_main, self.show_forgot, self.show_otp_login).pack(fill="both", expand=True)

    def show_forgot(self):
        self.clear()
        ForgotPasswordFrame(self, self.show_login).pack(fill="both", expand=True)

    def show_otp_login(self):
        self.clear()
        OTPLoginFrame(self, self.show_main, self.show_login).pack(fill="both", expand=True)

    def show_main(self, user):
        self.clear()
        MainApp(self, user, self.show_login).pack(fill="both", expand=True)


if __name__ == "__main__":
    try:
        App().mainloop()
    except Exception as exc:
        messagebox.showerror("Medi-Track Error", str(exc))
