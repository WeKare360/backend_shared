
FROM python:3.11
WORKDIR /app
COPY . .
RUN pip install fastapi uvicorn pydantic
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
