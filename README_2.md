### Notes on the implementation
1. `hit.sh` has been updated to create a task and poll until the task is completed.
2. To run the pytests
```bash
cd /path/to/root/of/api_playground
export PYTHONPATH=api/
pytest -vvv api/tests/
```
3. Was not sure if I was supposed to change the worker implementation so I did not write any test for it. We can test overflows at a later stage.
4. The cache in the `get_current_user` is just for showcase and the docs describe its limitations.
5. The cache can also be used to cache addition results.
6. The k8s deployment is fully functional but I did not plug it to a cloud environment. If you're using `kind`, you can use `deploy.sh` to bootstrap the cluster.
7. Install metrics service and configure a `HorizontalPodAutoscaler`
8. The docker deployment uses a process pool of size 5 (`concurrency=5`)
9. Persistent volumes have been created to store both Postgres and RabbitMQ data. `PersistentVolumeClaims` for k8s.

### TODOs
1. Move HTTP Exception to `api.py` using `try/except` blocks on the API level to translate service level errors to web layer errors
2. Database optimizations: 
   3. The cache can only be used currently on the `get_current_user` call.
   4. Connection pools
   5. Batching API calls
6. For a more elegant database connection, we can integrate [this design](https://medium.com/@tclaitken/setting-up-a-fastapi-app-with-async-sqlalchemy-2-0-pydantic-v2-e6c540be4308)
7. Event-driven worker autoscaling using `KEDA`: Workers can scale based on the size of the RabbitMQ queue. This can limit the potential number of IDLE Celery workers.