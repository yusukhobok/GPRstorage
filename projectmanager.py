from models import db, Project


def get_projects():
    projects = db.session.query(Project).all()
    return projects


def get_project(project_id):
    project = Project.query.filter_by(id=project_id).first()
    return project


def add_project(name):
    project = Project(name, "")
    db.session.add(project)
    db.session.commit()
    return True


def update_project(project_id, name, notes):
    project = Project.query.filter_by(id=project_id).first()
    project.name = name
    project.notes = notes
    db.session.add(project)
    db.session.commit()
    return True


def delete_project(project_id):
    project = Project.query.filter_by(id=project_id).first()
    if project is not None:
        db.session.delete(project)
        db.session.commit()
        return True
    else:
        return False
