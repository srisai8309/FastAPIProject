# FastAPI Student Management System

A backend Student Management System built using FastAPI, PostgreSQL, SQLAlchemy, JWT Authentication, and Pydantic.

## Features

- User registration and login
- JWT-based authentication
- Access and refresh tokens
- Role-based authorization
- Admin and normal user roles
- Student CRUD operations
- Student ownership and permission checks
- Pagination
- Search students by name
- Sorting students
- Request validation using Pydantic
- PostgreSQL database integration
- Environment variable configuration
- Automated API testing using pytest
- Docker configuration prepared for future containerization

## Technologies Used

- Python
- FastAPI
- SQLAlchemy
- PostgreSQL
- Pydantic
- JWT
- bcrypt
- pytest
- Postman
- Git & GitHub
- Docker configuration

## Project Structure

```text
FastAPIProject/
│
├── routers/
│   ├── auth_router.py
│   └── student.py
│
├── auth.py
├── database.py
├── main.py
├── models.py
├── schemas.py
├── test_main.py
├── requirements.txt
├── Dockerfile
├── .dockerignore
├── .gitignore
└── README.md