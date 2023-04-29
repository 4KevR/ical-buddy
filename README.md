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
Depending on the environment, you need a suitable web server configuration to expose your buddy to the web. This can be done with nginx but you can of course use the web server of your choice. For nginx, you can create a new configuration in your `sites-available` directory of nginx, often `/etc/nginx/sites-available`. There, you can use the following template when the **production** environment is used:
```
server {
    server_name <your domain>;
    location / {
        include         uwsgi_params;
        uwsgi_pass      127.0.0.1:5000;
    }
    listen 80;
}
```
Make sure to activate your configuration by using `sudo ln -s /etc/nginx/sites-available/<name> /etc/nginx/sites-enabled` and restarting your nginx service.

Of course, you can also add SSL configurations to this file so that you can securely access the web service. The simplest way to add SSL certificates to your site is to use Let's Encrypt and therefore [certbot](https://certbot.eff.org) which can also modify your nginx configuration to use port 443 and serve the generated SSL certificates.
