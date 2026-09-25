FROM python:3.12-slim
WORKDIR /app
COPY . .
CMD ["python","-c","from security_platform import SecurityPolicy; print('security policy ready')"]
