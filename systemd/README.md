# Single-host systemd deployment

This is an alternative to container deployment, not a second runtime that should run simultaneously on the same port.

Example installation outline (review paths and IDs before executing):

    sudo useradd --system --home /nonexistent --shell /usr/sbin/nologin ops-notes
    sudo install -d -o ops-notes -g ops-notes -m 0750 /var/lib/ops-notes-api
    sudo install -d -m 0755 /etc/ops-notes-api
    sudo install -m 0644 systemd/ops-notes-api.service /etc/systemd/system/ops-notes-api.service
    sudo systemctl daemon-reload
    sudo systemctl enable --now ops-notes-api
    systemctl status ops-notes-api --no-pager
    journalctl -u ops-notes-api -n 100 --no-pager

The checkout must be installed at /opt/ops-notes-api and readable by ops-notes; the writable state directory must be owned by that account. Check the service unit and your distro's Python path before enabling it. Keep HOST=127.0.0.1 when exposing the service only through a local reverse proxy.
