# Use Python official image
FROM python:3.9

# Set working directory
WORKDIR /app

# Copy requirements.txt
COPY requirements.txt .

# Uninstall packages not listed in requirements.txt
RUN pip freeze > installed_packages.txt && \
    grep -vxFf requirements.txt installed_packages.txt > packages_to_remove.txt && \
    pip uninstall -y -r packages_to_remove.txt || true && \
    rm installed_packages.txt packages_to_remove.txt

# Install only the necessary dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application files
COPY . .

# Expose default port
EXPOSE 80

# ✅ Use shell-form CMD to avoid exec format errors
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-80}
