#!/bin/bash

sleep 5
flask db upgrade

flask rates load ./deployment/exchange_rates_data/exchange_rates_2018-01-01_2018-12-31.csv
flask rates load ./deployment/exchange_rates_data/exchange_rates_2019-01-01_2019-12-31.csv
flask rates load ./deployment/exchange_rates_data/exchange_rates_2020-01-01_2020-12-31.csv
flask rates load ./deployment/exchange_rates_data/exchange_rates_2021-01-01_2021-12-31.csv
flask rates load ./deployment/exchange_rates_data/exchange_rates_2022-01-01_2022-12-31.csv

exec gunicorn  -w 2 -b :8080 wallit:app
