FROM ubuntu:16.04

RUN apt-get update -y && \
    apt-get install -y python-pip python-dev && \
    apt-get install -y python-flask && \
    apt-get install -y vim

# We copy just the requirements.txt first to leverage Docker cache
COPY ./requirements.txt /app/requirements.txt

WORKDIR /app

RUN pip install -r requirements.txt

COPY . /app

# ENTRYPOINT [ "python" ]

#CMD [ "app/warden-validating.py" ]

# CMD [ "app/bc-val.py" ]

# python app/bc-val.py

CMD ["sh", "-c", "tail -f /dev/null"]
