from datetime import datetime
from typing import Iterable

import croniter
from flask_apscheduler import APScheduler
from flask_sqlalchemy import SQLAlchemy
import requests
from sqlalchemy import event, func, inspect
from sqlalchemy.orm import Mapped, mapped_column, validates

from app.src import enums
from app.src.modules import image as eimage

db = SQLAlchemy()
scheduler = APScheduler()


class _BaseModel(db.Model):
    __abstract__ = True

    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow())
    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow, onupdate=datetime.utcnow)

    def as_dict(self, exclude: Iterable[str] = None, timestamps: bool = False):
        exclude = [] if exclude is None else exclude

        if not timestamps:
            exclude = list(set(exclude + ['created_at', 'updated_at']))

        # reference: https://stackoverflow.com/a/22466189
        return {
            field.name: getattr(self, field.name)
            for field in self.__table__.c if field.name not in exclude
        }


class Bookmark(_BaseModel):
    __tablename__ = 'bookmarks'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    # autoincrement by `generate_ordering`
    ordering: Mapped[int] = mapped_column(unique=True)
    company: Mapped[enums.EtaCompany]
    route: Mapped[str]
    direction: Mapped[enums.RouteDirection]
    service_type: Mapped[str]
    stop_code: Mapped[str]
    lang: Mapped[enums.EtaLocale]


class Schedule(_BaseModel):
    __tablename__ = 'schedules'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    schedule: Mapped[str]
    eta_type: Mapped[str]
    layout: Mapped[str]
    is_partial: Mapped[bool] = mapped_column(default=False)
    enabled: Mapped[bool] = mapped_column(default=False)

    def add_job(self) -> None:
        job_id = str(self.id)
        cron = self.schedule.split(' ')
        scheduler.add_job(job_id,  # invoking str() here makes the formatter unhappy
                          requests.get,
                          kwargs={
                              'url': 'http://localhost:8192/api/display/refresh',
                              'params': {
                                  'eta_type': eimage.enums.EtaType(self.eta_type),
                                  'layout': self.layout,
                                  'is_partial': self.is_partial
                              },
                          },
                          trigger='cron',
                          minute=cron[0],
                          hour=cron[1],
                          day=cron[2],
                          month=cron[3],
                          day_of_week=cron[-1])

    def remove_job(self) -> None:
        scheduler.remove_job(str(self.id))

    def __repr__(self) -> str:
        return f"Schedule({self.id}, {self.schedule})"

    @validates("schedule")
    def validate_schedule(self, key, schedule: "Schedule"):
        if (not croniter.croniter.is_valid(schedule)):
            raise SyntaxError('Invalid cron expression')
        return schedule


# ------------------------------------------------------------
#                       Event Listeners
# ------------------------------------------------------------

@event.listens_for(Schedule, 'after_insert')
def add_refresh_job(mapper, connection, target: Schedule):
    if target.enabled:
        target.add_job()


@event.listens_for(Schedule, 'after_delete')
def remove_refresh_job(mapper, connection, target: Schedule):
    if target.enabled:
        target.remove_job()


@event.listens_for(Schedule, 'after_update')
def update_refresh_job(mapper, connection, target: Schedule):
    old_values: dict = inspect(target).committed_state

    if old_values.get('enabled') is True and target.enabled == False:
        # is disabling
        target.remove_job()
    if target.enabled:
        target.add_job()


@event.listens_for(Bookmark, 'before_insert')
def generate_ordering(mapper, connection, target: Bookmark):
    if target.ordering is not None:
        return target

    crrt_max = db.session.query(func.max(Bookmark.ordering)).scalar()
    if crrt_max is None:
        crrt_max = -1

    # BUG: possible inconsistent with high traffic
    target.ordering = crrt_max + 1
    return target
