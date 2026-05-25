# Nitya Yoga – Yoga Management & Wellness Platform

## 📌 Overview
Nitya Yoga is a backend-based yoga management platform built using FastAPI and SQLAlchemy.  
The project helps manage yoga users, authentication, and wellness-related functionalities through REST APIs.

This project was created to improve backend development skills, API handling, authentication systems, and database management.

---

## 🚀 Features
- User Registration & Login
- JWT Authentication
- Secure Password Hashing
- CRUD Operations
- Database Integration using SQLite
- RESTful APIs
- API Testing with Postman
- Modular Project Structure

---

## 🛠️ Tech Stack
- Backend Framework: Python + FastAPI
- Database: SQLite
- ORM: SQLAlchemy
- Authentication: JWT Tokens
- API Testing: Postman
- Server: Uvicorn

---

## 📂 Project Structure

```bash
NityaYoga/
│── main.py
│── database.py
│── models.py
│── schemas.py
│── auth.py
│── routers/
│    └── users.py
│── requirements.txt
│── README.md
```

---

## ⚙️ Installation & Setup

### 1️⃣ Clone the Repository

```bash
git clone <your-repository-link>
cd NityaYoga
```

### 2️⃣ Create Virtual Environment

```bash
python -m venv venv
```

### 3️⃣ Activate Virtual Environment

#### Windows

```bash
venv\Scripts\activate
```

#### Linux/Mac

```bash
source venv/bin/activate
```

### 4️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

### 5️⃣ Run the Server

```bash
uvicorn main:app --reload
```

---

## 🌐 API Documentation

After running the server:

### Swagger UI
```bash
http://127.0.0.1:8000/docs
```

### ReDoc
```bash
http://127.0.0.1:8000/redoc
```

---

## 🔐 Authentication

The project uses JWT-based authentication:
- Login API generates access tokens
- Protected routes require Bearer Token authentication

---

## 📸 Sample API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/register` | Register User |
| POST | `/login` | User Login |
| GET | `/users` | Get All Users |
| PUT | `/users/{id}` | Update User |
| DELETE | `/users/{id}` | Delete User |

---

## 🎯 Learning Outcomes

Through this project, I learned:
- Backend API development
- Authentication systems using JWT
- Database management using ORM
- API testing and debugging
- FastAPI project structuring

---

## 👨‍💻 Author

**Tejas Kotalwar**  
Backend Developer | Python & FastAPI Enthusiast
