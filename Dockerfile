# Use an official Python runtime as a parent image
# Using the full image (not slim) to ensure all build headers and tools are present
FROM python:3.9

# Set the working directory in the container
WORKDIR /app

# Install system dependencies required for compilation (gfortran)
RUN apt-get update && apt-get install -y \
    gfortran \
    build-essential \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -U pip wheel && \
    pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Compile the Fortran extension
WORKDIR /app/gyro
# Using setup.py with explicit compiler flags and verbosity
RUN python setup.py build_ext --inplace --fcompiler=gnu95 -v


# Switch back to the root directory
WORKDIR /app

# Make port 8000 available to the world outside this container
EXPOSE 8000

# Run api.py when the container launches
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
