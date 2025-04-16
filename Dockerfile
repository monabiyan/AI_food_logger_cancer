FROM python:3.9

WORKDIR /app

COPY requirements.txt .

RUN pip freeze > installed_packages.txt && \
    grep -vxFf requirements.txt installed_packages.txt > packages_to_remove.txt && \
    pip uninstall -y -r packages_to_remove.txt || true && \
    rm installed_packages.txt packages_to_remove.txt

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 80

# ✅ This is the magic line
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT}"]
