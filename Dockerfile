# Base image with Ubuntu 20.04 and Python pre-installed
FROM ubuntu:20.04
ENV DEBIAN_FRONTEND noninteractive


# Install Python and other dependencies
RUN apt-get update && \
    apt-get install -y python3 python3-pip git&& \
    apt-get install -y  python3-dev default-libmysqlclient-dev && \
    apt-get install -y build-essential pkg-config libpango-1.0-0 libharfbuzz0b libpangoft2-1.0-0 libffi-dev libjpeg-dev libopenjp2-7-dev && \
    sudo apt-get install wkhtmltopdf \
    rm -rf /var/lib/apt/lists/*

# Set the working directory to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip3 install --trusted-host pypi.python.org -r requirements.txt

# Copy the entrypoint.sh script
COPY entrypoint.sh /entrypoint.sh

# Make entrypoint.sh executable
RUN chmod +x /entrypoint.sh

# Start the server using entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
