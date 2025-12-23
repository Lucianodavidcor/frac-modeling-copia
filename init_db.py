from app.db.session import engine, Base
from app.models.well_models import Project, Well

def init():
    print("Creando tablas en la base de datos...")
    Base.metadata.create_all(bind=engine)
    print("¡Tablas creadas con éxito!")

if __name__ == "__main__":
    init()