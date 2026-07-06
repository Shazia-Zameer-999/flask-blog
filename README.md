# ShazBlog

A production-minded publishing application built with Flask and MongoDB. Readers can discover and search articles, authenticated members can publish and manage stories, join discussions, and maintain a profile.

## Features

- Local authentication plus optional Google, GitHub, LinkedIn, and Facebook OAuth
- Article create, edit, publish/draft, delete, search, category filters, and pagination
- Article cover and profile avatar uploads from either a computer or an image URL
- Authenticated comments, editable profiles, and a persisted contact inbox
- CSRF protection, secure session defaults, ownership authorization, validation, friendly errors, and MongoDB indexes
- Responsive, keyboard-accessible interface with reduced-motion support

## Local setup

1. Create and activate a virtual environment.
2. Install dependencies: `pip install -r requirements.txt`
3. Copy `.env.example` to `.env` and set `SECRET_KEY` and `MONGO_URI`.
4. Create database indexes: `flask --app app init-db`
5. Run: `flask --app app run --debug --port 9000`

For production, run `gunicorn 'app:app'`, use an HTTPS reverse proxy, set a strong secret, and provide a managed MongoDB connection string. OAuth buttons only appear for providers with configured credentials.

Uploaded JPG, PNG, GIF, and WebP files are stored in `static/uploads` and are capped by the 2 MB request limit. For horizontally scaled production deployments, mount persistent shared storage or replace the local save helper with object storage such as S3.

## Data collections

- `users`: identity, provider, profile, and role
- `posts`: article content, publication state, author, and timestamps
- `comments`: article discussion linked to users and posts
- `messages`: contact submissions and triage status

Run `pytest` for the lightweight application checks.
