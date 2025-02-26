# FROM python:3.9-slim
FROM python:3.10-slim

WORKDIR /app

COPY ./app /app
RUN apt update 
RUN apt install openssh-client -y
RUN pip install -r requirements.txt

EXPOSE 8501

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

ENTRYPOINT ["streamlit", "run", "main.py", "--server.port=8501", "--server.address=0.0.0.0"]