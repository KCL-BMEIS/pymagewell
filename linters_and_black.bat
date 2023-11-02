echo 'Formatting code with black...'
python -m black --line-length 120 src/pymagewell
python -m black --line-length 120 src/tests
echo 'Running mypy...'
python -m mypy src/pymagewell
python -m mypy src/tests
echo 'Running flake8...'
python -m flake8 src/pymagewell
python -m flake8 src/tests
