# FastCore

A user accounts API built with Python and FastAPI. I'm building it one feature at a time, and every change goes through a reviewed pull request. It currently handles registration, login and full user CRUD, with salted password hashing, request logging and a pytest suite.

This project is still in progress. The [Roadmap](#roadmap) lists what isn't built yet.

## What it does

| Method | Endpoint | What it does |
|---|---|---|
| `GET` | `/` | Serves the registration form |
| `GET` | `/login` | Serves the login form |
| `POST` | `/register` | Registers a user from the HTML form |
| `POST` | `/login` | Checks an email and password, returns 200 or 401 |
| `POST` | `/users` | Creates a user from JSON (201, or 409 if the email is taken) |
| `GET` | `/users` | Lists all users |
| `GET` | `/users/{id}` | Gets one user (404 if not found) |
| `PUT` | `/users/{id}` | Updates a user's city and/or password |
| `DELETE` | `/users/{id}` | Deletes a user (204) |

FastAPI also generates interactive API docs at `/docs` while the app is running.

## How it works

- **Password storage.** Passwords are hashed with PBKDF2-SHA256 (100,000 iterations) and a random 16-byte salt per user. Logins are checked with `hmac.compare_digest`, so the comparison takes the same time whether or not the password is right.
- **No secrets in responses.** Separate Pydantic models for input (`UserCreate`, `UserUpdate`) and output (`UserPublic`) mean the password, salt and hash never appear in any response. A test checks this.
- **Storage behind a class.** All file reading and writing lives in `UserStorage` (`storage.py`). Routes get it through FastAPI's `Depends`, so tests can swap in a temporary file without touching the real data.
- **Logging.** Middleware logs the method, path, status code and duration of every request. The register, login and CRUD routes also log their outcome.

## Run it

You need Python 3.14 and pip 25.1 or newer.

```bash
git clone https://github.com/danzgeorg/FastCore.git
cd FastCore
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install --group dev

cd warmup/03_webapp
uvicorn main:app --reload
```

Then open http://127.0.0.1:8000 for the registration form, or http://127.0.0.1:8000/docs for the API docs. Users are saved to `users.json` in the folder you run it from.

## Run the tests

From `warmup/03_webapp`:

```bash
python -m pytest
```

There are 18 tests covering create, list, get, update and delete, duplicate and invalid emails, wrong passwords, unknown ids, a corrupt JSON file, and a check that no response leaks the salt or hash. Each test uses its own temporary storage file.

## Code quality

Every pull request to `main` runs two checks in GitHub Actions ([`lint.yml`](.github/workflows/lint.yml)):

- `ruff` with every rule enabled, plus a formatting check
- `mypy` in strict mode, with extra checks on top

`main` is protected, so changes only land through a reviewed pull request. The tests don't run in CI yet (see the Roadmap).

## Project structure

```
warmup/
  01_read_csv/          Reads people.csv, validates rows, writes a summary
  02_language_features/ Exercises on decorators, context managers and generators
  03_webapp/            The FastAPI app
    main.py             Routes and middleware
    models.py           Pydantic models and password hashing
    storage.py          UserStorage: all reading and writing of users.json
    static/             Registration and login HTML forms
    tests/              pytest suite and fixtures
```

## Roadmap

Nothing below is built yet. The tickets are in the GitHub issue backlog, in order. The main project is an auction house app that grows out of this API.

**Next up**

- [ ] Upload a CSV or Excel file and summarise it with pandas ([#8](https://github.com/danzgeorg/FastCore/issues/8)), in progress
- [ ] Split the app into routers ([#15](https://github.com/danzgeorg/FastCore/issues/15))
- [ ] Jinja2 pages ([#16](https://github.com/danzgeorg/FastCore/issues/16))
- [ ] JSON logging with request ids and audit events ([#17](https://github.com/danzgeorg/FastCore/issues/17))
- [ ] Docker basics: images, containers, ports and logs ([#18](https://github.com/danzgeorg/FastCore/issues/18))

<details>
<summary>Full backlog</summary>

**FastAPI**

- [ ] Register, log in and log out with a session cookie. Right now login returns 200 or 401 and nothing remembers the user, and any caller can update or delete any user ([#24](https://github.com/danzgeorg/FastCore/issues/24))
- [ ] Sell an item and browse the market ([#25](https://github.com/danzgeorg/FastCore/issues/25))
- [ ] Roles: moderators cancel auctions, admins run the players ([#29](https://github.com/danzgeorg/FastCore/issues/29))

**Database (MySQL)**

- [ ] MySQL in a container, with SQL by hand ([#19](https://github.com/danzgeorg/FastCore/issues/19))
- [ ] SQLAlchemy and MySQL: the items table and a session per request, replacing the JSON file ([#21](https://github.com/danzgeorg/FastCore/issues/21))
- [ ] Migrations with Alembic ([#22](https://github.com/danzgeorg/FastCore/issues/22))
- [ ] Run the tests against MySQL in CI ([#23](https://github.com/danzgeorg/FastCore/issues/23)). The tests don't run in CI at all yet.
- [ ] Gold balances and a ledger that always adds up ([#26](https://github.com/danzgeorg/FastCore/issues/26))
- [ ] Place a bid: holds, refunds and row locks ([#27](https://github.com/danzgeorg/FastCore/issues/27))
- [ ] Settle auctions and pay the seller when the timer runs out ([#28](https://github.com/danzgeorg/FastCore/issues/28))

**Docker**

- [ ] Docker Compose for the database, with a healthcheck ([#20](https://github.com/danzgeorg/FastCore/issues/20))
- [ ] A production Dockerfile for the app ([#30](https://github.com/danzgeorg/FastCore/issues/30))
- [ ] The whole stack in Compose: app, database, migrations, settler ([#31](https://github.com/danzgeorg/FastCore/issues/31))
- [ ] CI builds the image and publishes it to GitHub Container Registry ([#32](https://github.com/danzgeorg/FastCore/issues/32))

**Kubernetes (local kind cluster)**

- [ ] A kind cluster running on Docker ([#33](https://github.com/danzgeorg/FastCore/issues/33))
- [ ] MySQL on Kubernetes: Secret, StatefulSet and a persistent volume ([#34](https://github.com/danzgeorg/FastCore/issues/34))
- [ ] The app on Kubernetes: Deployment, Service, probes and a migration Job ([#35](https://github.com/danzgeorg/FastCore/issues/35))
- [ ] Open the site from the browser and settle auctions with a CronJob ([#36](https://github.com/danzgeorg/FastCore/issues/36))

**Helm**

- [ ] Install, upgrade and roll back someone else's chart ([#37](https://github.com/danzgeorg/FastCore/issues/37))
- [ ] Helm charts for MySQL and the auction app ([#38](https://github.com/danzgeorg/FastCore/issues/38))
- [ ] Releases with Helm: new versions, a failed upgrade, rollback and `helm test` ([#39](https://github.com/danzgeorg/FastCore/issues/39))

</details>

## Licence

[MIT](LICENSE)
