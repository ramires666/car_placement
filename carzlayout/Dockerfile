FROM python:3.12-slim
LABEL authors="grom.alexey"
# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /PLACEMENT

# Install dependencies
COPY requirements.txt /PLACEMENT/
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . /PLACEMENT/

# Run the application
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]