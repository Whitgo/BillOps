#!/usr/bin/env bash
celery -A app.celery_app.celery beat -l info
