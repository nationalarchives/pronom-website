FROM ghcr.io/nationalarchives/tna-python
COPY lambdas /app/lambdas
COPY app/app.py poetry.lock pyproject.toml indexes /app/
USER root
RUN chown -R app /app
USER app
RUN tna-build
ENTRYPOINT ["tna-run", "app:app"]
