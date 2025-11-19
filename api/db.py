# Simulated in-memory database
DATABASE = {
    "targets": [],
    "groups": [],
    "users": []
}

def generate_id(collection_name):
    return len(DATABASE[collection_name]) + 1
