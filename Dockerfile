# For more information, please refer to https://aka.ms/vscode-docker-python
FROM python:3.8-slim-buster

LABEL Description="WM Upgrade Support Check" \
      UsageIndependent="docker build . -t systest/central-console-view && \
             docker run --user $(id -u):$(id -g) --rm -d -v $HOME:/host -v $(pwd):/app \
             --network docker-net -p 5003:5003 \
             --name centralconsoleview systest/central-console-view" \
      UsageDockerCompose="export CURRENT_UID=$(id -u):$(id -g); \
                          docker-compose -f docker-compose.yml up -d --build  \
                          docker-compose -f docker-compose.yml down" \
      Logs=""



EXPOSE 5003

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

# Install pip requirements
ADD requirements.txt .
RUN python -m pip install -r requirements.txt

WORKDIR /app
ADD . /app

# Switching to a non-root user, please refer to https://aka.ms/vscode-docker-python-user-rights
RUN useradd appuser && chown -R appuser /app
USER appuser

# During debugging, this entry point will be overridden. For more information, please refer to https://aka.ms/vscode-docker-python-debug
CMD ["gunicorn", "--bind", "0.0.0.0:5003", "--workers=3","--timeout", "300" ,"src.run:app"]
