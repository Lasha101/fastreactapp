#!/bin/bash

# Run the database initialization script
python /app/initial_db.py

# Now, start the Gunicorn server
exec gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app --bind 0.0.0.0:8000