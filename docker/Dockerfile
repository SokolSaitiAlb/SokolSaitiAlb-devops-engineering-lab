FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HOST=0.0.0.0 \
    PORT=8080 \
    DATA_FILE=/data/notes.json \
    APP_VERSION=0.1.0

# This service uses only Python's standard library at runtime. Refresh Debian
# security updates, then remove pip/ensurepip from the runtime image: they are
# not used by the application and their embedded vendor SBOM was producing
# unrelated msgpack/setuptools/urllib3 findings in Trivy.
RUN set -eux; \
    apt-get update; \
    apt-get upgrade -y --no-install-recommends; \
    rm -rf /var/lib/apt/lists/*; \
    groupadd --system --gid 10001 app; \
    useradd --system --uid 10001 --gid app --home-dir /nonexistent --shell /usr/sbin/nologin app; \
    mkdir -p /data; \
    chown 10001:10001 /data; \
    rm -rf /usr/local/lib/python3.13/site-packages/pip \
           /usr/local/lib/python3.13/site-packages/pip-*.dist-info \
           /usr/local/lib/python3.13/ensurepip \
           /usr/local/bin/pip /usr/local/bin/pip3 /usr/local/bin/pip3.13

WORKDIR /app
COPY --chown=10001:10001 app/src/service.py /app/service.py
USER 10001:10001

EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD ["python", "-c", "from urllib.request import urlopen; urlopen('http://127.0.0.1:8080/healthz', timeout=2).read()"]

ENTRYPOINT ["python", "/app/service.py"]
