import datetime
from passlib.apps import custom_app_context as pwd_context

from app import app, db


class User(db.Model):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(32), index=True)
    password_hash = db.Column(db.String(128))
    projects = db.relationship('Project', backref='user', cascade="all, delete-orphan")

    def hash_password(self, password):
        self.password_hash = pwd_context.encrypt(password)

    def verify_password(self, password):
        return pwd_context.verify(password, self.password_hash)


class Project(db.Model):
    __tablename__ = "project"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(1000), nullable=False)
    notes = db.Column(db.Text)
    creation_datetime = db.Column(db.DateTime, nullable=False, default=datetime.datetime.utcnow)
    radargrams = db.relationship('Radargram', backref='project', cascade="all, delete-orphan")
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __init__(self, name, notes):
        self.name = name
        self.notes = notes

    def __repr__(self):
        return f"<Project {self.name}>"

    @property
    def serialize(self):
        return {
            "id": self.id,
            "name": self.name,
            "notes": self.notes,
            "createion_datetime": self.creation_datetime
        }


class Radargram(db.Model):
    __tablename__ = "radargram"

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    name = db.Column(db.String(1000), nullable=False)
    notes = db.Column(db.Text)
    stage_between_traces = db.Column(db.Float, nullable=False)
    time_base = db.Column(db.Float, nullable=False)
    traces_count = db.Column(db.Integer, nullable=False)
    samples_count = db.Column(db.Integer, nullable=False)
    distance_between_antennas = db.Column(db.Float, nullable=False)
    default_velocity = db.Column(db.Float, nullable=False)
    GPR_unit = db.Column(db.String(1000), nullable=False)
    antenna_name = db.Column(db.String(1000), nullable=False)
    frequency = db.Column(db.Float, nullable=False)
    creation_datetime = db.Column(db.DateTime, nullable=False, default=datetime.datetime.utcnow)
    traces = db.relationship('Trace', backref='radargram', cascade="all, delete-orphan")

    def __init__(self, project_id, name, notes, stage_between_traces, time_base, traces_count, samples_count, distance_between_antennas,
                 default_velocity, GPR_unit, antenna_name, frequency, creation_datetime):
        self.project_id = project_id
        self.name = name
        self.notes = notes
        self.stage_between_traces = stage_between_traces
        self.time_base = time_base
        self.traces_count = traces_count
        self.samples_count = samples_count
        self.distance_between_antennas = distance_between_antennas
        self.default_velocity = default_velocity
        self.GPR_unit = GPR_unit
        self.antenna_name = antenna_name
        self.frequency = frequency
        self.creation_datetime = creation_datetime

    def __repr__(self):
        return f"<Radargram {self.name}>"

    @property
    def serialize(self):
        return {
            "id": self.id,
            "project_id": self.project_id,
            "name": self.name,
            "notes": self.notes,
            "stage_between_traces": self.stage_between_traces,
            "time_base": self.time_base,
            "traces_count": self.traces_count,
            "samples_count": self.samples_count,
            "distance_between_antennas": self.distance_between_antennas,
            "default_velocity": self.default_velocity,
            "GPR_unit": self.GPR_unit,
            "antenna_name": self.antenna_name,
            "frequency": self.frequency,
            "creation_datetime": self.creation_datetime
        }


class Trace(db.Model):
    __tablename__ = "trace"

    id = db.Column(db.Integer, primary_key=True)
    radargram_id = db.Column(db.Integer, db.ForeignKey('radargram.id'), nullable=False)
    number = db.Column(db.Integer, nullable=False)
    X = db.Column(db.Float, nullable=False)
    Y = db.Column(db.Float, nullable=False)
    Z = db.Column(db.Float, nullable=False)
    PK = db.Column(db.Float, nullable=False)
    # sample_of_surface = db.Column(db.Integer, nullable=False)
    amplitudes = db.Column(db.PickleType, nullable=False)
    # time_collecting = db.Column(db.DateTime, nullable=False, default=datetime.datetime.utcnow)

    def __init__(self, radargram_id, number, X, Y, Z, PK, amplitudes):
        self.radargram_id = radargram_id
        self.number = number
        self.X = X
        self.Y = Y
        self.Z = Z
        self.PK = PK
        self.amplitudes = amplitudes

    def __repr__(self):
        return f"<Trace {self.name} #{self.number} (X={self.X}, Y={self.Y}, Z={self.Z})>"

    @property
    def serialize(self):
        return {
            "id": self.id,
            "radargram_id": self.radargram_id,
            "number": self.number,
            "X": self.X,
            "Y": self.Y,
            "Z": self.Z,
            "PK": self.PK,
            #"amplitudes": list(self.amplitudes)
        }


