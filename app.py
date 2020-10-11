import os
from flask import Flask, request, jsonify, abort, url_for, g
from flask_sqlalchemy import SQLAlchemy
from flask_httpauth import HTTPBasicAuth
from werkzeug.utils import secure_filename
from transliterate import translit


app = Flask(__name__)
app.config.from_object(os.environ['APP_SETTINGS'])
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
auth = HTTPBasicAuth()


@app.route('/api/users', methods = ['POST'])
def new_user():
    from models import User
    username = request.json.get('username')
    password = request.json.get('password')
    if username is None or password is None:
        abort(400)
    if User.query.filter_by(username=username).first() is not None:
        abort(400)
    user = User(username=username)
    user.hash_password(password)
    db.session.add(user)
    db.session.commit()
    return jsonify({ 'username': user.username }), 201, {'Location': url_for('get_user', id = user.id, _external = True)}


@app.route('/api/users/<int:id>')
def get_user(id):
    from models import User
    user = User.query.get(id)
    if not user:
        abort(400)
    return jsonify({'username': user.username})


@auth.verify_password
def verify_password(username, password):
    from models import User
    user = User.query.filter_by(username = username).first()
    if not user or not user.verify_password(password):
        return False
    g.user = user
    return True


@app.route('/projects', methods=['GET'])
@auth.login_required
def get_projects():
    import projectmanager
    projects = projectmanager.get_projects()
    return jsonify({"projects": [project.serialize for project in projects]})


@app.route('/projects/<int:project_id>', methods=['GET'])
@auth.login_required
def get_project(project_id: int):
    import projectmanager
    project = projectmanager.get_project(project_id)
    if project is not None:
        return jsonify(project.serialize)
    else:
        return jsonify({"Error": f"There is no project with project_id={project_id}"})


@app.route('/projects', methods=['POST'])
@auth.login_required
def add_project():
    import projectmanager
    data = request.form
    try:
        name = data["name"]
        ok = projectmanager.add_project(name)
        if ok:
            return "Add project"
        else:
            return jsonify({"Error": "Refuse adding project"})
    except KeyError:
        return jsonify({"Error": "There is no project name"})


@app.route('/projects/<int:project_id>', methods=['PUT'])
@auth.login_required
def update_project(project_id: int):
    import projectmanager
    data = request.form
    try:
        name = data["name"]
        notes = data["notes"]
        ok = projectmanager.update_project(project_id, name, notes)
        if ok:
            return "Update project"
        else:
            return jsonify({"Error": "Refuse updating project"})
    except KeyError:
        return jsonify({"Error": "There is no project name or project notes"})


@app.route('/projects/<int:project_id>', methods=['DELETE'])
@auth.login_required
def delete_project(project_id: int):
    import projectmanager
    ok = projectmanager.delete_project(project_id)
    if ok:
        return "Delete project"
    else:
        return jsonify({"Error": f"There is no project with project_id='{id}'"})


@app.route('/projects/<int:project_id>/radargrams', methods=['GET'])
@auth.login_required
def get_radargrams(project_id: int):
    import projectmanager, radargramsmanager
    project = projectmanager.get_project(project_id)
    if project is not None:
        radargrams = radargramsmanager.get_radargrams(project_id)
        return jsonify({"radargrams": [radargram.serialize for radargram in radargrams]})
    else:
        return jsonify({"Error": f"There is no project with project_id={id}"})


@app.route('/projects/<int:project_id>/radargrams/<int:radargram_id>', methods=['GET'])
@auth.login_required
def get_radargram(project_id: int, radargram_id: int):
    import projectmanager, radargramsmanager
    project = projectmanager.get_project(project_id)
    if project is not None:
        radargram = radargramsmanager.get_radargram(project_id, radargram_id)
        if radargram is not None:
            return jsonify(radargram.serialize)
        else:
            return jsonify({"Error": f"There is no radargram with radargram_id={radargram_id}"})
    else:
        return jsonify({"Error": f"There is no project with project_id={project_id}"})


@app.route('/projects/<int:project_id>/radargrams', methods=['POST'])
@auth.login_required
def add_radargram(project_id: int):
    import projectmanager, radargramsmanager
    project = projectmanager.get_project(project_id)
    if project is not None:
        if 'datafile' not in request.files:
            return jsonify({"Error": "File is not send (1)"})
        file = request.files['datafile']
        if not file:
            return jsonify({"Error": "File is not send (2)"})

        basename = os.path.basename(file.filename)
        filename = translit(file.filename, 'ru', reversed=True)
        filename = secure_filename(filename)
        filename = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filename)
        ok = radargramsmanager.add_radargram(project_id, filename, basename)
        if ok:
            return "Add radargram"
        else:
            return jsonify({"Error": "Refuse adding radargram"})
    else:
        return jsonify({"Error": f"There is no project with project_id={id}"})


@app.route('/projects/<int:project_id>/radargrams/<int:radargram_id>', methods=['DELETE'])
@auth.login_required
def delete_radargram(project_id: int, radargram_id: int):
    import projectmanager, radargramsmanager
    project = projectmanager.get_project(project_id)
    if project is not None:
        ok = radargramsmanager.delete_radargram(project_id, radargram_id)
        if ok:
            return "Delete radargram"
        else:
            return jsonify({"Error": "Refuse deleting radargram"})
    else:
        return jsonify({"Error": f"There is no project with project_id={id}"})


@app.route('/projects/<int:project_id>/radargrams/<int:radargram_id>/traces/headers', methods=['GET'])
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
            return jsonify({"Error": f"There is no radargram with radargram_id={radargram_id}"})
    else:
        return jsonify({"Error": f"There is no project with project_id={id}"})


@app.route('/projects/<int:project_id>/radargrams/<int:radargram_id>/traces/<int:trace_id>', methods=['GET'])
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
                return jsonify({"Error": f"There is no trace with trace_id={trace_id}"})
        else:
            return jsonify({"Error": f"There is no radargram with radargram_id={radargram_id}"})
    else:
        return jsonify({"Error": f"There is no project with project_id={id}"})


@app.route('/projects/<int:project_id>/radargrams/<int:radargram_id>/traces/amplitudes/<int:start_num>/<int:finish_num>/<int:stage>', methods=['GET'])
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
            return jsonify({"Error": f"There is no radargram with radargram_id={radargram_id}"})
    else:
        return jsonify({"Error": f"There is no project with project_id={id}"})






if __name__ == '__main__':
    app.run()