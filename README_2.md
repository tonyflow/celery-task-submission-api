1. Move HTTP Exception to `api.py` using `try/except` blocks on the API level to translate service level errors to web layer errors 
2. Database optimizations:3. 
   3. The cache can only be used currently on the `get_current_user` call.
   4. Connection pools
   5. Batching API calls
5. `async/await` pattern for all functions of the `api.py`
6. For a more elegant database connection, we can integrate [this design](https://medium.com/@tclaitken/setting-up-a-fastapi-app-with-async-sqlalchemy-2-0-pydantic-v2-e6c540be4308)
7. `hit.sh` has been updated to create a task and poll until the task is completed.
8. To run the pytests
```bash
cd /path/to/root/of/api_playground
export PYTHONPATH=api/
pytest -vvv api/tests/
```
9. Was not sure if I was supposed to change the worker implementation so I did not write any test for it.