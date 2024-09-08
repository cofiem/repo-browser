# syntax=docker/dockerfile:1

FROM python:3

RUN apt-get update && apt-get install -y \
        python-apt-common \
        python-apt-dev \
        && rm -rf /var/lib/apt/lists/*

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8001

CMD ["python", "-m", "daphne", "-b", "0.0.0.0", "-p", "8001", "examine.asgi:application"]
