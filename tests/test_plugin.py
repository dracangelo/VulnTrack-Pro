from api.services.plugin_loader import PluginLoader
import json

def test_plugin():
    loader = PluginLoader()
    print("Available plugins:", loader.list_plugins())
    
    print("\nRunning example_plugin...")
    result = loader.run_plugin('example_plugin', '127.0.0.1', {'custom_arg': 'test'})
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    test_plugin()
