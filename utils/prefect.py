import asyncio
from typing import Optional

from prefect import get_client
from prefect.client.schemas.filters import (
    FlowRunFilter,
    FlowRunFilterName,
    FlowRunFilterTags,
)


async def _schedule(
    deployment_name: str,
    flow_run_name: str,
    parameters: Optional[dict] = None,
    tags: Optional[list] = [],
):
    async with get_client() as client:
        deployment = await client.read_deployment_by_name(deployment_name)
        assert (
            deployment
        ), f"No deployment found in config for deployment_name {deployment_name}"
        flow_run = await client.create_flow_run_from_deployment(
            deployment.id,
            parameters=parameters,
            name=flow_run_name,
            tags=tags,
        )
    return flow_run.id


def schedule_prefect_flow(
    deployment_name: str,
    parameters: Optional[dict] = None,
    flow_run_name: Optional[str] = None,
    tags: Optional[list] = [],
):
    if not flow_run_name:
        model_name = parameters["model_name"]
        flow_run_name = f"{deployment_name}: {model_name}"
    flow_run_id = asyncio.run(
        _schedule(deployment_name, flow_run_name, parameters, tags)
    )
    return flow_run_id


async def _get_name(flow_run_id):
    async with get_client() as client:
        flow_run = await client.read_flow_run(flow_run_id)
        if flow_run.state.is_final():
            if flow_run.state.is_completed():
                return flow_run.name
        return None


def get_flow_run_name(flow_run_id):
    """Retrieves the name of the flow with the given id."""
    return asyncio.run(_get_name(flow_run_id))


async def _flow_run_query(tags, flow_run_name=None):
    flow_runs_by_name = []
    async with get_client() as client:
        flow_runs = await client.read_flow_runs(
            flow_run_filter=FlowRunFilter(
                name=FlowRunFilterName(like_=flow_run_name),
                tags=FlowRunFilterTags(all_=tags),
            ),
            sort="START_TIME_DESC",
        )
        for flow_run in flow_runs:
            if flow_run.state_name == "Failed":
                flow_name = f"❌ {flow_run.name}"
            elif flow_run.state_name == "Completed":
                flow_name = f"✅ {flow_run.name}"
            else:
                flow_name = f"🕑 {flow_run.name}"
            flow_runs_by_name.append({"label": flow_name, "value": str(flow_run.id)})
        return flow_runs_by_name


def query_flow_run(tags, flow_run_name=None):
    return asyncio.run(_flow_run_query(tags, flow_run_name))
