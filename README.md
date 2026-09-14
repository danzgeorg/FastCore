# FastCore
FastCode is a production-ready backend application built with Python and FastAPI, featuring PostgreSQL persistence, layered architecture, automated testing, Docker-based development, CI/CD, structured logging, and deployment to a live environment.

Login checks the submitted username and password against a stored hash and returns a 200 or 401 status code. There's no session, no token, no cookies. The browser has no way to prove to a later request that the user is logged in.