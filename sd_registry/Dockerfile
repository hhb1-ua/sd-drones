FROM python:3.11.2
WORKDIR /app
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
COPY . .

CMD python3 -u sd_registry.py
