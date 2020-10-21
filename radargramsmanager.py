from models import db, Project, Radargram, Trace
from radargramio import load_rdr
import datetime
from flask import g

def _check_project_by_user(project_id):
    projects = Project.query.filter_by(user_id=g.user.id, id=project_id)
    return projects is not None

def get_radargrams(project_id: int):
    if not _check_project_by_user(project_id):
        return None
    projects = Project.query.filter_by(user_id=g.user.id, id=project_id)
    if projects is None:
        return None
    radargrams = Radargram.query.filter_by(project_id=project_id)
    return radargrams


def get_radargram(project_id: int, radargram_id: int):
    if not _check_project_by_user(project_id):
        return None
    radargram = Radargram.query.filter_by(id=radargram_id, project_id=project_id).first()
    return radargram


def get_radargram_link(project_id: int, radargram_id: int):
    if not _check_project_by_user(project_id):
        return None
    radargram = Radargram.query.filter_by(id=radargram_id, project_id=project_id).first()
    file_name = radargram.file_name
    from s3work import get_link
    link = get_link(file_name)
    return link


def add_radargram(project_id: int, name: str, file, filename: str):
    if not _check_project_by_user(project_id):
        return None

    # from s3work import upload_file
    # upload_file(file, filename)
    # file.seek(0)

    data = load_rdr(file)
    if data is None: return False
    RadInfo, TrajectoryInfo, _, _, Notes, _ = data
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

    radargram = Radargram(project_id, name, filename, notes, stage_between_traces, time_base, traces_count, samples_count,
                          distance_between_antennas, default_velocity, GPR_unit, antenna_name, frequency, creation_datetime)
    db.session.add(radargram)
    db.session.commit()

    add_traces(project_id, radargram.id, RadInfo["DataTrace"], RadInfo["CoordTraces"], RadInfo["PK"])
    return radargram


def delete_radargram(project_id: int, radargram_id: int):
    if not _check_project_by_user(project_id):
        return None
    radargram = Radargram.query.filter_by(id=radargram_id, project_id=project_id).first()
    if radargram is not None:
        from s3work import delete_file
        delete_file(radargram.file_name)
        db.session.delete(radargram)
        db.session.commit()
        return True
    else:
        return False


def add_traces(project_id: int, radargram_id: int, DataTrace, CoordTraces, PK):
    if not _check_project_by_user(project_id):
        return None
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


def get_traces_headers(project_id: int, radargram_id: int):
    if not _check_project_by_user(project_id):
        return None
    traces = Trace.query.filter_by(radargram_id=radargram_id)
    return traces


def get_trace(project_id: int, radargram_id: int, trace_id: int):
    if not _check_project_by_user(project_id):
        return None
    trace = Trace.query.filter_by(id=trace_id, radargram_id=radargram_id).first()
    return trace


def get_traces_amplitudes(project_id: int, radargram_id: int, start_num: int, finish_num: int, stage: int):
    if not _check_project_by_user(project_id):
        return None
    traces = []
    for num in range(int(start_num), int(finish_num)+1, int(stage)):
        trace = Trace.query.filter_by(number=num, radargram_id=radargram_id).first()
        if trace is not None:
            traces.append(trace)
    return traces