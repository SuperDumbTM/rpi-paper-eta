# pylint: disable=too-few-public-methods

import logging
from datetime import datetime
from typing import Iterable

import apscheduler.jobstores.base
import croniter
from flask import current_app
from sqlalchemy import event, func, inspect
from sqlalchemy.orm import Mapped, mapped_column, validates

from paper_eta.src import extensions, site_data
from paper_eta.src.libs import hketa, renderer, refresher


class BaseModel(extensions.db.Model):
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


class Bookmark(BaseModel):
    __tablename__ = 'bookmarks'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    # autoincrement by `generate_ordering`
    ordering: Mapped[int]  # = mapped_column(unique=True)
    transport: Mapped[hketa.Company]
    no: Mapped[str]
    direction: Mapped[hketa.Direction]
    service_type: Mapped[str]
    stop_id: Mapped[str]
    locale: Mapped[hketa.Locale]
    enabled: Mapped[bool] = mapped_column(default=True)


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


class Schedule(BaseModel):
    __tablename__ = 'schedules'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    schedule: Mapped[str]
    eta_format: Mapped[str]
    layout: Mapped[str]
    is_partial: Mapped[bool] = mapped_column(default=False)
    enabled: Mapped[bool] = mapped_column(default=False)

    def __repr__(self) -> str:
        return f"Schedule({self.id}, {self.schedule})"

    def add_job(self) -> None:
        job_id = str(self.id)
        cron = self.schedule.split(' ')

        if extensions.scheduler.get_job(job_id) is not None:
            extensions.scheduler.remove_job(job_id)

        # BUG: hardcoded URL
        extensions.scheduler.add_job(job_id,  # invoking str() here makes the formatter unhappy
                                     refresher.refresh,
                                     kwargs={
                                         'epd_brand': site_data.AppConfiguration()['epd_brand'],
                                         'epd_model': site_data.AppConfiguration()['epd_model'],
                                         'eta_format': renderer.EtaFormat(self.eta_format),
                                         'layout': self.layout,
                                         'is_partial': self.is_partial,
                                         'is_dry_run': site_data.AppConfiguration()['dry_run'],
                                         'screen_dump_dir': current_app.config['DIR_SCREEN_DUMP'],
                                     },
                                     trigger='cron',
                                     minute=cron[0],
                                     hour=cron[1],
                                     day=cron[2],
                                     month=cron[3],
                                     day_of_week=cron[-1])

    def remove_job(self) -> None:
        try:
            extensions.scheduler.remove_job(str(self.id))
        except apscheduler.jobstores.base.JobLookupError:
            logging.exception('Removing non-exist job.')

    @validates("schedule")
    def validate_schedule(self, key, schedule: "Schedule"):
        if not croniter.croniter.is_valid(schedule):
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
def update_refresh_job_after(mapper, connection, target: Schedule):
    old_values: dict = inspect(target).committed_state

    if old_values.get('enabled') is True and not target.enabled:
        # is disabling
        target.remove_job()
    if target.enabled:
        target.remove_job()
        target.add_job()
