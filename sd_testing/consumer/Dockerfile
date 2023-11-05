FROM python:3.11.2
ARG TOPIC
ARG PARTITION
ENV TOPIC ${TOPIC}
ENV PARTITION ${PARTITION}
WORKDIR /app
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
COPY . .

CMD python3 -u consumer.py $TOPIC $PARTITION
