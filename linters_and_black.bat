echo 'Formatting code with black...'
black --line-length 120 pymagewell
black --line-length 120 tests
echo 'Running mypy...'
mypy pymagewell
mypy tests
echo 'Running flake8...'
flake8 pymagewell
flake8 tests
