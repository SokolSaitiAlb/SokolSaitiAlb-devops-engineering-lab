# Optional Nginx reverse proxy

Nginx is behind the Compose reverse-proxy profile and binds to 127.0.0.1:8081 by default:

    docker compose --profile reverse-proxy up --build -d
    curl -fsS http://127.0.0.1:8081/healthz
    docker compose logs --tail=100 nginx

The proxy sends requests to the internal api:8080 service and applies request-size limits and basic response headers. This demo does not configure public TLS, certificate renewal or authentication. Do not expose it publicly as-is.
