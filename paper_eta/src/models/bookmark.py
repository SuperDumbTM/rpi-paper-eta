from sqlalchemy import event, func
from sqlalchemy.orm import Mapped, mapped_column

from paper_eta.src.libs.hketa import enums

from ...src import extensions
from ._base import BaseModel


class Bookmark(BaseModel):
    __tablename__ = 'bookmarks'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    # autoincrement by `generate_ordering`
    ordering: Mapped[int]  # = mapped_column(unique=True)
    transport: Mapped[enums.Transport]
    no: Mapped[str]
    direction: Mapped[enums.Direction]
    service_type: Mapped[str]
    stop_id: Mapped[str]
    locale: Mapped[enums.Locale]


@event.listens_for(Bookmark, 'before_insert')
def generate_ordering(mapper, connection, target: Bookmark):
    if target.ordering is not None:
        return target

    crrt_max = extensions.db.session.query(
        func.max(Bookmark.ordering)).scalar()
    if crrt_max is None:
        crrt_max = -1

    # BUG: possible inconsistent with high traffic
    target.ordering = crrt_max + 1
    return target
