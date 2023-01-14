#!/bin/bash

case "${ENVIRONMENT}" in
  production) uwsgi app.ini ;;
  development) python app.py ;;
  *) echo "ENVIRONMENT value not allowed - use either production or development" ;;
esac