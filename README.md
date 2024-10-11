# Setup instructions

1. install docker
2. run `docker compose up --build`
3. Backend url (http://0.0.0.0:8000)
4. frontend url (http://localhost:8501)

# Install docker on EC2 instance
Based on the error messages you're encountering, it seems Docker is not properly installed on your Amazon Linux 2023 EC2 instance. Let's go through the steps to install and configure Docker on Amazon Linux 2023:

1. Update the system packages:

```bash
sudo yum update -y
```

2. Install Docker and python3:

```bash
sudo yum install docker -y
sudo yum install python3 python3-pip -y
```

3. Start the Docker service:

```bash
sudo systemctl start docker
```

4. Enable Docker to start on boot:

```bash
sudo systemctl enable docker
```

5. Add your user to the docker group:

```bash
sudo usermod -a -G docker ec2-user
```

6. Verify Docker installation:

```bash
docker --version
```

7. Check Docker service status:

```bash
sudo systemctl status docker
```

8. Log out and log back in for the group changes to take effect, or run:

```bash
newgrp docker
```

9. Verify you can run Docker commands without sudo:

```bash
docker info
```

If you encounter any issues with these steps, you may need to reboot the instance:

```bash
sudo reboot
```

After rebooting, log back in and try running Docker commands again.

If you're still facing issues after following these steps, please provide the output of the following commands:

```bash
sudo yum list installed | grep docker
sudo systemctl status docker
```