from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from inndxd_core.models.data_item import DataItem
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from inndxd_api.dependencies import get_db, get_tenant_id
from inndxd_api.schemas.data_item import DataItemList, DataItemRead

router = APIRouter()


@router.get("/", response_model=DataItemList)
async def list_data_items(
    project_id: UUID | None = None,
    brief_id: UUID | None = None,
    tenant_id: UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(DataItem).where(DataItem.tenant_id == tenant_id)

    if project_id:
        stmt = stmt.where(DataItem.project_id == project_id)
    if brief_id:
        stmt = stmt.where(DataItem.brief_id == brief_id)

    stmt = stmt.order_by(DataItem.created_at.desc())

    result = await db.execute(stmt)
    items = list(result.scalars().all())
    return DataItemList(data_items=items)


@router.get("/{data_item_id}", response_model=DataItemRead)
async def get_data_item(
    data_item_id: UUID,
    tenant_id: UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    data_item = await db.get(DataItem, data_item_id)
    if data_item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    if data_item.tenant_id != tenant_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    return data_item
