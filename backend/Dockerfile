FROM python:3.12-alpine
WORKDIR /app
COPY ./requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt
COPY ./subabot /app/subabot
CMD ["uvicorn", "subabot.main:app", "--host", "0.0.0.0", "--port", "8000", "--log-level", "debug"]
