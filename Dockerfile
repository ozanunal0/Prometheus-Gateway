# Use a lean Python base image
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /code

# Copy requirements.txt first to leverage Docker layer caching
COPY requirements.txt /code/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# Copy the application code
COPY ./app /code/app

# Command to run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"] 