import logging

import apscheduler.jobstores.base
import croniter
import requests
from sqlalchemy import event, inspect
from sqlalchemy.orm import Mapped, mapped_column, validates

from .. import extensions
from ..libs import eta_img
from ._base import BaseModel


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
                                     requests.get,
                                     kwargs={
                                         'url': 'http://localhost:8192/display/refresh',
                                         'params': {
                                             'eta_format': eta_img.enums.EtaFormat(self.eta_format),
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
        try:
            extensions.scheduler.remove_job(str(self.id))
        except apscheduler.jobstores.base.JobLookupError:
            logging.exception('Removing non-exist job.')

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


@event.listens_for(Schedule, 'before_update')
def update_refresh_job(mapper, connection, target: Schedule):
    target.remove_job()  # BUG: updating disabled jobs must cause JobLookupError


@event.listens_for(Schedule, 'after_update')
def update_refresh_job(mapper, connection, target: Schedule):
    old_values: dict = inspect(target).committed_state

    if old_values.get('enabled') is True and target.enabled == False:
        # is disabling
        target.remove_job()
    if target.enabled:
        target.add_job()
