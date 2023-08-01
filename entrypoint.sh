#!/bin/bash
echo "[+] ------ Apply database migrations ------ [+]"

python3 manage.py migrate

# echo "[+] ------ Populating Cities Light Data ------ [+]"
# python3 manage.py cities_light

#echo "[+] ------ Check for SuperUser and if not than create ------ [+]"
python3 manage.py makesuper

echo "Starting server"

# Start server
python3 manage.py runserver 0.0.0.0:8000
