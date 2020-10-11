from models import db, Radargram, Trace
from radargramio import load_rdr
import datetime


def get_radargrams(project_id: int):
    radargrams = Radargram.query.filter_by(project_id=project_id)
    return radargrams


def get_radargram(project_id: int, radargram_id: int):
    radargram = Radargram.query.filter_by(id=radargram_id, project_id=project_id).first()
    return radargram


def add_radargram(project_id: int, filename: str, basename: str):
    data = load_rdr(filename)
    if data is None: return False
    FileName, RadInfo, TrajectoryInfo, _, _, Notes, _ = data
    name = basename
    notes = Notes
    stage_between_traces = RadInfo["dL"]
    time_base = RadInfo["TimeBase"]
    traces_count = RadInfo["DataTrace"].shape[0]
    samples_count = RadInfo["DataTrace"].shape[1]
    distance_between_antennas = RadInfo["AntDist"]
    default_velocity = RadInfo["DefaultV"]
    GPR_unit = RadInfo["GPRUnit"]
    antenna_name = RadInfo["AntenName"]
    frequency = RadInfo["Frequency"]
    creation_datetime = datetime.datetime.utcnow()

    radargram = Radargram(project_id, name, notes, stage_between_traces, time_base, traces_count, samples_count,
                          distance_between_antennas, default_velocity, GPR_unit, antenna_name, frequency, creation_datetime)
    db.session.add(radargram)
    db.session.commit()

    add_traces(radargram.id, RadInfo["DataTrace"], RadInfo["CoordTraces"], RadInfo["PK"])
    return True


def delete_radargram(project_id: int, radargram_id: int):
    radargram = Radargram.query.filter_by(id=radargram_id, project_id=project_id).first()
    if radargram is not None:
        db.session.delete(radargram)
        db.session.commit()
        return True
    else:
        return False


def add_traces(radargram_id: int, DataTrace, CoordTraces, PK):
    X = CoordTraces["X"].values
    Y = CoordTraces["X"].values
    Z = CoordTraces["X"].values
    for i in range(DataTrace.shape[0]):
        amplitudes = DataTrace[i]
        x = X[i]
        y = Y[i]
        z = Z[i]
        pk = PK[i]
        trace = Trace(radargram_id, i, x, y, z, pk, amplitudes)
        db.session.add(trace)
    db.session.commit()


def get_traces_headers(radargram_id: int):
    traces = Trace.query.filter_by(radargram_id=radargram_id)
    return traces


def get_trace(radargram_id: int, trace_id: int):
    trace = Trace.query.filter_by(id=trace_id, radargram_id=radargram_id).first()
    return trace


def get_traces_amplitudes(radargram_id: int, start_num: int, finish_num: int, stage: int):
    traces = []
    for num in range(int(start_num), int(finish_num)+1, int(stage)):
        trace = Trace.query.filter_by(number=num, radargram_id=radargram_id).first()
        if trace is not None:
            traces.append(trace)
    return traces