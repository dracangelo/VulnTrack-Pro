import os

def test_write():
    path = os.path.join(os.getcwd(), 'instance', 'test.txt')
    print(f"Trying to write to {path}")
    try:
        with open(path, 'w') as f:
            f.write("Hello")
        print("Write successful")
        os.remove(path)
        print("Delete successful")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    test_write()
