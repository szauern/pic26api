#!/bin/sh
set -e

echo "=== Waiting for database ==="
until python -c "
import psycopg, os
from urllib.parse import urlparse
u = urlparse(os.environ['DATABASE_URL'])
conn = psycopg.connect(
    host=u.hostname, port=u.port or 5432,
    dbname=u.path.lstrip('/'),
    user=u.username, password=u.password,
    connect_timeout=3
)
conn.close()
" 2>/dev/null; do
  echo "DB not ready, retrying..."
  sleep 2
done
echo "DB ready"

echo "=== Running migrations ==="
python manage.py migrate --noinput

echo "=== Collecting static files ==="
python manage.py collectstatic --noinput

echo "=== Creating superuser if not exists ==="
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin')
    print('Superuser created: admin / admin')
else:
    print('Superuser already exists')
"

echo "=== Starting Django on port 8001 ==="
exec python manage.py runserver 0.0.0.0:8001
