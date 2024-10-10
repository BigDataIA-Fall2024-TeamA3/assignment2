# Setup instructions

1. install docker
2. run `docker compose up --build`
3. Backend url (http://0.0.0.0:8000)
4. frontend url (http://localhost:8501)


# Running them separately
```
cd fastapi
docker build -t fastapi-app .
docker run -d --name fastapi-container -p 8000:8000 fastapi-app
docker ps
```

# Errors
1. The container name "/fastapi-container" is already in use
```
# docker run -d --name fastapi-container -p 8000:8000 fastapi-app
# docker: Error response from daemon: Conflict. The container name "/fastapi-container" is already in use by 
# container "vldkfbjhebffhbefjkhebjhebjheb". You have to remove (or rename) that container to be able to reuse # # that name.
```

```
docker rm fastapi-container
docker run -d --name fastapi-container -p 8000:8000 fastapi-app
curl -X GET "http://localhost:8000/"
```