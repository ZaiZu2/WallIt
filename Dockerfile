FROM python:3.10-slim

# Tell Docker to use bash as a default shell
SHELL ["/bin/bash", "-c"]
RUN useradd wallit
WORKDIR /home/wallit

# Set env vars pointing to virtual environment
ENV VIRTUAL_ENV=/opt/venv
RUN python -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

COPY requirements_prod.txt requirements_prod.txt
RUN pip install -r requirements_prod.txt
RUN pip install gunicorn

COPY app app
COPY migrations migrations
COPY wallit.py config.py boot.sh ./
COPY ./deployment/exchange_rates_data ./deployment/exchange_rates_data
RUN chmod +x boot.sh

ENV FLASK_APP wallit.py

RUN chown -R wallit:wallit ./
USER wallit

EXPOSE 8080

ENTRYPOINT ["./boot.sh"]
