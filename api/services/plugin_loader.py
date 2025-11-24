import importlib.util
import os
import json

class PluginLoader:
    def __init__(self, plugin_dir='plugins'):
        self.plugin_dir = plugin_dir

    def load_plugin(self, plugin_name):
        """
        Loads a python plugin module by name (filename without extension).
        """
        file_path = os.path.join(self.plugin_dir, f"{plugin_name}.py")
        if not os.path.exists(file_path):
            return None

        spec = importlib.util.spec_from_file_location(plugin_name, file_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def run_plugin(self, plugin_name, target, args=None):
        """
        Runs the 'run' function of a plugin.
        """
        module = self.load_plugin(plugin_name)
        if not module:
            return {'error': f'Plugin {plugin_name} not found'}

        if not hasattr(module, 'run'):
            return {'error': f'Plugin {plugin_name} does not have a run function'}

        try:
            return module.run(target, args)
        except Exception as e:
            return {'error': f'Error running plugin {plugin_name}: {str(e)}'}

    def list_plugins(self):
        """
        Lists available plugins in the plugins directory.
        """
        plugins = []
        if not os.path.exists(self.plugin_dir):
            return plugins
            
        for filename in os.listdir(self.plugin_dir):
            if filename.endswith('.py') and filename != '__init__.py':
                plugins.append(filename[:-3])
        return plugins
