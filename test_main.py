from fastapi.testclient import TestClient
from main import app
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base
from models import User, Student
from auth import hash_password
from routers.student import get_db as student_get_db
from routers.auth_router import get_db as auth_get_db
import os

if os.path.exists("test.db"):
    os.remove("test.db")
TEST_DATABASE_URL = "sqlite:///test.db"
test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=test_engine
)
Base.metadata.create_all(bind=test_engine)
db = TestingSessionLocal()

admin_user = User(
    username="admin",
    email="admin@example.com",
    hashed_password=hash_password("admin123"),
    role="admin"
)

db.add(admin_user)
db.commit()
db.close()
client = TestClient(app)
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
app.dependency_overrides[student_get_db] = override_get_db
app.dependency_overrides[auth_get_db] = override_get_db
def test_home():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {
        "message": "Welcome"
    }
def test_register():
    response = client.post(
        "/register",
        json={
            "username": "testuser",
            "email": "testuser@example.com",
            "password": "password123"
        }
    )
    assert response.status_code == 200
    assert response.json() == {
        "message": "User registered successfully"
    }
def test_duplicate_username():
    response = client.post(
        "/register",
        json={
            "username": "testuser",
            "email": "another@example.com",
            "password": "password123"
        }
    )
    assert response.status_code == 409
    assert response.json() == {
        "detail": "Username already exists"
    }
def test_duplicate_email():
    response = client.post(
        "/register",
        json={
            "username": "anotheruser",
            "email": "testuser@example.com",
            "password": "password123"
        }
    )
    assert response.status_code == 409
    assert response.json() == {
        "detail": "Email already exists"
    }
def test_invalid_email():
    response = client.post(
        "/register",
        json={
            "username": "invaliduser",
            "email": "not-an-email",
            "password": "password123"
        }
    )

    assert response.status_code == 422
def test_invalid_password():
    response = client.post(
        "/register",
        json={
            "username": "shortpass",
            "email": "shortpass@example.com",
            "password": "123"
        }
    )

    assert response.status_code == 422
def test_login():
    response = client.post(
        "/login",
        data={
            "username": "testuser",
            "password": "password123"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
def test_login_wrong_password():
    response = client.post(
        "/login",
        data={
            "username": "testuser",
            "password": "wrongpassword"
        }
    )

    assert response.status_code == 401
    assert response.json() == {
        "detail": "Invalid username or password"
    }
def test_login_wrong_username():
    response = client.post(
        "/login",
        data={
            "username": "doesnotexist",
            "password": "password123"
        }
    )

    assert response.status_code == 401
    assert response.json() == {
        "detail": "Invalid username or password"
    }
def test_refresh_token():
    login_response = client.post(
        "/login",
        data={
            "username": "testuser",
            "password": "password123"
        }
    )

    assert login_response.status_code == 200

    refresh_token = login_response.json()["refresh_token"]

    response = client.post(
        "/refresh",
        json={
            "refresh_token": refresh_token
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert "access_token" in data
    assert data["token_type"] == "bearer"
def test_refresh_with_access_token():
    login_response = client.post(
        "/login",
        data={
            "username": "testuser",
            "password": "password123"
        }
    )

    assert login_response.status_code == 200

    access_token = login_response.json()["access_token"]

    response = client.post(
        "/refresh",
        json={
            "refresh_token": access_token
        }
    )

    assert response.status_code == 401
    assert response.json() == {
        "detail": "Invalid or expired refresh token"
    }
def test_get_students():
    login_response = client.post(
        "/login",
        data={
            "username": "testuser",
            "password": "password123"
        }
    )

    assert login_response.status_code == 200

    access_token = login_response.json()["access_token"]

    response = client.get(
        "/students",
        headers={
            "Authorization": f"Bearer {access_token}"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert "students" in data
    assert "page" in data
    assert "limit" in data
    assert "total" in data
def test_get_students_without_token():
    response = client.get("/students")

    assert response.status_code == 401
    assert response.json() == {
        "detail": "Not authenticated"
    }
def test_add_student():
    login_response = client.post(
        "/login",
        data={
            "username": "admin",
            "password": "admin123"
        }
    )

    assert login_response.status_code == 200

    access_token = login_response.json()["access_token"]

    response = client.post(
        "/student",
        json={
            "name": "Test Student"
        },
        headers={
            "Authorization": f"Bearer {access_token}"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["name"] == "Test Student"
    assert "id" in data
    assert "user_id" in data
def test_user_cannot_add_student():
    login_response = client.post(
        "/login",
        data={
            "username": "testuser",
            "password": "password123"
        }
    )

    assert login_response.status_code == 200

    access_token = login_response.json()["access_token"]

    response = client.post(
        "/student",
        json={
            "name": "Unauthorized Student"
        },
        headers={
            "Authorization": f"Bearer {access_token}"
        }
    )

    assert response.status_code == 403
    assert response.json() == {
        "detail": "Admin access required"
    }
def test_get_student():
    login_response = client.post(
        "/login",
        data={
            "username": "admin",
            "password": "admin123"
        }
    )

    assert login_response.status_code == 200

    access_token = login_response.json()["access_token"]

    create_response = client.post(
        "/student",
        json={
            "name": "Student For Get Test"
        },
        headers={
            "Authorization": f"Bearer {access_token}"
        }
    )

    assert create_response.status_code == 200

    student_id = create_response.json()["id"]

    response = client.get(
        f"/student/{student_id}",
        headers={
            "Authorization": f"Bearer {access_token}"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == student_id
    assert data["name"] == "Student For Get Test"
def test_get_student_not_found():
    login_response = client.post(
        "/login",
        data={
            "username": "admin",
            "password": "admin123"
        }
    )

    assert login_response.status_code == 200

    access_token = login_response.json()["access_token"]

    response = client.get(
        "/student/999999",
        headers={
            "Authorization": f"Bearer {access_token}"
        }
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Student not found"
    }
def test_update_student():
    login_response = client.post(
        "/login",
        data={
            "username": "admin",
            "password": "admin123"
        }
    )

    assert login_response.status_code == 200

    access_token = login_response.json()["access_token"]

    create_response = client.post(
        "/student",
        json={
            "name": "Old Student Name"
        },
        headers={
            "Authorization": f"Bearer {access_token}"
        }
    )

    assert create_response.status_code == 200

    student_id = create_response.json()["id"]

    response = client.put(
        f"/student/{student_id}",
        json={
            "name": "Updated Student Name"
        },
        headers={
            "Authorization": f"Bearer {access_token}"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == student_id
    assert data["name"] == "Updated Student Name"
def test_update_student_not_found():
    login_response = client.post(
        "/login",
        data={
            "username": "admin",
            "password": "admin123"
        }
    )

    assert login_response.status_code == 200

    access_token = login_response.json()["access_token"]

    response = client.put(
        "/student/999999",
        json={
            "name": "Updated Name"
        },
        headers={
            "Authorization": f"Bearer {access_token}"
        }
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Student not found"
    }
def test_delete_student():
    login_response = client.post(
        "/login",
        data={
            "username": "admin",
            "password": "admin123"
        }
    )

    assert login_response.status_code == 200

    access_token = login_response.json()["access_token"]

    create_response = client.post(
        "/student",
        json={
            "name": "Student For Delete Test"
        },
        headers={
            "Authorization": f"Bearer {access_token}"
        }
    )

    assert create_response.status_code == 200

    student_id = create_response.json()["id"]

    response = client.delete(
        f"/student/{student_id}",
        headers={
            "Authorization": f"Bearer {access_token}"
        }
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": "Student deleted successfully"
    }
def test_delete_student_not_found():
    login_response = client.post(
        "/login",
        data={
            "username": "admin",
            "password": "admin123"
        }
    )

    assert login_response.status_code == 200

    access_token = login_response.json()["access_token"]

    response = client.delete(
        "/student/999999",
        headers={
            "Authorization": f"Bearer {access_token}"
        }
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Student not found"
    }
def test_register_second_user():
    response = client.post(
        "/register",
        json={
            "username": "seconduser",
            "email": "seconduser@example.com",
            "password": "password123"
        }
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": "User registered successfully"
    }
def test_create_student_for_testuser():
    db = TestingSessionLocal()

    testuser = db.query(User).filter(
        User.username == "testuser"
    ).first()

    user_id = testuser.id

    student = Student(
        name="Testuser Owned Student",
        user_id=user_id
    )

    db.add(student)
    db.commit()
    db.refresh(student)

    db.close()

    assert student.user_id == user_id
def test_user_cannot_update_other_users_student():
    db = TestingSessionLocal()

    testuser = db.query(User).filter(
        User.username == "testuser"
    ).first()

    student = db.query(Student).filter(
        Student.user_id == testuser.id
    ).first()

    student_id = student.id

    db.close()

    login_response = client.post(
        "/login",
        data={
            "username": "seconduser",
            "password": "password123"
        }
    )

    assert login_response.status_code == 200

    access_token = login_response.json()["access_token"]

    response = client.put(
        f"/student/{student_id}",
        json={
            "name": "Unauthorized Update"
        },
        headers={
            "Authorization": f"Bearer {access_token}"
        }
    )

    assert response.status_code == 403
    assert response.json() == {
        "detail": "You do not have permission to modify this student"
    }
def test_user_cannot_delete_other_users_student():
    db = TestingSessionLocal()

    testuser = db.query(User).filter(
        User.username == "testuser"
    ).first()

    student = db.query(Student).filter(
        Student.user_id == testuser.id
    ).first()

    student_id = student.id

    db.close()

    login_response = client.post(
        "/login",
        data={
            "username": "seconduser",
            "password": "password123"
        }
    )

    assert login_response.status_code == 200

    access_token = login_response.json()["access_token"]

    response = client.delete(
        f"/student/{student_id}",
        headers={
            "Authorization": f"Bearer {access_token}"
        }
    )

    assert response.status_code == 403
    assert response.json() == {
        "detail": "You do not have permission to delete this student"
    }
def test_user_cannot_get_other_users_student():
    db = TestingSessionLocal()

    testuser = db.query(User).filter(
        User.username == "testuser"
    ).first()

    student = db.query(Student).filter(
        Student.user_id == testuser.id
    ).first()

    student_id = student.id

    db.close()

    login_response = client.post(
        "/login",
        data={
            "username": "seconduser",
            "password": "password123"
        }
    )

    assert login_response.status_code == 200

    access_token = login_response.json()["access_token"]

    response = client.get(
        f"/student/{student_id}",
        headers={
            "Authorization": f"Bearer {access_token}"
        }
    )

    assert response.status_code == 403
    assert response.json() == {
        "detail": "You do not have permission to view this student"
    }
def test_get_user_students():
    login_response = client.post(
        "/login",
        data={
            "username": "testuser",
            "password": "password123"
        }
    )

    assert login_response.status_code == 200

    access_token = login_response.json()["access_token"]

    response = client.get(
        "/user/students",
        headers={
            "Authorization": f"Bearer {access_token}"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)

    for student in data:
        assert student["user_id"] is not None
def test_students_pagination():
    login_response = client.post(
        "/login",
        data={
            "username": "admin",
            "password": "admin123"
        }
    )

    assert login_response.status_code == 200

    access_token = login_response.json()["access_token"]

    response = client.get(
        "/students?page=1&limit=2",
        headers={
            "Authorization": f"Bearer {access_token}"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["page"] == 1
    assert data["limit"] == 2
    assert len(data["students"]) <= 2
    assert data["total"] >= len(data["students"])
def test_students_search():
    login_response = client.post(
        "/login",
        data={
            "username": "admin",
            "password": "admin123"
        }
    )

    assert login_response.status_code == 200

    access_token = login_response.json()["access_token"]

    response = client.get(
        "/students?search=Testuser",
        headers={
            "Authorization": f"Bearer {access_token}"
        }
    )

    assert response.status_code == 200

    data = response.json()

    for student in data["students"]:
        assert "testuser" in student["name"].lower()
def test_students_sorting():
    login_response = client.post(
        "/login",
        data={
            "username": "admin",
            "password": "admin123"
        }
    )

    assert login_response.status_code == 200

    access_token = login_response.json()["access_token"]

    response = client.get(
        "/students?sort=asc",
        headers={
            "Authorization": f"Bearer {access_token}"
        }
    )
    assert response.status_code == 200
    data = response.json()
    names = [student["name"] for student in data["students"]]
    assert names == sorted(names)
def test_students_sorting_desc():
    login_response = client.post(
        "/login",
        data={
            "username": "admin",
            "password": "admin123"
        }
    )

    assert login_response.status_code == 200

    access_token = login_response.json()["access_token"]

    response = client.get(
        "/students?sort=desc",
        headers={
            "Authorization": f"Bearer {access_token}"
        }
    )

    assert response.status_code == 200

    data = response.json()

    names = [student["name"] for student in data["students"]]

    assert names == sorted(names, reverse=True)
def test_students_invalid_sort():
    login_response = client.post(
        "/login",
        data={
            "username": "admin",
            "password": "admin123"
        }
    )

    assert login_response.status_code == 200

    access_token = login_response.json()["access_token"]

    response = client.get(
        "/students?sort=random",
        headers={
            "Authorization": f"Bearer {access_token}"
        }
    )

    assert response.status_code == 422
def test_students_invalid_page():
    login_response = client.post(
        "/login",
        data={
            "username": "admin",
            "password": "admin123"
        }
    )

    assert login_response.status_code == 200

    access_token = login_response.json()["access_token"]

    response = client.get(
        "/students?page=0",
        headers={
            "Authorization": f"Bearer {access_token}"
        }
    )

    assert response.status_code == 422
def test_students_invalid_limit():
    login_response = client.post(
        "/login",
        data={
            "username": "admin",
            "password": "admin123"
        }
    )

    assert login_response.status_code == 200

    access_token = login_response.json()["access_token"]

    response = client.get(
        "/students?limit=0",
        headers={
            "Authorization": f"Bearer {access_token}"
        }
    )

    assert response.status_code == 422
def test_students_limit_too_large():
    login_response = client.post(
        "/login",
        data={
            "username": "admin",
            "password": "admin123"
        }
    )

    assert login_response.status_code == 200

    access_token = login_response.json()["access_token"]

    response = client.get(
        "/students?limit=101",
        headers={
            "Authorization": f"Bearer {access_token}"
        }
    )

    assert response.status_code == 422
def test_students_empty_search():
    login_response = client.post(
        "/login",
        data={
            "username": "admin",
            "password": "admin123"
        }
    )

    assert login_response.status_code == 200

    access_token = login_response.json()["access_token"]

    response = client.get(
        "/students?search=",
        headers={
            "Authorization": f"Bearer {access_token}"
        }
    )

    assert response.status_code == 422
def test_students_search_too_long():
    login_response = client.post(
        "/login",
        data={
            "username": "admin",
            "password": "admin123"
        }
    )

    assert login_response.status_code == 200

    access_token = login_response.json()["access_token"]

    long_search = "a" * 101

    response = client.get(
        "/students",
        params={
            "search": long_search
        },
        headers={
            "Authorization": f"Bearer {access_token}"
        }
    )

    assert response.status_code == 422
def test_students_search_sort_pagination():
    login_response = client.post(
        "/login",
        data={
            "username": "admin",
            "password": "admin123"
        }
    )

    assert login_response.status_code == 200

    access_token = login_response.json()["access_token"]

    response = client.get(
        "/students",
        params={
            "search": "Student",
            "sort": "asc",
            "page": 1,
            "limit": 2
        },
        headers={
            "Authorization": f"Bearer {access_token}"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["page"] == 1
    assert data["limit"] == 2
    assert len(data["students"]) <= 2
    names = [student["name"] for student in data["students"]]
    assert names == sorted(names)
    for name in names:
        assert "student" in name.lower()
def test_add_student_invalid_name():
    login_response = client.post(
        "/login",
        data={
            "username": "admin",
            "password": "admin123"
        }
    )

    assert login_response.status_code == 200

    access_token = login_response.json()["access_token"]

    response = client.post(
        "/student",
        json={
            "name": "A"
        },
        headers={
            "Authorization": f"Bearer {access_token}"
        }
    )

    assert response.status_code == 422
def test_add_student_name_too_long():
    login_response = client.post(
        "/login",
        data={
            "username": "admin",
            "password": "admin123"
        }
    )
    assert login_response.status_code == 200
    access_token = login_response.json()["access_token"]
    long_name = "A" * 101

    response = client.post(
        "/student",
        json={
            "name": long_name
        },
        headers={
            "Authorization": f"Bearer {access_token}"
        }
    )

    assert response.status_code == 422
def test_invalid_username():
    response = client.post(
        "/register",
        json={
            "username": "ab",
            "email": "shortusername@example.com",
            "password": "password123"
        }
    )

    assert response.status_code == 422
def test_username_too_long():
    long_username = "a" * 51

    response = client.post(
        "/register",
        json={
            "username": long_username,
            "email": "longusername@example.com",
            "password": "password123"
        }
    )

    assert response.status_code == 422
def test_password_too_long():
    long_password = "a" * 101

    response = client.post(
        "/register",
        json={
            "username": "longpassword",
            "email": "longpassword@example.com",
            "password": long_password
        }
    )

    assert response.status_code == 422
def test_password_max_length_valid():
    max_password = "a" * 100

    response = client.post(
        "/register",
        json={
            "username": "maxpassword",
            "email": "maxpassword@example.com",
            "password": max_password
        }
    )

    assert response.status_code == 200
def test_normal_user_sees_only_own_students():
    login_response = client.post(
        "/login",
        data={
            "username": "testuser",
            "password": "password123"
        }
    )

    assert login_response.status_code == 200

    access_token = login_response.json()["access_token"]

    response = client.get(
        "/students",
        headers={
            "Authorization": f"Bearer {access_token}"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] >= 1

    for student in data["students"]:
        assert student["user_id"] != None
def test_admin_sees_all_students():
    login_response = client.post(
        "/login",
        data={
            "username": "admin",
            "password": "admin123"
        }
    )

    assert login_response.status_code == 200

    access_token = login_response.json()["access_token"]

    response = client.get(
        "/students",
        headers={
            "Authorization": f"Bearer {access_token}"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] >= 1
    assert len(data["students"]) >= 1
def test_update_student_without_token():
    response = client.put(
        "/student/999999",
        json={
            "name": "Unauthorized Update"
        }
    )

    assert response.status_code == 401
    assert response.json() == {
        "detail": "Not authenticated"
    }
def test_delete_student_without_token():
    response = client.delete(
        "/student/999999"
    )

    assert response.status_code == 401
    assert response.json() == {
        "detail": "Not authenticated"
    }
def test_get_student_without_token():
    response = client.get(
        "/student/999999"
    )

    assert response.status_code == 401
    assert response.json() == {
        "detail": "Not authenticated"
    }
def test_get_user_students_without_token():
    response = client.get(
        "/user/students"
    )

    assert response.status_code == 401
    assert response.json() == {
        "detail": "Not authenticated"
    }
