FROM python:3.11-slim

# System libs: build tools for mysqlclient, plus the MySQL client headers.
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc default-libmysqlclient-dev pkg-config \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt /app/review_service/requirements.txt
RUN pip install --no-cache-dir -r /app/review_service/requirements.txt

# NLTK data needed by the lexicon fallback scorer.
ENV NLTK_DATA=/usr/share/nltk_data
RUN python -m nltk.downloader -d /usr/share/nltk_data \
    punkt punkt_tab stopwords averaged_perceptron_tagger averaged_perceptron_tagger_eng

COPY . /app/review_service/

EXPOSE 5005
CMD ["gunicorn", "--bind", "0.0.0.0:5005", "--workers", "2", "review_service.app:app"]
