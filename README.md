<div align="center">

# 💊 PharmaCore

**A Python + MySQL Medical Store Management System with a full-screen Tkinter GUI**

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![MySQL](https://img.shields.io/badge/Database-MySQL-4479A1?logo=mysql&logoColor=white)](https://www.mysql.com/)
[![Tkinter](https://img.shields.io/badge/GUI-Tkinter-orange)](https://docs.python.org/3/library/tkinter.html)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Active-brightgreen)]()

</div>

---

## 📖 Overview

PharmaCore is a desktop application for managing a medical store's day-to-day operations — inventory, sales, billing, and reporting — built to demonstrate Python programming, GUI development, MySQL DBMS, and Python Database Connectivity (PDBC).

It's designed to look and feel like a real point-of-sale / inventory tool a small pharmacy could actually use, not just a checklist of syllabus topics.

## 🖼️ Screenshots

| Login | Dashboard |
|:---:|:---:|
| ![Login](assets/screenshots/login.png) | ![Dashboard](assets/screenshots/dashboard.png) |

| Add Medicine | View Medicines |
|:---:|:---:|
| ![Add Medicine](assets/screenshots/add-medicine.png) | ![View Medicines](assets/screenshots/view-medicines.png) |

| Medicine Search | Sell Medicine |
|:---:|:---:|
| ![Medicine Search](assets/screenshots/medicine-search.png) | ![Sell Medicine](assets/screenshots/sell-medicine.png) |

| Invoice / Bill | Sales Record |
|:---:|:---:|
| ![Invoice](assets/screenshots/invoice-bill.png) | ![Sales Record](assets/screenshots/sales-record.png) |

## ✨ Features

### 🔐 Authentication
- Owner login system with a 3-attempt lockout
- Forgot Password flow with email-based OTP verification (demo OTP shown in-app; SMTP-ready)

### 💊 Medicine Management
- Add / view / search medicines
- Batch number as primary key
- Tracks name, category, manufacturer, purchase price, selling price, quantity, and expiry date

### 🛒 Sales
- Cart-based selling with customer name and phone capture
- Automatic bill calculation with discount support
- Automatic stock deduction on sale
- Sales record history and detailed invoice generation
- Print bill support (Windows)

### 📦 Stock & Expiry
- Stock validation before selling (no overselling, no expired sales)
- Low-stock alerts and expiry warnings
- Automatic date-based expiry checking

### 📊 Reports & Helpers
- Date-filtered sales reports with CSV export (via Pandas)
- Symptom-based medicine category suggestions *(educational only — not a diagnosis tool)*
- Temporary CSV log for in-progress updates

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Language | Python |
| GUI | Tkinter / ttk |
| Database | MySQL |
| DB Connector | mysql-connector-python |
| Reporting | Pandas |
| Other | datetime, tempfile, os, pathlib, csv |

## 📁 Project Structure

```text
PharmaCore/
├── app.py              # Main application & GUI
├── config.py           # Shop & environment configuration
├── database.py         # MySQL connection helpers
├── invoice.py          # Invoice generation
├── reports.py          # Sales reporting & CSV export
├── suggestions.py      # Symptom-based medicine suggestions
├── schema.sql          # Database schema & seed data
├── requirements.txt    # Python dependencies
└── invoices/           # Generated invoices (created automatically)
```

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- MySQL Server installed and running

### 1. Clone the repository
```bash
git clone https://github.com/<your-username>/PharmaCore.git
cd PharmaCore
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Set up the database
1. Open MySQL Workbench or the MySQL command line.
2. Run `schema.sql` to create the database and seed sample data.
3. Copy `.env.example` to `.env` (or edit `config.py`) and set your own MySQL credentials.

### 4. Run the app
```bash
python app.py
```

## 🔑 Demo Login

```text
Username: pushkar
Password: 1234
```

> ⚠️ This is a demo credential for evaluation only. Change it before any real-world use, and never commit real credentials to version control.

## ⚠️ Safety Note

The symptom helper provides **educational category suggestions only** — it is not a diagnosis or prescription system. Always consult a qualified pharmacist or doctor for medicine decisions, especially involving children, pregnancy, allergies, contraindications, or drug interactions.

## 🗺️ Roadmap / Future Improvements

- [ ] Real email OTP delivery via SMTP
- [ ] Strong password hashing (bcrypt)
- [ ] Role-based staff accounts
- [ ] Full customer management
- [ ] GST/tax calculation
- [ ] More detailed invoice templates
- [ ] Barcode scanning support
- [ ] Supplier management & purchase history
- [ ] Graphical sales charts (Matplotlib)

## 🤝 Contributing

This started as a college project, but suggestions and pull requests are welcome — feel free to open an issue if you spot a bug or have an idea for improvement.

## 📄 License

This project is licensed under the [MIT License](LICENSE).

---

<div align="center">
Made with Python & ☕ by <strong>Pushkar</strong>
</div>
