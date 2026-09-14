# 03_webapp

Warmup exercises building a small FastAPI app: a registration form
(warmup 3) and a JSON login endpoint (warmup 4).

## Authentication

Login checks the submitted password against the stored hash and salt for
that email, and returns 200 (with email and city) or 401. That is all it
does.

There is no session, no token set anywhere in this project.

This is not real authentication. It is verifying a password safely with the rest deliberately left out for a
future ticket.