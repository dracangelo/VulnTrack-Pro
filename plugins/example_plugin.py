def run(target, args=None):
    """
    Example plugin that checks if a specific port is open (mock).
    """
    print(f"Running example plugin on {target} with args: {args}")
    
    # Mock logic
    return {
        'plugin': 'example_plugin',
        'target': target,
        'status': 'success',
        'results': {
            'message': 'This is a custom plugin result',
            'args_received': args
        }
    }
