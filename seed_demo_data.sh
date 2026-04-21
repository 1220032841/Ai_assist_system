#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

if [ ! -f .env.online ]; then
  echo "[ERROR] .env.online not found."
  echo "Please deploy first and complete env config."
  exit 1
fi

COMPOSE=(docker compose -f docker-compose.online.yml --env-file .env.online)
API_URL="${API_URL:-http://127.0.0.1:8000/api/v1/users/}"

echo "==================================================="
echo "  Seed Demo Users and C++ Assignment"
echo "==================================================="
echo
echo "[1/2] Seeding demo users..."

"${COMPOSE[@]}" exec -T backend python - <<PY
import json
import urllib.error
import urllib.request

api_url = ${API_URL@Q}
users = [
    {"email": "admin@example.com", "password": "admin123", "full_name": "Admin User", "role": "admin", "is_active": True},
    {"email": "teacher1@teacher.com", "password": "teacher123", "full_name": "Course Teacher", "role": "instructor", "is_active": True},
    {"email": "student1@student.com", "password": "student123", "full_name": "Student One", "role": "student", "is_active": True},
    {"email": "student2@student.com", "password": "student123", "full_name": "Student Two", "role": "student", "is_active": True},
    {"email": "student3@student.com", "password": "student123", "full_name": "Student Three", "role": "student", "is_active": True},
    {"email": "student4@student.com", "password": "student123", "full_name": "Student Four", "role": "student", "is_active": True},
    {"email": "student5@student.com", "password": "student123", "full_name": "Student Five", "role": "student", "is_active": True},
]

for user in users:
    data = json.dumps(user).encode("utf-8")
    request = urllib.request.Request(api_url, data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(request) as response:
            if response.status == 200:
                print(f"[CREATED] {user['email']}")
            else:
                print(f"[FAILED ] {user['email']} status={response.status}")
    except urllib.error.HTTPError as error:
        body = error.read().decode("utf-8", errors="ignore")
        if error.code == 400 and "already exists" in body:
            print(f"[EXISTS ] {user['email']}")
        else:
            print(f"[FAILED ] {user['email']} status={error.code}")
            if body:
                print(body)
    except Exception as error:
        print(f"[FAILED ] {user['email']} {error}")
PY

echo
echo "[2/2] Seeding 1 C++ assignment..."
./seed_assignment.sh

echo
echo "[OK] Demo data ready."
echo "Teacher: teacher1@teacher.com / teacher123"
echo "Students: student1..student5@student.com / student123"