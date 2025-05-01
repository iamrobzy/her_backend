from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

load_dotenv()

def drop_all_tables():
    engine = create_engine(os.getenv("DATABASE_URL"))
    
    with engine.connect() as connection:
        # Drop all tables in public schema
        connection.execute(text("""
            DO $$ 
            DECLARE 
                r RECORD;
            BEGIN
                FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = 'public') LOOP
                    EXECUTE 'DROP TABLE IF EXISTS ' || quote_ident(r.tablename) || ' CASCADE';
                END LOOP;
            END $$;
        """))
        connection.commit()

if __name__ == "__main__":
    drop_all_tables()
    print("All tables dropped successfully")
