FROM python:3.13-alpine

RUN mkdir /code
WORKDIR /code

COPY requirements.txt exporter.py /code/
RUN pip install --no-cache-dir -r requirements.txt

CMD [ "python", "/code/exporter.py" ]
