# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY ./requirements.txt /app/requirements.txt

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the backend application's code into the container at /app
COPY . /app

# Make the prestart script executable
RUN chmod +x /app/prestart.sh

# Run the prestart script which will then start Gunicorn
CMD ["/app/prestart.sh"]