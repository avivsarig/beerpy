# Use an official Python 3.10.6 runtime as a parent image
FROM python:3.10.6-slim-buster

# Set the working directory in the container
WORKDIR .

# Add the current directory contents into the container at /app
COPY . .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port the app runs in
EXPOSE 8000

# Run the command to start uWSGI
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]