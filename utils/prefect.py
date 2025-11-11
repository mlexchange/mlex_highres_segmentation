import asyncio

from prefect import get_client
from prefect.client.schemas.objects import DeploymentStatus


async def _check_prefect_ready():
    async with get_client() as client:
        healthcheck_result = await client.api_healthcheck()
        if healthcheck_result is not None:
            raise Exception("Prefect API is not healthy.")


def check_prefect_ready():
    return asyncio.run(_check_prefect_ready())


async def _check_prefect_worker_ready(deployment_name: str):
    async with get_client() as client:
        deployment = await client.read_deployment_by_name(deployment_name)
        assert (
            deployment
        ), f"No deployment found in config for deployment_name {deployment_name}"
        if deployment.status != DeploymentStatus.READY:
            raise Exception("Deployment used for training and inference is not ready.")


def check_prefect_worker_ready(deployment_name: str):
    return asyncio.run(_check_prefect_worker_ready(deployment_name))

async def _get_flow_run_parent_id(flow_run_id):
    async with get_client() as client:
        child_flow_run = await client.read_flow_run(flow_run_id)
        parent_task_run_id = child_flow_run.parent_task_run_id
        parent_task_run = await client.read_task_run(parent_task_run_id)
        return parent_task_run.flow_run_id


def get_flow_run_parent_id(flow_run_id):
    return asyncio.run(_get_flow_run_parent_id(flow_run_id))
