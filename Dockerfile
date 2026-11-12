FROM python:3.10-slim
WORKDIR /app
COPY requirements-lock.txt pyproject.toml ./
RUN pip install --no-cache-dir -r requirements-lock.txt
COPY src ./src
COPY examples ./examples
RUN pip install --no-deps .
ENV PYTHONPATH=/app/src
EXPOSE 8501
CMD ["python", "-m", "streamlit", "run", "src/ma_deallab/ui/app.py", "--server.address=0.0.0.0", "--server.headless=true"]
