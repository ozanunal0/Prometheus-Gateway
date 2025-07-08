# Use a lean Python base image
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /code

# Copy requirements.txt first to leverage Docker layer caching
COPY requirements.txt /code/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# Download spaCy language model
RUN python -m spacy download en_core_web_lg

# Copy the application code
COPY ./app /code/app
COPY create_key.py /code/create_key.py
COPY config.yaml /code/config.yaml

# Command to run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"] 