#!/usr/bin/env bash
celery -A app.celery_app.celery worker -l info
