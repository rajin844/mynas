# backend/app/models.py
"""
ORM models for MyNAS (SQLAlchemy 1.4+ / 2.x async-ready)
Mapped to the async engine in backend/app/db.py
"""

from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Boolean,
    JSON,
    ForeignKey,
    Float,
    Text,
    UniqueConstraint,
    Index,
)
from sqlalchemy.orm import relationship
from backend.drivers.db import Base

# Optional: keep a reference to uploaded UI image for docs
UPLOADED_UI_IMAGE = "sandbox:/mnt/data/8c597831-60b1-4da2-93c3-e6492470f606.png"


class Pool(Base):
    __tablename__ = "pools"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(128), unique=True, nullable=False, index=True)
    status = Column(String(32), nullable=False, default="UNKNOWN")
    type = Column(String(32), nullable=True)
    size = Column(String(64), nullable=True)
    used = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # relationships
    vdevs = relationship("Vdev", back_populates="pool", cascade="all, delete-orphan", lazy="selectin")
    datasets = relationship("Dataset", back_populates="pool_obj", cascade="all, delete-orphan", lazy="selectin")

    def __repr__(self):
        return f"<Pool {self.name} ({self.status})>"


class Vdev(Base):
    __tablename__ = "vdevs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    pool_id = Column(Integer, ForeignKey("pools.id", ondelete="CASCADE"), nullable=False, index=True)
    vdev_type = Column(String(32), nullable=False)  # mirror/raidz1/raidz2/raidz3/single
    role = Column(String(32), nullable=True)  # data/log/cache/spare
    meta = Column(JSON, nullable=True)

    pool = relationship("Pool", back_populates="vdevs")
    disks = relationship("VdevDisk", back_populates="vdev", cascade="all, delete-orphan", lazy="selectin")

    def __repr__(self):
        return f"<Vdev {self.id} {self.vdev_type}>"


class VdevDisk(Base):
    __tablename__ = "vdev_disks"
    id = Column(Integer, primary_key=True, autoincrement=True)
    vdev_id = Column(Integer, ForeignKey("vdevs.id", ondelete="CASCADE"), nullable=False, index=True)
    disk_name = Column(String(128), nullable=False)

    vdev = relationship("Vdev", back_populates="disks")

    def __repr__(self):
        return f"<VdevDisk {self.disk_name} (vdev={self.vdev_id})>"


class Disk(Base):
    __tablename__ = "disks"
    name = Column(String(128), primary_key=True)  # e.g. sda
    devpath = Column(String(256), nullable=False)
    size_gb = Column(Float, nullable=True)
    model = Column(String(256), nullable=True)
    vendor = Column(String(128), nullable=True)
    rotational = Column(Boolean, default=True)
    serial = Column(String(128), nullable=True)
    smart_status = Column(String(32), default="UNKNOWN")
    temp_c = Column(Float, nullable=True)
    last_seen = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("ix_disks_model", "model"),
        Index("ix_disks_vendor", "vendor"),
    )

    def __repr__(self):
        return f"<Disk {self.name} {self.model}>"


class Dataset(Base):
    __tablename__ = "datasets"
    id = Column(Integer, primary_key=True, autoincrement=True)
    pool = Column(String(128), ForeignKey("pools.name", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(256), nullable=False)  # dataset name (without pool/ prefix)
    mountpoint = Column(String(512), nullable=True)
    compression = Column(String(64), nullable=True)
    quota = Column(String(64), nullable=True)
    used = Column(String(64), nullable=True)
    options = Column(JSON, nullable=True)

    pool_obj = relationship("Pool", back_populates="datasets", lazy="joined")

    __table_args__ = (
        UniqueConstraint("pool", "name", name="uq_dataset_pool_name"),
    )

    def __repr__(self):
        return f"<Dataset {self.pool}/{self.name}>"


class Snapshot(Base):
    __tablename__ = "snapshots"
    id = Column(Integer, primary_key=True, autoincrement=True)
    dataset_id = Column(Integer, ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(256), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    used = Column(String(64), nullable=True)
    meta = Column(JSON, nullable=True)

    def __repr__(self):
        return f"<Snapshot {self.name} on ds={self.dataset_id}>"


class Share(Base):
    __tablename__ = "shares"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(128), nullable=False)
    path = Column(String(512), nullable=False)
    protocol = Column(String(32), nullable=False)  # smb/nfs
    options = Column(JSON, nullable=True)

    __table_args__ = (
        Index("ix_shares_protocol", "protocol"),
    )

    def __repr__(self):
        return f"<Share {self.name} ({self.protocol})>"


class ACL(Base):
    __tablename__ = "acl"
    id = Column(Integer, primary_key=True, autoincrement=True)
    path = Column(String(512), nullable=False, index=True)
    user = Column(String(128), nullable=False)
    permissions = Column(String(64), nullable=False)

    __table_args__ = (
        Index("ix_acl_path_user", "path", "user"),
    )

    def __repr__(self):
        return f"<ACL {self.user} @ {self.path}>"


class SmartHistory(Base):
    __tablename__ = "smart_history"
    id = Column(Integer, primary_key=True, autoincrement=True)
    disk_name = Column(String(128), nullable=False, index=True)
    status = Column(String(32), nullable=True)
    temp_c = Column(Float, nullable=True)
    raw = Column(JSON, nullable=True)
    ts = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<SmartHistory {self.disk_name} @ {self.ts}>"


class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True, autoincrement=True)
    kind = Column(String(64), nullable=False)  # scrub/snapshot/replicate
    target = Column(String(256), nullable=True)
    status = Column(String(32), default="pending")
    progress = Column(Float, default=0.0)
    meta = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Task {self.kind} {self.status}>"


class Alert(Base):
    __tablename__ = "alerts"
    id = Column(Integer, primary_key=True, autoincrement=True)
    level = Column(String(16), nullable=False)  # critical/warning/info
    source = Column(String(128), nullable=True)
    message = Column(Text, nullable=False)
    acknowledged = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<Alert {self.level}: {self.message[:60]}>"
