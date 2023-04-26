import os, json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import date

from db_models import Model, Operation

def manual_db_load(MODEL_DIR):
    for model in os.listdir(MODEL_DIR):
        r = open(f"{MODEL_DIR}/{model}", "r")
        data = json.load(r)

        session = load_session()
        if session.query(Model).filter(Model.uid == data['metadata']['uid']).first() is None:
            model = Model(
                uid=data['metadata']['uid'],
                model_metadata=data['metadata'],
                first_seen=date.today(),
                last_seen=date.today()
            )
            session.add(model)
            session.commit()

        # Need to iterate through all operations and check if we know about them.
        model = session.query(Model).filter(Model.uid == data['metadata']['uid']).first()
        operations = []
        for operation in data['operations'].items():
            exists = any(operation[0] == op.name for op in model.operations)
            if not exists:
                # Check if the download_location exists
                download_locations = []

                operations.append(Operation(
                    name=operation[0],
                    operation_metadata=operation[1],
                    first_seen=date.today(),
                    last_seen=date.today(),
                    download_locations=download_locations
                ))

        model.operations += operations

        session.add(model)
        session.commit()


def add_model(model):
    session = load_session()

    model = Model(
        uid=model['metadata']['uid'],
        model_metadata=model['metadata'],
        first_seen=date.today(),
        last_seen=date.today()
    )
    session.add(model)
    session.commit()


def load_session():
    engine = create_engine(
        'sqlite:///models.db'
    )
    Session = sessionmaker(bind=engine)
    return Session()