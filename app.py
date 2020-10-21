import os
from flask import Flask, request, jsonify, abort, url_for, g
from flask_sqlalchemy import SQLAlchemy
from flask_httpauth import HTTPBasicAuth
from flask_cors import CORS
from werkzeug.utils import secure_filename
from transliterate import translit

import flask_s3
from flask_s3 import FlaskS3

app = Flask(__name__, static_url_path='', static_folder='')
# CORS(app)
cors = CORS(app, resources={r"/api/*": {"origins": "*"}})
app.config['CORS_HEADERS'] = 'Content-Type'

app.config.from_object(os.environ['APP_SETTINGS'])
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# @app.after_request
# def after_request(response):
#   response.headers.add('Access-Control-Allow-Origin', '*')
#   # response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
#   # response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
#   return response

db = SQLAlchemy(app)
auth = HTTPBasicAuth()

s3 = FlaskS3(app)
s3.init_app(app)
# flask_s3.create_all(app)


@app.route('/api/users/registration', methods=['POST'])
def new_user():
    from models import User
    username = request.json.get('username')
    password = request.json.get('password')
    if username is None or password is None:
        abort(400, "There is no credentials")
    if User.query.filter_by(username=username).first() is not None:
        abort(400, "Existed username")
    user = User(username=username)
    user.hash_password(password)
    db.session.add(user)
    db.session.commit()
    return jsonify({'username': user.username}), 201, {'Location': url_for('get_user', user_id=user.id, _external=True)}


@app.route('/api/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    from models import User
    user = User.query.get(user_id)
    if not user:
        abort(400, f"There is no user with id={user_id}")
    return jsonify({'username': user.username})


@app.route('/api/users/signin', methods=['POST'])
def enter_user():
    from models import User
    username = request.json.get('username')
    password = request.json.get('password')
    if username is None or password is None:
        abort(400, "There is no credentials")
    if verify_password(username, password):
        return jsonify({'username': g.user.username}), 201, {'Location': url_for('get_user', user_id=g.user.id, _external=True)}
    else:
        abort(400, "There is no such username or password")

# @app.route('/api/users', methods=['GET'])
# def get_users():
#     from models import User
#     users = User.query.all()
#     return jsonify({"users": [user.username for user in users]})

@auth.verify_password
def verify_password(username, password):
    from models import User
    user = User.query.filter_by(username = username).first()
    if not user or not user.verify_password(password):
        return False
    g.user = user
    return True


@app.route('/api/projects', methods=['GET'])
@auth.login_required
def get_projects():
    import projectmanager
    projects = projectmanager.get_projects()
    return jsonify({"projects": [project.serialize for project in projects]})


@app.route('/api/projects/<int:project_id>', methods=['GET'])
@auth.login_required
def get_project(project_id: int):
    import projectmanager
    project = projectmanager.get_project(project_id)
    if project is not None:
        return jsonify(project.serialize)
    else:
        abort(500, f"There is no project with project_id={project_id}")


@app.route('/api/projects', methods=['POST'])
@auth.login_required
def add_project():
    import projectmanager
    try:
        name = request.json.get('name')
        notes = request.json.get('notes')
        project = projectmanager.add_project(name, notes)
        if project is not None:
            return jsonify(project.serialize)
        else:
            abort(500, "Refuse adding project")
    except KeyError:
        abort(500, "There is no project name")


@app.route('/api/projects/<int:project_id>', methods=['PUT'])
@auth.login_required
def update_project(project_id: int):
    import projectmanager
    try:
        name = request.json.get('name')
        notes = request.json.get('notes')
        project = projectmanager.update_project(project_id, name, notes)
        if project is not None:
            return jsonify(project.serialize)
        else:
            abort(500, f"There is no project with project_id='{id}'")
    except KeyError:
        abort(500, "There is no project name or project notes")


@app.route('/api/projects/<int:project_id>', methods=['DELETE'])
@auth.login_required
def delete_project(project_id: int):
    import projectmanager
    ok = projectmanager.delete_project(project_id)
    if ok:
        return "Delete successfully"
    else:
        abort(500, f"There is no project with project_id='{id}'")


@app.route('/api/projects/<int:project_id>/radargrams', methods=['GET'])
@auth.login_required
def get_radargrams(project_id: int):
    import projectmanager, radargramsmanager
    project = projectmanager.get_project(project_id)
    if project is not None:
        radargrams = radargramsmanager.get_radargrams(project_id)
        return jsonify({"radargrams": [radargram.serialize for radargram in radargrams]})
    else:
        abort(500, f"There is no project with project_id={project_id}")


@app.route('/api/projects/<int:project_id>/radargrams/<int:radargram_id>', methods=['GET'])
@auth.login_required
def get_radargram(project_id: int, radargram_id: int):
    import projectmanager, radargramsmanager
    project = projectmanager.get_project(project_id)
    if project is not None:
        radargram = radargramsmanager.get_radargram(project_id, radargram_id)
        if radargram is not None:
            return jsonify(radargram.serialize)
        else:
            abort(500, f"There is no radargram with radargram_id={radargram_id}")
    else:
        abort(500, f"There is no project with project_id={project_id}")

@app.route('/api/projects/<int:project_id>/radargrams/<int:radargram_id>/link', methods=['GET'])
@auth.login_required
def get_radargram_link(project_id: int, radargram_id: int):
    import projectmanager, radargramsmanager
    project = projectmanager.get_project(project_id)
    if project is not None:
        link = radargramsmanager.get_radargram_link(project_id, radargram_id)
        if link is not None:
            return link
        else:
            abort(500, f"There is no radargram with radargram_id={radargram_id}")
    else:
        abort(500, f"There is no project with project_id={project_id}")


@app.route('/api/projects/<int:project_id>/radargrams', methods=['POST'])
@auth.login_required
def add_radargram(project_id: int):
    import projectmanager, radargramsmanager
    project = projectmanager.get_project(project_id)
    if project is not None:
        if 'datafile' not in request.files:
            abort(500, "File is not send (1)")
        file = request.files['datafile']
        if not file:
            abort(500, "File is not send (2)")
        name = os.path.basename(file.filename)
        filename = translit(file.filename, 'ru', reversed=True)
        filename = secure_filename(filename)
        filename = os.path.join(f"{g.user.id}_{project_id}_{filename}")

        return "HELLO"

        radargram = radargramsmanager.add_radargram(project_id, name, file, filename)
        if radargram is not None:
            return jsonify(radargram.serialize)
        else:
            abort(500, "Refuse adding radargram")
    else:
        return jsonify({"Error": f"There is no project with project_id={id}"})


@app.route('/api/projects/<int:project_id>/radargrams/<int:radargram_id>', methods=['DELETE'])
@auth.login_required
def delete_radargram(project_id: int, radargram_id: int):
    import projectmanager, radargramsmanager
    project = projectmanager.get_project(project_id)
    if project is not None:
        ok = radargramsmanager.delete_radargram(project_id, radargram_id)
        if ok:
            return "Delete successfully"
        else:
            abort(500, "Refuse deleting radargram")
    else:
        return jsonify({"Error": f"There is no project with project_id={project_id}"})


@app.route('/api/projects/<int:project_id>/radargrams/<int:radargram_id>/traces/headers', methods=['GET'])
@auth.login_required
def get_traces_headers(project_id: int, radargram_id: int):
    import projectmanager, radargramsmanager
    project = projectmanager.get_project(project_id)
    if project is not None:
        radargram = radargramsmanager.get_radargram(project_id, radargram_id)
        if radargram is not None:
            traces = radargramsmanager.get_traces_headers(project_id, radargram_id)
            return jsonify({"traces": [trace.serialize for trace in traces]})
        else:
            abort(500, f"There is no radargram with radargram_id={radargram_id}")
    else:
        abort(500, f"There is no project with project_id={project_id}")


@app.route('/api/projects/<int:project_id>/radargrams/<int:radargram_id>/traces/<int:trace_id>', methods=['GET'])
@auth.login_required
def get_traces(project_id: int, radargram_id: int, trace_id: int):
    import projectmanager, radargramsmanager
    project = projectmanager.get_project(project_id)
    if project is not None:
        radargram = radargramsmanager.get_radargram(project_id, radargram_id)
        if radargram is not None:
            trace = radargramsmanager.get_trace(project_id, radargram_id, trace_id)
            if trace is not None:
                data = trace.serialize
                data.update({"amplitudes": list(trace.amplitudes)})
                return jsonify(data)
            else:
                abort(500, f"There is no trace with trace_id={trace_id}")
        else:
            abort(500, f"There is no radargram with radargram_id={radargram_id}")
    else:
        abort(500, f"There is no project with project_id={project_id}")


@app.route('/api/projects/<int:project_id>/radargrams/<int:radargram_id>/traces/amplitudes/<int:start_num>/<int:finish_num>/<int:stage>', methods=['GET'])
@auth.login_required
def get_traces_amplitudes(project_id: int, radargram_id: int, start_num: int, finish_num: int, stage: int):
    import projectmanager, radargramsmanager
    project = projectmanager.get_project(project_id)
    if project is not None:
        radargram = radargramsmanager.get_radargram(project_id, radargram_id)
        if radargram is not None:
            traces = radargramsmanager.get_traces_amplitudes(project_id, radargram_id, start_num, finish_num, stage)
            return jsonify({"amplitudes": [list(trace.amplitudes) for trace in traces]})
        else:
            abort(500, f"There is no radargram with radargram_id={radargram_id}")
    else:
        abort(500, f"There is no project with project_id={project_id}")






if __name__ == '__main__':
    app.run()