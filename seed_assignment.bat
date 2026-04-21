@echo off
setlocal
cd /d "%~dp0"

if not exist ".env.online" (
	echo [ERROR] .env.online not found.
	echo Please run start_local_online.bat once and complete env config.
	pause
	exit /b 1
)

for /f "usebackq tokens=1,* delims==" %%A in (`findstr /R "^[A-Za-z_][A-Za-z0-9_]*=" ".env.online"`) do (
	set "%%A=%%B"
)

if not defined POSTGRES_USER set "POSTGRES_USER=postgres"
if not defined POSTGRES_DB set "POSTGRES_DB=app"

set COMPOSE=docker compose -f docker-compose.online.yml --env-file .env.online

echo Resetting assignments and seeding 1 C++ arithmetic assignment...

:: 1) Clean old submissions and assignments
echo Deleting existing assignment-related data...
%COMPOSE% exec -T db psql -U %POSTGRES_USER% -d %POSTGRES_DB% -c "DELETE FROM feedbacks WHERE submission_id IN (SELECT id FROM submissions WHERE assignment_id IN (SELECT id FROM assignments));"
%COMPOSE% exec -T db psql -U %POSTGRES_USER% -d %POSTGRES_DB% -c "DELETE FROM static_analysis_results WHERE submission_id IN (SELECT id FROM submissions WHERE assignment_id IN (SELECT id FROM assignments));"
%COMPOSE% exec -T db psql -U %POSTGRES_USER% -d %POSTGRES_DB% -c "DELETE FROM execution_results WHERE submission_id IN (SELECT id FROM submissions WHERE assignment_id IN (SELECT id FROM assignments));"
%COMPOSE% exec -T db psql -U %POSTGRES_USER% -d %POSTGRES_DB% -c "DELETE FROM submissions WHERE assignment_id IN (SELECT id FROM assignments);"
%COMPOSE% exec -T db psql -U %POSTGRES_USER% -d %POSTGRES_DB% -c "DELETE FROM assignments;"

:: 2) Ensure course exists and bound to teacher/admin
echo Ensuring course (ID: 1)...
%COMPOSE% exec -T db psql -U %POSTGRES_USER% -d %POSTGRES_DB% -c "INSERT INTO courses (id, title, description, term, instructor_id) VALUES (1, 'C++ Arithmetic Practice', 'Single assignment for basic batch addition and subtraction processing.', '2026', COALESCE((SELECT id FROM users WHERE lower(role::text) IN ('admin','instructor') ORDER BY id LIMIT 1), 1)) ON CONFLICT (id) DO UPDATE SET title=EXCLUDED.title, description=EXCLUDED.description, term=EXCLUDED.term, instructor_id=EXCLUDED.instructor_id;"

:: 3) Insert one C++ assignment (kept consistent with hidden tests in grader)
echo Inserting 1 assignment...
%COMPOSE% exec -T db psql -U %POSTGRES_USER% -d %POSTGRES_DB% -c "INSERT INTO assignments (id, course_id, title, description, allowed_concepts) VALUES (1, 1, 'C++ Example: Basic Addition and Subtraction', 'Input two integers a and b. Output a+b and a-b.', '{\"topics\":[\"basic input/output\",\"integer arithmetic\"]}'::json) ON CONFLICT (id) DO UPDATE SET title=EXCLUDED.title, description=EXCLUDED.description, allowed_concepts=EXCLUDED.allowed_concepts;"

echo.
echo Done! You can now submit to assignment_id: 1 (C++)
exit /b 0
