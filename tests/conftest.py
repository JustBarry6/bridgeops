import pytest
from fastapi.testclient import TestClient
from sqlalchemy import event
from sqlalchemy.orm import sessionmaker

from app.core.database import Base, engine, get_db
from app.main import app


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture
def db_session():
    """
    Isole chaque test dans une transaction annulée à la fin, même si le code
    testé appelle db.commit() (ce qui est le cas de nos endpoints). On utilise
    un SAVEPOINT imbriqué relancé après chaque commit — pattern recommandé
    par la documentation SQLAlchemy pour les tests d'intégration.
    """
    connection = engine.connect()
    transaction = connection.begin()
    session = sessionmaker(bind=connection)()
    session.begin_nested()

    @event.listens_for(session, "after_transaction_end")
    def restart_savepoint(sess, trans):
        if trans.nested and not trans._parent.nested:
            sess.begin_nested()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()
    

@pytest.fixture
def authenticated_client(client):
    client.post("/auth/register", json={"email": "pytest@example.com", "password": "testpassword123"})
    response = client.post(
        "/auth/login",
        data={"username": "pytest@example.com", "password": "testpassword123"},
    )
    token = response.json()["access_token"]
    client.headers.update({"Authorization": f"Bearer {token}"})
    return client