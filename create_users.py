import urllib.request
import json
import os

DEFAULT_API_URL = "http://127.0.0.1/api/v1/users/"
API_URL = (os.getenv("API_URL") or DEFAULT_API_URL).strip()

users = [
    {
        "email": "admin@example.com",
        "password": "admin123",
        "full_name": "Admin User",
        "role": "admin",
        "is_active": True
    },
    {
        "email": "teacher1@teacher.com",
        "password": "teacher123",
        "full_name": "Course Teacher",
        "role": "instructor",
        "is_active": True
    },
    {
        "email": "student1@student.com",
        "password": "student123",
        "full_name": "Student One",
        "role": "student",
        "is_active": True
    },
    {
        "email": "student2@student.com",
        "password": "student123",
        "full_name": "Student Two",
        "role": "student",
        "is_active": True
    },
    {
        "email": "student3@student.com",
        "password": "student123",
        "full_name": "Student Three",
        "role": "student",
        "is_active": True
    },
    {
        "email": "student4@student.com",
        "password": "student123",
        "full_name": "Student Four",
        "role": "student",
        "is_active": True
    },
    {
        "email": "student5@student.com",
        "password": "student123",
        "full_name": "Student Five",
        "role": "student",
        "is_active": True
    }
]

def create_user(user):
    data = json.dumps(user).encode('utf-8')
    req = urllib.request.Request(API_URL, data=data, headers={'Content-Type': 'application/json'})
    
    try:
        with urllib.request.urlopen(req) as response:
            if response.status == 200:
                print(f"[SUCCESS] Created user: {user['email']}")
            else:
                print(f"[FAILED] Could not create user {user['email']}. Status: {response.status}")
    except urllib.error.HTTPError as e:
        if e.code == 400:
             print(f"[INFO] User {user['email']} already exists.")
        else:
            print(f"[ERROR] Failed to create user {user['email']}: {e}")
    except Exception as e:
        print(f"[ERROR] Connection failed: {e}")
        print("Make sure the service is running and API_URL is correct.")


def run_seed(target_url: str) -> None:
    global API_URL
    API_URL = target_url
    print(f"Using API: {API_URL}")
    for user in users:
        create_user(user)

if __name__ == "__main__":
    print("Creating initial users...")
    run_seed(API_URL)

    print("\nDone!")
    print("You can now login with:")
    print("  Admin:   admin@example.com / admin123")
    print("  Teacher: teacher1@teacher.com / teacher123")
    print("  Students:")
    print("    student1@student.com / student123")
    print("    student2@student.com / student123")
    print("    student3@student.com / student123")
    print("    student4@student.com / student123")
    print("    student5@student.com / student123")
