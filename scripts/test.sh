echo "Running Python tests..."
python -m tornado.test.runtests tests/test_decorators.py
python -m tornado.test.runtests tests/test_converters.py
python -m tornado.test.runtests tests/test_validators.py