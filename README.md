# FastAPI Student Management System

A production-ready Student Management System built using FastAPI, SQLAlchemy, PostgreSQL, JWT Authentication, Role-Based Authorization, and automated testing.

## 🚀 Live Demo

Live API:
https://fastapiproject-rwkk.onrender.com

Swagger API Documentation:
https://fastapiproject-rwkk.onrender.com/docs

## 🛠️ Technologies Used

- Python
- FastAPI
- SQLAlchemy
- PostgreSQL
- Pydantic
- JWT Authentication
- bcrypt
- OAuth2
- pytest
- Git & GitHub
- Render

## ✨ Features

### Authentication & Authorization

- User registration
- User login
- Password hashing using bcrypt
- JWT access tokens
- JWT refresh tokens
- Role-based authorization
- Admin and normal user roles
- Ownership-based authorization

### Student Management

- Create student
- Get student by ID
- Get students
- Update student
- Delete student
- Search students
- Sort students
- Pagination
- Response validation

### Security

- Protected API endpoints
- Admin-only operations
- User ownership checks
- Password hashing
- Environment variables for sensitive configuration

### Testing

- Automated API tests using pytest
- 50 tests passing

## 📁 Project Structure

```text
FastAPIProject/
│
├── main.py
├── database.py
├── models.py
├── schemas.py
├── auth.py
│
├── routers/
│   ├── auth_router.py
│   └── student.py
│
├── test_main.py
├── requirements.txt
├── Dockerfile
├── .dockerignore
├── .gitignore
└── README.md