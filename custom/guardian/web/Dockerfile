FROM python:3.12-slim
WORKDIR /srv
COPY app.py store.py mcp.py inventory.py /srv/
COPY static /srv/static
COPY entrypoint.sh /srv/entrypoint.sh
RUN chmod +x /srv/entrypoint.sh && mkdir -p /state && chmod 777 /state
EXPOSE 8787
ENV STATE_DIR=/state
ENTRYPOINT ["/srv/entrypoint.sh"]
