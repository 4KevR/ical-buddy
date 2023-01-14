# ical-buddy
***Work in progress - expect bugs***

Do you subscribe to ICal calendars that contain parts of information that you don't need?

If that's the case, the ical-buddy can assist you. It's a tool ready to be self-hosted on a server with Docker available, and it demonstrates the power of vanilla Bootstrap 5.

## Features
The basic feature is to take public ICal calendars and filter out entries with pre-configured names. The server creates a new publicly exposed URL that can be entered into a calendar of your choice that supports the consumption of public ICal calendars. Additionally, the buddy supports the following:
* ICal profile management
* Authentication via JWT
* Account management
* Registration via OTP codes

## Set up
To set up the server, clone the repository and create the file *.env* based on the content from *.env.example*. Set all the environment variables accordingly:
1. ENVIRONMENT: production or development
    * development: Uses the basic werkzeug http server from flask for a simple configuration
    * production: Uses a uWsgi configuration to set up a server which can comminucate via the uwsgi protocol
2. JWT_SECRET_KEY: Random string that is used for the signing of the JWT cookies
3. JWT_COOKIE_SECURE: True or False (depends on your server configuration - set on True for https)
4. INITIAL_OTP: The entered code can be used to register the first admin account of the instance

The last step includes starting the Docker container, which can be done with the command:
```
docker-compose up --build -d
```
Depending on the environment, you need a suitable webserver configuration (e.g., nginx) to expose your buddy to the web (more information about the configuration will follow in the future).
