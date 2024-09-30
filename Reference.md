# Reference

## Docker

```
docker run # (docker create + run)
docker create # creates a new container
docker start <container>
docker stop / kill <container>
docker container logs
docker ls
docker container exec
docker container rm 
docker restart
docker rename

```

### Building and running your application

When you're ready, start your application by running:
`docker compose up --build`.

Your application will be available at http://localhost:8000.

### Deploying your application to the cloud

First, build your image, e.g.: `docker build -t myapp .`.
If your cloud uses a different CPU architecture than your development
machine (e.g., you are on a Mac M1 and your cloud provider is amd64),
you'll want to build the image for that platform, e.g.:
`docker build --platform=linux/amd64 -t myapp .`.

Then, push it to your registry, e.g. `docker push myregistry.com/myapp`.

Consult Docker's [getting started](https://docs.docker.com/go/get-started-sharing/)
docs for more detail on building and pushing.

### References
* [Docker's Python guide](https://docs.docker.com/language/python/)


## Github
### Frequently used commands

```zsh
# initialises a new git
git init

```
```zsh
# Committing your changes - dont copy and run directly!
# replace as needed
# Step 1: staging your files
git add <file>
# or (adding all the files that have been changed)
git add .

# Step 2: # take a snapshot of the staging area (anything that's been added)
git commit -m "Message"

# step 3: Making sure we are on the same "level" with the merging branch (this basically fetches and auto-merges remote change on our local! and keeps us "conflict" free :D)
git pull origin <branch-name>

# Step 4: Publishing your changes
git push origin <branch-name>
```
```zsh
# If you want to ignore a file that is already checked in, you must untrack the file before you add a rule to ignore it. From your terminal, untrack the file.


git rm --cached <filename>


# For multiple fileformats / folders / whatever
git rm -rf --cached .

```

```zsh
# other commands - dont copy and run directly!
# replace as needed

# getting a remote repo on our local
git clone <.git-url>

# adding a new remote repo url
git remote add <name:origin\/upstream> <url>

# removing the remote repo
git remote rm <name>

# creating a branch called `feature-a` from current branch and checking out into it
git checkout -b feature-a

# change into the existing branch called `feature-a`
git checkout feature-a

```

### Further reading!
1. https://training.github.com/downloads/github-git-cheat-sheet.pdf
2. https://github.com/github/gitignore --> never post your envs again XD

