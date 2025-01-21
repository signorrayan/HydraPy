import pytest
import asyncio
from unittest.mock import patch, AsyncMock
import json

from hydrapy import HydraAttack, HydraConfig, AttackResult


@pytest.fixture
def hydra_attack():
    return HydraAttack()


@pytest.fixture
def hydra_config():
    return HydraConfig()


@pytest.fixture
def mock_process():
    process = AsyncMock()
    process.stdout = AsyncMock()
    process.stderr = AsyncMock()
    process.returncode = 0
    return process


# Test IP validation
@pytest.mark.parametrize("ip,expected", [
    ("192.168.1.1", True),
    ("256.256.256.256", False),
    ("2001:0db8:85a3:0000:0000:8a2e:0370:7334", True),
    ("invalid_ip", False),
    ("127.0.0.", False),
])
def test_validate_ip(hydra_attack, ip, expected):
    assert hydra_attack.validate_ip(ip) == expected


# Test hostname validation
@pytest.mark.parametrize("hostname,expected", [
    ("example.com", True),
    ("sub.example.com", True),
    ("invalid..com", False),
    ("a" * 256, False),
    ("-invalid.com", False),
])
def test_validate_hostname(hydra_attack, hostname, expected):
    assert hydra_attack.validate_hostname(hostname) == expected


# Test target validation
@pytest.mark.parametrize("ip,hostname,expected", [
    ("192.168.1.1", None, "192.168.1.1"),
    (None, "example.com", "example.com"),
    ("invalid", None, None),
    (None, "invalid..com", None),
    (None, None, None),
])
def test_validate_target(hydra_attack, ip, hostname, expected):
    assert hydra_attack.validate_target(ip, hostname) == expected


# Test credential parsing
@pytest.mark.parametrize("line,expected", [
    (
            "[21][ftp] host: 127.0.0.1   login: admin   password: 123456",
            {
                'port': '21',
                'username': 'admin',
                'password': '123456',
            }
    ),
    (
            "[161][snmp] host: 127.0.0.1 password: public",
            {
                'port': '161',
                'password': 'public'
            }
    ),
    ("invalid line", None),
])
def test_parse_credentials(hydra_attack, line, expected):
    result = hydra_attack._parse_credentials(line)
    if expected is None:
        assert result is None
    else:
        # Remove timestamp for comparison since it will always be different
        actual_timestamp = result.pop('timestamp', None)
        assert actual_timestamp is not None
        assert result == expected  # Compare the rest of the fields


# Test command building
def test_build_command(hydra_attack):
    target = "example.com"
    protocol = "ftp"
    login_file = "logins.txt"
    password_file = "passwords.txt"
    tasks = 16
    port = 21
    stop_on_success = True

    command = hydra_attack._build_command(
        target, protocol, login_file, password_file,
        tasks, port, stop_on_success
    )

    assert command[0] == "hydra"
    assert "-P" in command
    assert str(password_file) in command
    assert "-t" in command
    assert str(tasks) in command
    assert "-f" in command
    assert "-s" in command
    assert str(port) in command
    assert f"{protocol}://{target}" in command


# Test save results
def test_save_results(hydra_attack, tmp_path):
    hydra_attack.results_dir = tmp_path

    result = AttackResult(
        target="example.com",
        protocol="ftp",
        credentials=[{"username": "admin", "password": "password"}],
        start_time=1000.0,
        end_time=1010.0,
        status="success",
        port="21"
    )

    hydra_attack.save_results(result)

    # Check if file was created
    result_files = list(tmp_path.glob("attack_*.json"))
    assert len(result_files) == 1

    # Verify content
    with open(result_files[0]) as f:
        saved_data = json.load(f)
        assert saved_data["target"] == "example.com"
        assert saved_data["protocol"] == "ftp"
        assert saved_data["port"] == "21"
        assert len(saved_data["credentials"]) == 1


@pytest.mark.asyncio
async def test_run_attack_success(hydra_attack, mock_process):
    with patch('asyncio.create_subprocess_exec', return_value=mock_process) as mock_exec:
        # Mock process output
        mock_process.stdout.readline = AsyncMock(side_effect=[
            b"[21][ftp] host: 127.0.0.1   login: admin   password: 123456\n",
            b""
        ])
        mock_process.stderr.readline = AsyncMock(return_value=b"")

        result = await hydra_attack.run_attack(
            ip="127.0.0.1",
            protocol="ftp",
            port=21
        )

        assert result.status == "success"
        assert len(result.credentials) == 1
        assert result.target == "127.0.0.1"
        assert result.protocol == "ftp"
        assert mock_exec.called


@pytest.mark.asyncio
async def test_run_attack_timeout(hydra_attack, mock_process):
    with patch('asyncio.create_subprocess_exec', return_value=mock_process) as mock_exec:
        mock_process.stdout.readline = AsyncMock(side_effect=asyncio.TimeoutError())

        result = await hydra_attack.run_attack(
            ip="127.0.0.1",
            protocol="ftp",
            timeout=1
        )

        assert result.status == "timeout"
        assert result.error is not None
        assert len(result.credentials) == 0


@pytest.mark.asyncio
async def test_run_attack_hydra_not_found(hydra_attack):
    with patch('asyncio.create_subprocess_exec', side_effect=FileNotFoundError()):
        result = await hydra_attack.run_attack(
            ip="127.0.0.1",
            protocol="ftp"
        )

        assert result.status == "failed"
        assert "Hydra is not installed" in result.error


if __name__ == "__main__":
    pytest.main([__file__])