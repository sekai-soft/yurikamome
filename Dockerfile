FROM python:3.12-slim-bullseye

# Set the working directory in the container to /app
WORKDIR /app

# Copy only requirements.txt first to leverage Docker cache
COPY ./requirements.txt /app/requirements.txt

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Install gunicorn
RUN pip install gunicorn==22.0.0

# Add the current directory contents into the container at /app
COPY . /app

# Run gunicorn when the container launches
CMD ["bash", "-c", "flask sqlite init && gunicorn --bind 0.0.0.0:5000 --workers 1 app:app"]
