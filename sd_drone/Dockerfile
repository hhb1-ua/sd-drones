FROM python:3.11.2
ARG IDENTIFIER
ARG ALIAS
# RUN echo $IDENTIFIER
# RUN echo $ALIAS
ENV IDENTIFIER ${IDENTIFIER}
ENV ALIAS ${ALIAS}
WORKDIR /app
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
COPY . .

CMD python3 -u sd_drone.py $IDENTIFIER $ALIAS
