FROM python:3.12-slim
WORKDIR /srv
COPY app.py /srv/app.py
COPY static /srv/static
EXPOSE 8787
USER nobody
CMD ["python", "-u", "/srv/app.py"]
