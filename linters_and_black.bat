echo 'Formatting code with black...'
black --line-length 120 src/pymagewell
black --line-length 120 src/tests
echo 'Running mypy...'
mypy src/pymagewell
mypy src/tests
echo 'Running flake8...'
flake8 src/pymagewell
flake8 src/tests
