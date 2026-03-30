DO $$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'django_user') THEN
    CREATE USER django_user WITH PASSWORD 'django_secret';
  END IF;
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'fastapi_user') THEN
    CREATE USER fastapi_user WITH PASSWORD 'fastapi_secret';
  END IF;
END
$$;

GRANT ALL PRIVILEGES ON DATABASE projectdb TO django_user;
GRANT ALL ON SCHEMA public TO django_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO django_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO django_user;

GRANT CONNECT ON DATABASE projectdb TO fastapi_user;
GRANT USAGE ON SCHEMA public TO fastapi_user;
