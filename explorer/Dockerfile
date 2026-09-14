FROM python:3.12-slim
RUN useradd -m -u 1000 user
WORKDIR /app
COPY --chown=user:user . /app
USER user
ENV HOST=0.0.0.0 PORT=7860
EXPOSE 7860
CMD ["python", "app.py"]
