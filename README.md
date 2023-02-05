# WallIt - protect your wallet from petty expenses

To experience the deployed app, click [here](https://wallit.fly.dev/).
You can use credentials given in the login placeholders to omit account creation.

### ***Features***
Wallit was created as a remedy to the end-of-the-month confusion, when expenses, which you supposedly kept under a very strict control, yet again consumed your whole monthly wage. It allows you to focus on the essential task of controlling your cash flow, while abstracting away all the annoying parts of the process.
  - Sift, sort, skim through and filter your transactions in a functional table.
  - Do you buy useless trinkets from AliExpress with USD, spend EUR on Amazon and do your groceries using local currency? No problem, set your account currency, and all your transactions will be automatically exchanged to the target currency.
  - There's no need to document every smallest transaction - import your bank statements, and WallIt will parse all the transactions for you.
  - Add, modify or delete transactions if you want to be CRUDe.
  - Manage and assign custom categories to transactions, to discern necessities from financial mistakes.
  - Leverage dynamically generated charts to understand trends in your spendings. Yes, those bars visualize it better than you probably can.

### ***Tech Stack***
  - Frontend – HTML, CSS, JavaScript, Preact, ChartJS, GridJS
  - Backend – Flask, Marshmallow, SQLAlchemy, Alembic, PostgreSQL, Nginx, Docker
### ***Backend***
#### 1. Server-side rendering
While this is not a pure SPA application, there are only two main endpoints for which content is server-side rendered.
#### 2. API
Majority of WallIt functionality is provided with Ajax calls. API part of the application is clearly separated from SSR part, with standardized routes and using REST-like principles.
#### 3. Database
Application utilizes PostgreSQL database, with the help of SQLAlchemy and Alembic. It features complete migration history.
#### 4. CLI
Custom CLI commands for downloading/loading exchange rate is implemented. This allows to run Cron Jobs to update exchange rates daily.
#### 5. Validation
Input validation is conducted in two ways. For welcome page, all inputs are validated using WTForms. Addionally, ORM models have various Marshmallow schemas assigned, which are used to validate data sent to API endpoints. Reason behind implementing various validation methods is purely educational - in the future, the app is expected to use only Marshmallow.
#### 6. Unit tests
Unit tests are performed using Pytest. pytest-cov is used for generating coverage reports.
#### 7. Deployment
Wallit is continuously deployed on fly.io PaaS with a Postgres cluster. Instead of using native python platform, Dockerfile is leveraged to provide maximum compatibility. Additionally, docker-compose file is present with a configuration for Nginx serving static files, while forwarding request to gUnicorn.

### ***Frontend***
#### 1. HTML & CSS
While frontend was never the focus of this project, the presentational layer is unfortunately necessary. It also posed a perfect chance to gain understanding of how frontend intertwines with the backend, how web pages work and interact with user. The CSS for this app is completely custom-made. Was it necessary? Probably not. Did it equip me with solid understanding of web page styling? Definitely.
#### 2. Interactiveness
This app relies heavily on Vanilla JS to offer interactiveness to the user. In later phases, dynamic components were started to be built with the use of PReact. In the future, most of the interactiveness is expected to be provided by PReact.
#### 3. Charts
ChartsJS are used to dynamically draw charts in response to changed parameters.
#### 4. Table
The main table in the app is heavily-styled GridJS table plugin.

### ***Disclaimer***
  This application is purely educational endeavor. It's general concept guided me on my learning path, allowing me to recognize various issues and the tools necessary to deal with them. There are more and less obvious bugs in the code. As this application accompanied me from the very start, every line of this code was rewritten at least multiple times, yet the mistakes of old (and also recent) days are still present. Most of them are known to the author, and are scheduled to be dealt with.
