FROM python:3.9-slim

# Set environment variables to prevent Python from writing .pyc files and buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Copy requirements first to leverage Docker layer caching
COPY requirements.txt .

# Clean any pre-installed unnecessary packages (optional)
RUN pip freeze > installed_packages.txt && \
    grep -vxFf requirements.txt installed_packages.txt > packages_to_remove.txt && \
    pip uninstall -y -r packages_to_remove.txt || true && \
    rm installed_packages.txt packages_to_remove.txt

# Install only what's needed
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire app source
COPY . .

# Open container port
EXPOSE 80

# Run the app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]
