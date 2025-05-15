"""
Unit tests for the OPS Portal API module using pytest.
"""

import pytest
from unittest.mock import MagicMock
import requests
from ops_api.ops_portal.api import OpsPortalClient, send


@pytest.fixture
def valid_config():
    """Fixture for valid configuration."""
    return {
        'auth_url': 'https://test-auth-url.com',
        'item_url': 'https://test-item-url.com',
        'client_id': 'test_client_id',
        'client_secret': 'test_client_secret',
        'verify_ssl': False
    }


@pytest.fixture
def test_record():
    """Fixture for a test record."""
    return {
        'tenantItemID': 'test_id_123',
        'title': 'Test Record',
        'description': 'This is a test record'
    }


@pytest.fixture
def test_records():
    """Fixture for test records."""
    return [
        {
            'tenantItemID': 'test_id_1',
            'title': 'Test Record 1',
            'description': 'This is test record 1'
        },
        {
            'tenantItemID': 'test_id_2',
            'title': 'Test Record 2',
            'description': 'This is test record 2'
        }
    ]


def test_init_with_valid_config(valid_config):
    """Test initialization with valid configuration."""
    client = OpsPortalClient(valid_config)
    
    assert client.auth_url == valid_config['auth_url']
    assert client.item_url == valid_config['item_url']
    assert client.client_id == valid_config['client_id']
    assert client.client_secret == valid_config['client_secret']
    assert client.verify_ssl == valid_config['verify_ssl']
    assert client.token is None
    
    # Check session headers
    assert client.session.headers['Accept'] == 'application/json'
    assert client.session.headers['Content-Type'] == 'application/json'
    assert client.session.verify == False


def test_init_with_missing_auth_url(valid_config):
    """Test initialization with missing auth_url."""
    invalid_config = valid_config.copy()
    invalid_config.pop('auth_url')
    
    with pytest.raises(ValueError) as excinfo:
        OpsPortalClient(invalid_config)
    
    assert "Missing required configuration: auth_url" in str(excinfo.value)


def test_init_with_missing_item_url(valid_config):
    """Test initialization with missing item_url."""
    invalid_config = valid_config.copy()
    invalid_config.pop('item_url')
    
    with pytest.raises(ValueError) as excinfo:
        OpsPortalClient(invalid_config)
    
    assert "Missing required configuration: item_url" in str(excinfo.value)


def test_init_with_default_values():
    """Test initialization with default values."""
    minimal_config = {
        'auth_url': 'https://test-auth-url.com',
        'item_url': 'https://test-item-url.com'
    }
    
    client = OpsPortalClient(minimal_config)
    
    assert client.client_id == ''
    assert client.client_secret == ''
    assert client.verify_ssl == True


def test_authenticate_success(valid_config, monkeypatch):
    """Test successful authentication."""
    # Mock the response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = "test_token"
    
    # Mock the post method
    def mock_post(self, url, **kwargs):
        assert url == valid_config['auth_url']
        assert kwargs['json'] == {
            'clientId': valid_config['client_id'],
            'clientSecret': valid_config['client_secret']
        }
        return mock_response
    
    monkeypatch.setattr('requests.Session.post', mock_post)
    
    client = OpsPortalClient(valid_config)
    result = client.authenticate()
    
    # Verify the result
    assert result is True
    assert client.token == "test_token"
    assert client.session.headers['Authorization'] == 'Bearer test_token'


def test_authenticate_failure(valid_config, monkeypatch):
    """Test authentication failure."""
    # Mock the post method to raise an exception
    def mock_post(self, url, **kwargs):
        raise requests.exceptions.RequestException("Authentication failed")
    
    monkeypatch.setattr('requests.Session.post', mock_post)
    
    client = OpsPortalClient(valid_config)
    result = client.authenticate()
    
    # Verify the result
    assert result is False
    assert client.token is None


def test_send_record_success(valid_config, test_record, monkeypatch):
    """Test successful sending of a record."""
    # Mock the response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"status": "success"}
    
    # Mock the post method
    def mock_post(self, url, **kwargs):
        assert url == valid_config['item_url']
        assert kwargs['json'] == test_record
        return mock_response
    
    monkeypatch.setattr('requests.Session.post', mock_post)
    
    client = OpsPortalClient(valid_config)
    client.token = "test_token"  # Set token manually for testing
    
    status_code, response_data = client.send_record(test_record)
    
    # Verify the result
    assert status_code == 200
    assert response_data == {"status": "success"}


def test_send_record_failure(valid_config, test_record, monkeypatch):
    """Test failure when sending a record."""
    # Mock the response
    mock_response = MagicMock()
    mock_response.status_code = 400
    mock_response.json.return_value = {"error": "Bad request"}
    
    # Mock the post method
    def mock_post(self, url, **kwargs):
        return mock_response
    
    monkeypatch.setattr('requests.Session.post', mock_post)
    
    client = OpsPortalClient(valid_config)
    client.token = "test_token"  # Set token manually for testing
    
    status_code, response_data = client.send_record(test_record)
    
    # Verify the result
    assert status_code == 400
    assert response_data == {"error": "Bad request"}


def test_send_record_exception(valid_config, test_record, monkeypatch):
    """Test exception handling when sending a record."""
    # Mock the post method to raise an exception
    def mock_post(self, url, **kwargs):
        raise requests.exceptions.RequestException("Connection error")
    
    monkeypatch.setattr('requests.Session.post', mock_post)
    
    client = OpsPortalClient(valid_config)
    client.token = "test_token"  # Set token manually for testing
    
    status_code, response_data = client.send_record(test_record)
    
    # Verify the result
    assert status_code == 0
    assert response_data == "Connection error"


def test_send_records_success(valid_config, test_records, monkeypatch):
    """Test successful sending of multiple records."""
    # Mock the authenticate method
    def mock_authenticate(self):
        self.token = "test_token"
        return True
    
    monkeypatch.setattr(OpsPortalClient, 'authenticate', mock_authenticate)
    
    # Mock the send_record method
    send_record_calls = []
    def mock_send_record(self, record):
        send_record_calls.append(record)
        return (200, {"status": "success"})
    
    monkeypatch.setattr(OpsPortalClient, 'send_record', mock_send_record)
    
    client = OpsPortalClient(valid_config)
    responses = client.send_records(test_records)
    
    # Verify the result
    assert len(responses) == 2
    assert responses['test_id_1'] == (200, {"status": "success"})
    assert responses['test_id_2'] == (200, {"status": "success"})
    
    # Verify the send_record method was called for each record
    assert len(send_record_calls) == 2
    assert send_record_calls[0] == test_records[0]
    assert send_record_calls[1] == test_records[1]


def test_send_records_with_token(valid_config, test_records, monkeypatch):
    """Test sending records when token is already set."""
    # Mock the authenticate method
    authenticate_called = False
    def mock_authenticate(self):
        nonlocal authenticate_called
        authenticate_called = True
        return True
    
    monkeypatch.setattr(OpsPortalClient, 'authenticate', mock_authenticate)
    
    # Mock the send_record method
    send_record_calls = []
    def mock_send_record(self, record):
        send_record_calls.append(record)
        return (200, {"status": "success"})
    
    monkeypatch.setattr(OpsPortalClient, 'send_record', mock_send_record)
    
    client = OpsPortalClient(valid_config)
    client.token = "test_token"  # Set token manually for testing
    responses = client.send_records(test_records)
    
    # Verify the authenticate method was not called
    assert authenticate_called is False
    
    # Verify the send_record method was called for each record
    assert len(send_record_calls) == 2


def test_send_records_authentication_failure(valid_config, test_records, monkeypatch):
    """Test sending records when authentication fails."""
    # Mock the authenticate method to fail
    def mock_authenticate(self):
        return False
    
    monkeypatch.setattr(OpsPortalClient, 'authenticate', mock_authenticate)
    
    client = OpsPortalClient(valid_config)
    responses = client.send_records(test_records)
    
    # Verify the result
    assert len(responses) == 2
    assert responses['test_id_1'] == (0, "Authentication failed")
    assert responses['test_id_2'] == (0, "Authentication failed")


def test_send_function(valid_config, test_records, monkeypatch):
    """Test the standalone send function."""
    # Mock the send_records method
    send_records_called_with = None
    def mock_send_records(self, records):
        nonlocal send_records_called_with
        send_records_called_with = records
        return {
            'test_id_1': (200, {"status": "success"}),
            'test_id_2': (200, {"status": "success"})
        }
    
    monkeypatch.setattr(OpsPortalClient, 'send_records', mock_send_records)
    
    responses = send(test_records, valid_config)
    
    # Verify the result
    assert responses == {
        'test_id_1': (200, {"status": "success"}),
        'test_id_2': (200, {"status": "success"})
    }
    
    # Verify the send_records method was called with the correct records
    assert send_records_called_with == test_records


def test_send_function_with_default_config(test_records, monkeypatch):
    """Test the standalone send function with default configuration."""
    # Mock the send_records method
    send_records_called_with = None
    def mock_send_records(self, records):
        nonlocal send_records_called_with
        send_records_called_with = records
        return {
            'test_id_1': (200, {"status": "success"}),
            'test_id_2': (200, {"status": "success"})
        }
    
    monkeypatch.setattr(OpsPortalClient, 'send_records', mock_send_records)
    
    responses = send(test_records)
    
    # Verify the send_records method was called with the correct records
    assert send_records_called_with == test_records
