FROM python:3.12-slim

WORKDIR /app
COPY expedition ./expedition
COPY harness ./harness

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV EXPEDITION_BIND_HOST=0.0.0.0
ENV EXPEDITION_TRUST_PROXY=1
ENV PORT=8080

EXPOSE 8080
CMD ["python3", "-m", "expedition", "serve"]
