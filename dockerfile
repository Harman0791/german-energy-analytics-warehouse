# Base image: a minimal Linux with Python 3.12
FROM python:3.13-slim

# All following commands run inside /app in the container
WORKDIR /app

# 1. Install dependencies first (cached separately from the code)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 2. Copy the project code
COPY . .

# 3. dbt settings for Docker, and install dbt packages (dbt_utils)
ENV DBT_PROFILES_DIR=/app/docker
RUN dbt deps

# 4. What the container does when it starts
CMD ["python", "analytics/prefect/energy_pipeline.py"]