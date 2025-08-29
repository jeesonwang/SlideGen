from datetime import datetime

from celery import states  # type: ignore
from sqlalchemy import DateTime, Integer, LargeBinary, PickleType, Sequence, Text
from sqlmodel import Column, Field

from slidegen.models.base import Base
from slidegen.utils.time import now_datetime


class CeleryTask(Base, table=True):
    """Task result/status."""

    __tablename__ = "celery_taskmeta"

    id: int = Field(sa_column=Column(Integer, Sequence("task_id_sequence"), primary_key=True, autoincrement=True))
    task_id: str = Field(max_length=155, unique=True, description="task id")
    status: str = Field(default=states.PENDING, max_length=50, description="task status")
    result: PickleType | None = Field(
        default=None, sa_column=Column(PickleType, nullable=True), description="task result"
    )
    date_done: datetime | None = Field(
        sa_column=Column(
            DateTime(timezone=True),
            default=now_datetime,
            onupdate=now_datetime,
            nullable=True,
        ),
        description="done time",
    )
    traceback: str | None = Field(default=None, sa_column=Column(Text, nullable=True), description="error traceback")
    name: str | None = Field(default=None, max_length=155, description="task name")
    args: bytes | None = Field(default=None, sa_column=Column(LargeBinary, nullable=True), description="args")
    kwargs: bytes | None = Field(default=None, sa_column=Column(LargeBinary, nullable=True), description="kwargs")
    worker: str | None = Field(default=None, max_length=155, description="worker")
    retries: int | None = Field(default=None, description="retries")
    queue: str | None = Field(default=None, max_length=155, description="queue")


class CeleryTaskSet(Base, table=True):
    """TaskSet result."""

    __tablename__ = "celery_tasksetmeta"

    id: int = Field(sa_column=Column(Integer, Sequence("taskset_id_sequence"), autoincrement=True, primary_key=True))
    taskset_id: str = Field(max_length=155, unique=True, description="taskset id")
    result: PickleType | None = Field(
        default=None, sa_column=Column(PickleType, nullable=True), description="taskset result"
    )
    date_done: datetime | None = Field(
        sa_column=Column(DateTime(timezone=True), default=now_datetime, nullable=True), description="done time"
    )
