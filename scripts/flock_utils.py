#!/usr/bin/env python3
"""
flock_utils.py - Shared flock locking utilities for Python cron scripts
Usage: Use the @with_flock decorator or FlockLock context manager
"""

import fcntl
import os
import sys
from pathlib import Path
from functools import wraps
from contextlib import contextmanager

# Default lock directory
LOCK_DIR = Path("/tmp/openclaw-locks")
LOCK_DIR.mkdir(parents=True, exist_ok=True)


class FlockLock:
    """
    Context manager for file-based locking using flock.
    
    Usage:
        with FlockLock("my_script"):
            # Your code here - only one instance runs at a time
            pass
    """
    
    def __init__(self, name: str, timeout: int = 0, blocking: bool = False):
        """
        Initialize the lock.
        
        Args:
            name: Unique name for this lock (usually the script name)
            timeout: Seconds to wait for lock (0 = no timeout)
            blocking: If True, wait indefinitely for lock
        """
        self.name = name
        self.lock_file = LOCK_DIR / f"{name}.lock"
        self.timeout = timeout
        self.blocking = blocking
        self.fd = None
        self.acquired = False
    
    def __enter__(self):
        """Acquire the lock when entering context."""
        self.fd = open(self.lock_file, 'w')
        
        try:
            if self.blocking:
                # Blocking lock
                fcntl.flock(self.fd.fileno(), fcntl.LOCK_EX)
            elif self.timeout > 0:
                # Non-blocking with timeout
                import time
                start = time.time()
                while True:
                    try:
                        fcntl.flock(self.fd.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                        break
                    except (IOError, OSError):
                        if time.time() - start >= self.timeout:
                            raise TimeoutError(f"Could not acquire lock '{self.name}' after {self.timeout}s")
                        time.sleep(0.1)
            else:
                # Non-blocking, fail immediately if locked
                fcntl.flock(self.fd.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            
            # Write our PID to the lock file
            self.fd.write(str(os.getpid()))
            self.fd.flush()
            self.acquired = True
            
        except (IOError, OSError) as e:
            self.fd.close()
            self.fd = None
            raise LockHeldError(f"Lock '{self.name}' is held by another process") from e
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Release the lock when exiting context."""
        if self.fd:
            try:
                fcntl.flock(self.fd.fileno(), fcntl.LOCK_UN)
                self.fd.close()
            except:
                pass
            self.fd = None
        self.acquired = False
        return False


class LockHeldError(Exception):
    """Raised when a lock is already held by another process."""
    pass


@contextmanager
def acquire_lock(name: str, timeout: int = 0, blocking: bool = False):
    """
    Context manager to acquire a lock.
    
    Args:
        name: Unique name for this lock
        timeout: Seconds to wait (0 = no wait)
        blocking: If True, block until lock is available
    
    Raises:
        LockHeldError: If lock cannot be acquired
        TimeoutError: If timeout is reached
    
    Usage:
        with acquire_lock("my_script"):
            # Only one instance runs at a time
            pass
    """
    lock = FlockLock(name, timeout=timeout, blocking=blocking)
    try:
        lock.__enter__()
        yield lock
    finally:
        lock.__exit__(None, None, None)


def with_flock(name: str, skip_on_locked: bool = True):
    """
    Decorator to ensure only one instance of a function runs at a time.
    
    Args:
        name: Unique name for this lock
        skip_on_locked: If True, silently exit when lock is held. 
                       If False, raise LockHeldError.
    
    Usage:
        @with_flock("my_script")
        def main():
            # Only one instance runs at a time
            pass
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                with acquire_lock(name):
                    return func(*args, **kwargs)
            except LockHeldError:
                if skip_on_locked:
                    print(f"[{name}] Lock held by another instance, skipping")
                    return None
                raise
        return wrapper
    return decorator


def try_lock(name: str) -> bool:
    """
    Try to acquire a lock without blocking.
    
    Args:
        name: Unique name for this lock
    
    Returns:
        True if lock was acquired, False otherwise
    """
    try:
        with acquire_lock(name, timeout=0):
            return True
    except LockHeldError:
        return False
