# MySQL Database Dockerfile
FROM mysql:8.0

# Set environment variables
ENV MYSQL_ROOT_PASSWORD=root_password_secure_2024
ENV MYSQL_DATABASE=fivoria_ai
ENV MYSQL_USER=fivoria_user
ENV MYSQL_PASSWORD=fivoria_secure_password_2024

# Copy initialization script
COPY database/schema.sql /docker-entrypoint-initdb.d/

# Expose port
EXPOSE 3306

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD mysqladmin ping -h localhost -u root -p${MYSQL_ROOT_PASSWORD} || exit 1
