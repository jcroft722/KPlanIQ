from sqlalchemy import create_engine

# Test both URL formats
urls = [
    'postgresql://postgres:Cooper@localhost:5432/kplan',
    'postgresql+psycopg2://postgres:Cooper@localhost:5432/kplan'
]

for url in urls:
    print(f"\nTesting connection with URL: {url}")
    try:
        engine = create_engine(url)
        with engine.connect() as conn:
            print("Connection successful!")
    except Exception as e:
        print(f"Connection failed: {str(e)}") 