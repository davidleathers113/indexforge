# Docker Testing Framework Refactoring TODO

## Remaining Test Categories to Refactor

### 1. Runtime Tests

- ✅ `test_container_startup.py` (exists)
- ✅ `test_health_checks.py` (exists)
- 🔲 Need to create:
  - `test_logging.py` - Log output validation
  - `test_signal_handling.py` - Container signal responses
  - `test_environment.py` - Environment variable handling

### 2. Resource Management Tests

- ✅ `test_resource_limits.py` (exists)
- 🔲 Need to create:
  - `test_memory_management.py` - Detailed memory behavior
  - `test_cpu_scheduling.py` - CPU allocation and throttling
  - `test_disk_io.py` - Storage I/O limits

### 3. Storage Tests

- 🔲 Need to split into:
  - `test_volume_persistence.py` - Data persistence
  - `test_volume_permissions.py` - Access controls
  - `test_volume_sharing.py` - Multi-container volume usage
  - `test_tmpfs_mounts.py` - Temporary storage

### 4. Security Tests

- 🔲 Need to create:
  - `test_capabilities.py` - Linux capabilities
  - `test_seccomp.py` - Syscall filtering
  - `test_user_namespace.py` - User mapping
  - `test_apparmor.py` - AppArmor profiles

### 5. Cleanup Tests

- 🔲 Need to create:
  - `test_container_cleanup.py` - Container removal
  - `test_volume_cleanup.py` - Volume cleanup
  - `test_network_cleanup.py` - Network cleanup
  - `test_image_cleanup.py` - Image removal

## Progress Tracking

- ✅ Completed
- 🔲 To Do

## Guidelines for New Test Files

1. Each file should have a single responsibility
2. Keep files under 100 lines (excluding docstrings)
3. Include proper error handling
4. Use specific exception types
5. Maintain clear test boundaries
