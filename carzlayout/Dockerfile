FROM python:3.12-slim
LABEL authors="Grom.Alexey"

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /PLACEMENT

# Install dependencies
COPY requirements.txt /PLACEMENT/
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install gunicorn



# Copy project
COPY . /PLACEMENT/

# Collect static files
RUN python manage.py collectstatic --no-input

# Run the application with Gunicorn
CMD ["gunicorn", "carzlayout.wsgi:application", "--bind", "0.0.0.0:8000"]
