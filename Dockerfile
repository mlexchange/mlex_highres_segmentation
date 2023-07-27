FROM python:3.9

# Create and set working directory
WORKDIR /app

# Install Python dependencies
RUN python -m pip install --upgrade pip
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the remainder of the code into the image
COPY . ./

EXPOSE 8050
# Run Dash app with gunicorn
CMD ["gunicorn", "-b", "0.0.0.0:8075", "--reload", "app:server"]
# Better than the alternative running of app.py directly with
#CMD ["python", "app.py"]
