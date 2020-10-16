from flask import g

from models import db, Project


def get_projects():
    projects = Project.query.filter_by(user_id=g.user.id)
    return projects


def get_project(project_id):
    project = Project.query.filter_by(id=project_id, user_id=g.user.id).first()
    return project


def add_project(name, notes):
    project = Project(name, notes)
    project.user_id = g.user.id
    db.session.add(project)
    db.session.commit()
    return project


def update_project(project_id, name, notes):
    project = Project.query.filter_by(id=project_id, user_id=g.user.id).first()
    project.name = name
    project.notes = notes
    db.session.add(project)
    db.session.commit()
    return project


def delete_project(project_id):
    project = Project.query.filter_by(id=project_id, user_id=g.user.id).first()
    if project is not None:
        db.session.delete(project)
        db.session.commit()
        return True
    else:
        return False
