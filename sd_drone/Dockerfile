FROM python:3.11.2
ARG IDENTIFIER
ARG ALIAS
ARG PASSWORD
ENV IDENTIFIER ${IDENTIFIER}
ENV ALIAS ${ALIAS}
ENV PASSWORD ${PASSWORD}
WORKDIR /app
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
COPY . .

CMD python3 -u sd_drone.py $IDENTIFIER $ALIAS $PASSWORD
