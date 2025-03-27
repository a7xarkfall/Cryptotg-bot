FROM python:3.11-slim

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

# Делаем start.sh исполняемым здесь
RUN chmod +x start.sh

# Команда запуска
CMD ["./start.sh"]
