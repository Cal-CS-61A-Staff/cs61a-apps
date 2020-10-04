import enum
import json
import os
import pickle
import sys
from datetime import datetime

sys.path.append(os.path.abspath("../oh_queue"))
sys.path.append(os.path.abspath(".."))
os.chdir("..")

import models
from oh_queue import app

app.config["SQLALCHEMY_DATABASE_URL"] = os.getenv("DATABASE_URL")

EXPORTING = False


def dump(obj):
    fields = {}
    for field in [x for x in dir(obj) if not x.startswith("_") and x != "metadata"]:
        if field + "_id" in dir(obj):
            fields[field] = None
            continue
        data = obj.__getattribute__(field)
        try:
            if not isinstance(data, datetime) and not isinstance(data, enum.Enum):
                json.dumps(data)
            fields[field] = data
        except TypeError:
            continue

    return fields


out = {}

MIGRATED_COURSES = ["cs61a", "cs61c"]

OBJECTS = [
    models.User,
    models.ConfigEntry,
    models.Assignment,
    models.Location,
    models.Ticket,
    models.TicketEvent,
    models.Appointment,
    models.AppointmentSignup,
    models.Group,
    models.GroupAttendance,
    models.ChatMessage,
]

FIELD_MAP = {"helper": "user"}

if EXPORTING:
    with app.app_context():
        for cls in OBJECTS:
            print(cls, file=sys.stderr)
            out[cls.__tablename__] = {}
            for obj in cls.query.all():
                if obj.course in MIGRATED_COURSES:
                    continue
                out[cls.__tablename__][obj.id] = dump(obj)

    with open("scripts/oh2.json", "wb") as f:
        pickle.dump(out, f)

if not EXPORTING:
    with open("scripts/oh2.json", "rb") as f:
        data = pickle.load(f)
    with app.app_context():
        lookup = {}
        cache = {}
        live_objects = {}
        for cls in OBJECTS:
            lookup[cls.__tablename__] = {}
            cache[cls.__tablename__] = {}
            live_objects[cls.__tablename__] = {obj.id: obj for obj in cls.query.all()}
            for obj in data[cls.__tablename__].values():
                id = obj.pop("id")
                if (
                    id in live_objects[cls.__tablename__]
                    and live_objects[cls.__tablename__][id].course == obj["course"]
                ):
                    # it's the same object, no need to upload
                    continue

                # need to duplicate
                print(id, obj)

                obj.pop("get_id", None)
                obj.pop("is_authenticated", None)
                obj.pop("is_anonymous", None)
                obj.pop("is_active", None)
                obj.pop("heartbeat_time", None)
                obj.pop("short_name", None)

                for field in list(obj.keys()):
                    if "_id" in field:
                        # lookup ORM object
                        target_id = obj.pop(field)
                        obj_field_name = field[:-3]
                        model_name = FIELD_MAP.get(obj_field_name, obj_field_name)
                        if target_id in lookup[model_name]:
                            obj[obj_field_name] = lookup[model_name][target_id]
                            assert obj["course"] == obj[obj_field_name].course
                        else:
                            [target_cls] = (
                                cls
                                for cls in OBJECTS
                                if cls.__tablename__ == model_name
                            )
                            if target_id is not None:
                                obj[obj_field_name] = live_objects[model_name][
                                    target_id
                                ]
                                assert obj["course"] == obj[obj_field_name].course, (
                                    obj[obj_field_name].course,
                                    obj_field_name,
                                )
                            else:
                                obj[obj_field_name] = None

                obj = cls(**obj)  # hydrate SQLAlchemy object
                models.db.session.add(obj)
                lookup[cls.__tablename__][id] = obj
        models.db.session.commit()
