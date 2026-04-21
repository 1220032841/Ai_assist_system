#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

if [ ! -f .env.online ]; then
  echo "[ERROR] .env.online not found."
  echo "Please run deploy first and complete env config."
  exit 1
fi

set -a
. <(sed 's/\r$//' ./.env.online)
set +a

POSTGRES_USER="${POSTGRES_USER:-postgres}"
POSTGRES_DB="${POSTGRES_DB:-app}"

echo "Resetting assignments and seeding 1 C++ arithmetic assignment..."

COMPOSE=(docker compose -f docker-compose.online.yml --env-file .env.online)

"${COMPOSE[@]}" exec -T db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" <<'SQL'
DELETE FROM feedbacks WHERE submission_id IN (SELECT id FROM submissions WHERE assignment_id IN (SELECT id FROM assignments));
DELETE FROM static_analysis_results WHERE submission_id IN (SELECT id FROM submissions WHERE assignment_id IN (SELECT id FROM assignments));
DELETE FROM execution_results WHERE submission_id IN (SELECT id FROM submissions WHERE assignment_id IN (SELECT id FROM assignments));
DELETE FROM submissions WHERE assignment_id IN (SELECT id FROM assignments);
DELETE FROM assignments;

INSERT INTO courses (id, title, description, term, instructor_id)
VALUES (
  1,
  'C++ Arithmetic Practice',
  'Single assignment for basic addition and subtraction.',
  '2026',
  COALESCE((SELECT id FROM users WHERE lower(role::text) IN ('admin','instructor') ORDER BY id LIMIT 1), 1)
)
ON CONFLICT (id)
DO UPDATE SET
  title = EXCLUDED.title,
  description = EXCLUDED.description,
  term = EXCLUDED.term,
  instructor_id = EXCLUDED.instructor_id;

INSERT INTO assignments (id, course_id, title, description, allowed_concepts)
VALUES (
  1,
  1,
  'C++ Example: Basic Addition and Subtraction',
  'Input two integers a and b. Output a+b and a-b.',
  '{"topics":["basic input/output","integer arithmetic"]}'::json
)
ON CONFLICT (id)
DO UPDATE SET
  title = EXCLUDED.title,
  description = EXCLUDED.description,
  allowed_concepts = EXCLUDED.allowed_concepts;
SQL

echo "Done! You can now submit to assignment_id: 1 (C++)."
