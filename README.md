## HydraPy
A simple wrapper for thc-hydra in Python.

### Dependency Installation (thc-hydra binary)
```bash
python3 install.py
```

### Usage
- As a library:
```python
from hydrapy import HydraAttack

# Initialize HydraAttack object
hydra = HydraAttack()
result = await attack.run_attack(
    ip,
    hostname,
    protocol,
    login_file=login_file,
    password_file=password_file,
    tasks=tasks,
    port=port,
    stop_on_success=not continue_on_success,
    timeout=timeout
)
```

- As a command line tool:
```bash
python3 hydrapy.py -h

# Using default wordlists for username and password:
python3 hydrapy.py --ip 10.10.10.20 --protocol ssh --port 2222

# Using custom wordlists for username and password:
python3 hydrapy.py --ip --ip 10.10.10.20 --protocol ssh --port 2222 --login-file usernames.txt --password-file passwords.txt
```