from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.diario import Diario
from app.schemas.diario import DiarioCreate, DiarioUpdate


class DiarioRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, data: DiarioCreate) -> Diario:
        diario = Diario(**data.model_dump())
        self.db.add(diario)
        await self.db.commit()
        await self.db.refresh(diario)
        return diario

    async def get_by_url(self, url: str) -> Diario | None:
        result = await self.db.execute(select(Diario).where(Diario.url == url))
        return result.scalar_one_or_none()

    async def list(
        self,
        portal: str | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[int, list[Diario]]:
        query = select(Diario)
        if portal:
            query = query.where(Diario.portal == portal)

        count = await self.db.scalar(select(func.count()).select_from(query.subquery()))
        result = await self.db.execute(query.offset(skip).limit(limit))
        return count, result.scalars().all()

    async def update(self, diario_id: int, data: DiarioUpdate) -> Diario | None:
        result = await self.db.execute(select(Diario).where(Diario.id == diario_id))
        diario = result.scalar_one_or_none()
        if not diario:
            return None
        for field, value in data.model_dump(exclude_none=True).items():
            setattr(diario, field, value)
        await self.db.commit()
        await self.db.refresh(diario)
        return diario

    async def upsert(self, data: DiarioCreate) -> Diario:
        existing = await self.get_by_url(data.url)
        if existing:
            return existing
        return await self.create(data)
