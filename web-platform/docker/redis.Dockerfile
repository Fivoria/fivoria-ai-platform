# Redis Dockerfile
FROM redis:7-alpine

# Set environment variables
ENV REDIS_PASSWORD=redis_secure_password_2024

# Copy redis configuration
RUN echo "requirepass ${REDIS_PASSWORD}" > /usr/local/etc/redis/redis.conf

# Expose port
EXPOSE 6379

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD redis-cli -a ${REDIS_PASSWORD} ping || exit 1

# Start Redis with configuration
CMD ["redis-server", "/usr/local/etc/redis/redis.conf"]
