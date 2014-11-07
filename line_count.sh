#!/bin/sh

echo "Code:"
echo
find . -name '*.py' ! -name 'tests.py' ! -name '0001_initial.py' ! -name 'manage.py' | xargs wc -l
echo
echo
echo "Tests:"
echo
find . -name 'tests.py' | xargs wc -l