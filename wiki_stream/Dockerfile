FROM python:3.9.9-bullseye

WORKDIR /workdir

COPY requirements.txt .

ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --upgrade pip

COPY wiki_to_kafka.py .

ENTRYPOINT ["python3", "wiki_to_kafka.py"]