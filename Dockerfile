FROM python:3.10

WORKDIR /app

COPY . /app

RUN pip install --upgrade pip
RUN pip install -r backend/requirements.txt

EXPOSE 7860

CMD ["python", "backend/app.py"]