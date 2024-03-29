# Используйте официальный образ Python как образ родителя
FROM python:3.8.0

# Установите рабочую директорию в контейнере
WORKDIR /TESTASK

# Копируйте файлы зависимостей в контейнер
COPY requirements.txt .

# Установите любые зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируйте содержимое вашего приложения в контейнер
COPY . .

# Укажите команду для запуска вашего приложения
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]
